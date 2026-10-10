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

    data_list = []

    for filename in all_files:
        base_name = os.path.basename(filename)
        date_str = base_name.replace('sec_bhavdata_', '').replace('.csv', '')
        if len(date_str) == 8:
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        else:
            continue

        try:
            df = pd.read_csv(filename)
            df.columns = df.columns.str.strip()
            
            if 'SYMBOL' in df.columns and 'SERIES' in df.columns:
                filtered = df[(df['SERIES'] == 'EQ') & (df['SYMBOL'].isin(fo_symbols))].copy()
                
                for _, row in filtered.iterrows():
                    symbol = str(row['SYMBOL']).strip()
                    deliv_qty = float(row.get('DELIV_QTY', 0))
                    
                    data_list.append({
                        'Date': formatted_date,
                        'Symbol': symbol,
                        'DelivQty': deliv_qty
                    })
        except Exception as e:
            continue

    if not data_list:
        print("डेटा प्रोसेस करने में विफल।")
        return

    df_all = pd.DataFrame(data_list)
    df_all['Date'] = pd.to_datetime(df_all['Date'])
    df_all = df_all.sort_values(['Symbol', 'Date'])

    # 3. 5-दिन का मूविंग एवरेज कैलकुलेट करें
    df_all['Avg5_Deliv'] = df_all.groupby('Symbol')['DelivQty'].transform(lambda x: x.rolling(window=5, min_periods=5).mean())
    df_all['Ratio_Pct'] = (df_all['DelivQty'] / df_all['Avg5_Deliv']) * 100

    # 4. सिग्नल जनरेट करें
    signals = df_all[df_all['Ratio_Pct'] >= 100]
    
    print(f"\nकुल सिग्नल मिले: {len(signals)}")
    print(signals.head(10))

if __name__ == '__main__':
    run_backtest()
