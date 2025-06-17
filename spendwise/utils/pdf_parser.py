# spendwise/utils/pdf_parser.py
import sys
import os # For __main__ example and path manipulation
if not __package__ and not hasattr(sys, 'frozen'):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

import pdfplumber
import logging
import re
from decimal import Decimal, InvalidOperation
from spendwise.utils.categorizer import categorize_transaction # Import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PDF_HEADER_KEYWORDS = {
    'date': ['date', 'day', 'time', 'when'],
    'description': ['description', 'details', 'narrative', 'memo', 'activity', 'item'],
    'amount': ['amount', 'value', 'sum', 'total', 'credit', 'debit', 'price', 'cost']
}
AMOUNT_REGEX = re.compile(r'([\$€£]?\s*-?[\d,]+\.?\d{0,2})')

def clean_text(text):
    if text is None: return ""
    return str(text).replace('\n', ' ').strip()

def looks_like_date(text):
    text = clean_text(text)
    return bool(re.match(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,}\s+\d{2,4})', text))

def parse_amount(text):
    if text is None: return None
    text = clean_text(str(text))
    cleaned_text = text.replace('$', '').replace('€', '').replace('£', '').replace('USD', '').replace('EUR', '').replace('GBP', '').strip()
    if re.search(r'\d,\d{3}\.\d{2}', cleaned_text):
        cleaned_text = cleaned_text.replace(',', '')
    elif re.search(r'\d\.\d{3},\d{2}', cleaned_text):
        cleaned_text = cleaned_text.replace('.', '').replace(',', '.')
    else:
        cleaned_text = cleaned_text.replace(',', '')
    try:
        return Decimal(cleaned_text)
    except InvalidOperation:
        match = AMOUNT_REGEX.search(text)
        if match:
            try:
                num_str = match.group(1).replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
                return Decimal(num_str)
            except InvalidOperation: pass
        # logging.warning(f"Could not parse '{text}' as a decimal amount.") # Reduced verbosity for this helper
        return None

def row_data_has_column(row_data, col_idx):
    return row_data and col_idx is not None and len(row_data) > col_idx

def identify_columns(table_data, num_header_rows_to_check=3):
    if not table_data or not table_data[0] : return None
    col_indices = {'date': None, 'description': None, 'amount': None}
    num_cols = len(table_data[0])

    for row_idx, row in enumerate(table_data[:num_header_rows_to_check]):
        if not row: continue
        for col_idx, cell_text in enumerate(row):
            if cell_text is None: continue
            text_lower = clean_text(cell_text).lower()
            for canonical_name, keywords in PDF_HEADER_KEYWORDS.items():
                if col_indices[canonical_name] is None and any(keyword in text_lower for keyword in keywords):
                    col_indices[canonical_name] = col_idx
                    break

    if any(v is None for v in col_indices.values()) and len(table_data) > num_header_rows_to_check:
        logging.info("PDF: Attempting content-based column ID as header matching was incomplete.")
        data_sample_rows = table_data[num_header_rows_to_check : min(len(table_data), num_header_rows_to_check + 5)]
        for col_idx in range(num_cols):
            if not any(row_data_has_column(row, col_idx) for row in data_sample_rows): continue # Ensure column exists in sample

            if col_indices['date'] is None and any(looks_like_date(clean_text(row[col_idx])) for row in data_sample_rows if row_data_has_column(row, col_idx)):
                col_indices['date'] = col_idx; logging.info(f"PDF: Guessed 'date' column by content: {col_idx}")
            elif col_indices['amount'] is None and any(parse_amount(clean_text(row[col_idx])) is not None for row in data_sample_rows if row_data_has_column(row, col_idx)):
                col_indices['amount'] = col_idx; logging.info(f"PDF: Guessed 'amount' column by content: {col_idx}")

        if col_indices['description'] is None:
            potential_desc_cols = [c for c in range(num_cols) if c not in col_indices.values()]
            for c_idx in potential_desc_cols:
                 if any(len(clean_text(row[c_idx])) > 10 for row in data_sample_rows if row_data_has_column(row, c_idx)):
                    col_indices['description'] = c_idx; logging.info(f"PDF: Guessed 'description' column by content: {c_idx}")
                    break

    if any(col_indices.get(k) is None for k in ['date', 'description', 'amount']):
        logging.warning(f"PDF: Could not reliably identify all required columns. Identified: {col_indices}")
        return None # Return None if essential columns are missing
    return col_indices

def parse_pdf(file_path):
    result = {'transactions': [], 'success_count': 0, 'skipped_count': 0}
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                logging.info(f"PDF P{page_num+1}: Found {len(tables)} tables.")
                if not tables: continue

                for table_idx, table_data in enumerate(tables):
                    if not table_data or not table_data[0]:
                        logging.info(f"PDF P{page_num+1} T{table_idx+1}: Table is empty or malformed.")
                        result['skipped_count'] += len(table_data) if table_data else 0
                        continue

                    col_map = identify_columns(table_data)
                    if not col_map:
                        logging.warning(f"PDF P{page_num+1} T{table_idx+1}: Skipping table, identify_columns failed to find all required columns.")
                        result['skipped_count'] += len(table_data)
                        continue

                    header_rows_guess = 0
                    for r_idx, r_data in enumerate(table_data[:min(len(table_data), 5)]):
                        is_data_row = False
                        if row_data_has_column(r_data, col_map['amount']) and parse_amount(r_data[col_map['amount']]) is not None: is_data_row = True
                        elif row_data_has_column(r_data, col_map['date']) and looks_like_date(r_data[col_map['date']]): is_data_row = True
                        if is_data_row: header_rows_guess = r_idx; break
                        if r_idx == min(len(table_data), 5) - 1 and not is_data_row: header_rows_guess = 1

                    logging.info(f"PDF P{page_num+1} T{table_idx+1}: Column map: {col_map}. Assuming {header_rows_guess} header rows.")
                    for row_num, row_data in enumerate(table_data[header_rows_guess:]):
                        actual_row_num_in_table = row_num + header_rows_guess

                        if not all(row_data_has_column(row_data, col_map[key]) for key in ['date', 'description', 'amount']):
                            logging.warning(f"PDF P{page_num+1} T{table_idx+1} R{actual_row_num_in_table}: Skipping row, missing mapped columns.")
                            result['skipped_count'] += 1; continue

                        date_str = clean_text(row_data[col_map['date']])
                        desc_str = clean_text(row_data[col_map['description']])
                        amount_str = clean_text(row_data[col_map['amount']])

                        if not looks_like_date(date_str):
                            logging.warning(f"PDF P{page_num+1} T{table_idx+1} R{actual_row_num_in_table}: Skipped, '{date_str}' not date-like.")
                            result['skipped_count'] += 1; continue

                        amount_val = parse_amount(amount_str)
                        if not date_str or not desc_str or amount_val is None:
                            logging.warning(f"PDF P{page_num+1} T{table_idx+1} R{actual_row_num_in_table}: Skipped missing/invalid essential data. "
                                            f"D:'{date_str}', Desc:'{desc_str}', Amt Str:'{amount_str}'")
                            result['skipped_count'] += 1; continue

                        category = categorize_transaction(desc_str)

                        result['transactions'].append({
                            'date': date_str, 'description': desc_str,
                            'amount': float(amount_val), 'category': category
                        })
                        result['success_count'] += 1
    except Exception as e:
        if "PDFSyntaxError" in str(type(e)) or "pdf syntax" in str(e).lower():
             logging.error(f"Failed to parse PDF {file_path} due to a PDF syntax-related error: {e}", exc_info=True)
        else:
             logging.error(f"An unexpected error occurred while parsing PDF {file_path}: {e}", exc_info=True)
        # Return result even on error, counts will reflect what was processed before error.

    if result['success_count'] == 0 and result['skipped_count'] == 0 and not result['transactions']:
        logging.info(f"No transaction data extracted from PDF {file_path}.")
    else:
        logging.info(f"PDF parsing for {file_path} complete. Success: {result['success_count']}, Skipped: {result['skipped_count']}")
    return result

if __name__ == '__main__':
    logging.info("Testing PDF parser with categorization (placeholder - requires actual PDF files).")
    # Dummy PDF creation is commented out.
    # try:
    #     from reportlab.lib.pagesizes import letter
    #     from reportlab.platypus import SimpleDocTemplate, Table
    #     dummy_pdf_path = 'dummy_transactions_cat.pdf'
    #     # ... (reportlab code to create a PDF with a table) ...
    #     # elements.append(Table([["Date", "Description", "Amount"], ["01/11/2023", "Test Item for PDF", "19.99"]]))
    #     # doc.build(elements)
    #     # parsed_result = parse_pdf(dummy_pdf_path)
    #     # logging.info(f"Parsed Result from dummy PDF: {parsed_result}")
    #     # if os.path.exists(dummy_pdf_path): os.remove(dummy_pdf_path)
    # except ImportError:
    #     logging.warning("ReportLab not installed. Skipping dummy PDF creation for pdf_parser.py testing.")
    # except Exception as e:
    #     logging.error(f"Error in PDF parser __main__ test: {e}", exc_info=True)

    ne_result = parse_pdf('non_existent_cat.pdf') # Test non-existent file
    logging.info(f"Non-existent PDF file result: {ne_result}")

    # The sys.path manipulation is now at the top of the file.
    logging.info("PDF parser categorization test placeholder finished.")
