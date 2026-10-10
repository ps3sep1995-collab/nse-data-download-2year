import os
import time
from datetime import datetime, timedelta
import requests
import hashlib

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
    start_date = end_date - timedelta(days=4000)
    
    current_date = start_date
    os.makedirs("nse_bhavcopies", exist_ok=True)

    print(f"डेटा डाउनलोड शुरू हो रहा है: {start_date.strftime('%Y-%m-%d')} से {end_date.strftime('%Y-%m-%d')} तक...\n")

    seen_hashes = {}
    downloaded_count = 0
    duplicate_count = 0

    # डेटा डाउनलोड और ऑन-द-फ्लाई डुप्लीकेट फिल्ट्रेशन
    while current_date <= end_date:
        date_str_nse = current_date.strftime("%d%m%Y") # NSE URL के लिए DDMMYYYY
        date_str_file = current_date.strftime("%Y%m%d") # फाइल सेव करने के लिए YYYYMMDD
        
        file_path = f"nse_bhavcopies/sec_bhavdata_{date_str_file}.csv"
        
        # अगर फाइल पहले से मौजूद नहीं है तभी डाउनलोड करें
        if not os.path.exists(file_path):
            url = f"https://archives.nseindia.com/products/content/sec_bhavdata_full_{date_str_nse}.csv"
            try:
                response = session.get(url, timeout=10)
                if response.status_code == 200 and len(response.content) > 1000:
                    
                    # डाउनलोड करते ही मेमोरी में हैश निकालें
                    file_hash = hashlib.md5(response.content).hexdigest()
                    
                    # चेक करें कि क्या यह डेटा पहले आ चुका है (हॉलिडे पर पुरानी फाइल देना)
                    if file_hash in seen_hashes:
                        print(f"डुप्लीकेट हटाई गई (स्किल): {date_str_file} (मूल फाइल: {seen_hashes[file_hash]})")
                        duplicate_count += 1
                    else:
                        # अगर यूनीक है, तभी फोल्डर में सेव करें
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        seen_hashes[file_hash] = date_str_file
                        downloaded_count += 1
                        print(f"सफलतापूर्वक सेव हुआ: {date_str_file}")
            except Exception as ex:
                pass
            
            time.sleep(1.2)
        else:
            # अगर फाइल पहले से ही लोकल/रिपॉजिटरी में है, तो उसका भी हैश याद रखang ताकि आगे डुप्लीकेट न हो
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    seen_hashes[file_hash] = date_str_file
            except:
                pass

        current_date += timedelta(days=1)

    print(f"\nप्रक्रिया पूरी हुई!")
    print(f"कुल नई फाइलें सेव हुईं: {downloaded_count}")
    print(f"कुल डुप्लीकेट फाइलें रोकी गईं: {duplicate_count}")
    print("अब 'nse_bhavcopies' फोल्डर में पूरी तरह शुद्ध, साफ़ और सही क्रम में डेटा मौजूद है।")

if __name__ == "__main__":
    download_and_clean_nse_data()
