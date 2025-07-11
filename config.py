import os
from dotenv import load_dotenv

load_dotenv()

STOCK_SYMBOLS = [
    "AAPL", "MSFT", "TSLA", "BABA", "SAP", 
    "AMZN", "TM", "SHEL", "NFLX", 
    "ASML", "NVO", "SHOP"
]

DB_CONFIG = {
    'host': '91.99.20.15',
    'port': 5432,
    'database': 'postgres',
    'user': 'nils',
    'password': os.getenv('DB_PASSWORD')
}

# Updated prompt for batch analysis of all questions
BASE_ANALYSIS_PROMPT = """
You are a financial analysis expert. I will provide you with financial data from FMP API for a stock and specific questions. Your task is to analyze and summarize the data into concise, structured answers for each stock. These summaries will be displayed on a non-interactive financial dashboard, so they must be informative and digestible at a glance.

The data includes current market data (quote) and recent price history (historical). If a required data field is missing, acknowledge it concisely and continue. When helpful, you may incorporate other fields to support or explain the analysis.

For each question, provide the output exactly as:
symbol: {symbol}
question_id: [question_id]
Answer [question_id]: [Your answer]

Questions to answer:
{questions}

Instructions:
– Each answer should be concise (preferably ≤ 50 words) and provide key takeaways rather than technical detail.
– Use a professional tone appropriate for a financial research dashboard. Analytical and neutral with mild narrative flow.
– Predictive statements are allowed if grounded in evidence, but avoid speculation.
– If relevant, explain confidence or uncertainty behind your conclusion (e.g., "Based on a limited sample of earnings…").
– Do not compare one stock to others unless explicitly asked. Each stock is to be evaluated independently.

This output will be presented to end users without interaction. It must deliver value at a glance, highlight relevant insights, and avoid raw data dumps or excessive detail.

Data:
{json_data}
"""

# FMP API configuration
FMP_CONFIG = {
    'base_url': 'https://financialmodelingprep.com/api/v3',
    'api_key': os.getenv('FMP_API_KEY'),
    'timeout': 30,
    'max_retries': 3
}

# Data limits to stay within Groq token limits (llama3-8b-8192 max: 8192 tokens)
# Approximately 4 chars per token, so ~32KB max input
DATA_LIMITS = {
    'historical_days': 10,
    'max_json_size': 25000,
    'truncate_threshold': 20000
}