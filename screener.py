import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def calculate_return(stock, years):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365 * years)
    hist = yf.Ticker(stock).history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    if len(hist) < 2:
        return None

    start_price = hist['Close'].iloc[0]
    end_price = hist['Close'].iloc[-1]
    return ((end_price - start_price) / start_price) * 100  # Return as percentage


def main():
    sp_table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    sp500_df = sp_table[0]

    stock_df = []
    for _, stock in sp500_df.iterrows():
        stock_df.append((stock["Symbol"], stock["GICS Sub-Industry"]))

    data = []

    
    one_avg = 0
    three_avg = 0
    five_avg = 0
    iterations = 0
    total_cap = 0


    for ticker, industry in stock_df:
        stock = yf.Ticker(ticker)
        info = stock.info

        market_cap = info.get('marketCap')
        if isinstance(market_cap, (int, float)):
           total_cap += market_cap

        if( info.get('trailingPE') == None and info.get('shortName') != None):
            iterations += 1
            oney = calculate_return(ticker, 1)
            threey = calculate_return(ticker, 3)
            fivey = calculate_return(ticker, 5)

            one_avg += oney
            three_avg += threey
            five_avg += fivey

            data.append({
                'Ticker': ticker,
                'Company': info.get('shortName'),
                'Sector': info.get('sector'),
                'Industry': industry,
                'YFIndustry': info.get('Industry'),
                'Market Cap': market_cap,
                'PE': info.get('trailingPE'),
                'Percent of S&P': None,
                '1yr Return': oney,
                '3yr Return': threey,
                '5yr Return': fivey
            })
    
    for stock in data:
        stock['Percent of S&P'] = stock['Market Cap'] / total_cap * 100

    df = pd.DataFrame(data)
    print(df.to_string(index=False))   

    print(f"one year average: {one_avg / iterations}")
    print(f"three year average: {three_avg / iterations}")
    print(f"five year average: {five_avg / iterations}")
    print(f"Total Market Cap: {total_cap}")

    






if __name__ == "__main__":
    main()