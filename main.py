# main.py
import os
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from spendwise.utils.csv_parser import parse_csv
from spendwise.utils.excel_parser import parse_excel
from spendwise.utils.pdf_parser import parse_pdf
from spendwise.utils.data_storage import save_transactions_jsonl, load_transactions_jsonl, DEFAULT_TRANSACTIONS_FILE
import logging
from collections import defaultdict
from datetime import datetime
import re # For date parsing fallback in monthly_trend

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_FOLDER = os.path.join('spendwise', 'data', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'spendwise', 'templates'),
            static_folder=os.path.join(BASE_DIR, 'spendwise', 'static'))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey_for_spendwise_app'

ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'transaction_file' not in request.files:
        flash('No file part in the request.', 'error')
        return redirect(url_for('index'))
    file = request.files['transaction_file']
    if file.filename == '':
        flash('No file selected.', 'info')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(file_path)
            parser_result = {'transactions': [], 'success_count': 0, 'skipped_count': 0}
            file_ext = filename.rsplit('.', 1)[1].lower(); file_processed = False
            if file_ext == 'csv':
                parser_result = parse_csv(file_path); file_processed = True
            elif file_ext in ['xls', 'xlsx']:
                parser_result = parse_excel(file_path); file_processed = True
            elif file_ext == 'pdf':
                parser_result = parse_pdf(file_path); file_processed = True

            transactions = parser_result.get('transactions', [])
            success_count = parser_result.get('success_count', 0)
            skipped_count = parser_result.get('skipped_count', 0)

            if file_processed:
                if success_count > 0:
                    flash(f"Successfully imported {success_count} records from {filename}.", 'success')
                    if skipped_count > 0:
                        flash(f"{skipped_count} records from {filename} were skipped or could not be fully processed.", 'warning') # Changed to warning
                    if save_transactions_jsonl(transactions, DEFAULT_TRANSACTIONS_FILE):
                        logging.info(f"Saved {success_count} transactions.")
                    else:
                        flash("Critical: Failed to save processed transactions.", 'error')
                        logging.error(f"Critical: Failed to save {success_count} transactions from {filename} to storage.")
                elif skipped_count > 0:
                     flash(f"Processed {filename}: No records were imported. {skipped_count} records were skipped or could not be fully processed.", 'warning') # Changed to warning
                     logging.info(f"From {filename}: No records imported, {skipped_count} skipped.")
                else:
                    flash(f"Could not extract any transaction data from {filename}. The file might be empty, not contain recognizable transaction information, or be in an unsupported structure for its type.", 'info')
                    logging.info(f"No transactions or processable data found in {filename}.")
        except Exception as e:
            logging.error(f"Critical error during upload/processing for {filename}: {e}", exc_info=True)
            flash(f'Critical error processing {filename}: {e}', 'error')
        return redirect(url_for('index'))
    else:
        file_ext_raw = file.filename.rsplit(".", 1);
        file_type_msg = f'"{file_ext_raw[1]}"' if len(file_ext_raw) > 1 else "selected"
        flash(f'File type {file_type_msg} not allowed. Please upload CSV, Excel, or PDF files.', 'error')
        return redirect(url_for('index'))

@app.route('/view_data')
def view_data_page():
    return render_template('data_view.html')

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    logging.info("API call to /api/transactions received.")
    try:
        transactions = load_transactions_jsonl(DEFAULT_TRANSACTIONS_FILE)
        for tx in transactions:
            if hasattr(tx.get('amount'), 'quantize'):
                tx['amount'] = float(tx['amount'])
        return jsonify(transactions)
    except Exception as e:
        logging.error(f"Error loading transactions for API: {e}", exc_info=True)
        return jsonify({"error": "Could not load transactions"}), 500

@app.route('/dashboard')
def dashboard_page():
    """Renders the dashboard page."""
    return render_template('dashboard.html')

# --- Dashboard API Endpoints ---
@app.route('/api/dashboard/total_spent', methods=['GET'])
def get_total_spent():
    transactions = load_transactions_jsonl(DEFAULT_TRANSACTIONS_FILE)
    total = sum(float(tx['amount']) for tx in transactions if tx.get('amount') and float(tx['amount']) > 0)
    return jsonify({'total_spent': round(total, 2)})

@app.route('/api/dashboard/monthly_trend', methods=['GET'])
def get_monthly_trend():
    transactions = load_transactions_jsonl(DEFAULT_TRANSACTIONS_FILE)
    monthly_data = defaultdict(float)
    for tx in transactions:
        try:
            amount = float(tx.get('amount', 0))
            if amount <= 0:
                continue
            date_str = tx.get('date')
            if not date_str: continue

            year_month = None
            try:
                dt_obj = datetime.strptime(date_str, '%Y-%m-%d')
                year_month = dt_obj.strftime('%Y-%m')
            except ValueError:
                try:
                    dt_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    year_month = dt_obj.strftime('%Y-%m')
                except ValueError:
                    try:
                         dt_obj = datetime.strptime(date_str, '%d/%m/%Y')
                         year_month = dt_obj.strftime('%Y-%m')
                    except ValueError:
                        if re.match(r'^\d{4}-\d{2}', date_str): # Check YYYY-MM...
                             year_month = date_str[:7]
                        else:
                            logging.warning(f"Could not parse date '{date_str}' for monthly trend.")
                            continue
            if year_month:
                monthly_data[year_month] += amount
        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping transaction in monthly trend due to data error: {tx}, Error: {e}")
            continue

    trend = [{'month': month, 'total': round(total, 2)} for month, total in sorted(monthly_data.items())]
    return jsonify(trend)

@app.route('/api/dashboard/category_breakdown', methods=['GET'])
def get_category_breakdown():
    transactions = load_transactions_jsonl(DEFAULT_TRANSACTIONS_FILE)
    category_data = defaultdict(float)
    for tx in transactions:
        try:
            amount = float(tx.get('amount', 0))
            if amount <= 0:
                continue
            category = tx.get('category', 'Miscellaneous')
            category_data[category] += amount
        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping transaction in category breakdown due to data error: {tx}, Error: {e}")
            continue

    breakdown = [{'category': cat, 'total': round(total, 2)} for cat, total in sorted(category_data.items(), key=lambda item: item[1], reverse=True)]
    return jsonify(breakdown)

if __name__ == '__main__':
    app.run(debug=True)
