import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
warnings.filterwarnings('ignore')

class MZ50Index:
    def __init__(self, initial_capital=100000, max_workers=10):
        self.initial_capital = initial_capital
        self.max_workers = max_workers
        self.sp500_data = self._get_sp500_data()
        self.portfolio_value = initial_capital
        self.portfolio_history = []
        self.spy_history = []
        self.rebalance_dates = []
        self.lock = threading.Lock()
        
    def _get_sp500_data(self):
        """Fetch S&P 500 data from Wikipedia using pandas"""
        print("Fetching S&P 500 data from Wikipedia...")
        
        # Use pandas to read the Wikipedia table
        sp_table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        sp500_df = sp_table[0]
        
        # Extract the data we need
        data = []
        for _, stock in sp500_df.iterrows():
            ticker = stock["Symbol"]
            company = stock["Security"]
            sector = stock["GICS Sector"]
            sub_industry = stock["GICS Sub-Industry"]
            
            data.append({
                'ticker': ticker,
                'company': company,
                'sector': sector,
                'sub_industry': sub_industry
            })
        
        print(f"Successfully fetched {len(data)} S&P 500 companies")
        return data
    
    def get_industry_mapping(self):
        """Create industry mapping from S&P 500 data"""
        industry_mapping = {}
        
        for stock in self.sp500_data:
            sub_industry = stock['sub_industry']
            ticker = stock['ticker']
            
            if sub_industry not in industry_mapping:
                industry_mapping[sub_industry] = []
            
            industry_mapping[sub_industry].append(ticker)
        
        # Filter out industries with too few stocks (less than 3)
        filtered_mapping = {k: v for k, v in industry_mapping.items() if len(v) >= 3}
        
        print(f"Found {len(filtered_mapping)} sub-industries with 3+ stocks")
        for industry, tickers in list(filtered_mapping.items())[:10]:  # Show first 10
            print(f"  {industry}: {len(tickers)} stocks")
        if len(filtered_mapping) > 10:
            print(f"  ... and {len(filtered_mapping) - 10} more sub-industries")
        
        return filtered_mapping
    
    def get_fundamental_data(self, ticker, date):
        """Get fundamental data for a ticker at a specific date"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get historical data
            hist = stock.history(start=date - timedelta(days=365), end=date)
            if hist.empty:
                return None
            
            # Get financial data
            info = stock.info
            
            # Calculate metrics
            pe_ratio = info.get('trailingPE', float('inf'))
            roe = info.get('returnOnEquity', 0)
            debt_to_equity = info.get('debtToEquity', float('inf'))
            market_cap = info.get('marketCap', 0)
            
            # Get price data
            current_price = hist['Close'].iloc[-1] if not hist.empty else 0
            
            return {
                'ticker': ticker,
                'pe_ratio': pe_ratio,
                'roe': roe,
                'debt_to_equity': debt_to_equity,
                'market_cap': market_cap,
                'price': current_price
            }
        except:
            return None
    
    def process_industry(self, industry, tickers, date):
        """Process a single industry to find the best stock"""
        industry_stocks = []
        
        for ticker in tickers:
            data = self.get_fundamental_data(ticker, date)
            if data and data['pe_ratio'] != float('inf') and data['debt_to_equity'] != float('inf'):
                industry_stocks.append(data)
        
        if industry_stocks:
            # Sort by criteria: low P/E, high ROE, low Debt/Equity
            industry_stocks.sort(key=lambda x: (
                x['pe_ratio'],  # Lower is better
                -x['roe'],      # Higher is better (negative for ascending sort)
                x['debt_to_equity']  # Lower is better
            ))
            
            # Select the best stock from this industry
            best_stock = industry_stocks[0]
            
            with self.lock:
                print(f"  {industry}: {best_stock['ticker']} (P/E: {best_stock['pe_ratio']:.2f}, ROE: {best_stock['roe']:.2%}, D/E: {best_stock['debt_to_equity']:.2f})")
            
            return industry, best_stock
        
        return industry, None
    
    def screen_stocks(self, date):
        """Screen stocks based on fundamentals using multithreading"""
        print(f"Screening stocks for {date.strftime('%Y-%m-%d')}...")
        
        industry_mapping = self.get_industry_mapping()
        screened_stocks = {}
        
        # Use ThreadPoolExecutor to process industries in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all industry processing tasks
            future_to_industry = {
                executor.submit(self.process_industry, industry, tickers, date): industry
                for industry, tickers in industry_mapping.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_industry):
                industry, best_stock = future.result()
                if best_stock:
                    screened_stocks[industry] = best_stock
        
        return screened_stocks
    
    def calculate_weights(self, selected_stocks):
        """Calculate market cap weighted allocations"""
        total_market_cap = sum(stock['market_cap'] for stock in selected_stocks.values())
        
        weights = {}
        for industry, stock in selected_stocks.items():
            weights[industry] = stock['market_cap'] / total_market_cap
        
        return weights
    
    def calculate_portfolio_value(self, allocations, date):
        """Calculate current portfolio value"""
        total_value = 0
        
        for industry, alloc in allocations.items():
            ticker = alloc['ticker']
            shares = alloc['shares']
            
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=date, end=date + timedelta(days=1))
                if not hist.empty:
                    current_price = hist['Close'].iloc[0]
                    position_value = shares * current_price
                    total_value += position_value
            except:
                # If we can't get current price, use previous allocation value
                total_value += alloc['amount']
        
        return total_value
    
    def get_spy_value(self, date):
        """Get SPY value for comparison"""
        try:
            spy = yf.Ticker('SPY')
            hist = spy.history(start=date, end=date + timedelta(days=1))
            if not hist.empty:
                return hist['Close'].iloc[0]
        except:
            pass
        return None
    
    def run_backtest(self, start_date, end_date):
        """Run the backtest with multithreaded quarterly processing"""
        print(f"Running M&Z50 backtest from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Generate all quarterly rebalancing dates
        rebalance_dates = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.month in [1, 4, 7, 10] and current_date.day == 1:
                rebalance_dates.append(current_date)
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)
        
        print(f"Found {len(rebalance_dates)} quarterly rebalancing periods")
        
        # Process each quarter in parallel
        quarterly_results = {}
        
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(rebalance_dates))) as executor:
            # Submit all quarterly processing tasks
            future_to_date = {
                executor.submit(self.process_quarter, date): date
                for date in rebalance_dates
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_date):
                date = future_to_date[future]
                try:
                    allocations = future.result()
                    quarterly_results[date] = allocations
                    print(f"Completed rebalancing for {date.strftime('%Y-%m-%d')}")
                except Exception as e:
                    print(f"Error processing {date.strftime('%Y-%m-%d')}: {e}")
        
        # Sort results by date and run the backtest
        sorted_dates = sorted(quarterly_results.keys())
        self.run_backtest_with_results(sorted_dates, quarterly_results, start_date, end_date)
    
    def process_quarter(self, date):
        """Process a single quarterly rebalancing"""
        print(f"Processing quarter: {date.strftime('%Y-%m-%d')}")
        
        # Screen stocks for this quarter
        selected_stocks = self.screen_stocks(date)
        
        if not selected_stocks:
            print(f"No stocks passed screening criteria for {date.strftime('%Y-%m-%d')}")
            return None
        
        # Calculate weights
        weights = self.calculate_weights(selected_stocks)
        
        # Calculate allocation amounts
        allocations = {}
        for industry, weight in weights.items():
            allocations[industry] = {
                'ticker': selected_stocks[industry]['ticker'],
                'weight': weight,
                'amount': self.initial_capital * weight,  # Use initial capital for allocation calculation
                'shares': int((self.initial_capital * weight) / selected_stocks[industry]['price'])
            }
        
        return allocations
    
    def run_backtest_with_results(self, sorted_dates, quarterly_results, start_date, end_date):
        """Run the backtest using pre-computed quarterly results"""
        print("Running backtest with pre-computed quarterly results...")
        
        current_date = start_date
        allocations = None
        portfolio_value = self.initial_capital
        
        while current_date <= end_date:
            # Check if this is a rebalancing date
            if current_date in quarterly_results:
                allocations = quarterly_results[current_date]
                self.rebalance_dates.append(current_date)
                print(f"Rebalancing on {current_date.strftime('%Y-%m-%d')} with {len(allocations)} positions")
            
            if allocations:
                # Calculate current portfolio value
                portfolio_value = self.calculate_portfolio_value(allocations, current_date)
            
            # Get SPY value
            spy_value = self.get_spy_value(current_date)
            
            # Record values
            self.portfolio_history.append({
                'date': current_date,
                'value': portfolio_value
            })
            
            if spy_value:
                self.spy_history.append({
                    'date': current_date,
                    'value': spy_value
                })
            
            # Move to next month
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)
        
        self.portfolio_value = portfolio_value
    
    def plot_results(self):
        """Plot the results"""
        if not self.portfolio_history or not self.spy_history:
            print("No data to plot")
            return
        
        # Convert to DataFrames
        portfolio_df = pd.DataFrame(self.portfolio_history)
        spy_df = pd.DataFrame(self.spy_history)
        
        # Normalize to starting values
        portfolio_start = portfolio_df['value'].iloc[0]
        spy_start = spy_df['value'].iloc[0]
        
        portfolio_df['normalized'] = portfolio_df['value'] / portfolio_start * 100000
        spy_df['normalized'] = spy_df['value'] / spy_start * 100000
        
        # Calculate performance metrics
        portfolio_return = (portfolio_df['normalized'].iloc[-1] - 100000) / 100000
        spy_return = (spy_df['normalized'].iloc[-1] - 100000) / 100000
        
        # Plot
        plt.figure(figsize=(12, 8))
        
        plt.plot(portfolio_df['date'], portfolio_df['normalized'], 
                label=f'M&Z50 Index ({portfolio_return:.1%})', linewidth=2, color='blue')
        plt.plot(spy_df['date'], spy_df['normalized'], 
                label=f'SPY ({spy_return:.1%})', linewidth=2, color='red', alpha=0.7)
        
        # Mark rebalance dates
        for date in self.rebalance_dates:
            plt.axvline(x=date, color='gray', alpha=0.3, linestyle='--')
        
        plt.title('M&Z50 Index vs SPY Performance', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Portfolio Value ($)', fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Print performance summary
        print(f"\n{'='*50}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*50}")
        print(f"Initial Investment: ${self.initial_capital:,.0f}")
        print(f"Final M&Z50 Value: ${portfolio_df['normalized'].iloc[-1]:,.0f}")
        print(f"Final SPY Value: ${spy_df['normalized'].iloc[-1]:,.0f}")
        print(f"M&Z50 Return: {portfolio_return:.2%}")
        print(f"SPY Return: {spy_return:.2%}")
        print(f"Excess Return: {portfolio_return - spy_return:.2%}")
        print(f"Number of Rebalances: {len(self.rebalance_dates)}")
        
        plt.show()

def main():
    """Main function to run the M&Z50 index backtest"""
    # Set date range (5 years of data)
    end_date = datetime.now().replace(day=1)
    start_date = end_date - timedelta(days=5*365)
    
    # Create and run the index with multithreading
    mz50 = MZ50Index(initial_capital=100000, max_workers=10)
    mz50.run_backtest(start_date, end_date)
    mz50.plot_results()

if __name__ == "__main__":
    main()
