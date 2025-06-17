from FOC import FOC, OptionType
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone

ref_foc = FOC()

def get_call_options(ticker, start, end):
    
    stock = yf.Ticker(ticker)
    historical = stock.history(period="1d")
    price = historical["Close"].iloc[0]
    
    data = []
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=5)

    expiries = stock.options
    for expiry in expiries[start:end]:
        sum_ppc = 0
        iteration = 1

        opt_chain = stock.option_chain(expiry)
        calls = opt_chain.calls
        dailys = []
        for _, call in calls.iterrows():
            if call["ask"] > 0.01 and call["lastTradeDate"] >= cutoff:

                change_percent = abs( ( ( call["strike"] - price )/ price ) ) * 100

                ppc = call["ask"] * change_percent

                sum_ppc += ppc
                iteration += 1

                dailys.append((call["strike"], ppc))

        #         print(
        #             f"iteration: {iteration}\n"
        #             f"PPC: {ppc}\n"
        #             f"Last Price: {call['lastPrice']}\n"
        #             f"Percent Change: {change_percent}\n"
        #         )
                
        # ndf = pd.DataFrame(dailys, columns=["strike", "PPC"])
        # plt.figure(figsize=(12, 6))
        # plt.plot(ndf["strike"], ndf["PPC"], marker='o', linestyle='-', color='b')
        # plt.title(f"PPC vs Strike for {expiry}")
        # plt.xlabel("Strike")
        # plt.ylabel("PPC")
        # plt.grid(True)
        # plt.xticks(rotation=45)
        # plt.tight_layout()
        # plt.show()

        
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        days_to_expiry = (expiry_date - datetime.today().date()).days
        average_ppc = sum_ppc / iteration
        if days_to_expiry > 0:
            average_ppc = average_ppc / days_to_expiry

        data.append((expiry, average_ppc))
    
    df = pd.DataFrame(data, columns=["Expiry", "Average PPC"])
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df["Expiry"], df["Average PPC"], marker='o', linestyle='-', color='b')
    plt.title(f"Average PPC vs Expiry for {ticker}")
    plt.xlabel("Expiry Date")
    plt.ylabel("Average PPC")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def get_put_options(ticker, start, end):
    
    stock = yf.Ticker(ticker)
    historical = stock.history(period="1d")
    price = historical["Close"].iloc[0]
    
    data = []

    cutoff = datetime.now(timezone.utc) - timedelta(days=5)


    expiries = stock.options
    for expiry in expiries[start:end]:
        sum_ppc = 0
        iteration = 1

        opt_chain = stock.option_chain(expiry)
        puts = opt_chain.puts
        
        dailys = []
        for _, put in puts.iterrows():
            if put["ask"] > 0.01 and put["lastTradeDate"] >= cutoff: #put["strike"] < price and 1

                change_percent = abs( ( put["strike"] / price ) - 1  ) * 100

                ppc = ( put["ask"] ) * change_percent

                sum_ppc += ppc
                iteration += 1

                dailys.append((put["strike"], ppc))

                # print(
                #     f"iteration: {iteration}\n"
                #     f"PPC: {ppc}\n"
                #     f"Last Price: {call['lastPrice']}\n"
                #     f"Percent Change: {change_percent}\n"
                # )
                
        # ndf = pd.DataFrame(dailys, columns=["strike", "PPC"])
        # plt.figure(figsize=(12, 6))
        # plt.plot(ndf["strike"], ndf["PPC"], marker='o', linestyle='-', color='b')
        # plt.title(f"PPC vs Strike for {expiry}")
        # plt.xlabel("Strike")
        # plt.ylabel("PPC")
        # plt.grid(True)
        # plt.xticks(rotation=45)
        # plt.tight_layout()
        # plt.show()

        
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        days_to_expiry = (expiry_date - datetime.today().date()).days
        average_ppc = sum_ppc / iteration
        if days_to_expiry > 0:
            average_ppc = average_ppc / days_to_expiry

        data.append((expiry, average_ppc))
    
    df = pd.DataFrame(data, columns=["Expiry", "Average PPC"])
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df["Expiry"], df["Average PPC"], marker='o', linestyle='-', color='b')
    plt.title(f"Average PPC vs Expiry for {ticker}")
    plt.xlabel("Expiry Date")
    plt.ylabel("Average PPC")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
        
def sendToExcel(ticker):
    stock = yf.Ticker(ticker)
    historical = stock.history(period="1d")
    price = historical["Close"].iloc[0]
    cutoff = datetime.now(timezone.utc) - timedelta(days=5)
    expiries = stock.options
    with pd.ExcelWriter(f"{ticker}_options.xlsx", engine="openpyxl", mode="w") as writer:
        for expiry in expiries:
            opt_chain = stock.option_chain(expiry)
            calls = opt_chain.calls
            calls["lastTradeDate"] = pd.to_datetime(calls["lastTradeDate"]).dt.tz_localize(None)
            # Filter calls
            filtered_calls = calls[
                (calls["ask"] > 0.01) & 
                (pd.to_datetime(calls["lastTradeDate"]) >= cutoff)
            ]

            # Write to separate sheet named after expiry
            if not filtered_calls.empty:
                # Sheet names can't be longer than 31 characters
                sheet_name = expiry if len(expiry) <= 31 else expiry[:31]
                sheet_name = sheet_name.replace('-', '')  # Excel doesn't allow hyphens in sheet names
                filtered_calls.to_excel(writer, sheet_name=sheet_name, index=False)

def call_modifications(ticker, start, end):
    
    stock = yf.Ticker(ticker)
    historical = stock.history(period="1d")
    price = historical["Close"].iloc[0]
    
    data = []
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=5)

    expiries = stock.options

    

    for expiry in expiries[start:end]:
        sum_ppc = 0
        iteration = 1
        chain = ref_foc.get_options_chain_greeks(ticker, expiry, OptionType.CALL)

        opt_chain = stock.option_chain(expiry)
        calls = opt_chain.calls
        dailys = []
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        days_to_expiry = (expiry_date - datetime.today().date()).days

        for _, call in calls.iterrows():
            if call["ask"] > 0.01 and call["lastTradeDate"] >= cutoff and abs( (( call["strike"] - price ) / price)) * 100 < 100:

                match = chain[chain["strike"] == call["strike"]]

                theta = match.iloc[0]["c_Theta"]

                change_percent = abs( ( ( call["strike"] - price ) / price ) - 1  ) * 100

                ppc = call["ask"] * change_percent

                theta_score = days_to_expiry +  theta * days_to_expiry

                ppc = ppc / theta_score

                sum_ppc += ppc
                iteration += 1

                dailys.append((call["strike"], ppc))

                print(
                    f"iteration: {iteration}\n"
                    f"PPC: {ppc}\n"
                    f"Last Price: {call['lastPrice']}\n"
                    f"Percent Change: {change_percent}\n"
                    f"strike : {call["strike"]}\n"
                )
                
        ndf = pd.DataFrame(dailys, columns=["strike", "PPC"])
        plt.figure(figsize=(12, 6))
        plt.plot(ndf["strike"], ndf["PPC"], marker='o', linestyle='-', color='b')
        plt.title(f"PPC vs Strike for {expiry}")
        plt.xlabel("Strike")
        plt.ylabel("PPC")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

        
        
        average_ppc = sum_ppc / iteration

        data.append((expiry, average_ppc))
    
    df = pd.DataFrame(data, columns=["Expiry", "Average PPC"])
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df["Expiry"], df["Average PPC"], marker='o', linestyle='-', color='b')
    plt.title(f"Average PPC vs Expiry for {ticker}")
    plt.xlabel("Expiry Date")
    plt.ylabel("Average PPC")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
def compare_iv(ticker):
    stock = yf.Ticker(ticker)
    historical = stock.history(period="1d")
    price = historical["Close"].iloc[0]
    exp = stock.options
    data = []
    for expiry in exp:
        chain = stock.option_chain(expiry)
        calls = chain.calls
        puts = chain.puts
        total_vol = 0
        iterations = 0
        for _, call in calls.iterrows():
            put = puts[puts["strike"] == call["strike"]]
            if not put.empty:
                total_vol += call["impliedVolatility"] - put.iloc[0]["impliedVolatility"]
                iterations += 1
        if iterations > 0:
            avg_vol_diff = total_vol / iterations
        data.append((expiry, avg_vol_diff))

# Create DataFrame
    df = pd.DataFrame(data, columns=["Expiry", "Avg_IV_Diff"])

    # Sort by expiry just in case
    df = df.sort_values("Expiry")

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df["Expiry"], df["Avg_IV_Diff"], marker='o')
    plt.title("Average Implied Volatility Difference (Call - Put)")
    plt.xlabel("Expiry Date")
    plt.ylabel("Avg IV Difference")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    ticker = ""
    start = 0
    end = None
    

    while True:
        print("\nOptions:")
        print("1. Set Ticker")
        print("2. Get Call Options")
        print("3. Get Put Options")
        print("4. Exit")
        print("5. Set amount of expiries(default all)")
        print("6. Todays options data to Excel file")

        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            ticker = input("Enter the ticker symbol: ").upper()
            print(f"Ticker set to {ticker}")
        elif choice == "2":
            if ticker:
                get_call_options(ticker, start, end)
            else:
                print("Please set the ticker first (option 1).")
        elif choice == "3":
            if ticker:
                get_put_options(ticker, start, end)
            else:
                print("Please set the ticker first (option 1).")
        elif choice == "4":
            print("Exiting program.")
            break
        elif choice == "5":
            start = int(input("Enter the amount of expiries you would like to bypass: "))
            amt = int(input("Enter the amount of expiries you would like to include: "))
            end = start + amt
        elif choice == "6":
            if ticker:
                sendToExcel(ticker)
            else:
                print("Please set the ticker first (option 1).")
                
        elif choice == "7":
            if ticker:
                call_modifications(ticker, start, end)
            else:
                print("Please set the ticker first (option 1).")
        elif choice == "8":
            if ticker:
                compare_iv(ticker)
            else:
                print("Please set the ticker first (option 1).")
        else:
            print("Invalid choice. Please enter a number from 1 to 4.")
 
if __name__ == "__main__":
    main()

