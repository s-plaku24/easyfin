import json
from config import BASE_ANALYSIS_PROMPT
from database.raw_data_handler import get_combined_raw_data

def create_analysis_prompt(symbol, question_text, raw_data=None):
    try:
        if raw_data is None:
            raw_data = get_combined_raw_data(symbol)
        
        if not raw_data:
            return None
        
        data_json = json.dumps(raw_data, default=str, indent=2)
        
        full_prompt = BASE_ANALYSIS_PROMPT.format(
            json_data=data_json,
            question=question_text
        )
        
        return full_prompt
        
    except Exception as e:
        return None

def clean_response(response):
    if not response:
        return ""
    
    try:
        cleaned = response.strip()
        cleaned = cleaned.replace('```', '')
        cleaned = cleaned.replace('\n\n\n', '\n\n')
        
        return cleaned
        
    except Exception as e:
        return response

def validate_analysis_response(response):
    if not response:
        return False
    
    try:
        if len(response.strip()) < 10:
            return False
        
        error_indicators = ['error', 'failed', 'unable', 'cannot analyze']
        response_lower = response.lower()
        
        if any(indicator in response_lower for indicator in error_indicators):
            return False
        
        return True
        
    except Exception as e:
        return False