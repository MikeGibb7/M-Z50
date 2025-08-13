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

def fetch_all_earnings(tickers, start_date, end_date, max_workers=5):
    earnings = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(extract_chart_data_from_url, ticker, start_date, end_date): ticker
            for ticker, _ in tickers
        }
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                data = future.result()
                earnings[ticker] = data
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
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

# Example usage
def main():
    choice = input("Enter 'b' for backtest, 't' for today test, 'g' for growth screener: ").strip().lower()
    
    if choice == 'b':
        years = int(input("Enter number of years to backtest: "))
        dates = generate_quarter_dates(years)
        print(f"Starting {years}-year backtest...")
        backtest(dates, screentype='s')
        print("Backtest completed.")
    elif choice == 't':
        dates = [(date.today().isoformat(), date.today().isoformat())]
        print("Starting today test...")
        backtest(dates, screentype='s')
        print("Today test completed.")
    elif choice == 'g':
        years = int(input("Enter number of years for growth screener: "))
        dates = generate_quarter_dates(years)
        print(f"Starting {years}-year growth screener...")
        backtest(dates, screentype='g', years=years)
        print("Growth screener completed.")
    elif choice == 'q':
        print("Exiting the program.")
        exit(0)
    else:
        print("Invalid input. Please enter 'b', 't', 'g', or 'q'.")

def backtest(dates, screentype, years):
    capital = 100000
    spy_cap = 100000

    today = date.today()

    # Earnings start date = 1 year before the user's range
    earnings_start = (today - relativedelta(years=years+1)).isoformat()
    earnings_end = today.isoformat()

    tickers, changes_df = gsp()
    quarter_changes = get_quarterly_ticker_changes(changes_df, dates)

    # Add removed tickers
    for q in quarter_changes:
        for rem in q['removed']:
            if rem not in tickers:
                tickers.append(rem)

    # Add added tickers
    for q in quarter_changes:
        for add in q['added']:
            if add not in tickers:
                tickers.append(add)

    tickers = fetch_industries(tickers)

    if "GOOGL" in [t[0] for t in tickers]:
        tickers = [(t, ind) for t, ind in tickers if t != "GOOGL"]

    # Fetch earnings with multithreading
    earnings = fetch_all_earnings(tickers, earnings_start, earnings_end, max_workers=5)

    ticker_list = [(t, ind) for t, ind in tickers if earnings.get(t)]

    # Portfolio initial point: start of user's range
    first_portfolio_date = (today - relativedelta(years=years)).replace(month=1, day=1).isoformat()

    portfolio = [{
        'Date': first_portfolio_date,
        'Quarter Return': 0,
        'Capital': capital,
        'SPY Return': 0,
        'SPY Capital': spy_cap
    }]

    for start_date, end_date in dates:
        for change in quarter_changes:
            start_dt = datetime.fromisoformat(start_date)
            change_dt = datetime.fromisoformat(change['start'])

            if change_dt <= start_dt:
                for added_ticker in change['added']:
                    if added_ticker not in [t[0] for t in ticker_list]:
                        industry = fetch_industry(added_ticker)
                        ticker_list.append((added_ticker, industry))
                ticker_list = [t for t in ticker_list if t[0] not in change['removed']]
            elif change_dt > start_dt:
                ticker_list = [t for t in ticker_list if t[0] not in change['added']]

        if screentype == 'g':
            month_ret, spy_ret = growth_screen(ticker_list, earnings, start_date, end_date)
        else:
            month_ret, spy_ret = screen(ticker_list, earnings, start_date, end_date)

        capital += capital * month_ret / 100
        if spy_ret is not None:
            spy_cap += spy_cap * spy_ret / 100

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
