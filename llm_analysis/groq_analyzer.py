from groq import Groq
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, date
from llm_analysis.prompt_processor import create_analysis_prompt, clean_response

def convert_data_for_groq(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
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

def analyze_stock_question_groq(symbol, question_text, raw_data=None):
    try:
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            return None
        
        client = Groq(api_key=api_key)
        
        prompt = create_analysis_prompt(symbol, question_text, raw_data)
        
        if not prompt:
            return None
        
        if len(prompt) > 15000:
            prompt = prompt[:15000] + "\n\nPlease analyze this stock data and provide your answer:"
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",
            max_tokens=8000,
            temperature=0.7
        )
        
        response = chat_completion.choices[0].message.content
        return clean_response(response)
        
    except Exception as e:
        return None

def test_groq_connection():
    try:
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            return False
        
        client = Groq(api_key=api_key)
        
        test_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Hello, this is a test. Please respond with 'OK'.",
                }
            ],
            model="llama3-8b-8192",
            max_tokens=50
        )
        
        response = test_completion.choices[0].message.content
        return "OK" in response or "ok" in response.lower()
        
    except Exception as e:
        return False