# get_sp500.py

import pandas as pd
import requests

def get_sp500_companies():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    # Add headers to mimic a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        sp_table = pd.read_html(url, header=0)
        sp500_df = sp_table[0]

        stock_df = []
        for _, stock in sp500_df.iterrows():
            symbol = stock["Symbol"].replace('.', '-')  # optional fix for e.g., BRK.B
            stock_df.append(symbol)
            
        changes_df = sp_table[1]
        
        return stock_df, changes_df
    except Exception as e:
        print(f"Error fetching S&P 500 data: {e}")
        # Fallback to a basic list of major S&P 500 stocks
        fallback_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'JPM', 'JNJ']
        print("Using fallback stock list...")
        return fallback_stocks, pd.DataFrame()

def get_sp500_companies_windustry():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    # Add headers to mimic a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        sp_table = pd.read_html(url, header=0)
        sp500_df = sp_table[0]

        stock_df = []
        for _, stock in sp500_df.iterrows():
            symbol = stock["Symbol"].replace('.', '-')  # optional fix for e.g., BRK.B
            industry = stock["GICS Sub-Industry"]
            stock_df.append((symbol, industry))
            
        changes_df = sp_table[1]
        
        return stock_df, changes_df
    except Exception as e:
        print(f"Error fetching S&P 500 data: {e}")
        # Fallback to a basic list of major S&P 500 stocks with industries
        fallback_stocks = [
            ('AAPL', 'Technology Hardware'), ('MSFT', 'Software'), ('GOOGL', 'Internet Services'),
            ('AMZN', 'Internet Retail'), ('TSLA', 'Automobiles'), ('META', 'Internet Services'),
            ('NVDA', 'Semiconductors'), ('BRK-B', 'Insurance'), ('JPM', 'Banks'), ('JNJ', 'Pharmaceuticals')
        ]
        print("Using fallback stock list...")
        return fallback_stocks, pd.DataFrame()
