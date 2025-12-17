import yfinance as yf
import pandas as pd
import os
import datetime

# Configuration
# Indian Tickers:
# ^NSEI: Nifty 50
# ^BSESN: S&P BSE SENSEX
# ^NSEBANK: Nifty Bank
# RELIANCE.NS, TCS.NS, etc.
TICKERS = [
    "^NSEI", "^BSESN", "^NSEBANK", 
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "TATAMOTORS.NS"
]
DATA_DIR = "data_ist"
INTERVAL = "5m"
TIMEZONE = "Asia/Kolkata"

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_last_datetime(file_path):
    """
    Reads the last line of the CSV to get the last datetime.
    """
    try:
        with open(file_path, 'rb') as f:
            try:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            
            last_line = f.readline().decode('utf-8').strip()
            if not last_line or ',' not in last_line:
                return None
            
            # Assuming Datetime is first column
            date_str = last_line.split(',')[0]
            
            if date_str.lower() == "datetime" or date_str.lower() == "date":
                return None

            try:
                dt = pd.to_datetime(date_str)
                return dt
            except Exception as e:
                return None
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def fetch_and_save_data(ticker):
    print(f"Processing {ticker}...")
    
    ticker_dir = os.path.join(DATA_DIR, ticker)
    ensure_dir(ticker_dir)
    
    file_path = os.path.join(ticker_dir, f"{ticker}_data.csv")
    
    start_dt = None
    existing_data = False
    
    if os.path.exists(file_path):
        last_dt = get_last_datetime(file_path)
        if last_dt:
            print(f"  Found data up to {last_dt}")
            start_dt = last_dt
            existing_data = True

    try:
        # Download data
        # period="60d" is max for 5m data
        if start_dt:
            # Check if start_dt (in IST) is older than 60 days
            # Convert start_dt to UTC for comparison if needed, or convert limit to IST
            # Easier to check against UTC now
            
            # Convert start_dt to UTC slightly loosely to check validity against 60d limit
            if start_dt.tzinfo is None:
                 # Assume IST if naive (though pandas usually reads with tz if written with tz)
                 start_dt = start_dt.tz_localize(TIMEZONE)
            
            # 60 days limits
            limit_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=59)
            
            if start_dt.astimezone(datetime.timezone.utc) < limit_date:
                 print("  Existing data is older than 60 days limit. Fetching max available 60d...")
                 data = yf.download(ticker, period="60d", interval=INTERVAL, progress=False, auto_adjust=True)
            else:
                print(f"  Fetching data from {start_dt.date()}...")
                data = yf.download(ticker, start=start_dt.date(), interval=INTERVAL, progress=False, auto_adjust=True)
        else:
            print("  Fetching max available history (60d)...")
            data = yf.download(ticker, period="60d", interval=INTERVAL, progress=False, auto_adjust=True)
        
        if data.empty:
            print("  No new data found.")
            return

        # Clean-up columns 
        if isinstance(data.columns, pd.MultiIndex):
            try:
                data.columns = data.columns.get_level_values(0)
            except IndexError:
                pass
        
        # Convert Timezone to IST
        if data.index.tz is None:
             # Should natively be UTC from yfinance, but sometimes naive. Assume UTC.
             data.index = data.index.tz_localize('UTC')
        
        # Convert to target timezone
        data.index = data.index.tz_convert(TIMEZONE)

        # Filter new data only if appending
        if existing_data and start_dt:
            # Ensure start_dt has same timezone for comparison
            # We already localized start_dt to TIMEZONE if it was naive above
            if start_dt.tzinfo != data.index.tz:
                start_dt = start_dt.tz_convert(data.index.tz)

            # Keep only rows strictly after last_dt
            new_data = data[data.index > start_dt]
            
            if new_data.empty:
                print("  No new rows to append.")
                return
            
            new_data.to_csv(file_path, mode='a', header=False)
            print(f"  Appended {len(new_data)} rows.")
            
        else:
            data.to_csv(file_path)
            print(f"  Saved {len(data)} rows to new file.")
            
    except Exception as e:
        print(f"  Failed to fetch data for {ticker}: {e}")

def main():
    ensure_dir(DATA_DIR)
    print(f"Starting stock data collection for {len(TICKERS)} tickers (Interval: {INTERVAL}, Timezone: {TIMEZONE})...")
    
    for ticker in TICKERS:
        fetch_and_save_data(ticker)
        
    print("All done.")

if __name__ == "__main__":
    main()
