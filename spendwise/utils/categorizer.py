# spendwise/utils/categorizer.py
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define categories and associated keywords
# Keywords should be lowercase for case-insensitive matching
CATEGORIES_KEYWORDS = {
    'Food & Dining': ['coffee', 'starbucks', 'restaurant', 'lunch', 'dinner', 'groceries', 'grocery', 'mcdonalds', 'cafe', 'kfc', 'burger king', 'pizza', 'food', 'bakery', 'dining', 'eats'], # Added 'grocery'
    'Utilities': ['electricity', 'water bill', 'gas bill', 'internet', 'phone bill', 'comcast', 'verizon', 'at&t', 'utility', 'power', 'broadband'],
    'Transport': ['uber', 'lyft', 'gasoline', 'shell', 'mobil', 'bp', 'chevron', 'subway', 'metro', 'taxi', 'parking', 'bus', 'train', 'fuel', 'transportation'],
    'Shopping': ['amazon', 'target', 'walmart', 'macys', 'best buy', 'clothes', 'shoes', 'apparel', 'store', 'market', 'shop', 'purchase', 'retail'],
    'Entertainment': ['netflix', 'spotify', 'hulu', 'cinema', 'movies', 'concert', 'games', 'disney', 'steam', 'playstation', 'xbox', 'music', 'theater'],
    'Health & Wellness': ['pharmacy', 'cvs', 'walgreens', 'doctor', 'hospital', 'gym', 'fitness', 'health', 'medical', 'clinic', 'dentist'],
    'Travel': ['airbnb', 'hotel', 'flight', 'booking.com', 'expedia', 'airline', 'travel', 'vacation', 'trip'],
    'Housing': ['rent', 'mortgage', 'hoa', 'strata', 'housing'],
    'Education': ['school', 'college', 'university', 'tuition', 'books', 'course'],
    'Income': ['salary', 'paycheck', 'deposit', 'interest income', 'dividend'], # Example for income, though most are expenses
    'Miscellaneous': [] # Default, or for things not easily categorized by keywords
}

DEFAULT_CATEGORY = 'Miscellaneous'

def categorize_transaction(description):
    """
    Categorizes a transaction based on keywords in its description.

    Args:
        description (str): The transaction description.

    Returns:
        str: The determined category name.
    """
    if not description or not isinstance(description, str):
        return DEFAULT_CATEGORY

    desc_lower = description.lower()

    for category, keywords in CATEGORIES_KEYWORDS.items():
        if any(keyword in desc_lower for keyword in keywords):
            return category

    return DEFAULT_CATEGORY

if __name__ == '__main__':
    logging.info("Testing categorizer...")
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
        "A random unknown transaction": "Miscellaneous",
        "BP Gas": "Transport",
        "": "Miscellaneous", # Empty description
        None: "Miscellaneous" # None description
    }
    passed_count = 0
    failed_tests = []
    for desc, expected_cat in test_cases.items():
        cat = categorize_transaction(desc)
        if cat == expected_cat:
            logging.info(f"PASS: Description: '{desc}' -> Category: '{cat}'")
            passed_count+=1
        else:
            logging.error(f"FAIL: Description: '{desc}' -> Expected '{expected_cat}', got '{cat}'")
            failed_tests.append(f"Desc: '{desc}', Expected: '{expected_cat}', Got: '{cat}'")

    if passed_count == len(test_cases):
        logging.info("All categorizer tests passed.")
    else:
        logging.error(f"{len(test_cases) - passed_count} categorizer tests failed:")
        for failure in failed_tests:
            logging.error(f"  - {failure}")
