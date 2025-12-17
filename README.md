# Cloud Setup Guide

To run the stock collector in the cloud for free, follow these steps to connect GitHub Actions with your Google Drive.

## 1. Google Cloud Setup (Service Account)
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Create a New Project** (e.g., "Stock-Data-Collector").
3.  **Enable Google Drive API**:
    *   Go to "APIs & Services" > "Library".
    *   Search for "Google Drive API" and click **Enable**.
4.  **Create Service Account**:
    *   Go to "IAM & Admin" > "Service Accounts".
    *   Click **Create Service Account**.
    *   Name it (e.g., "drive-uploader"). Click **Create and Continue**.
    *   Role: Select **"Editor"** (Basic > Editor). Click **Done**.
5.  **Generate Key (JSON)**:
    *   Click on the newly created service account email.
    *   Go to the **Keys** tab > **Add Key** > **Create new key**.
    *   Select **JSON** and click **Create**.
    *   A `.json` file will download to your computer. **Keep this safe!**

## 2. Google Drive Setup
1.  Go to your Google Drive.
2.  Create a new folder where you want the stock data (e.g., "StockData").
3.  **Get Folder ID**:
    *   Open the folder.
    *   Look at the URL: `drive.google.com/drive/folders/12345abcdef...`
    *   The part `12345abcdef...` is your **Folder ID**. Copy it.
4.  **Share Folder**:
    *   Right-click the folder > **Share**.
    *   In the "Add people" box, paste the **Service Account Email** (found in your JSON file or Cloud Console, checks ends in `.iam.gserviceaccount.com`).
    *   Make sure it has **Editor** access.
    *   Click **Send** (The service account now has access to this folder).

## 3. GitHub Setup
1.  Create a new Repository on GitHub and upload these files.
2.  Go to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret**.
4.  **Add 1st Secret**:
    *   Name: `GDRIVE_FOLDER_ID`
    *   Secret: Paste the Folder ID you copied from the URL.
5.  **Add 2nd Secret**:
    *   Name: `GDRIVE_CREDENTIALS`
    *   Secret: Open the `.json` key file you downloaded in a text editor. **Copy the entire content** and paste it here.

## 4. Run It!
*   Go to the **Actions** tab in your GitHub repository.
*   Select "Daily Stock Data Collection" on the left.
*   Click **Run workflow** to test it immediately.
*   After it finishes, check your Google Drive folder. You should see `^NSEI_data.csv` etc. being created!
