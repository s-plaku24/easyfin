# Automated Stock Analysis with AI

An automated financial analysis system that fetches real-time stock data, analyzes it using AI, and stores insights in a PostgreSQL database. The system runs daily via GitHub Actions and provides structured answers to predefined financial questions.

## 🎯 Project Overview

This project automatically:
- Fetches current market data and price history from Financial Modeling Prep (FMP) API
- Analyzes 12 major stocks using Groq's LLaMA model
- Stores structured analysis results in PostgreSQL
- Runs daily at 6 AM Berlin time via GitHub Actions
- Provides failure resilience and comprehensive logging

## 📊 Analyzed Stocks

The system analyzes these 12 stocks daily:
- **AAPL** (Apple), **MSFT** (Microsoft), **TSLA** (Tesla)
- **BABA** (Alibaba), **SAP** (SAP SE), **AMZN** (Amazon)
- **TM** (Toyota), **SHEL** (Shell), **NFLX** (Netflix)
- **ASML** (ASML Holding), **NVO** (Novo Nordisk), **SHOP** (Shopify)

## 🤖 AI Analysis Questions

Each stock is analyzed against these financial questions:
1. Current performance vs recent historical trend
2. Valuation assessment (overvalued/undervalued)
3. Key financial strengths or weaknesses
4. Insider and institutional activity insights
5. Volatility and risk profile vs market

## 🏗️ Architecture

```
├── data_extraction/         # FMP API integration
│   └── fmp_fetcher.py       # Fetch quote and historical data
├── database/                # Database operations
│   ├── answers_handler.py   # AI analysis results storage
│   ├── db_connection.py     # Connection management
│   ├── questions_handler.py # Analysis questions management
│   ├── raw_data_handler.py  # Raw market data storage
│   └── stocks_handler.py    # Stock information
├── llm_analysis/            # AI analysis engine
│   ├── groq_analyzer.py     # Groq API integration
│   └── prompt_processor.py  # Prompt optimization
├── .github/workflows/       # Automation
│   └── daily-stock-analysis.yml
├── main.py                  # Main execution pipeline
└── config.py                # Configuration settings
```

## 🗄️ Database Schema

### Core Tables
- **`stocks`**: Company information (symbol, name, exchange, sector)
- **`questions_templates`**: Analysis questions stored in database
- **`raw_data`**: JSON storage of FMP API responses
- **`answers`**: AI-generated analysis results with question references

## ⚙️ Installation & Setup

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd stock-analysis-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```
### 2. API Keys Setup
This project requires two API keys to function properly. Both services offer free tiers suitable for this project.

#### Financial Modeling Prep (FMP) API Key
**Free Tier**: 250 API calls per day (sufficient for 12 stocks × 2 endpoints)

1. **Create Account**
   - Visit financialmodelingprep.com
   - Click "Get API Key" or "Sign Up"
   - Register with your email and create a password

2. **Get API Key**
   - After registration, log into your dashboard
   - Navigate to "API Keys" or "Dashboard" section
   - Copy your API key (format: `your_api_key_here`)
   - **Important**: The free tier provides 250 calls/day, which is perfect for this project's daily analysis of 12 stocks

#### Groq API Key (LLaMA 3)
**Free Tier**: Generous limits for AI model usage

1. **Create Account**
   - Visit console.groq.com
   - Click "Sign Up" or "Get Started"
   - Sign up with Google, GitHub, or email

2. **Generate API Key**
   - After logging in, go to "API Keys" section
   - Click "Create API Key"
   - Give it a descriptive name (e.g., "Stock Analysis Project")
   - Copy the generated key (format: `gsk_...`)
   - **Important**: Save this key immediately - you won't be able to see it again

### 3. Environment Variables
Create a `.env` file:
```env

# Database configuration
DB_HOST=your_database_host_ip
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_username
DB_PASSWORD=your_postgresql_password

# API keys
GROQ_API_KEY=your_groq_api_key
FMP_API_KEY=your_fmp_api_key
```

## 🚀 Usage

### Manual Execution
```bash
python main.py
```

### Automated Execution
The GitHub Action runs daily at 4:00 AM UTC (6:00 AM Berlin time):
```yaml
schedule:
  - cron: '0 4 * * *'
```

## 📋 API Requirements

### Financial Modeling Prep (FMP)
- **Required endpoints**: Quote, Historical Price
- **Rate limits**: Respects API limits with 2-second delays
- **Free tier**: 250 requests/day (sufficient for 12 stocks × 2 endpoints)

### Groq (LLaMA 3)
- **Model**: `llama3-8b-8192`
- **Token limits**: Optimized prompts for 8K context window
- **Rate limits**: Built-in retry logic and fallback strategies

## 🔧 Configuration Options

### Stock Selection
Modify `STOCK_SYMBOLS` in `config.py`:
```python
STOCK_SYMBOLS = ["AAPL", "MSFT", "TSLA", ...]  # Add/remove stocks
```

### Analysis Questions
Questions are stored in database and can be modified:
```python
from database.questions_handler import insert_question
insert_question("Your new analysis question here")
```

### Data Retention
Configure cleanup policies in `config.py`:
```python
DATA_LIMITS = {
    'historical_days': 10,        # Days of price history
    'max_json_size': 25000,      # Max data size for AI analysis
    'truncate_threshold': 20000   # When to truncate data
}
```

## 📊 Output Format

Each analysis produces structured answers:
```json
{
  "symbol": "AAPL",
  "question_id": 1,
  "answer_text": "Apple shows strong upward momentum with 3.2% gain over past week, outperforming its 50-day average. Volume increased 15% suggesting institutional interest.",
  "created_at": "2025-07-15T06:00:00Z"
}
```

## 🛡️ Error Handling & Resilience

- **API Failures**: Continues with existing data if fresh data unavailable
- **Rate Limiting**: Automatic delays and retry logic
- **Token Limits**: Dynamic data truncation for AI model constraints
- **Database Issues**: Transaction rollback and detailed error logging
- **Partial Failures**: Processes all possible stocks even if some fail

## 📈 Performance Metrics

- **Processing Time**: ~5 minutes for 12 stocks
- **Success Rate**: >90% analysis completion
- **Data Efficiency**: Optimized prompts fit within token limits
- **API Usage**: 24 FMP calls + 12 Groq calls per day

## 🔍 Monitoring & Logs

### GitHub Actions Monitoring
- Automatic issue creation on failures
- Error log artifacts (7-day retention)
- Email notifications for workflow failures

### Local Logging
```bash
# View logs
tail -f stock_analysis.log

# Check specific component
python -c "from database.answers_handler import get_dashboard_data; print(get_dashboard_data())"
```

## 🚨 Troubleshooting

### Common Issues
1. **API Key Errors**: Verify `.env` file and API key validity
2. **Database Connection**: Check PostgreSQL credentials and network access
3. **Token Limit Exceeded**: Review data size limits in `config.py`
4. **Missing Dependencies**: Ensure all `requirements.txt` packages installed

## Thank YOU!
