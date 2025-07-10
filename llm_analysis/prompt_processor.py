"""
Prompt processor for formatting data and handling LLM responses
"""

import json
from config import ANALYSIS_PROMPT
from llm_analysis.huggingface_client import HuggingFaceClient

def create_analysis_prompt(symbol, ticker_data, market_data):
    """
    Create the full analysis prompt with stock data
    
    Args:
        symbol (str): Stock symbol
        ticker_data (dict): Ticker data from yfinance
        market_data (dict): Market data from yfinance
    
    Returns:
        str: Formatted prompt ready for LLM
    """
    try:
        # Combine ticker and market data
        combined_data = {
            'symbol': symbol,
            'ticker_data': ticker_data,
            'market_data': market_data
        }
        
        # Convert to JSON string for the prompt
        data_json = json.dumps(combined_data, default=str, indent=2)
        
        # Create the full prompt
        full_prompt = f"""
{ANALYSIS_PROMPT}

Here is the JSON data for stock {symbol}:

{data_json}

Please analyze this stock data and provide the structured response as specified above.
"""
        
        return full_prompt
        
    except Exception as e:
        return None

def analyze_stock(symbol, ticker_data, market_data):
    """
    Analyze a stock using the LLM
    
    Args:
        symbol (str): Stock symbol
        ticker_data (dict): Ticker data from yfinance
        market_data (dict): Market data from yfinance
    
    Returns:
        str: LLM analysis response or None if failed
    """
    try:
        # Create the prompt
        prompt = create_analysis_prompt(symbol, ticker_data, market_data)
        if not prompt:
            return None
        
        # Initialize Hugging Face client
        client = HuggingFaceClient()
        
        # Get analysis from LLM
        analysis = client.query_model(prompt)
        
        if analysis:
            return analysis
        else:
            return None
            
    except Exception as e:
        return None

def clean_response(response):
    """
    Clean and format the LLM response
    
    Args:
        response (str): Raw LLM response
    
    Returns:
        str: Cleaned response
    """
    if not response:
        return ""
    
    try:
        # Remove any extra whitespace
        cleaned = response.strip()
        
        # Remove any markdown formatting that might interfere
        cleaned = cleaned.replace('```', '')
        
        # Ensure proper line breaks
        cleaned = cleaned.replace('\n\n\n', '\n\n')
        
        return cleaned
        
    except Exception as e:
        return response

def extract_company_name(ticker_data):
    """
    Extract company name from ticker data
    
    Args:
        ticker_data (dict): Ticker data from yfinance
    
    Returns:
        str: Company name or symbol if not found
    """
    try:
        if ticker_data and 'info' in ticker_data:
            info = ticker_data['info']
            
            # Try different fields for company name
            for field in ['longName', 'shortName', 'companyName', 'name']:
                if field in info and info[field]:
                    return info[field]
        
        return ticker_data.get('symbol', 'Unknown')
        
    except Exception as e:
        return 'Unknown'

def validate_analysis_response(response):
    """
    Validate that the analysis response contains the expected structure
    
    Args:
        response (str): LLM analysis response
    
    Returns:
        bool: True if response appears valid, False otherwise
    """
    if not response:
        return False
    
    try:
        # Check for key components
        required_elements = [
            'Stock Name:',
            'Stock Symbol:',
            'Question 1:',
            'Answer 1:',
            'Question 2:',
            'Answer 2:',
            'Question 3:',
            'Answer 3:',
            'Question 4:',
            'Answer 4:',
            'Question 5:',
            'Answer 5:'
        ]
        
        response_lower = response.lower()
        
        for element in required_elements:
            if element.lower() not in response_lower:
                return False
        
        return True
        
    except Exception as e:
        return False