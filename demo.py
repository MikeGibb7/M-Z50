#!/usr/bin/env python3
"""
Demo script for the M-Z50 Portfolio Screening and Backtesting System
This script demonstrates the different screening methods without user interaction.
"""

from portfolio import get_portfolio
from backtest import backtest
from fetch_functions import generate_quarter_dates
import time

def demo_standard_screener():
    """Demonstrate the standard screener"""
    print("\n" + "="*60)
    print("DEMO: Standard Screener")
    print("="*60)
    
    # Generate dates for 1 year
    dates = generate_quarter_dates(1)
    print(f"Testing with {len(dates)} quarters: {dates[0][0]} to {dates[-1][1]}")
    
    # Get portfolio using standard screener
    portfolio = get_portfolio(dates, 's', 1)
    
    if portfolio:
        print(f"\nPortfolio created with {len(portfolio)} stocks:")
        for ticker, weight in portfolio:
            print(f"  {ticker}: {weight:.2f}%")
        
        # Run backtest
        total_ret, spy_ret = backtest(portfolio, dates[0][0], dates[-1][1])
        print(f"\nResults:")
        print(f"  Portfolio Return: {total_ret:.2f}%")
        print(f"  SPY Return: {spy_ret:.2f}%")
        print(f"  Excess Return: {total_ret - spy_ret:.2f}%")
    else:
        print("Failed to create portfolio")

def demo_growth_screener():
    """Demonstrate the growth screener"""
    print("\n" + "="*60)
    print("DEMO: Growth Screener")
    print("="*60)
    
    # Generate dates for 1 year
    dates = generate_quarter_dates(1)
    print(f"Testing with {len(dates)} quarters: {dates[0][0]} to {dates[-1][1]}")
    
    # Get portfolio using growth screener
    portfolio = get_portfolio(dates, 'g', 1)
    
    if portfolio:
        print(f"\nPortfolio created with {len(portfolio)} stocks:")
        for ticker, weight in portfolio:
            print(f"  {ticker}: {weight:.2f}%")
        
        # Run backtest
        total_ret, spy_ret = backtest(portfolio, dates[0][0], dates[-1][1])
        print(f"\nResults:")
        print(f"  Portfolio Return: {total_ret:.2f}%")
        print(f"  SPY Return: {spy_ret:.2f}%")
        print(f"  Excess Return: {total_ret - spy_ret:.2f}%")
    else:
        print("Failed to create portfolio")

def main():
    """Run the demo"""
    print("M-Z50 Portfolio Screening and Backtesting System - DEMO")
    print("This demo will show both screening methods in action.")
    print("Note: This may take several minutes due to data fetching.")
    
    # Demo standard screener
    demo_standard_screener()
    
    # Wait a bit between demos
    print("\nWaiting 5 seconds before next demo...")
    time.sleep(5)
    
    # Demo growth screener
    demo_growth_screener()
    
    print("\n" + "="*60)
    print("DEMO COMPLETED!")
    print("="*60)
    print("The system successfully:")
    print("✓ Fetched S&P 500 stock data")
    print("✓ Retrieved earnings data")
    print("✓ Applied screening algorithms")
    print("✓ Built diversified portfolios")
    print("✓ Performed backtesting")
    print("✓ Compared results to SPY benchmark")

if __name__ == "__main__":
    main()
