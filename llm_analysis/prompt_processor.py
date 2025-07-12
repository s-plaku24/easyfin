import json
from config import BASE_ANALYSIS_PROMPT, DATA_LIMITS
from database.raw_data_handler import get_combined_raw_data
from database.questions_handler import get_all_questions

def create_batch_analysis_prompt(symbol, raw_data=None):
    """Creates a prompt with all questions for batch analysis using FMP data"""
    try:
        if raw_data is None:
            raw_data = get_combined_raw_data(symbol)
        
        if not raw_data:
            print(f"[ERROR] No raw data found for {symbol}")
            return None
        
        # Get all questions from database
        questions = get_all_questions()
        if not questions:
            print("[ERROR] No questions found in database")
            return None
        
        # Format questions for the prompt
        questions_text = ""
        for q in questions:
            questions_text += f"{q['id']}: {q['question_text']}\n"
        
        # Optimize data for token limits
        optimized_data = optimize_data_for_tokens(raw_data, symbol)
        data_json = json.dumps(optimized_data, default=str, indent=1)  # Compact indentation
        
        # Check final size
        if len(data_json) > DATA_LIMITS['max_json_size']:
            print(f"[WARN] Data still too large for {symbol}, further truncating...")
            data_json = data_json[:DATA_LIMITS['max_json_size']] + "..."
        
        full_prompt = BASE_ANALYSIS_PROMPT.format(
            symbol=symbol,
            questions=questions_text,
            json_data=data_json
        )
        
        print(f"[INFO] Created prompt for {symbol}: {len(full_prompt)} characters")
        return full_prompt
        
    except Exception as e:
        print(f"[ERROR] Failed to create batch analysis prompt for {symbol}: {e}")
        return None


def optimize_data_for_tokens(raw_data, symbol):
    """Optimize FMP data structure to minimize token usage while preserving analysis value"""
    try:
        optimized = {
            'symbol': symbol,
            'data_source': 'FMP_API'
        }
        
        # Process quote data (current market data)
        if raw_data.get('quote'):
            quote = raw_data['quote']
            optimized['current_market'] = {
                'price': quote.get('price'),
                'change': quote.get('change'),
                'change_percent': quote.get('changesPercentage'),
                'volume': quote.get('volume'),
                'market_cap': quote.get('marketCap'),
                'pe_ratio': quote.get('pe'),
                'day_range': {
                    'low': quote.get('dayLow'),
                    'high': quote.get('dayHigh')
                },
                'year_range': {
                    'low': quote.get('yearLow'),
                    'high': quote.get('yearHigh')
                },
                'averages': {
                    'volume_avg': quote.get('avgVolume'),
                    'price_50d': quote.get('priceAvg50'),
                    'price_200d': quote.get('priceAvg200')
                },
                'fundamentals': {
                    'eps': quote.get('eps'),
                    'shares_outstanding': quote.get('sharesOutstanding')
                }
            }
        
        # Process historical data (keep only essential recent data)
        if raw_data.get('historical') and raw_data['historical'].get('historical'):
            historical = raw_data['historical']['historical']
            
            # Keep only last 7 days to save tokens but provide trend analysis
            recent_history = historical[:7] if len(historical) >= 7 else historical
            
            optimized['price_history'] = []
            for record in recent_history:
                optimized['price_history'].append({
                    'date': record.get('date'),
                    'close': record.get('close'),
                    'volume': record.get('volume'),
                    'change_pct': record.get('changePercent')
                })
        
        # Add computed metrics for analysis
        if optimized.get('current_market') and optimized.get('price_history'):
            try:
                current_price = optimized['current_market']['price']
                year_high = optimized['current_market']['year_range']['high']
                year_low = optimized['current_market']['year_range']['low']
                
                if current_price and year_high and year_low:
                    # Calculate position in 52-week range
                    range_position = ((current_price - year_low) / (year_high - year_low)) * 100
                    optimized['computed_metrics'] = {
                        'year_range_position_percent': round(range_position, 2),
                        'distance_from_high_percent': round(((year_high - current_price) / year_high) * 100, 2)
                    }
            except:
                pass  # Skip computed metrics if calculation fails
        
        return optimized
        
    except Exception as e:
        print(f"[ERROR] Failed to optimize data for tokens: {e}")
        return raw_data

def parse_batch_response(response, symbol):
    """Parse the batch response and extract individual answers"""
    try:
        if not response:
            return {}
        
        answers = {}
        lines = response.split('\n')
        current_question_id = None
        current_answer = ""
        
        for line in lines:
            line = line.strip()
            
            # Look for question_id pattern
            if line.startswith('question_id:'):
                # Save previous answer if exists
                if current_question_id and current_answer:
                    answers[current_question_id] = current_answer.strip()
                
                # Extract new question ID
                try:
                    current_question_id = int(line.split(':')[1].strip())
                    current_answer = ""
                except:
                    current_question_id = None
            
            # Look for answer pattern
            elif line.startswith('Answer') and ':' in line and current_question_id:
                # Extract answer text after the colon
                answer_text = line.split(':', 1)[1].strip()
                current_answer = answer_text
            
            # Continue building current answer if we're in an answer block
            elif current_question_id and current_answer and line:
                if not line.startswith('symbol:') and not line.startswith('question_id:'):
                    current_answer += " " + line
        
        # Don't forget the last answer
        if current_question_id and current_answer:
            answers[current_question_id] = current_answer.strip()
        
        print(f"[INFO] Parsed {len(answers)} answers for {symbol}")
        return answers
        
    except Exception as e:
        print(f"[ERROR] Failed to parse batch response: {e}")
        return {}

def clean_response(response):
    """Clean and optimize response text"""
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
    """Validate if the analysis response is acceptable"""
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