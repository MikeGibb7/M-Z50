# M&Z50 Custom Index

A Python script that builds a custom index called the M&Z50, which includes the best stock from each industry in the S&P 500 based on fundamental analysis.

## Features

- **Fundamental Screening**: Selects stocks based on low P/E ratio, high ROE, and low Debt/Equity ratio
- **Industry Diversification**: Picks the best stock from each major industry sector
- **Quarterly Rebalancing**: Rebalances the portfolio every quarter
- **Market Cap Weighting**: Weights selected stocks by market capitalization
- **Performance Comparison**: Compares performance against SPY (S&P 500 ETF)
- **Visualization**: Plots both portfolios on a graph with rebalancing dates marked

## Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```
 
## Usage

Run the script:

```bash
python zarektest.py
```

## How It Works

1. **Stock Selection**: The script screens stocks from major S&P 500 companies across different industries
2. **Fundamental Analysis**: For each industry, it selects the stock with the best combination of:
   - Low Price-to-Earnings (P/E) ratio
   - High Return on Equity (ROE)
   - Low Debt-to-Equity ratio
3. **Portfolio Construction**: Selected stocks are weighted by market capitalization
4. **Quarterly Rebalancing**: The portfolio is rebalanced every quarter (January, April, July, October)
5. **Performance Tracking**: Tracks performance over 5 years starting with $100,000
6. **Comparison**: Compares results against SPY performance

## Output

The script will:
- Print screening results for each rebalancing period
- Show portfolio allocations
- Display a performance comparison chart
- Print a summary of returns and excess performance

## Customization

You can modify the script to:
- Change the initial investment amount
- Adjust the screening criteria
- Modify the rebalancing frequency
- Add more industries or stocks
- Change the backtest period

## Disclaimer

This is for educational and research purposes only. Past performance does not guarantee future results. Always do your own research before making investment decisions. 
