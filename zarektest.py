import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
warnings.filterwarnings('ignore')
from mz50Index import MZ50Index

def main():
    """Main function to run the M&Z50 index backtest"""
    # Set date range (5 years of data)
    end_date = datetime.now().replace(day=1)
    start_date = end_date - timedelta(days=2*365)
    
    # Create and run the index with multithreading
    mz50 = MZ50Index(initial_capital=100000, max_workers=20)
    mz50.run_backtest(start_date, end_date)
    mz50.plot_results()

if __name__ == "__main__":
    main()
