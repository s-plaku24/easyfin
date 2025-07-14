from groq import Groq
import os
import json
from llm_analysis.prompt_processor import create_batch_analysis_prompt, parse_batch_response

def analyze_stock_batch_groq(symbol, raw_data=None):
    """Analyze all questions for a stock in one API call with FMP data"""
    try:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            return {}
        
        client = Groq(api_key=api_key)
        prompt = create_batch_analysis_prompt(symbol, raw_data)
        
        if not prompt:
            return {}
        
        # Monitor prompt size for Groq limits
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 4
        
        # Truncate if too close to token limit
        if estimated_tokens > 6000:
            max_chars = 6000 * 4
            prompt = prompt[:max_chars] + "\n\nPlease analyze the available data and provide answers:"
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                max_tokens=2000,
                temperature=0.7,
                top_p=1,
                stream=False
            )
            
            response = chat_completion.choices[0].message.content
            
            if not response or len(response.strip()) < 50:
                return {}
            
            # Parse the batch response to extract individual answers
            answers = parse_batch_response(response, symbol)
            
            if not answers:
                # Try fallback parsing
                answers = fallback_parse_response(response)
            
            return answers
            
        except Exception as api_error:
            # Check if it's a token limit error
            if "token" in str(api_error).lower() or "length" in str(api_error).lower():
                return analyze_with_minimal_data(symbol, raw_data, client)
            return {}
        
    except Exception:
        return {}

def fallback_parse_response(response):
    """Fallback parser that's more flexible with response format"""
    try:
        if not response:
            return {}
        
        answers = {}
        lines = response.split('\n')
        
        import re
        for line in lines:
            line = line.strip()
            answer_match = re.search(r'Answer\s+(\d+):\s*(.*)', line, re.IGNORECASE)
            if answer_match:
                question_id = int(answer_match.group(1))
                answer_text = answer_match.group(2).strip()
                
                if answer_text:
                    answers[question_id] = answer_text
        
        return answers
    except Exception:
        return {}

def analyze_with_minimal_data(symbol, raw_data, client):
    """Fallback analysis with minimal data when token limits are hit"""
    try:
        minimal_data = extract_minimal_data(raw_data, symbol)
        
        from database.questions_handler import get_all_questions
        questions = get_all_questions()
        
        if not questions:
            return {}
        
        questions_text = ""
        for q in questions[:3]:
            questions_text += f"{q['id']}: {q['question_text']}\n"
        
        minimal_prompt = f"""
Analyze this stock data and answer these questions concisely (≤50 words each):

{questions_text}

Data for {symbol}:
{json.dumps(minimal_data, indent=1)}

Format each answer as: "Answer X: [your answer]" where X is the question number.
"""
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": minimal_prompt}],
            model="llama3-8b-8192",
            max_tokens=1000,
            temperature=0.7
        )
        
        response = chat_completion.choices[0].message.content
        return fallback_parse_response(response)
        
    except Exception:
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
                minimal['recent'] = historical[:3]
        
        return minimal
    except Exception:
        return {'symbol': symbol, 'error': 'data_extraction_failed'}

def test_groq_connection():
    """Test Groq API connection"""
    try:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            return False
        
        client = Groq(api_key=api_key)
        test_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Test connection. Respond with 'OK'."}],
            model="llama3-8b-8192",
            max_tokens=50
        )
        
        response = test_completion.choices[0].message.content
        return "OK" in response or "ok" in response.lower()
    except Exception:
        return False