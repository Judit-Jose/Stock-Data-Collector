from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

# Scopes required
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    if not os.path.exists('credentials.json'):
        print("Error: 'credentials.json' not found. Please download it from Google Cloud Console.")
        print("Create Credentials > OAuth Client ID > Desktop App > Download JSON")
        return

    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    creds = flow.run_local_server(port=0)
    
    # Save the credentials to a JSON format we can copy to GitHub Secrets
    token_json = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    
    print("\n\nSUCCESS! Copy the content below (starting with { and ending with }) and paste it into GitHub Secrets as 'GDRIVE_TOKEN':\n")
    print(json.dumps(token_json))

if __name__ == '__main__':
    main()
