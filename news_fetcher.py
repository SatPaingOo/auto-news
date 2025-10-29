import os
import requests
import gspread
import json
import time 
import sys 
from google.oauth2.service_account import Credentials

# --- 1. Environment Variables & Setup ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_CREDENTIALS_JSON_STRING = os.getenv('GOOGLE_CREDENTIALS_JSON')
CREDENTIALS_FILE_PATH = 'service_account_credentials.json'

# Gemini Flash Model Endpoint (Text & Search အတွက်)
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent' 

def setup_google_credentials():
    # ... (unchanged)
    if GOOGLE_CREDENTIALS_JSON_STRING:
        try:
            credentials_data = json.loads(GOOGLE_CREDENTIALS_JSON_STRING)
            with open(CREDENTIALS_FILE_PATH, 'w') as f:
                json.dump(credentials_data, f, indent=2)
            return True
        except json.JSONDecodeError as e:
            print(f"Error decoding GOOGLE_CREDENTIALS_JSON: {e}")
            return False
    return False

# --- 2. Gemini Functions ---

def fetch_and_structure_news(category="General"):
    # ... (unchanged)
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found.")
        return []

    headers = { 'Content-Type': 'application/json', }
    
    prompt_text = (
        f"Search for the top 5 most trending **{category}** news headlines from today. "
        # ... (rest of prompt)
        "with keys: 'title', 'summary', 'date', 'source_url'."
    )
    
    data = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "config": {
            "tools": [{"google_search": {}}]
        }
    }
    
    print(f"Fetching news for category: {category}...")
    try:
        response = requests.post(
            GEMINI_API_URL, 
            headers=headers, 
            json=data, 
            params={'key': GEMINI_API_KEY} 
        )
        response.raise_for_status()
        # ... (rest of fetch_and_structure_news)
        return formatted_news
        
    except Exception as e:
        print(f"Error fetching or parsing structured news: {e}")
        return []

def rewrite_content_with_gemini(content):
    # ... (unchanged)
    return content 

def generate_visual_keyword(title, content):
    # ... (unchanged)
    return keyword_phrase
        
    except Exception as e:
        return "" 

# --- 3. Google Sheets Function ---

def save_to_google_sheets(news_data):
    """
    သတင်းအချက်အလက်များကို Google Sheets တွင် သိမ်းဆည်းခြင်း။
    """
    if not setup_google_credentials():
        print("Google Sheets credentials setup failed. Cannot save data.")
        return

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets', # 📌 FIXED: Correct scopes format
        'https://www.googleapis.com/auth/drive'         # 📌 FIXED: Correct scopes format
    ]
    
    print("Connecting to Google Sheets...")
    try:
        credentials = Credentials.from_service_account_file(CREDENTIALS_FILE_PATH, scopes=scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(GOOGLE_SHEET_ID)
        worksheet = sh.sheet1
        
        HEADER_ROW = ['Title (EN)', 'Type (Category)', 'Rewritten Content (MM)', 'Visual Keyword (EN)', 'Original Content (MM)', 'Date', 'Source URL', 'Added Date']
        if not worksheet.row_values(1):
             worksheet.append_row(HEADER_ROW)

        existing_titles = set(row[0] for row in worksheet.get_all_values() if row)
        
        # ... (rest of save_to_google_sheets)
        
    except Exception as e:
        print(f"An error occurred during Google Sheets operation: {e}")

# --- 4. Main Execution ---

def main(category="General"):
    # ... (unchanged)
    if not GEMINI_API_KEY or not GOOGLE_SHEET_ID or not GOOGLE_CREDENTIALS_JSON_STRING:
        print("Missing required environment variables. Please check GitHub Secrets.")
        return

    news_data = fetch_and_structure_news(category)
    if news_data:
        save_to_google_sheets(news_data)

if __name__ == '__main__':
    category_arg = sys.argv[1] if len(sys.argv) > 1 else "General" 
    main(category_arg)