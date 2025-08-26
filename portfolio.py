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
from fetch_functions import fetch_industries, fetch_all_earnings, fetch_industry, get_quarterly_ticker_changes

def get_portfolio(dates, screentype, years):
    print("Starting portfolio generation...")
    capital = 100000
    spy_cap = 100000

    today = date.today()

    # Earnings start date = 1 year before the user's range
    earnings_start = (today - relativedelta(years=years+1)).isoformat()
    earnings_end = today.isoformat()
    print(f"Fetching earnings data from {earnings_start} to {earnings_end}...")

    tickers, changes_df = gsp()
    
    # Only process quarter changes if we have actual changes data
    if not changes_df.empty:
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
    else:
        # If using fallback stock list, no quarter changes to process
        print("Using fallback stock list - no quarterly changes to process")

    print(f"Processing {len(tickers)} tickers...")
    tickers = fetch_industries(tickers)

    if "GOOGL" in [t[0] for t in tickers]:
        tickers = [(t, ind) for t, ind in tickers if t != "GOOGL"]

    print("Fetching earnings data (this may take a few minutes)...")
    # Fetch earnings with multithreading
    earnings = fetch_all_earnings(tickers, earnings_start, earnings_end, max_workers=5)

    ticker_list = [(t, ind) for t, ind in tickers if earnings.get(t)]
    print(f"Found earnings data for {len(ticker_list)} tickers")
    
    if not ticker_list:
        print("No tickers with earnings data found.")
        return None
    
    print(f"Running {screentype} screener...")
    # Screen stocks based on screentype
    if screentype == 's':
        # Use standard screener
        portfolio, total_ret, spy_ret = screen(ticker_list, earnings, dates[0][0], dates[-1][1])
    elif screentype == 'g':
        # Use growth screener
        portfolio, total_ret, spy_ret = growth_screen(ticker_list, earnings, dates[0][0], dates[-1][1])
    else:
        print(f"Unknown screentype: {screentype}")
        return None
    
    print(f"Portfolio created with {len(portfolio)} stocks")
    # Return the screened portfolio
    return portfolio
