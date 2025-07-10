# Stock Analysis Project - Setup Instructions (No Logging Version)

## Project Overview
This project automatically fetches stock data for 15 predefined stocks, analyzes them using an LLM, and stores the results in a PostgreSQL database. It's designed to run daily at 6 AM.

## Prerequisites
- Python 3.8 or higher
- PostgreSQL database access
- Hugging Face API account

## Installation Steps

### 1. Create Project Directory
```bash
mkdir stock_analysis_project
cd stock_analysis_project
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
1. Copy the `.env` file template
2. Get your Hugging Face API key from: https://huggingface.co/settings/tokens
3. Update the `.env` file with your actual API key:
```
HUGGINGFACE_API_KEY=hf_your_actual_api_key_here
DB_PASSWORD=EABD2024
```

### 5. Create Directory Structure
Make sure your project has this exact structure:
```
stock_analysis_project/
├── main.py
├── config.py
├── requirements.txt
├── .env
├── .gitignore
├── data_extraction/
│   ├── __init__.py
│   └── yfinance_fetcher.py
├── database/
│   ├── __init__.py
│   ├── db_connection.py
│   ├── raw_data_handler.py
│   └── answers_handler.py
└── llm_analysis/
    ├── __init__.py
    ├── huggingface_client.py
    └── prompt_processor.py
```

### 6. Create Empty __init__.py Files
Create empty `__init__.py` files in each package directory if they don't exist.

## Database Schema
Make sure your PostgreSQL database has these tables:

```sql
-- raw_files table
CREATE TABLE raw_files (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    type TEXT NOT NULL,
    raw_data JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- stocks table (for reference)
CREATE TABLE stocks (
    symbol TEXT PRIMARY KEY,
    name TEXT,
    country TEXT,
    sector TEXT,
    region TEXT,
    industry TEXT,
    exchange TEXT,
    currency TEXT,
    ipo_year INTEGER,
    isin TEXT
);

-- answers table
CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Running the Project

### Manual Execution
```bash
python main.py
```

### Daily Automation (6 AM)

#### On Windows (Task Scheduler):
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to Daily at 6:00 AM
4. Set action to start program: `python`
5. Add arguments: `path\to\your\project\main.py`
6. Set start in: `path\to\your\project`

#### On macOS/Linux (Cron):
```bash
# Edit crontab
crontab -e

# Add this line for 6 AM daily:
0 6 * * * cd /path/to/your/project && /path/to/your/venv/bin/python main.py
```

## Testing
Before running the full process, you can test individual components:

```python
# Test database connection
python -c "from database.db_connection import DatabaseConnection; db = DatabaseConnection(); print('DB OK' if db.connect() else 'DB Failed')"

# Test yfinance
python -c "from data_extraction.yfinance_fetcher import test_connection; print('YFinance OK' if test_connection() else 'YFinance Failed')"

# Test Hugging Face API
python -c "from llm_analysis.huggingface_client import HuggingFaceClient; client = HuggingFaceClient(); print('HF OK' if client.test_connection() else 'HF Failed')"
```

## Output
The system will print status messages to the console showing:
- Connection test results
- Progress for each stock
- Final summary with success/failure counts

## Troubleshooting

### Common Issues:
1. **Database Connection Failed**: Check your database credentials in `config.py`
2. **Hugging Face API Failed**: Verify your API key in `.env` file
3. **YFinance Failed**: Check internet connection and try again
4. **Module Import Errors**: Make sure all `__init__.py` files exist
5. **Permission Errors**: Ensure you have write permissions to the database

### Rate Limits:
- YFinance: Generally no strict limits for reasonable usage
- Hugging Face: Free tier has limits, check your account dashboard

## Stocks Being Analyzed
- AAPL (Apple)
- MSFT (Microsoft)
- TSLA (Tesla)
- BABA (Alibaba)
- SAP (SAP SE)
- NESN (Nestlé)
- AMZN (Amazon)
- TM (Toyota)
- RDSA (Royal Dutch Shell)
- NFLX (Netflix)
- ASML (ASML Holding)
- SIE (Siemens)
- NVO (Novo Nordisk)
- TCS (Tata Consultancy Services)
- SHOP (Shopify)

## Support
If you encounter issues:
1. Check the console output for error messages
2. Verify all API keys and database credentials
3. Test individual components as shown above
4. Ensure all required packages are installed