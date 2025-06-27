import requests
import re
import json
from sp_tickers import get_sp500_companies as gsp
import yfinance as yf
from datetime import datetime
from screener import screen

def extract_chart_data_from_url(ticker, start_date=None, end_date=None):
    url = f"https://www.alphaquery.com/stock/{ticker}/earnings-history"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page. {response.status_code}")
        return None

    html = response.text
    match = re.search(r'chartEarningsHistoryData\s*=\s*(\[\{.*?\}\])', html)
    if not match:
        print("Earnings data not found.")
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
        print("Error parsing JSON:", e)
        return None

# Example usage
def main():
    dates = [
    # ("2024-01-01", "2024-03-31"),  # Q1
    # ("2024-04-01", "2024-06-30"),  # Q2
    ("2024-07-01", "2024-09-30"),  # Q3
    ("2024-10-01", "2024-12-31")   # Q4
    ]
    capital = 100000

    start_date="2023-01-01"
    end_date="2025-01-01"

    tickers = gsp()
    ticker_list = []
    earnings = {}
    for ticker, industry in tickers[:20]:
        ticker_list.append((ticker, industry))
        earnings_data = extract_chart_data_from_url(ticker, start_date, end_date)
        earnings[ticker] = earnings_data
        # dates = earnings_data['x']
        
        # if earnings_data:
            # for point in earnings_data:
            #     print(f"Date: {point['x']}, Estimated: {point['epsEstimated']}, Actual: {point['epsActual']}")
    
    for start_date, end_date in dates:
        month_ret = screen(ticker_list, earnings, start_date, end_date)
        capital = capital + capital * month_ret / 100
    print(capital)



if __name__ == "__main__":
    main()
