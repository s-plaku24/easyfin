"""
Groq analyzer for stock analysis
"""

from groq import Groq
import os
from config import ANALYSIS_PROMPT
import json
import pandas as pd
import numpy as np
from datetime import datetime, date

def convert_data_for_groq(obj):
    """Recursively convert pandas objects to JSON-serializable format for Groq"""
    if isinstance(obj, dict):
        # Convert dictionary keys and values
        new_dict = {}
        for key, value in obj.items():
            # Convert keys to strings if they're timestamps
            if isinstance(key, (pd.Timestamp, datetime, date)):
                new_key = key.isoformat()
            else:
                new_key = str(key)
            new_dict[new_key] = convert_data_for_groq(value)
        return new_dict
    elif isinstance(obj, (list, tuple)):
        return [convert_data_for_groq(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
        return obj.isoformat()
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

def analyze_stock_groq(symbol, ticker_data, market_data):
    """
    Analyze stock using Groq LLM (free)
    """
    try:
        # Get API key from environment
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            print(f"No Groq API key found for {symbol}")
            return None
        
        print(f"Using Groq API for {symbol}")
        
        client = Groq(api_key=api_key)
        
        # Combine and convert data (fix timestamp issues)
        combined_data = {
            'symbol': symbol,
            'ticker_data': ticker_data,
            'market_data': market_data
        }
        
        # Convert the entire data structure to handle timestamps
        converted_data = convert_data_for_groq(combined_data)
        
        # Create smaller data summary for the prompt
        data_summary = json.dumps(converted_data)[:8000]  # Increased limit
        
        full_prompt = f"""{ANALYSIS_PROMPT}

Here is the JSON data for stock {symbol}:

{data_summary}

Please analyze this stock data and provide the structured response as specified above."""
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            model="llama3-8b-8192",  # Free model
            max_tokens=1500,
            temperature=0.7
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        print(f"Groq API error for {symbol}: {str(e)}")
        return None