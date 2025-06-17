# tests/test_categorizer.py
import unittest
import sys
import os

# Add project root to sys.path to allow absolute imports of spendwise modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from spendwise.utils.categorizer import categorize_transaction, DEFAULT_CATEGORY, CATEGORIES_KEYWORDS

class TestCategorizer(unittest.TestCase):

    def test_categorization(self):
        test_cases = {
            "Starbucks coffee morning": "Food & Dining",
            "Monthly electricity bill": "Utilities",
            "Uber ride to airport": "Transport",
            "Amazon purchase electronics": "Shopping",
            "Netflix subscription": "Entertainment",
            "CVS Pharmacy prescription": "Health & Wellness",
            "Flight to London on BA": "Travel",
            "Rent payment for apartment": "Housing",
            "University tuition fee": "Education",
            "Salary deposit from work": "Income",
            "A random unknown transaction": DEFAULT_CATEGORY,
            "BP Gas": "Transport",
            "local grocery store purchase": "Food & Dining", # Test case insensitivity and multiple words
            "Paycheck from ACME Corp": "Income"
        }
        for description, expected_category in test_cases.items():
            with self.subTest(description=description):
                self.assertEqual(categorize_transaction(description), expected_category)

    def test_empty_or_none_description(self):
        self.assertEqual(categorize_transaction(""), DEFAULT_CATEGORY)
        self.assertEqual(categorize_transaction(None), DEFAULT_CATEGORY)

    def test_no_matching_keywords(self):
        self.assertEqual(categorize_transaction("unique_unseen_description_xyz"), DEFAULT_CATEGORY)

    def test_keywords_case_insensitivity(self):
        # Assuming 'Food & Dining' has 'coffee' as a keyword
        self.assertEqual(categorize_transaction("COFFEE TIME"), "Food & Dining")
        self.assertEqual(categorize_transaction("My CoFfEe"), "Food & Dining")


if __name__ == '__main__':
    unittest.main()
