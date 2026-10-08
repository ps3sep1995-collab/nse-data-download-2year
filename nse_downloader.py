import os
import time
from datetime import datetime, timedelta
import requests
import hashlib

def get_file_hash(filepath):
    """फाइल का हैश (Hash) निकालकर यह चेक करने के लिए कि फाइल डुप्लीकेट है या नहीं"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def download_and_clean_bhavcopy(start_date, end_date):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        session.get("https://www.nseindia.com", timeout=10)
    except Exception as e:
        print("NSE Connection Error:", e)
        return

    current_date = start_date
    os.makedirs("nse_bhavcopies", exist_ok=True)

    downloaded_files = []

    while current_date <= end_date:
        date_str = current_date.strftime("%d%m%Y")
        url = f"https://archives.nseindia.com/products/content/sec_bhavdata_full_{date_str}.csv"
        file_path = f"nse_bhavcopies/sec_bhavdata_{date_str}.csv"
        
        if not os.path.exists(file_path):
            try:
                response = session.get(url, timeout=10)
                if response.status_code == 200 and len(response.content) > 1000:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"डाउनलोड सफल: {date_str}")
                else:
                    pass
            except Exception as ex:
                print(f"त्रुटि {date_str}: {ex}")
            
            time.sleep(1.5)
        
        current_date += timedelta(days=1)

    print("\nअब डुप्लीकेट (छुट्टियों वाली एक जैसी) फाइलों की जाँच और सफाई की जा रही है...")
    
    # डुप्लीकेट हटाने का लॉजिक (Content Hash के आधार पर)
    seen_hashes = {}
    for filename in os.listdir("nse_bhavcopies"):
        if filename.endswith(".csv"):
            f_path = os.path.join("nse_bhavcopies", filename)
            file_hash = get_file_hash(f_path)
            
            if file_hash in seen_hashes:
                # अगर यह फाइल पहले से मौजूद किसी फाइल जैसी है (यानी हॉलिडे पर पुरानी फाइल मिल गई)
                os.remove(f_path)
                print(f"डुप्लीकेट हटाई गई: {filename} (मूल फाइल: {seen_hashes[file_hash]})")
            else:
                seen_hashes[file_hash] = filename

    print("डेटा डाउनलोड और क्लीनिंग प्रक्रिया पूरी हो गई है!")

if __name__ == "__main__":
    # पिछले 2 साल (730 दिन)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    print(f"प्रक्रिया शुरू: {start_date.strftime('%Y-%m-%d')} से {end_date.strftime('%Y-%m-%d')} तक...")
    download_and_clean_bhavcopy(start_date, end_date)
