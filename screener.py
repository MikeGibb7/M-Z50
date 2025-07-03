from collections import defaultdict
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.error import HTTPError
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

def screen(stock_df, earnings, start, end):

    data = []

    tickers = [ticker for ticker, _ in stock_df]
    iterations = 0
    total_cap = 0
    total_ret = 0

    histories = yf.download(tickers, start=start, end=end, group_by='ticker')
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

            # Sum up epsActual values
            ttm_eps = sum(e['epsActual'] for e in ttm_entries)
            if ttm_eps:
                try:
                    # yf_ticker = yf.Ticker(ticker)
                    # info = yf_ticker.info
                    # market_cap = info.get('marketCap')
                    # if isinstance(market_cap, (int, float)):
                    #     total_cap += market_cap

                    # if(info.get('shortName') != None): # ttm_eps > 0 and 
                    iterations += 1
                    closes = histories[ticker]['Close'].dropna()

                    if len(closes) >=2:
                        start_price = closes.iloc[0]
                        pe = start_price / ttm_eps
                        end_price = closes.iloc[-1]
                        ret = ((end_price - start_price) / start_price) * 100
                    else:
                        ret = 0

                    data.append({
                        'Ticker': ticker,
                        # 'Company': info.get('shortName'),
                        # 'Sector': info.get('sector'),
                        'Industry': industry,
                        'return' : ret,
                        # 'Market Cap': market_cap,
                        'Percent of M&Z': None,
                        'PE': pe,
                        'TTM_EPS': ttm_eps,
                    })
                    # time.sleep(0.05)
                except Exception as e:
                    print(f"Error for ticker {ticker}: {e}")
            
    # industry_map = defaultdict(list)
    # for stock in data:
    #     if stock['PE'] is not None:
    #         industry_map[stock['Industry']].append(stock)

    # filtered_data = []
    # for industry, stocks in industry_map.items():
    #     # Sort by PE and take the first one (lowest PE)
    #     lowest_pe_stock = min(stocks, key=lambda x: x['PE'])
    #     filtered_data.append(lowest_pe_stock)
    #     # highest_pe_stock = max(stocks, key=lambda x: x['PE'])
    #     # filtered_data.append(highest_pe_stock)

    # data = filtered_data
    
    df = pd.DataFrame(data)
     # Apply scoring functions to each row
    df['PE_Score'] = df['PE'].apply(score_pe)
    df['EPS_Growth_Score'] = df['TTM_EPS'].apply(score_eps_growth)
    df['Return_Score'] = df['return'].apply(score_return)
    
    # Calculate total score
    df['Total_Score'] = df['PE_Score'] + df['EPS_Growth_Score'] + df['Return_Score']
    
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
        return 5
    elif pe <= 20:
        return 4
    elif pe <= 30:
        return 3
    elif pe <= 40:
        return 2
    else:
        return 1

def score_eps_growth(eps_growth):
    if eps_growth > 20:
        return 5
    elif eps_growth > 10:
        return 4
    elif eps_growth > 5:
        return 3
    elif eps_growth > 1:
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

   

    