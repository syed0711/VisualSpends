# tests/test_data_storage.py
import unittest
import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spendwise.utils.data_storage import save_transactions_jsonl, load_transactions_jsonl

# Define a temporary test file path within the tests directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
TEST_TRANSACTIONS_FILE = os.path.join(TEST_DATA_DIR, 'test_transactions.jsonl')


class TestDataStorage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test_data directory if it doesn't exist
        if not os.path.exists(TEST_DATA_DIR):
            os.makedirs(TEST_DATA_DIR)

    def setUp(self):
        # Ensure the test file is clean before each test
        if os.path.exists(TEST_TRANSACTIONS_FILE):
            os.remove(TEST_TRANSACTIONS_FILE)

    def tearDown(self):
        # Clean up the test file after each test
        if os.path.exists(TEST_TRANSACTIONS_FILE):
            os.remove(TEST_TRANSACTIONS_FILE)

    @classmethod
    def tearDownClass(cls):
        # Clean up the test_data directory if empty (optional)
        # Check if directory exists and is empty
        if os.path.exists(TEST_DATA_DIR) and not os.listdir(TEST_DATA_DIR):
            try:
                os.rmdir(TEST_DATA_DIR)
            except OSError as e:
                # This might fail if hidden files like .DS_Store exist, ignore then.
                print(f"Could not remove {TEST_DATA_DIR}: {e}", file=sys.stderr)


    def test_save_and_load_transactions(self):
        transactions1 = [
            {'date': '2023-01-01', 'description': 'Test A', 'amount': 10.0, 'category': 'Test'},
            {'date': '2023-01-02', 'description': 'Test B', 'amount': 20.5, 'category': 'Test'}
        ]
        save_transactions_jsonl(transactions1, TEST_TRANSACTIONS_FILE)
        loaded_transactions = load_transactions_jsonl(TEST_TRANSACTIONS_FILE)
        self.assertEqual(len(loaded_transactions), 2)
        self.assertEqual(loaded_transactions, transactions1)

    def test_append_transactions(self):
        transactions1 = [{'date': '2023-01-01', 'description': 'Apples', 'amount': 5.0, 'category': 'Groceries'}]
        transactions2 = [{'date': '2023-01-02', 'description': 'Coffee', 'amount': 3.5, 'category': 'Food & Dining'}]

        save_transactions_jsonl(transactions1, TEST_TRANSACTIONS_FILE)
        save_transactions_jsonl(transactions2, TEST_TRANSACTIONS_FILE) # Append

        loaded_transactions = load_transactions_jsonl(TEST_TRANSACTIONS_FILE)
        self.assertEqual(len(loaded_transactions), 2)
        self.assertEqual(loaded_transactions, transactions1 + transactions2)

    def test_load_non_existent_file(self):
        loaded_transactions = load_transactions_jsonl("non_existent_test_file.jsonl")
        self.assertEqual(loaded_transactions, [])

    def test_save_empty_list(self):
        save_result = save_transactions_jsonl([], TEST_TRANSACTIONS_FILE)
        self.assertFalse(save_result) # Function should indicate no operation by returning False
        self.assertFalse(os.path.exists(TEST_TRANSACTIONS_FILE)) # File should not be created for empty list

    def test_load_empty_file(self):
        # Create an empty file
        open(TEST_TRANSACTIONS_FILE, 'w').close()
        loaded_transactions = load_transactions_jsonl(TEST_TRANSACTIONS_FILE)
        self.assertEqual(loaded_transactions, [])

    def test_load_malformed_jsonl_file(self):
        with open(TEST_TRANSACTIONS_FILE, 'w') as f:
            f.write('{"date": "2023-01-03", "description": "Good one", "amount": 1.0, "category": "Ok"}\n')
            f.write('this is not valid json\n')
            f.write('{"date": "2023-01-04", "description": "Another good", "amount": 2.0, "category": "Ok"}\n')

        loaded_transactions = load_transactions_jsonl(TEST_TRANSACTIONS_FILE)
        self.assertEqual(len(loaded_transactions), 2)
        self.assertEqual(loaded_transactions[0]['description'], "Good one")
        self.assertEqual(loaded_transactions[1]['description'], "Another good")

if __name__ == '__main__':
    unittest.main()
