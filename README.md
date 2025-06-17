# SpendWise - Personal Spending Companion

SpendWise is a simple, locally-run web application designed to help you import, view, and understand your spending habits. It supports importing transactions from CSV, Excel, and PDF files, automatically categorizes them, and provides insights through a data table and a summary dashboard. All data is stored locally on your computer, ensuring privacy.

## Key Features

*   **Multiple File Formats**: Import transactions from CSV, Excel (.xls, .xlsx), and basic PDF table structures.
*   **Automatic Categorization**: Transactions are automatically assigned categories (e.g., Food & Dining, Utilities, Transport) based on keywords in their descriptions.
*   **Transaction Overview**: Browse all your imported transactions in a sortable table view.
*   **Spending Dashboard**: Get insights into your finances, including:
    *   Total amount spent.
    *   Monthly spending trends.
    *   Breakdown of spending by category.
*   **Local Data Storage**: All your transaction data is stored locally in the `spendwise/data/transactions.jsonl` file. No internet connection is required to use the app after setup.
*   **Error Reporting**: Clear feedback on successful imports and any records that were skipped due to errors.

## Project Structure

```
spendwise_project_root/
├── main.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── spendwise/              # Main application package
│   ├── __init__.py
│   ├── data/               # Stores uploaded files (temporary) and processed data
│   │   ├── uploads/        # Temp storage for uploaded raw files
│   │   └── transactions.jsonl # Processed transaction data
│   ├── static/             # CSS, JavaScript (if any more complex JS is added)
│   │   └── style.css       # Basic styles (currently in templates)
│   ├── templates/          # HTML templates
│   │   ├── index.html      # File upload page
│   │   ├── data_view.html  # Transaction table view
│   │   └── dashboard.html  # Dashboard view
│   └── utils/              # Helper modules
│       ├── __init__.py
│       ├── categorizer.py
│       ├── csv_parser.py
│       ├── excel_parser.py
│       ├── pdf_parser.py
│       └── data_storage.py
└── tests/                  # Unit tests
    ├── __init__.py
    ├── test_categorizer.py
    ├── test_csv_parser.py
    ├── test_data_storage.py
    └── test_excel_parser.py # (Assuming test_pdf_parser.py might be added later)
```

## Setup and Installation

1.  **Clone the Repository (if applicable)**
    If this project were hosted on Git, you would clone it:
    ```bash
    git clone <repository-url>
    cd spendwise_project_root
    ```
    For now, ensure you have all the project files in a local directory.

2.  **Create a Virtual Environment (Recommended)**
    It's good practice to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install Dependencies**
    Install the required Python packages using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run SpendWise

1.  **Navigate to the Project Root Directory**
    Ensure your terminal is in the `spendwise_project_root` directory (the one containing `main.py`).

2.  **Run the Flask Application**
    ```bash
    python main.py
    ```

3.  **Access in Browser**
    Open your web browser and go to:
    ```
    http://127.0.0.1:5000/
    ```
    (Flask usually runs on port 5000 by default. Check your terminal output for the exact URL if it differs.)

## How to Use

1.  **Upload Transactions**:
    *   On the "Upload New File" page, click "Choose File".
    *   Select your transaction file (CSV, Excel, or PDF).
    *   Click "Import".
    *   You'll see a "Processing..." message, followed by flash messages indicating the import status (e.g., number of records imported/skipped).

2.  **View Transactions**:
    *   Click the "View Transactions" link in the navigation bar.
    *   This page displays all imported transactions in a table.
    *   You can click on column headers (Date, Description, Amount, Category) to sort the data.

3.  **Explore Dashboard**:
    *   Click the "Dashboard" link in the navigation bar.
    *   This page shows:
        *   Your total spending.
        *   A trend of your spending month by month.
        *   A breakdown of your spending across different categories.

4.  **Update Anytime**:
    *   You can upload new files at any time. New transactions will be appended to your existing data. The views will update accordingly when you revisit them.

## Notes

*   **PDF Parsing**: PDF parsing is complex. The current implementation works best with PDFs that have clear, simple table structures. Scanned PDFs or very complex layouts might not parse correctly.
*   **Categorization**: Categorization is based on a predefined set of keywords. You can extend or modify these keywords in `spendwise/utils/categorizer.py` if needed.
*   **Data Persistence**: If you delete the `spendwise/data/transactions.jsonl` file, all imported transaction data will be lost.
