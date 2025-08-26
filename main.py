import requests
import re
import json
from sp_tickers import get_sp500_companies as gsp
import yfinance as yf
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta  
from screener import screen
from growth_screener import growth_screen
from backtest import backtest
from portfolio import get_portfolio
from fetch_functions import generate_quarter_dates
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


# Example usage
def main():
    choice = input("Enter 'b' for backtest, 't' for today test, 'g' for growth screener: ").strip().lower()
    
    if choice == 'b':
        years = int(input("Enter number of years to backtest: "))
        print(f"Starting {years}-year backtest...")
        dates = generate_quarter_dates(years)
        portfolio_data = get_portfolio(dates, 's', years)
        if portfolio_data:
            total_ret, spy_ret = backtest(portfolio_data, dates[0][0], dates[-1][1])
            print(f"Portfolio Return: {total_ret:.2f}%")
            print(f"SPY Return: {spy_ret:.2f}%")
        print("Backtest completed.")
    elif choice == 't':
        dates = [(date.today().isoformat(), date.today().isoformat())]
        print("Starting today test...")
        portfolio_data = get_portfolio(dates, 's', 1)
        if portfolio_data:
            total_ret, spy_ret = backtest(portfolio_data, dates[0][0], dates[-1][1])
            print(f"Portfolio Return: {total_ret:.2f}%")
            print(f"SPY Return: {spy_ret:.2f}%")
        print("Today test completed.")
    elif choice == 'g':
        years = int(input("Enter number of years for growth screener: "))
        print(f"Starting {years}-year growth screener...")
        dates = generate_quarter_dates(years)
        portfolio_data = get_portfolio(dates, 'g', years)
        if portfolio_data:
            total_ret, spy_ret = backtest(portfolio_data, dates[0][0], dates[-1][1])
            print(f"Portfolio Return: {total_ret:.2f}%")
            print(f"SPY Return: {spy_ret:.2f}%")
        print("Growth screener completed.")
    elif choice == 'q':
        print("Exiting the program.")
        exit(0)
    else:
        print("Invalid input. Please enter 'b', 't', 'g', or 'q'.")


if __name__ == "__main__":
    main()
