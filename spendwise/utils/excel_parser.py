# spendwise/utils/excel_parser.py
import sys
import os # For __main__ test and path manipulation
if not __package__ and not hasattr(sys, 'frozen'):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

import pandas as pd
import logging
from spendwise.utils.categorizer import categorize_transaction # Import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADER_MAPPINGS = {
    'date': ['date', 'transaction date', 'posting date'],
    'description': ['description', 'narrative', 'details', 'memo'],
    'amount': ['amount', 'value', 'credit', 'debit']
}
def normalize_headers(df):
    df_normalized = df.copy()
    new_columns = {}
    current_headers_lower = [str(col).lower() for col in df_normalized.columns]
    for canonical_name, variations in HEADER_MAPPINGS.items():
        found = False
        for variation in variations:
            try:
                idx = current_headers_lower.index(variation)
                new_columns[df_normalized.columns[idx]] = canonical_name
                found = True; break
            except ValueError: continue
        if not found: logging.warning(f"Excel: Canonical header '{canonical_name}' not found. Variations: {variations}")
    df_normalized.rename(columns=new_columns, inplace=True)
    return df_normalized

def parse_excel(file_path):
    result = {'transactions': [], 'success_count': 0, 'skipped_count': 0}
    try:
        # Ensure os is imported if not already at the top for __main__
        # import os # Already imported at the top for the original __main__ test
        date_col_variations = HEADER_MAPPINGS.get('date', ['date'])
        dtype_spec = {col_name: str for col_name in date_col_variations}
        df = pd.read_excel(file_path, sheet_name=0, dtype=dtype_spec)

        if df.empty:
            logging.info(f"Excel file {file_path} is empty or first sheet has no data.")
            return result

        df_normalized = normalize_headers(df)
        required_canonical_headers = {'date', 'description', 'amount'}
        if not required_canonical_headers.issubset(df_normalized.columns):
            logging.error(f"Excel file {file_path} is missing required canonical headers after normalization. "
                          f"Expected: {required_canonical_headers}. Found: {list(df_normalized.columns)}")
            result['skipped_count'] = df.shape[0]
            return result

        for index, row in df_normalized.iterrows():
            try:
                date_val = row.get('date')
                desc_val = row.get('description')
                amount_val = row.get('amount')

                date_str = None
                if pd.isna(date_val):
                    logging.warning(f"Skipping Excel row {index+1} in {file_path} due to missing Date. Row: {row.to_dict()}")
                    result['skipped_count'] += 1
                    continue

                if isinstance(date_val, pd.Timestamp) or pd.api.types.is_datetime64_any_dtype(date_val):
                    date_str = date_val.strftime('%Y-%m-%d')
                else:
                    try:
                        date_str = pd.to_datetime(str(date_val)).strftime('%Y-%m-%d')
                    except ValueError:
                        logging.warning(f"Skipping Excel row {index+1} in {file_path} due to unparsable date: '{date_val}'. Row: {row.to_dict()}")
                        result['skipped_count'] += 1
                        continue

                if pd.isna(desc_val) or pd.isna(amount_val):
                    logging.warning(f"Skipping Excel row {index+1} in {file_path} due to missing Description or Amount (Date: {date_str}). Row: {row.to_dict()}")
                    result['skipped_count'] += 1
                    continue

                try:
                    amount_float = float(str(amount_val).replace('$', '').replace(',', '')) if not isinstance(amount_val, (int, float)) else float(amount_val)
                except ValueError:
                    logging.warning(f"Skipping Excel row {index+1} in {file_path} due to invalid amount: '{amount_val}'. Row: {row.to_dict()}")
                    result['skipped_count'] += 1
                    continue

                desc_str_for_cat = str(desc_val) # Ensure description is string
                category = categorize_transaction(desc_str_for_cat)

                result['transactions'].append({
                    'date': date_str,
                    'description': desc_str_for_cat,
                    'amount': amount_float,
                    'category': category
                })
                result['success_count'] += 1
            except Exception as e:
                logging.warning(f"Error processing Excel row {index+1} in {file_path}: {e}. Row: {row.to_dict()}")
                result['skipped_count'] += 1
                continue
    except FileNotFoundError:
        logging.error(f"Excel file not found: {file_path}")
        return result
    except pd.errors.EmptyDataError:
        logging.error(f"No data or sheets found in Excel file: {file_path}")
        return result
    except Exception as e:
        logging.error(f"Failed to read or parse Excel file {file_path}: {e}", exc_info=True)
        return result

    if result['success_count'] == 0 and result['skipped_count'] == 0 and not result['transactions']:
        logging.info(f"No data found or all rows failed very early in Excel {file_path}.")
    else:
        logging.info(f"Excel parsing for {file_path} complete. Success: {result['success_count']}, Skipped: {result['skipped_count']}")
    return result

if __name__ == '__main__':
    logging.info("Testing Excel parser with categorization...")
    dummy_excel_path = 'dummy_transactions_cat.xlsx'

    data = {
        'Transaction Date': [pd.Timestamp('2023-01-15'), pd.Timestamp('2023-01-16'), '2023-01-17'],
        'Details': ['Uber Ride', 'Groceries from Walmart', 'Lunch at a cafe'],
        'Amount': [25.50, 150.75, 12.00]
    }
    df_test = pd.DataFrame(data)

    try:
        df_test.to_excel(dummy_excel_path, sheet_name='Sheet1', index=False)
        logging.info(f"Testing Excel parser with {dummy_excel_path}")
        parsed_result = parse_excel(dummy_excel_path)
        logging.info(f"Parsed Result: {parsed_result}")

        if parsed_result['transactions']:
            logging.info(f"Successfully parsed {parsed_result['success_count']} transactions:")
            for tx in parsed_result['transactions']: # tx will include 'category'
                logging.info(tx)
        if parsed_result['skipped_count'] > 0:
            logging.info(f"Skipped {parsed_result['skipped_count']} rows.")
    except Exception as e:
        logging.error(f"Error during __main__ test setup/run for Excel: {e}", exc_info=True)
    finally:
        if os.path.exists(dummy_excel_path):
            os.remove(dummy_excel_path)
    # The sys.path manipulation is now at the top of the file.
    logging.info("Excel parser categorization tests complete.")
