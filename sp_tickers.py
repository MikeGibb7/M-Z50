# get_sp500.py

import pandas as pd
import requests

def get_sp500_companies():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()

        sp_table = pd.read_html(resp.text)   # pass HTML, not URL
        sp500_df = sp_table[0]

        stock_df = [stock["Symbol"].replace('.', '-') for _, stock in sp500_df.iterrows()]
        changes_df = sp_table[1]
        
        return stock_df, changes_df
    except Exception as e:
        print(f"Error fetching S&P 500 data: {e}")
        fallback_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'JPM', 'JNJ']
        print("Using fallback stock list...")
        return fallback_stocks, pd.DataFrame()


def get_sp500_companies_windustry():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()

        sp_table = pd.read_html(resp.text)   # pass HTML, not URL
        sp500_df = sp_table[0]

        stock_df = [
            (stock["Symbol"].replace('.', '-'), stock["GICS Sub-Industry"])
            for _, stock in sp500_df.iterrows()
        ]
        changes_df = sp_table[1]
        
        return stock_df, changes_df
    except Exception as e:
        print(f"Error fetching S&P 500 data: {e}")
        fallback_stocks = [
            ('AAPL', 'Technology Hardware'), ('MSFT', 'Software'), ('GOOGL', 'Internet Services'),
            ('AMZN', 'Internet Retail'), ('TSLA', 'Automobiles'), ('META', 'Internet Services'),
            ('NVDA', 'Semiconductors'), ('BRK-B', 'Insurance'), ('JPM', 'Banks'), ('JNJ', 'Pharmaceuticals')
        ]
        print("Using fallback stock list...")
        return fallback_stocks, pd.DataFrame()
