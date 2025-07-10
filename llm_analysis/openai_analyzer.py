"""
OpenAI analyzer for stock analysis
"""

import openai
from config import ANALYSIS_PROMPT, OPENAI_API_KEY
import json

def analyze_stock_openai(symbol, ticker_data, market_data):
    """
    Analyze stock using OpenAI GPT
    """
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Combine data (limit size for API)
        combined_data = {
            'symbol': symbol,
            'ticker_data': ticker_data,
            'market_data': market_data
        }
        
        # Create smaller data summary for the prompt
        data_summary = json.dumps(combined_data, default=str)[:6000]  # Limit to 6000 chars
        
        full_prompt = f"""{ANALYSIS_PROMPT}

Here is the JSON data for stock {symbol}:

{data_summary}

Please analyze this stock data and provide the structured response as specified above."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"OpenAI API error for {symbol}: {str(e)}")
        return None