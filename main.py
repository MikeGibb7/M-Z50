import yfinance as yf
import pandas as pd

ticker = yf.Ticker("GOOGL")
historical = ticker.history(period="1D")
print(historical["Close"].iloc[0])

# Get financials (Income Statement) — this includes revenue
financials = ticker.financials

# Transpose to get years as rows, then get the 'Total Revenue'
revenue = financials.loc['Total Revenue']

print(revenue)