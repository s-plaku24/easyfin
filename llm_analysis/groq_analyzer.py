from groq import Groq
import os
import json
from datetime import datetime
from llm_analysis.prompt_processor import (
    create_batch_analysis_prompt,
    parse_batch_response,
    clean_response
)
from config import DATA_LIMITS

def analyze_stock_batch_groq(symbol, raw_data=None):
    """Analyze all questions for a stock in one API call with FMP data"""
    try:
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            print("[ERROR] GROQ_API_KEY not found")
            return {}
        
        client = Groq(api_key=api_key)
        
        prompt = create_batch_analysis_prompt(symbol, raw_data)
        
        if not prompt:
            print(f"[ERROR] Failed to create prompt for {symbol}")
            return {}
        
        # Monitor prompt size for Groq limits (llama3-8b-8192)
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 4  # Rough estimate: 4 chars per token
        
        print(f"[INFO] Prompt for {symbol}: {prompt_length} chars (~{estimated_tokens} tokens)")
        
        # Truncate if too close to token limit (leave room for response)
        max_input_tokens = 6000  # Conservative limit to leave room for response
        if estimated_tokens > max_input_tokens:
            max_chars = max_input_tokens * 4
            prompt = prompt[:max_chars] + "\n\nPlease analyze the available data and provide answers:"
            print(f"[WARN] Truncated prompt for {symbol} to fit token limits")
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama3-8b-8192",
                max_tokens=2000,  # Conservative output limit
                temperature=0.7,
                top_p=1,
                stream=False
            )
            
            response = chat_completion.choices[0].message.content
            cleaned_response = clean_response(response)
            
            # Parse the batch response to extract individual answers
            answers = parse_batch_response(cleaned_response, symbol)
            
            print(f"[INFO] Groq analysis completed for {symbol}: {len(answers)} answers")
            return answers
            
        except Exception as api_error:
            print(f"[ERROR] Groq API call failed for {symbol}: {api_error}")
            
            # Check if it's a token limit error
            if "token" in str(api_error).lower() or "length" in str(api_error).lower():
                print(f"[ERROR] Token limit exceeded for {symbol}, trying with reduced data...")
                return analyze_with_minimal_data(symbol, raw_data, client)
            
            return {}
        
    except Exception as e:
        print(f"[ERROR] Groq batch analysis failed for {symbol}: {e}")
        return {}

def analyze_with_minimal_data(symbol, raw_data, client):
    """Fallback analysis with minimal data when token limits are hit"""
    try:
        print(f"[INFO] Attempting minimal data analysis for {symbol}")
        
        # Create a very minimal prompt with only essential data
        minimal_data = extract_minimal_data(raw_data, symbol)
        
        from database.questions_handler import get_all_questions
        questions = get_all_questions()
        
        if not questions:
            return {}
        
        # Create a much shorter prompt
        questions_text = ""
        for q in questions[:3]:  # Only first 3 questions to save tokens
            questions_text += f"{q['id']}: {q['question_text']}\n"
        
        minimal_prompt = f"""
Analyze this stock data and answer these questions concisely (≤50 words each):

{questions_text}

Data for {symbol}:
{json.dumps(minimal_data, indent=1)}

Format: question_id: [id] Answer [id]: [answer]
"""
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": minimal_prompt}],
            model="llama3-8b-8192",
            max_tokens=1000,
            temperature=0.7
        )
        
        response = chat_completion.choices[0].message.content
        answers = parse_batch_response(response, symbol)
        
        print(f"[INFO] Minimal analysis completed for {symbol}: {len(answers)} answers")
        return answers
        
    except Exception as e:
        print(f"[ERROR] Minimal analysis failed for {symbol}: {e}")
        return {}

def extract_minimal_data(raw_data, symbol):
    """Extract only the most essential data points for analysis"""
    try:
        minimal = {'symbol': symbol}
        
        if raw_data and raw_data.get('quote'):
            quote = raw_data['quote']
            minimal['current'] = {
                'price': quote.get('price'),
                'change_pct': quote.get('changesPercentage'),
                'volume': quote.get('volume'),
                'market_cap': quote.get('marketCap'),
                'pe': quote.get('pe')
            }
        
        if raw_data and raw_data.get('historical'):
            historical = raw_data['historical'].get('historical', [])
            if historical:
                # Only last 3 days
                minimal['recent'] = historical[:3]
        
        return minimal
        
    except Exception as e:
        print(f"[ERROR] Failed to extract minimal data: {e}")
        return {'symbol': symbol, 'error': 'data_extraction_failed'}

def test_groq_connection():
    """Test Groq API connection with token-aware test"""
    try:
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            print("[ERROR] GROQ_API_KEY not found")
            return False
        
        client = Groq(api_key=api_key)
        
        test_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Test connection. Respond with 'OK' and current token limit status.",
                }
            ],
            model="llama3-8b-8192",
            max_tokens=50
        )
        
        response = test_completion.choices[0].message.content
        print(f"[INFO] Groq test response: {response}")
        return "OK" in response or "ok" in response.lower()
        
    except Exception as e:
        print(f"[ERROR] Groq connection test failed: {e}")
        return False

def get_token_usage_estimate(text):
    """Get rough estimate of token usage for a text"""
    # Rough approximation: 4 characters per token for English text
    return len(text) // 4

def validate_prompt_size(prompt, max_tokens=6000):
    """Validate that prompt is within acceptable token limits"""
    estimated_tokens = get_token_usage_estimate(prompt)
    
    if estimated_tokens > max_tokens:
        print(f"[WARN] Prompt too large: ~{estimated_tokens} tokens (max: {max_tokens})")
        return False
    
    print(f"[INFO] Prompt size OK: ~{estimated_tokens} tokens")
    return True