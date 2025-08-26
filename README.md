# M-Z50 Portfolio Screening and Backtesting System

A comprehensive portfolio screening and backtesting system that analyzes S&P 500 stocks based on fundamental metrics and historical performance.

## Features

- **Portfolio Screening**: Screen stocks based on PE ratios, EPS growth, and historical returns
- **Growth Screening**: Advanced screening with EPS growth analysis and quarterly performance
- **Backtesting**: Historical performance analysis of screened portfolios vs. SPY benchmark
- **Multi-threaded Data Fetching**: Efficient data collection from multiple sources
- **Industry-based Selection**: Select best stocks from each industry for diversification

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Main Program
Run the interactive main program:
```bash
python main.py
```

Choose from the following options:
- **b**: Backtest - Run a multi-year backtest
- **t**: Today Test - Test with today's data
- **g**: Growth Screener - Use growth-based screening
- **q**: Quit

### Testing
Run the test suite to verify functionality:
```bash
python test_run.py
```

### Demo
Run the automated demo to see both screening methods in action:
```bash
python demo.py
```

**Note**: The demo script will take several minutes to complete as it fetches real market data and performs actual screening and backtesting.

## System Architecture

### Core Components

1. **`main.py`** - Main program interface and user interaction
2. **`portfolio.py`** - Portfolio generation and management
3. **`screener.py`** - Standard stock screening based on PE, EPS, and returns
4. **`growth_screener.py`** - Advanced screening with growth metrics
5. **`backtest.py`** - Historical performance analysis
6. **`fetch_functions.py`** - Data fetching utilities
7. **`sp_tickers.py`** - S&P 500 ticker management

### Data Flow

1. **Data Collection**: Fetch S&P 500 tickers and industry classifications
2. **Earnings Data**: Collect quarterly earnings data for all tickers
3. **Screening**: Apply scoring algorithms to rank stocks
4. **Portfolio Construction**: Select top stocks from each industry
5. **Backtesting**: Calculate historical returns vs. SPY benchmark

## Screening Criteria

### Standard Screener
- **PE Score**: Lower PE ratios get higher scores (1-5)
- **EPS Growth Score**: Higher EPS growth gets higher scores (1-5)
- **Return Score**: Higher historical returns get higher scores (1-5)

### Growth Screener
- **PE Score**: Lower PE ratios get higher scores (1-5)
- **EPS Growth Score**: Higher EPS growth rates get higher scores (1-5)
- **Previous Quarter Return**: Higher previous quarter returns get higher scores (1-5)

## Error Handling

The system includes robust error handling:
- Fallback stock lists if S&P 500 data is unavailable
- Graceful handling of missing earnings data
- Error recovery for individual ticker failures
- Comprehensive logging of issues

## Dependencies

- `yfinance`: Yahoo Finance data access
- `pandas`: Data manipulation and analysis
- `matplotlib`: Charting and visualization
- `requests`: HTTP requests for data fetching
- `python-dateutil`: Date manipulation utilities

## Notes

- The system uses fallback stock lists if Wikipedia S&P 500 data is unavailable
- Earnings data is fetched from AlphaQuery with rate limiting
- All calculations are done with proper error handling and fallbacks
- The system is designed to be robust and handle real-world data inconsistencies

## Troubleshooting

If you encounter issues:
1. Run `python test_run.py` to identify specific problems
2. Check your internet connection for data fetching
3. Verify all dependencies are installed correctly
4. Check the console output for specific error messages 