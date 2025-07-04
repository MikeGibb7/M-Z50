# get_sp500.py

import pandas as pd

def get_sp500_companies():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    sp_table = pd.read_html(url)
    sp500_df = sp_table[0]

    stock_df = []
    for _, stock in sp500_df.iterrows():
        symbol = stock["Symbol"].replace('.', '-')  # optional fix for e.g., BRK.B
        industry = stock["GICS Sub-Industry"]
        stock_df.append(symbol)  #((symbol, industry))
        
    changes_df = sp_table[1]
    
    return stock_df, changes_df
def get_sp500_companies_windustry():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    sp_table = pd.read_html(url)
    sp500_df = sp_table[0]

    stock_df = []
    for _, stock in sp500_df.iterrows():
        symbol = stock["Symbol"].replace('.', '-')  # optional fix for e.g., BRK.B
        industry = stock["GICS Sub-Industry"]
        stock_df.append((symbol, industry))
        
    changes_df = sp_table[1]
    
    return stock_df, changes_df
