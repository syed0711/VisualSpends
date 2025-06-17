import json
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STORAGE_DIR = os.path.join('spendwise', 'data')
DEFAULT_TRANSACTIONS_FILE = os.path.join(STORAGE_DIR, 'transactions.jsonl')

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def save_transactions_jsonl(transactions, file_path=DEFAULT_TRANSACTIONS_FILE):
    """
    Appends a list of transaction dictionaries to a JSON Lines file.
    Each transaction is stored as a JSON object on a new line.

    Args:
        transactions (list): A list of transaction dictionaries.
        file_path (str): The path to the JSONL file.
    """
    if not transactions:
        logging.info("No transactions provided to save.")
        return False

    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            for transaction in transactions:
                json.dump(transaction, f)
                f.write('\n')
        logging.info(f"Successfully appended {len(transactions)} transactions to {file_path}")
        return True
    except IOError as e:
        logging.error(f"IOError writing to {file_path}: {e}")
    except TypeError as e:
        logging.error(f"TypeError: Could not serialize transaction to JSON. Ensure transactions are JSON serializable. Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while saving transactions to {file_path}: {e}")
    return False

def load_transactions_jsonl(file_path=DEFAULT_TRANSACTIONS_FILE):
    """
    Loads all transactions from a JSON Lines file.

    Args:
        file_path (str): The path to the JSONL file.

    Returns:
        list: A list of transaction dictionaries. Returns an empty list if the file
              doesn't exist or an error occurs.
    """
    transactions = []
    if not os.path.exists(file_path):
        logging.info(f"Transaction file {file_path} not found. Returning empty list.")
        return transactions

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        transactions.append(json.loads(line))
                    except json.JSONDecodeError as jde:
                        logging.warning(f"Skipping malformed JSON line in {file_path}: {line}. Error: {jde}")
                        continue
        logging.info(f"Successfully loaded {len(transactions)} transactions from {file_path}")
    except IOError as e:
        logging.error(f"IOError reading from {file_path}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading transactions from {file_path}: {e}")

    return transactions

if __name__ == '__main__':
    # Example Usage for testing data_storage
    logging.info("Testing data_storage functions...")

    # Ensure the storage directory exists (it should be created by the module already)
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

    test_file = os.path.join(STORAGE_DIR, 'test_transactions.jsonl')

    # Clean up old test file if it exists
    if os.path.exists(test_file):
        os.remove(test_file)

    sample_transactions1 = [
        {'date': '2023-01-01', 'description': 'Test A', 'amount': 10.0},
        {'date': '2023-01-02', 'description': 'Test B', 'amount': 20.5},
    ]
    sample_transactions2 = [
        {'date': '2023-01-03', 'description': 'Test C', 'amount': 30.0},
    ]

    logging.info(f"Saving first batch of transactions to {test_file}")
    save_transactions_jsonl(sample_transactions1, test_file)

    logging.info(f"Saving second batch of transactions to {test_file}")
    save_transactions_jsonl(sample_transactions2, test_file)

    logging.info(f"Loading all transactions from {test_file}")
    all_loaded_transactions = load_transactions_jsonl(test_file)

    expected_total = len(sample_transactions1) + len(sample_transactions2)
    if len(all_loaded_transactions) == expected_total:
        logging.info(f"Successfully loaded {len(all_loaded_transactions)} transactions, matching expected {expected_total}.")
        # Print them to verify
        # for tx in all_loaded_transactions:
        #    print(tx)
    else:
        logging.error(f"Loaded {len(all_loaded_transactions)} transactions, but expected {expected_total}.")

    # Test loading from a non-existent file
    logging.info("Testing loading from a non-existent file...")
    non_existent_transactions = load_transactions_jsonl("non_existent.jsonl")
    if not non_existent_transactions:
        logging.info("Correctly returned empty list for non-existent file.")
    else:
        logging.error("Should have returned an empty list for non-existent file.")

    # Test saving empty list
    logging.info("Testing saving an empty list of transactions...")
    save_transactions_jsonl([], test_file) # Should just log and return False

    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)
    logging.info("Data storage tests complete.")
