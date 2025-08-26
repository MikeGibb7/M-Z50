import requests
import re
import json
from sp_tickers import get_sp500_companies as gsp
import yfinance as yf
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta  
from screener import screen
from growth_screener import growth_screen
import matplotlib.pyplot as plt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


def extract_chart_data_from_url(ticker, start_date=None, end_date=None):
    ticker = ticker.replace('-', '.')
    url = f"https://www.alphaquery.com/stock/{ticker}/earnings-history"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)  # 10 second timeout

        if response.status_code != 200:
            print(f"Failed to fetch page for {ticker}. {response.status_code}")
            return None

        html = response.text
        match = re.search(r'chartEarningsHistoryData\s*=\s*(\[\{.*?\}\])', html)
        if not match:
            print(f"Earnings data not found for {ticker}.")
            return None

        raw_json = match.group(1)

        try:
            data = json.loads(raw_json)
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)

            if start_date or end_date:
                data = [
                    entry for entry in data
                    if (not start_date or datetime.fromisoformat(entry['x'][:10]) >= start_dt) and
                       (not end_date or datetime.fromisoformat(entry['x'][:10]) <= end_dt)
                ]
            
            for entry in data:
                entry['x'] = entry['x'][:10]
            
            return data
        
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {ticker}: {e}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"Timeout fetching data for {ticker}")
        return None
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def get_quarterly_ticker_changes(changes_df, dates):
    # Check if DataFrame is empty
    if changes_df.empty:
        print("No changes data available - returning empty results")
        return []
    
    # Step 1: Flatten column MultiIndex
    changes_df.columns = [' '.join(col).strip() for col in changes_df.columns]

    # Step 2: Clean + parse Date column
    changes_df['Date Date'] = changes_df['Date Date'].astype(str).str.strip()
    changes_df['Date Date'] = pd.to_datetime(changes_df['Date Date'], errors='coerce')

    # Step 3: Rename columns for clarity (optional but cleaner)
    changes_df = changes_df.rename(columns={
        'Date Date': 'Date',
        'Added Ticker': 'Added',
        'Removed Ticker': 'Removed'
    })

    results = []

    for start_str, end_str in dates:
        start = pd.to_datetime(start_str)
        end = pd.to_datetime(end_str)

        # Filter changes in date range
        quarter_changes = changes_df[(changes_df['Date'] >= start) & (changes_df['Date'] <= end)]

        # Collect added and removed tickers
        added = quarter_changes['Added'].dropna().unique().tolist()
        removed = quarter_changes['Removed'].dropna().unique().tolist()

        results.append({
            'start': start_str,
            'end': end_str,
            'added': added,
            'removed': removed
        })

    return results

def fetch_industries(ticker_list):
    results = []
    for ticker in ticker_list:
        try:
            info = yf.Ticker(ticker).info
            industry = info.get('industry')
        except Exception:
            print(f"error finding industry for: {ticker}")
            industry = 'Unknown'
        results.append((ticker, industry))
    return results

def fetch_industry(ticker):
    try:
        info = yf.Ticker(ticker).info
        industry = info.get('industry')
    except Exception:
        industry = 'Unknown'
    return industry

def fetch_all_earnings(tickers, start_date, end_date, max_workers=5):
    earnings = {}
    print(f"Fetching earnings for {len(tickers)} tickers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(extract_chart_data_from_url, ticker, start_date, end_date): ticker
            for ticker, _ in tickers
        }
        
        completed = 0
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            completed += 1
            if completed % 10 == 0:  # Progress update every 10 tickers
                print(f"Processed {completed}/{len(tickers)} tickers...")
            
            try:
                data = future.result(timeout=30)  # 30 second timeout per ticker
                earnings[ticker] = data
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                earnings[ticker] = None
    
    print(f"Earnings fetch completed. Found data for {len([e for e in earnings.values() if e is not None])} tickers.")
    return earnings

def generate_quarter_dates(years):
    """Generate list of (start_date, end_date) tuples for last N years up to current date."""
    today = date.today()
    end_year = today.year
    start_year = end_year - years + 1  # include current year

    quarters = [
        ("01-01", "03-31"),  # Q1
        ("04-01", "06-30"),  # Q2
        ("07-01", "09-30"),  # Q3
        ("10-01", "12-31"),  # Q4
    ]

    dates = []
    for year in range(start_year, end_year + 1):
        for start_suffix, end_suffix in quarters:
            start_date = date.fromisoformat(f"{year}-{start_suffix}")
            end_date = date.fromisoformat(f"{year}-{end_suffix}")

            # Skip if the quarter starts in the future
            if start_date > today:
                break  # stop processing further quarters in this year

            # If quarter ends in the future, cap it at today
            if end_date > today:
                end_date = today

            dates.append((start_date.isoformat(), end_date.isoformat()))
    
    return dates