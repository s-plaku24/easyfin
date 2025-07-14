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
            return None
        
        questions = get_all_questions()
        if not questions:
            return None
        
        questions_text = ""
        for q in questions:
            questions_text += f"{q['id']}: {q['question_text']}\n"
        
        optimized_data = optimize_data_for_tokens(raw_data, symbol)
        data_json = json.dumps(optimized_data, default=str, indent=1)
        
        if len(data_json) > DATA_LIMITS['max_json_size']:
            data_json = data_json[:DATA_LIMITS['max_json_size']] + "..."
        
        full_prompt = BASE_ANALYSIS_PROMPT.format(
            symbol=symbol,
            questions=questions_text,
            json_data=data_json
        )
        
        return full_prompt
    except Exception:
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
                    range_position = ((current_price - year_low) / (year_high - year_low)) * 100
                    optimized['computed_metrics'] = {
                        'year_range_position_percent': round(range_position, 2),
                        'distance_from_high_percent': round(((year_high - current_price) / year_high) * 100, 2)
                    }
            except:
                pass
        
        return optimized
    except Exception:
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
            
            if line.startswith('question_id:'):
                if current_question_id and current_answer:
                    answers[current_question_id] = current_answer.strip()
                
                try:
                    current_question_id = int(line.split(':')[1].strip())
                    current_answer = ""
                except:
                    current_question_id = None
            
            elif line.startswith('Answer') and ':' in line and current_question_id:
                answer_text = line.split(':', 1)[1].strip()
                current_answer = answer_text
            
            elif current_question_id and current_answer and line:
                if not line.startswith('symbol:') and not line.startswith('question_id:'):
                    current_answer += " " + line
        
        if current_question_id and current_answer:
            answers[current_question_id] = current_answer.strip()
        
        return answers
    except Exception:
        return {}