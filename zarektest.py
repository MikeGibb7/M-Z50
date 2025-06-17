import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class MZ50Index:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.sp500_data = self._get_sp500_data()
        self.portfolio_value = initial_capital
        self.portfolio_history = []
        self.spy_history = []
        self.rebalance_dates = []
        
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
    
    def screen_stocks(self, date):
        """Screen stocks based on fundamentals"""
        print(f"Screening stocks for {date.strftime('%Y-%m-%d')}...")
        
        industry_mapping = self.get_industry_mapping()
        screened_stocks = {}
        
        for industry, tickers in industry_mapping.items():
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
                screened_stocks[industry] = best_stock
                print(f"  {industry}: {best_stock['ticker']} (P/E: {best_stock['pe_ratio']:.2f}, ROE: {best_stock['roe']:.2%}, D/E: {best_stock['debt_to_equity']:.2f})")
        
        return screened_stocks
    
    def calculate_weights(self, selected_stocks):
        """Calculate market cap weighted allocations"""
        total_market_cap = sum(stock['market_cap'] for stock in selected_stocks.values())
        
        weights = {}
        for industry, stock in selected_stocks.items():
            weights[industry] = stock['market_cap'] / total_market_cap
        
        return weights
    
    def rebalance_portfolio(self, date):
        """Rebalance the portfolio"""
        print(f"\nRebalancing portfolio on {date.strftime('%Y-%m-%d')}...")
        
        # Screen stocks
        selected_stocks = self.screen_stocks(date)
        
        if not selected_stocks:
            print("No stocks passed screening criteria")
            return
        
        # Calculate weights
        weights = self.calculate_weights(selected_stocks)
        
        # Calculate allocation amounts
        allocations = {}
        for industry, weight in weights.items():
            allocations[industry] = {
                'ticker': selected_stocks[industry]['ticker'],
                'weight': weight,
                'amount': self.portfolio_value * weight,
                'shares': int((self.portfolio_value * weight) / selected_stocks[industry]['price'])
            }
        
        # Print allocation
        print("\nPortfolio Allocation:")
        for industry, alloc in allocations.items():
            print(f"  {industry}: {alloc['ticker']} - {alloc['weight']:.2%} (${alloc['amount']:,.0f})")
        
        return allocations
    
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
        """Run the backtest"""
        print(f"Running M&Z50 backtest from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        current_date = start_date
        allocations = None
        spy_initial = self.get_spy_value(start_date)
        
        while current_date <= end_date:
            # Rebalance quarterly (every 3 months)
            if current_date.month in [1, 4, 7, 10] and current_date.day == 1:
                allocations = self.rebalance_portfolio(current_date)
                self.rebalance_dates.append(current_date)
            
            if allocations:
                # Calculate current portfolio value
                self.portfolio_value = self.calculate_portfolio_value(allocations, current_date)
            
            # Get SPY value
            spy_value = self.get_spy_value(current_date)
            
            # Record values
            self.portfolio_history.append({
                'date': current_date,
                'value': self.portfolio_value
            })
            
            if spy_value:
                self.spy_history.append({
                    'date': current_date,
                    'value': spy_value
                })
            
            # Move to next month
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)
    
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
    
    # Create and run the index
    mz50 = MZ50Index(initial_capital=100000)
    mz50.run_backtest(start_date, end_date)
    mz50.plot_results()

if __name__ == "__main__":
    main()
