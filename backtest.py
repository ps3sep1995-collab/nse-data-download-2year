import os
import glob
import pandas as pd

def run_backtest():
    # 1. fo_symbols.txt से F&O स्टॉक्स लोड करें
    fo_symbols = set()
    if os.path.exists('fo_symbols.txt'):
        with open('fo_symbols.txt', 'r', encoding='utf-8') as f:
            for line in f:
                sym = line.strip().upper()
                if sym:
                    fo_symbols.add(sym)
    
    # 2. सभी Bhavcopy फाइलों की लिस्ट लें और तारीख के अनुसार सॉर्ट करें
    path = 'nse_bhavcopies'
    all_files = sorted(glob.glob(os.path.join(path, "sec_bhavdata_*.csv")))
    
    if not all_files:
        print("कोई Bhavcopy फाइल नहीं मिली!")
        return

    print(f"कुल {len(all_files)} फाइलों पर बैकटेस्ट प्रक्रिया शुरू हो रही है...")

    # सभी डेटा को एक स्ट्रक्चर में इकट्ठा करें
    data_list = []

    for filename in all_files:
        # फाइल नाम से तारीख निकालें (जैसे sec_bhavdata_20241010.csv)
        base_name = os.path.basename(filename)
        date_str = base_name.replace('sec_bhavdata_', '').replace('.csv', '')
        if len(date_str) == 8:
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        else:
            continue

        try:
            df = pd.read_csv(filename)
            # कॉलम के नामों से अतिरिक्त स्पेस हटाएं
            df.columns = df.columns.str.strip()
            
            # आवश्यक कॉलम चेक करें (Symbol, Series, Delivery Qty, Close Price आदि)
            if 'SYMBOL' in df.columns and 'SERIES' in df.columns:
                # केवल F&O और EQ सीरीज छांटें
                filtered = df[(df['SERIES'] == 'EQ') & (df['SYMBOL'].isin(fo_symbols))].copy()
                
                for _, row in filtered.iterrows():
                    symbol = str(row['SYMBOL']).strip()
                    # डिलीवरी क्वांटिटी और प्राइस चेंज निकालने के लिए कॉलम नाम एनएससी के फॉर्मेट के अनुसार देखें
                    deliv_qty = float(row.get('DELIV_QTY', row.get('Net_Turnover', 0))) # जरूरत पड़ने पर कॉलम नेम मैच करें
                    change_pct = float(row.get('FUT_CONT', row.get('%_Chg', 0)))     # उदाहरण के लिए
                    
                    data_list.append({
                        'Date': formatted_date,
                        'Symbol': symbol,
                        'DelivQty': deliv_qty
                    })
        except Exception as e:
            continue

    # पांडास DataFrame में कन्वर्ट करें
    if not data_list:
        print("डेटा प्रोसेस करने में विफल। कृपया CSV के कॉलम नाम चेक करें।")
        return

    df_all = pd.DataFrame(data_list)
    df_all['Date'] = pd.to_datetime(df_all['Date'])
    df_all = df_all.sort_values(['Symbol', 'Date'])

    # 3. 5-दिन का मूविंग एवरेज कैलकुलेट करें
    df_all['Avg5_Deliv'] = df_all.groupby('Symbol')['DelivQty'].transform(lambda x: x.rolling(window=5, min_periods=5).mean())
    df_all['Ratio_Pct'] = (df_all['DelivQty'] / df_all['Avg5_Deliv']) * 100

    # 4. सिग्नल जनरेट करें (जहाँ आज की डिलीवरी 5-दिन के औसत से 100% या अधिक हो)
    signals = df_all[df_all['Ratio_Pct'] >= 100]
    
    print(f"\nकुल सिग्नल मिले: {len(signals)}")
    print(signals.head(10))

if __name__ == '__main__':
    run_backtest()
