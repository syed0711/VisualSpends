# tests/test_csv_parser.py
import unittest
import os
import csv
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spendwise.utils.csv_parser import parse_csv
from spendwise.utils.categorizer import DEFAULT_CATEGORY # For checking category

# Define a temporary test file path within the tests directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
DUMMY_CSV_VALID = os.path.join(TEST_DATA_DIR, 'dummy_valid.csv')
DUMMY_CSV_INVALID_ROW = os.path.join(TEST_DATA_DIR, 'dummy_invalid_row.csv')
DUMMY_CSV_EMPTY = os.path.join(TEST_DATA_DIR, 'dummy_empty.csv')
DUMMY_CSV_MISSING_HEADER = os.path.join(TEST_DATA_DIR, 'dummy_missing_header.csv')


class TestCSVParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test_data directory if it doesn't exist
        if not os.path.exists(TEST_DATA_DIR):
            os.makedirs(TEST_DATA_DIR)

        # Create dummy CSV files for testing
        with open(DUMMY_CSV_VALID, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Description', 'Amount'])
            writer.writerow(['2023-01-15', 'Coffee Shop', '5.75'])
            writer.writerow(['2023-01-16', 'Grocery Store', '75.20'])

        with open(DUMMY_CSV_INVALID_ROW, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Description', 'Amount'])
            writer.writerow(['2023-01-17', 'Book Store', '15.00'])
            writer.writerow(['2023-01-18', 'Invalid Data', 'ABC']) # Invalid amount
            writer.writerow(['2023-01-19', 'Electronics Store', '120.50']) # Changed description to include 'store' for category testing


        with open(DUMMY_CSV_EMPTY, 'w', newline='') as f:
            # Write headers for an empty data file, or leave completely empty
            # If DictReader expects headers, an empty file will behave differently than file with only headers
            writer = csv.writer(f)
            writer.writerow(['Date', 'Description', 'Amount'])


        with open(DUMMY_CSV_MISSING_HEADER, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Details']) # Missing 'Amount' header
            writer.writerow(['2023-01-20', 'Test Data'])


    @classmethod
    def tearDownClass(cls):
        # Clean up dummy files
        if os.path.exists(DUMMY_CSV_VALID): os.remove(DUMMY_CSV_VALID)
        if os.path.exists(DUMMY_CSV_INVALID_ROW): os.remove(DUMMY_CSV_INVALID_ROW)
        if os.path.exists(DUMMY_CSV_EMPTY): os.remove(DUMMY_CSV_EMPTY)
        if os.path.exists(DUMMY_CSV_MISSING_HEADER): os.remove(DUMMY_CSV_MISSING_HEADER)
        # Clean up the test_data directory if empty
        if os.path.exists(TEST_DATA_DIR) and not os.listdir(TEST_DATA_DIR):
            try:
                os.rmdir(TEST_DATA_DIR)
            except OSError as e:
                print(f"Could not remove {TEST_DATA_DIR}: {e}", file=sys.stderr)


    def test_parse_valid_csv(self):
        result = parse_csv(DUMMY_CSV_VALID)
        self.assertEqual(result['success_count'], 2)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(len(result['transactions']), 2)
        self.assertEqual(result['transactions'][0]['description'], 'Coffee Shop')
        self.assertEqual(result['transactions'][0]['amount'], 5.75)
        self.assertEqual(result['transactions'][0]['category'], "Food & Dining") # "Coffee Shop" -> "Food & Dining"
        self.assertEqual(result['transactions'][1]['category'], "Food & Dining") # Corrected: "Grocery Store" -> "Food & Dining"

    def test_parse_csv_with_invalid_row(self):
        result = parse_csv(DUMMY_CSV_INVALID_ROW)
        self.assertEqual(result['success_count'], 2)
        self.assertEqual(result['skipped_count'], 1) # 'ABC' amount row
        self.assertEqual(len(result['transactions']), 2)
        self.assertEqual(result['transactions'][0]['category'], "Shopping") # "Book Store"
        self.assertEqual(result['transactions'][1]['category'], "Shopping") # "Electronics Store"


    def test_parse_empty_csv_with_headers(self): # Renamed for clarity
        result = parse_csv(DUMMY_CSV_EMPTY)
        self.assertEqual(result['success_count'], 0)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(len(result['transactions']), 0)

    def test_parse_csv_missing_header(self):
        result = parse_csv(DUMMY_CSV_MISSING_HEADER)
        self.assertEqual(result['success_count'], 0)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(len(result['transactions']), 0)

    def test_parse_non_existent_csv(self):
        result = parse_csv("non_existent_file.csv")
        self.assertEqual(result['success_count'], 0)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(len(result['transactions']), 0)

if __name__ == '__main__':
    unittest.main()
