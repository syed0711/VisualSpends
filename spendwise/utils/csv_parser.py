# spendwise/utils/csv_parser.py
# Attempt to fix direct script execution with absolute imports:
import sys
import os
if not __package__ and not hasattr(sys, 'frozen'):
    # Add the project root (parent of 'spendwise' directory) to sys.path
    # This allows 'from spendwise.utils.categorizer import ...' to work when run directly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

import csv
import logging
from spendwise.utils.categorizer import categorize_transaction # Import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_csv(file_path):
    result = {'transactions': [], 'success_count': 0, 'skipped_count': 0}
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            required_headers = {'date', 'description', 'amount'}
            # Ensure reader.fieldnames is not None before processing
            fieldnames_lower = [str(f).lower() for f in reader.fieldnames] if reader.fieldnames else []
            if not required_headers.issubset(set(fieldnames_lower)):
                logging.error(f"CSV file {file_path} is missing required headers. "
                              f"Expected variations of {', '.join(required_headers)}. Found: {reader.fieldnames}")
                return result

            for i, row in enumerate(reader):
                try:
                    row_lower_keys = {str(k).lower(): v for k, v in row.items() if k} # Ensure k is string

                    date_val = row_lower_keys.get('date')
                    desc_val = row_lower_keys.get('description')
                    amount_str = row_lower_keys.get('amount')

                    if date_val is None or desc_val is None or amount_str is None:
                        logging.warning(
                            f"Skipping CSV row {i+1} in {file_path} due to missing Date, Description, or Amount. Row: {row}"
                        )
                        result['skipped_count'] += 1
                        continue
                    try:
                        amount_val = float(str(amount_str).replace('$', '').replace(',', ''))
                    except ValueError:
                        logging.warning(
                            f"Skipping CSV row {i+1} in {file_path} due to invalid amount: '{amount_str}'. Row: {row}"
                        )
                        result['skipped_count'] += 1
                        continue

                    category = categorize_transaction(desc_val) # Categorize

                    result['transactions'].append({
                        'date': date_val,
                        'description': desc_val,
                        'amount': amount_val,
                        'category': category # Add category
                    })
                    result['success_count'] += 1
                except Exception as e:
                    logging.warning(f"Error processing CSV row {i+1} in {file_path}: {e}. Row: {row}")
                    result['skipped_count'] += 1
                    continue
    except FileNotFoundError:
        logging.error(f"CSV file not found: {file_path}")
        return result # Return dict on error
    except Exception as e:
        logging.error(f"Failed to read or parse CSV file {file_path}: {e}")
        return result # Return dict on error

    if result['success_count'] == 0 and result['skipped_count'] == 0 and not result['transactions']:
        logging.info(f"No data found or all rows failed very early in CSV {file_path}.")
    else:
        logging.info(f"CSV parsing for {file_path} complete. Success: {result['success_count']}, Skipped: {result['skipped_count']}")
    return result

if __name__ == '__main__':
    # Example usage (for testing purposes) - now includes category
    dummy_csv_path = 'dummy_transactions_cat.csv'
    with open(dummy_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Description', 'Amount'])
        writer.writerow(['2023-01-15', 'Starbucks Coffee', '5.75'])
        writer.writerow(['2023-01-16', 'Grocery Store', '75.20'])
        writer.writerow(['2023-01-17', 'Invalid Data', 'ABC'])
        writer.writerow(['2023-01-18', 'Amazon.com purchase', '15.00'])

    logging.info(f"Testing CSV parser with categorization: {dummy_csv_path}")
    parsed_result = parse_csv(dummy_csv_path)
    logging.info(f"Parsed Result: {parsed_result}")
    if parsed_result['transactions']:
        logging.info(f"Successfully parsed {parsed_result['success_count']} transactions:")
        for tx in parsed_result['transactions']: # Now tx includes 'category'
            logging.info(tx)
    if parsed_result['skipped_count'] > 0:
        logging.info(f"Skipped {parsed_result['skipped_count']} rows.")

    import os
    # The sys.path manipulation is now at the top of the file.
    os.remove(dummy_csv_path)
