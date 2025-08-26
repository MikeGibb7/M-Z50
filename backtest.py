from collections import defaultdict
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.error import HTTPError
from dateutil.relativedelta import relativedelta
import time


def calculate_spy_return(start_date, end_date):
    spy = yf.download('SPY', start=start_date, end=end_date, progress=False)

    if spy.empty:
        print("No SPY data found for the given date range.")
        return None

    start_price = spy['Close'].iloc[0].item()
    end_price = spy['Close'].iloc[-1].item()

    spy_return = (end_price - start_price) / start_price * 100

    print(f"SPY return from {start_date} to {end_date}: {spy_return}")
    return spy_return

def backtest(portfolio, start, end):
    if not portfolio:
        print("No portfolio data provided.")
        return 0, 0
    
    data = []

    tickers = [ticker for ticker, _ in portfolio]
    iterations = 0
    total_ret = 0

    start_dt = datetime.fromisoformat(start)
    histories = yf.download(tickers, start=start_dt, end=end, group_by='ticker')
    
    for ticker, weight in portfolio:
        try:
            if ticker in histories and not histories[ticker].empty:
                closes = histories[ticker]['Close'].dropna()
                if len(closes) >= 2:
                    start_price = closes.iloc[0]
                    end_price = closes.iloc[-1]
                    ret = ((end_price - start_price) / start_price) * 100
                else:
                    ret = 0
            else:
                ret = 0
                print(f"No data found for {ticker}")

            data.append({
                'Ticker': ticker,
                'return': ret,
                'weight': weight,
            })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            data.append({
                'Ticker': ticker,
                'return': 0,
                'weight': weight,
            })

    df = pd.DataFrame(data)

    # Calculate weighted return
    df['Weighted_Return'] = (df['weight'] / 100) * df['return']
    total_ret = df['Weighted_Return'].sum()

    spy_ret = calculate_spy_return(start, end)

    return total_ret, spy_ret
