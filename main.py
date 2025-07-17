import requests
import re
import json
from sp_tickers import get_sp500_companies as gsp
import yfinance as yf
from datetime import datetime, timedelta
from screener import screen
from growth_screener import growth_screen
import matplotlib.pyplot as plt
import pandas as pd

def graph_portfolio(portfolio):
    df = pd.DataFrame(portfolio)

    # Make sure dates are datetime type for proper plotting
    df['Date'] = pd.to_datetime(df['Date'])

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['Date'], df['Capital'], label='Portfolio Capital', marker='o')
    plt.plot(df['Date'], df['SPY Capital'], label='SPY Capital', marker='o')

    # Labels and title
    plt.title('Portfolio vs SPY Capital Over Time')
    plt.xlabel('Date')
    plt.ylabel('Capital ($)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Show the plot
    plt.show()

def extract_chart_data_from_url(ticker, start_date=None, end_date=None):
    ticker = ticker.replace('-', '.')
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

def get_quarterly_ticker_changes(changes_df, dates):
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

# Example usage
def main():
    choice = input("Enter 'b' for backtest or 't' for today test: ").strip().lower()
    
    if choice == 'b':
        dates = [
        ("2021-01-01", "2021-03-31"),  # 2021 Q1
        ("2021-04-01", "2021-06-30"),  # 2021 Q2
        ("2021-07-01", "2021-09-30"),  # 2021 Q3
        ("2021-10-01", "2021-12-31"),  # 2021 Q4
        ("2022-01-01", "2022-03-31"),  # 2022 Q1
        ("2022-04-01", "2022-06-30"),  # 2022 Q2
        ("2022-07-01", "2022-09-30"),  # 2022 Q3
        ("2022-10-01", "2022-12-31"),  # 2022 Q4
        ("2023-01-01", "2023-03-31"),  # 2023 Q1
        ("2023-04-01", "2023-06-30"),  # 2023 Q2
        ("2023-07-01", "2023-09-30"),  # 2023 Q3
        ("2023-10-01", "2023-12-31"),  # 2023 Q4
        ("2024-01-01", "2024-03-31"),  # 2024 Q1
        ("2024-04-01", "2024-06-30"),  # 2024 Q2
        ("2024-07-01", "2024-09-30"),  # 2024 Q3
        ("2024-10-01", "2024-12-31"),  # 2024 Q4
        ("2025-01-01", "2025-03-31"),  # 2025 Q1
        ("2025-04-01", "2025-06-30"),  # 2025 Q2
        ]
        print("Starting backtest...")
        backtest(dates, screentype='s')
        print("Backtest completed.")
    elif choice == 't':
        #######################################
        # ("2025-07-01", "2025-09-30"),  # 2025 Q3
        # ("2025-10-01", "2025-12-31")   # 2025 Q4
        dates = [
        ("2025-07-02", "2025-07-03")
        ]
        print("Starting today test...")
        backtest(dates, screentype='s')
        print("Today test completed.")
    elif choice == 'g':
        dates = [
        ("2021-01-01", "2021-03-31"),  # 2021 Q1
        ("2021-04-01", "2021-06-30"),  # 2021 Q2
        ("2021-07-01", "2021-09-30"),  # 2021 Q3
        ("2021-10-01", "2021-12-31"),  # 2021 Q4
        ("2022-01-01", "2022-03-31"),  # 2022 Q1
        ("2022-04-01", "2022-06-30"),  # 2022 Q2
        ("2022-07-01", "2022-09-30"),  # 2022 Q3
        ("2022-10-01", "2022-12-31"),  # 2022 Q4
        ("2023-01-01", "2023-03-31"),  # 2023 Q1
        ("2023-04-01", "2023-06-30"),  # 2023 Q2
        ("2023-07-01", "2023-09-30"),  # 2023 Q3
        ("2023-10-01", "2023-12-31"),  # 2023 Q4
        ("2024-01-01", "2024-03-31"),  # 2024 Q1
        ("2024-04-01", "2024-06-30"),  # 2024 Q2
        ("2024-07-01", "2024-09-30"),  # 2024 Q3
        ("2024-10-01", "2024-12-31"),  # 2024 Q4
        ("2025-01-01", "2025-03-31"),  # 2025 Q1
        ("2025-04-01", "2025-06-30"),  # 2025 Q2
        ]
        print("Starting growth screener...")
        backtest(dates, screentype='g')
        print("Growth screener completed.")
    elif choice == 'q':
        print("Exiting the program.")
        exit(0)
    else:
        print("Invalid input. Please enter 'b' or 't'.")

def backtest(dates, screentype):

    capital = 100000
    spy_cap = 100000

    start_date="2019-01-01"
    end_date="2025-07-03"

    tickers, changes_df = gsp()  # your get_sp500_companies() wrapper
    quarter_changes = get_quarterly_ticker_changes(changes_df, dates)
    tickers.extend([rem for q in quarter_changes for rem in q['removed']])
    
    # Add removed tickers if not already in the list
    for q in quarter_changes:
        for rem in q['removed']:
            if rem not in tickers:
                tickers.append(rem)

    # Add added tickers if not already in the list
    for q in quarter_changes:
        for add in q['added']:
            if add not in tickers:
                tickers.append(add)

    tickers = fetch_industries(tickers)
    ticker_list = []
    earnings = {}
    
    for ticker, industry in tickers:
        if ticker != "GOOGL":
            earnings_data = extract_chart_data_from_url(ticker, start_date, end_date)
            earnings[ticker] = earnings_data
            if earnings_data:
                ticker_list.append((ticker, industry))
        # dates = earnings_data['x']
        
        # if earnings_data:
        #     for point in earnings_data:
        #         print(f"Date: {point['x']}, Estimated: {point['epsEstimated']}, Actual: {point['epsActual']}")
    
    portfolio = []
    portfolio.append({
        'Date': "2021-01-01",
        'Quarter Return': 0,
        'Capital': capital,
        'SPY Return': 0,
        'SPY Capital': spy_cap
    })
    for start_date, end_date in dates:
        for change in quarter_changes:
            
            start_dt = datetime.fromisoformat(start_date)
            change_dt = datetime.fromisoformat(change['start'])

            if change_dt <= start_dt:
                # Add new tickers if not already in the list
                for added_ticker in change['added']:
                    if added_ticker not in [t[0] for t in ticker_list]:
                        # Find industry for this ticker (fallback to 'Unknown')
                        industry = fetch_industry(added_ticker)
                        ticker_list.append((added_ticker, industry))

                # Remove tickers that were removed before this quarter
                ticker_list = [t for t in ticker_list if t[0] not in change['removed']]
            elif change_dt > start_dt:
                # Remove tickers that were added after this quarter
                ticker_list = [t for t in ticker_list if t[0] not in change['added']]

        if screentype == 'g':
            month_ret, spy_ret = growth_screen(ticker_list, earnings, start_date, end_date)
        else:
            month_ret, spy_ret = screen(ticker_list, earnings, start_date, end_date)
        capital = capital + capital * month_ret / 100
        if spy_ret is not None:
            spy_cap = spy_cap + spy_cap * spy_ret / 100
        portfolio.append({
            'Date': end_date,
            'Quarter Return': round(float(month_ret), 2),
            'Capital': round(float(capital), 2),
            'SPY Return': round(float(spy_ret), 2) if spy_ret is not None else None,
            'SPY Capital': round(float(spy_cap), 2)
        })
    print(portfolio)
    graph_portfolio(portfolio)



if __name__ == "__main__":
    main()
