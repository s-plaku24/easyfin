import os
from dotenv import load_dotenv

load_dotenv()

STOCK_SYMBOLS = [
    "AAPL", "MSFT", "TSLA", "BABA", "SAP", 
    "NESN.SW", "AMZN", "TM", "SHEL", "NFLX", 
    "ASML", "SIE.DE", "NVO", "TCS.NS", "SHOP"
]

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'yfin_try',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD')
}

BASE_ANALYSIS_PROMPT = """
You are a financial analysis expert. I will provide you with a JSON data dump from the Yahoo Finance API for a stock and a specific question about that stock. Your task is to analyze the data and provide a concise, structured answer.

The raw JSON data will be passed to you as-is, without preprocessing. You should extract only the necessary values from this JSON to answer the question. If a required data field is missing, acknowledge it concisely and continue.

Instructions:
- Your answer should be concise (preferably ≤ 150 words) and provide key takeaways rather than technical detail.
- Use a professional tone appropriate for a financial research dashboard.
- Predictive statements are allowed if grounded in evidence, but avoid speculation.
- If relevant, explain confidence or uncertainty behind your conclusion.
- Do not compare to other stocks unless explicitly asked.

JSON Data:
{json_data}

Question: {question}

Please provide your analysis answer:
"""