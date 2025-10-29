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
    """
    GitHub Secret မှ JSON string ကို gspread အတွက် ဖိုင်အဖြစ် ရေးသားခြင်း
    """
    if GOOGLE_CREDENTIALS_JSON_STRING:
        try:
            # JSON String ကို load ပြီး ဖိုင်အဖြစ် ရေးသား
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
    """
    Gemini API ကို Google Search Tool ဖြင့် သတင်း ၅ ပုဒ်ကို JSON format ဖြင့် ရယူခြင်း။
    """
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found.")
        return []

    headers = { 'Content-Type': 'application/json', }
    
    # Prompt တွင် Category ထည့်သွင်းပြီး မြန်မာလို အကျဉ်းချုပ်ခိုင်းသည်
    prompt_text = (
        f"Search for the top 5 most trending **{category}** news headlines from today. "
        "Summarize each news item in Myanmar language. "
        "For each news item, provide the title in English, the summary in Myanmar language, "
        "the current date, and the URL link to the source. "
        "Return the output as a clean, valid JSON array of objects, "
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
        result = response.json()
        
        # Code block များ ဖယ်ရှားခြင်း
        json_string = result['candidates'][0]['content']['parts'][0]['text']
        if json_string.strip().startswith("```json"):
            json_string = json_string.strip()[7:-3].strip() 
            
        news_list = json.loads(json_string)
        
        formatted_news = []
        for news_item in news_list:
            formatted_news.append({
                'title': news_item.get('title', ''), 
                'type': category, 
                'content': news_item.get('summary', ''),
                'date': news_item.get('date', ''),
                'source': news_item.get('source_url', '')
            })
        print(f"Successfully fetched {len(formatted_news)} news items.")
        return formatted_news
        
    except Exception as e:
        print(f"Error fetching or parsing structured news: {e}")
        return []

def rewrite_content_with_gemini(content):
    """
    သတင်းအကြောင်းအရာကို မြန်မာလို ပုံစံဖြင့် ပြန်လည်ရေးသားခြင်း။
    """
    if not GEMINI_API_KEY or not content:
        return content

    headers = { 'Content-Type': 'application/json', }
    
    prompt = f"အောက်ပါသတင်းအကျဉ်းချုပ်ကို သတင်းလွှာအတွက် ဖတ်ရလွယ်ကူပြီး စိတ်ဝင်စားစရာကောင်းသော မြန်မာစကားဖြင့် စာပိုဒ်တိုတစ်ခုအဖြစ် ပြန်လည်ရေးသားပေးပါ။ မူရင်းသတင်းအကျဉ်းချုပ်မှာ - {content}"
    
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    
    try:
        response = requests.post(
            GEMINI_API_URL, 
            headers=headers, 
            json=data, 
            params={'key': GEMINI_API_KEY} 
        )
        response.raise_for_status()
        result = response.json()
        
        rewritten = result['candidates'][0]['content']['parts'][0]['text']
        return rewritten
        
    except Exception as e:
        return content 

def generate_visual_keyword(title, content):
    """
    Stock Photo Search အတွက် သော့ချက်စကားလုံး ထုတ်ပေးခြင်း။
    """
    if not GEMINI_API_KEY:
        return ""

    headers = { 'Content-Type': 'application/json', }
    
    prompt = (
        f"Based on the news title: '{title}' and the Myanmar summary: '{content}'. "
        "Generate a single, short, concise, and highly effective keyword phrase (max 5 words) "
        "suitable for searching a professional stock photo database (like Unsplash) "
        "to find a relevant visual. The output MUST be in English. "
        "ONLY return the keyword phrase, no other text or punctuation."
    )
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(
            GEMINI_API_URL, 
            headers=headers, 
            json=data, 
            params={'key': GEMINI_API_KEY} 
        )
        response.raise_for_status()
        result = response.json()
        
        keyword_phrase = result['candidates'][0]['content']['parts'][0]['text'].strip()
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

    # 📌 FINAL FIX: Scopes များကို မှန်ကန်သော Plain String များအဖြစ် ပြင်ဆင်ခြင်း
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets', 
        'https://www.googleapis.com/auth/drive'         
    ]
    
    print("Connecting to Google Sheets...")
    try:
        credentials = Credentials.from_service_account_file(CREDENTIALS_FILE_PATH, scopes=scopes)
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(GOOGLE_SHEET_ID)
        worksheet = sh.sheet1
        
        # Header Row မရှိသေးရင် ထည့်သွင်းခြင်း
        HEADER_ROW = ['Title (EN)', 'Type (Category)', 'Rewritten Content (MM)', 'Visual Keyword (EN)', 'Original Content (MM)', 'Date', 'Source URL', 'Added Date']
        if not worksheet.row_values(1):
            worksheet.append_row(HEADER_ROW)

        # Title အဟောင်းများ စစ်ဆေးခြင်း
        existing_titles = set(row[0] for row in worksheet.get_all_values() if row)
        
        new_rows = []
        for item in news_data:
            title = item.get('title', '')
            original_content = item.get('content', '')
            source_url = item.get('source', '')
            
            if title and title not in existing_titles:
                print(f"Processing new item: {title[:40]}...")
                
                rewritten_content = rewrite_content_with_gemini(original_content)
                visual_keyword = generate_visual_keyword(title, rewritten_content)
                
                new_rows.append([
                    title,
                    item.get('type', ''),
                    rewritten_content,
                    visual_keyword,
                    original_content,
                    item.get('date', ''),
                    source_url,
                    time.strftime("%Y-%m-%d %H:%M:%S")
                ])
                existing_titles.add(title)

        if new_rows:
            worksheet.append_rows(new_rows)
            print(f"Successfully added {len(new_rows)} new rows to Google Sheet.")
        else:
            print("No new news items to add.")
            
    except Exception as e:
        # Sheet Authorization Error များကို ဖမ်းယူခြင်း
        print(f"An error occurred during Google Sheets operation: {e}")

# --- 4. Main Execution ---

def main(category="General"):
    """
    Main function သည် command line မှ category ကို လက်ခံပါသည်။
    """
    if not GEMINI_API_KEY or not GOOGLE_SHEET_ID or not GOOGLE_CREDENTIALS_JSON_STRING:
        print("Missing required environment variables. Please check GitHub Secrets.")
        return

    news_data = fetch_and_structure_news(category)
    if news_data:
        save_to_google_sheets(news_data)

if __name__ == '__main__':
    # Command line argument မှ category ကို လက်ခံသည်။ မရှိပါက 'General' ကို သုံးသည်။
    category_arg = sys.argv[1] if len(sys.argv) > 1 else "General" 
    main(category_arg)