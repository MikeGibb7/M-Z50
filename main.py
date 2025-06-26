import requests
import re
import json
from sp_tickers import get_sp500_companies as gsp

def extract_chart_data_from_url(ticker):
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
        return data
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        return None

# Example usage
tickers = gsp()
print(tickers)
for ticker, _ in tickers:
    earnings_data = extract_chart_data_from_url(ticker)
    if earnings_data:
        for point in earnings_data:
            print(f"Date: {point['x']}, Estimated: {point['epsEstimated']}, Actual: {point['epsActual']}")