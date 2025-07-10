# Stock Analysis Project - Updated Version

## Project Overview
This project automatically fetches stock data, analyzes them using an LLM by answering specific questions from the database, and stores the results in a PostgreSQL database. Questions are now stored in the database and can be modified without code changes.

## Key Changes
- Questions are now stored in the `questions_templates` table
- Each question is analyzed individually for each stock
- Answers are stored with question_id references
- Stock information is extracted and stored in the `stocks` table
- Raw data is stored in the `raw_data` table with foreign key constraints

## Database Schema
The project uses 4 main tables:
- `stocks`: Store stock information (symbol, name, sector, etc.)
- `questions_templates`: Store analysis questions
- `raw_data`: Store raw yfinance data
- `answers`: Store individual answers for each stock/question combination

## Installation
1. Create virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Set up `.env` file with your API keys: