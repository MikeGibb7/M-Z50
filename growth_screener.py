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

def calculate_return(stock, years):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365 * years)
    hist = yf.Ticker(stock).history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    if len(hist) < 2:
        return None

    start_price = hist['Close'].iloc[0]
    end_price = hist['Close'].iloc[-1]
    return ((end_price - start_price) / start_price) * 100  # Return as percentage


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

def growth_screen(stock_df, earnings, start, end):

    data = []

    tickers = [ticker for ticker, _ in stock_df]
    iterations = 0
    total_cap = 0
    total_ret = 0
    
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    extended_start = start_dt - relativedelta(months=4)

    histories = yf.download(tickers, start=extended_start, end=end, group_by='ticker')
    # stock_info = 
    for ticker, industry in stock_df:

        hist_earn = earnings[ticker]
        
        end_dt = datetime.fromisoformat(start)
        if hist_earn is not None:
            filtered = [
                earn for earn in hist_earn 
                if datetime.fromisoformat(earn['x']) < end_dt
            ]
            filtered.sort(key=lambda e: datetime.fromisoformat(e['x']), reverse=True)

            # Take the most recent 4 quarters
            ttm_entries = filtered[:4]
            ttm_previous = filtered[4:8] if len(filtered) > 4 else []

            # Sum up epsActual values
            ttm_eps = sum(e['epsActual'] for e in ttm_entries)
            if ttm_eps:
                try:
                    iterations += 1
                    closes = histories[ticker]['Close'].dropna()
                    print(closes)

                    prev_range = closes[(closes.index >= extended_start) & (closes.index < start_dt)]
                    curr_range = closes[(closes.index >= start_dt) & (closes.index <= end_dt)]
                    print(f"Ticker: {ticker}, Previous Range: {prev_range}, Current Range: {curr_range}")
                    prev_ret = 0
                    if not prev_range.empty and len(prev_range) > 1:
                        prev_start = prev_range.iloc[0]
                        prev_end = prev_range.iloc[-1]
                        prev_ret = ((prev_end - prev_start) / prev_start) * 100

                    curr_ret = 0
                    if not curr_range.empty and len(curr_range) > 1:
                        curr_start = curr_range.iloc[0]
                        curr_end = curr_range.iloc[-1]
                        curr_ret = ((curr_end - curr_start) / curr_start) * 100

                    pe = curr_start / ttm_eps if ttm_eps else None
                    eps_growth = None
                    if len(ttm_previous) == len(ttm_entries):
                        growth_rates = []
                        for current, previous in zip(ttm_entries, ttm_previous):
                            prev_eps = previous['epsActual']
                            curr_eps = current['epsActual']

                            if prev_eps not in [None, 0]:  # avoid divide-by-zero or invalid growth
                                growth = (curr_eps - prev_eps) / abs(prev_eps)
                                growth_rates.append(growth)

                        if growth_rates:
                            eps_growth = sum(growth_rates) / len(growth_rates)

                    data.append({
                        'Ticker': ticker,
                        # 'Company': info.get('shortName'),
                        # 'Sector': info.get('sector'),
                        'Industry': industry,
                        'return' : curr_ret,
                        'Previous_ret': prev_ret,
                        # 'Market Cap': market_cap,
                        'Percent of M&Z': None,
                        'PE': pe,
                        'TTM_EPS': ttm_eps,
                        'EPS_Growth': eps_growth
                    })
                    # time.sleep(0.05)
                except Exception as e:
                    print(f"Error for ticker {ticker}: {e}")
    
    df = pd.DataFrame(data)
     # Apply scoring functions to each row
    df['PE_Score'] = df['PE'].apply(score_pe)
    df['EPS_Growth_Score'] = df['EPS_Growth'].apply(score_eps_growth)
    df['Return_Score'] = df['Previous_ret'].apply(score_return)
    
    # Calculate total score
    df['Total_Score'] = df['PE_Score'] + df['EPS_Growth_Score'] + df['Return_Score']

    
    # df = df[df['Total_Score'] >= 10].reset_index(drop=True) # try without
    
    # Sort by total score descending
    ranked_df = df.sort_values(by='Total_Score', ascending=False).reset_index(drop=True)
    df = df.loc[df.groupby('Industry')['Total_Score'].idxmax()].reset_index(drop=True)

    df['Percent of M&Z'] = 100 / len(df)

    # Calculate weighted return
    df['Weighted_Return'] = (df['Percent of M&Z'] / 100) * df['return']
    total_ret = df['Weighted_Return'].sum()

    print(df.to_string(index=False))  
    # print(f"Total Market Cap: {total_cap}")
    spy_ret = calculate_spy_return(start, end)
    # print(f"Our Return: {total_ret}")

    return total_ret, spy_ret


def score_pe(pe):
    if pe <= 10:
        return 10
    elif pe <= 20:
        return 8
    elif pe <= 30:
        return 6
    elif pe <= 40:
        return 4
    else:
        return 1

def score_eps_growth(eps_growth):
    if eps_growth is None:
        return 1  # No data, assign lowest score
    elif eps_growth > 0.30:
        return 5
    elif eps_growth > 0.20:
        return 4
    elif eps_growth > 0.10:
        return 3
    elif eps_growth > 0:
        return 2
    else:
        return 1

def score_return(ret):
    if ret > 20:
        return 5
    elif ret > 10:
        return 4
    elif ret > 5:
        return 3
    elif ret > 0:
        return 2
    else:
        return 1

   

    