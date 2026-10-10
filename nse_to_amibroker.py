import os
import time
from datetime import datetime, timedelta
import requests
import hashlib

def get_file_hash(filepath):
    """फाइल का MD5 हैश निकालकर यह चेक करने के लिए कि फाइल डुप्लीकेट है या नहीं"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def download_and_clean_nse_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # पहले एनएसई की वेबसाइट से सेशन कुकीज़ प्राप्त करें
    try:
        session.get("https://www.nseindia.com", timeout=10)
    except Exception as e:
        print("NSE Connection Init Error:", e)
        return

    # पिछले 2 साल (730 दिन) की अवधि सेट की गई है
    end_date = datetime.now()
    start_date = end_date - timedelta(days=50)
    
    current_date = start_date
    os.makedirs("nse_bhavcopies", exist_ok=True)

    print(f"डेटा डाउनलोड शुरू हो रहा है: {start_date.strftime('%Y-%m-%d')} से {end_date.strftime('%Y-%m-%d')} तक...\n")

    # 1. डेटा डाउनलोड करने की प्रक्रिया
    while current_date <= end_date:
        date_str_nse = current_date.strftime("%d%m%Y") # NSE के URL के लिए DDMMYYYY format
        date_str_file = current_date.strftime("%Y%m%d") # फाइल सेव करने के लिए YYYYMMDD format
        
        url = f"https://archives.nseindia.com/products/content/sec_bhavdata_full_{date_str_nse}.csv"
        file_path = f"nse_bhavcopies/sec_bhavdata_{date_str_file}.csv"
        
        if not os.path.exists(file_path):
            try:
                response = session.get(url, timeout=10)
                if response.status_code == 200 and len(response.content) > 1000:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"सफलतापूर्वक डाउनलोड हुआ: {date_str_file}")
            except Exception as ex:
                pass
            
            time.sleep(1.2)
        
        current_date += timedelta(days=1)

    print("\nछुट्टियों के कारण एनएसई द्वारा दी गई डुप्लीकेट (पुरानी) फाइलों की सफाई की जा रही है...")
    
    # 2. डुप्लीकेट हटाने का लॉजिक (Content Hash के आधार पर)
    seen_hashes = {}
    removed_count = 0
    
    for filename in sorted(os.listdir("nse_bhavcopies")):
        if filename.endswith(".csv"):
            f_path = os.path.join("nse_bhavcopies", filename)
            try:
                file_hash = get_file_hash(f_path)
                if file_hash in seen_hashes:
                    os.remove(f_path)
                    print(f"डुप्लीकेट हटाई गई: {filename} (मूल फाइल: {seen_hashes[file_hash]})")
                    removed_count += 1
                else:
                    seen_hashes[file_hash] = filename
            except Exception as e:
                print(f"फाइल प्रोसेस करने में त्रुटि {filename}: {e}")

    print(f"\nप्रक्रिया पूरी हुई! कुल {removed_count} डुप्लीकेट फाइलें हटा दी गई हैं।")
    print("अब शुद्ध और साफ़ डेटा 'nse_bhavcopies' फोल्डर में YYYYMMDD फॉर्मेट में उपलब्ध है।")

if __name__ == "__main__":
    download_and_clean_nse_data()
