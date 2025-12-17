import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import stock_collector

# Configuration
# These will be set in GitHub Secrets
SERVICE_ACCOUNT_JSON = os.environ.get('GDRIVE_CREDENTIALS') 
FOLDER_ID = os.environ.get('GDRIVE_FOLDER_ID')
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_drive():
    """Authenticates using Service Account Key from Environment Variable."""
    if not SERVICE_ACCOUNT_JSON:
        print("Error: GDRIVE_CREDENTIALS environment variable not set.")
        return None
    
    try:
        # If the secret is the raw JSON string
        creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
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
        print("Skipping Drive Sync (Running purely local or Auth failed).")
        # Still run the collector even if Drive fails, or maybe exit? 
        # For now, let's run collector so at least local runner generates data (though it will be lost if not uploaded)
    else:
        # 1. Download existing history
        download_files(service)
    
    # 2. Run the collector
    print("\n--- Running Stock Collector ---\n")
    stock_collector.main()
    print("\n--- Collector Finished ---\n")
    
    if service:
        # 3. Upload updated data
        upload_files(service)

if __name__ == "__main__":
    main()
