import json
from config import BASE_ANALYSIS_PROMPT
from database.raw_data_handler import get_combined_raw_data

def create_analysis_prompt(symbol, question_text, raw_data=None):
    """
    Create the analysis prompt for a specific question
    """
    try:
        # Get raw data if not provided
        if raw_data is None:
            raw_data = get_combined_raw_data(symbol)
        
        if not raw_data:
            return None
        
        # Convert to JSON string for the prompt
        data_json = json.dumps(raw_data, default=str, indent=2)
        
        # Create the full prompt
        full_prompt = BASE_ANALYSIS_PROMPT.format(
            json_data=data_json,
            question=question_text
        )
        
        return full_prompt
        
    except Exception as e:
        print(f"Error creating prompt for {symbol}: {str(e)}")
        return None

def clean_response(response):
    """
    Clean and format the LLM response
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
        print(f"Error cleaning response: {str(e)}")
        return response

def validate_analysis_response(response):
    """
    Validate that the analysis response is reasonable
    """
    if not response:
        return False
    
    try:
        # Basic validation - check if response has reasonable length
        if len(response.strip()) < 10:
            return False
        
        # Check if it's not just an error message
        error_indicators = ['error', 'failed', 'unable', 'cannot analyze']
        response_lower = response.lower()
        
        if any(indicator in response_lower for indicator in error_indicators):
            return False
        
        return True
        
    except Exception as e:
        print(f"Error validating response: {str(e)}")
        return False