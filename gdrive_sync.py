import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import stock_collector

# Configuration
# These will be set in GitHub Secrets
TOKEN_JSON_STR = os.environ.get('GDRIVE_TOKEN') 
FOLDER_ID = os.environ.get('GDRIVE_FOLDER_ID')
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_drive():
    """Authenticates using OAuth Token from Environment Variable."""
    if not TOKEN_JSON_STR:
        print("Error: GDRIVE_TOKEN environment variable not set.")
        return None
    
    try:
        # Load the token data
        token_info = json.loads(TOKEN_JSON_STR)
        
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

def find_file_in_folder(service, filename, folder_id):
    """Checks if a file exists in the specific Drive folder."""
    query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    return files[0] if files else None

def download_files(service):
    """Downloads existing data from Drive to local data_ist folder."""
    print("Checking for existing data on Drive...")
    
    # Ensure local directory exists
    if not os.path.exists(stock_collector.DATA_DIR):
        os.makedirs(stock_collector.DATA_DIR)

    for ticker in stock_collector.TICKERS:
        ticker_dir = os.path.join(stock_collector.DATA_DIR, ticker)
        if not os.path.exists(ticker_dir):
            os.makedirs(ticker_dir)
            
        filename = f"{ticker}_data.csv"
        file_path = os.path.join(ticker_dir, filename)
        
        # Check if file exists in Drive folder
        drive_file = find_file_in_folder(service, filename, FOLDER_ID)
        
        if drive_file:
            print(f"  Downloading {filename} from Drive...")
            file_id = drive_file['id']
            request = service.files().get_media(fileId=file_id)
            with open(file_path, 'wb') as f:
                f.write(request.execute())
        else:
            print(f"  {filename} not found on Drive. Will create new.")

def upload_files(service):
    """Uploads updated files from local data_ist folder to Drive."""
    print("Uploading updated data to Drive...")
    
    for ticker in stock_collector.TICKERS:
        filename = f"{ticker}_data.csv"
        file_path = os.path.join(stock_collector.DATA_DIR, ticker, filename)
        
        if not os.path.exists(file_path):
            continue
            
        drive_file = find_file_in_folder(service, filename, FOLDER_ID)
        
        media = MediaFileUpload(file_path, mimetype='text/csv', resumable=True)
        
        if drive_file:
            print(f"  Updating {filename} (ID: {drive_file['id']})...")
            service.files().update(
                fileId=drive_file['id'],
                media_body=media
            ).execute()
        else:
            print(f"  Creating new file {filename} in Drive...")
            file_metadata = {
                'name': filename,
                'parents': [FOLDER_ID]
            }
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

def main():
    service = authenticate_drive()
    if not service:
        print("CRITICAL ERROR: Google Drive Authentication Failed.")
        print("Please check the 'GDRIVE_TOKEN' secret in GitHub Settings.")
        import sys
        sys.exit(1)
    
    # 1. Download existing history
    download_files(service)
    
    # 2. Run the collector
    print("\n--- Running Stock Collector ---\n")
    stock_collector.main()
    print("\n--- Collector Finished ---\n")

    # DEBUG: List all files generated
    print("DEBUG: Listing files in data_ist:")
    if os.path.exists(stock_collector.DATA_DIR):
        for root, dirs, files in os.walk(stock_collector.DATA_DIR):
            for file in files:
                print(f"  Found: {os.path.join(root, file)}")
    else:
        print(f"  ERROR: Directory {stock_collector.DATA_DIR} does NOT exist.")

    if service:
        # 3. Upload updated data
        upload_files(service)

if __name__ == "__main__":
    main()
