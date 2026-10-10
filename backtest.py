import os
import glob
import pandas as pd
import json

def generate_dashboard_json():
    # 1. fo_symbols.txt लोड करें
    fo_symbols = set()
    if os.path.exists('fo_symbols.txt'):
        with open('fo_symbols.txt', 'r', encoding='utf-8') as f:
            for line in f:
                sym = line.strip().upper()
                if sym:
                    fo_symbols.add(sym)
    
    path = 'nse_bhavcopies'
    all_files = sorted(glob.glob(os.path.join(path, "sec_bhavdata_*.csv")))
    
    if not all_files:
        print("कोई Bhavcopy फाइल नहीं मिली!")
        return

    print(f"कुल {len(all_files)} फाइलों को प्रोसेस किया जा रहा है...")

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
            
            # कॉलम के नाम डायनेमिक तरीके से ढूंढें
            sym_col = next((c for c in df.columns if 'SYMBOL' in c.upper()), None)
            series_col = next((c for c in df.columns if 'SERIES' in c.upper()), None)
            deliv_col = next((c for c in df.columns if 'DELIV_QTY' in c.upper() or 'DELIV QTY' in c.upper()), None)

            if sym_col and deliv_col:
                for _, row in df.iterrows():
                    symbol = str(row[sym_col]).strip().upper()
                    series = str(row[series_col]).strip().upper() if series_col else 'EQ'
                    
                    if series == 'EQ' and (not fo_symbols or symbol in fo_symbols):
                        try:
                            deliv_qty = float(str(row[deliv_col]).replace(',', ''))
                            data_list.append({
                                'Date': formatted_date,
                                'Symbol': symbol,
                                'DelivQty': deliv_qty
                            })
                        except:
                            pass
        except Exception as e:
            continue

    if not data_list:
        print("डेटा प्रोसेस करने में विफल।")
        return

    df_all = pd.DataFrame(data_list)
    df_all['Date'] = pd.to_datetime(df_all['Date'])
    df_all = df_all.sort_values(['Symbol', 'Date'])

    # 5-दिन का मूविंग एवरेज कैलकुलेट करें
    df_all['Avg5_Deliv'] = df_all.groupby('Symbol')['DelivQty'].transform(lambda x: x.rolling(window=5, min_periods=2).mean())
    df_all['Ratio_Pct'] = (df_all['DelivQty'] / df_all['Avg5_Deliv']) * 100

    df_all['DateStr'] = df_all['Date'].dt.strftime('%Y-%m-%d')
    
    # तारीख के हिसाब से JSON स्ट्रक्चर बनाएं
    result_dict = {}
    for date_val, group in df_all.groupby('DateStr'):
        day_records = []
        for _, row in group.iterrows():
            if pd.notna(row['Ratio_Pct']):
                day_records.append({
                    'symbol': row['Symbol'],
                    'delivQty': int(row['DelivQty']),
                    'avg5Qty': int(row['Avg5_Deliv']),
                    'ratioPct': round(float(row['Ratio_Pct']), 2)
                })
        result_dict[date_val] = day_records

    with open('dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(result_dict, f)

    print("सफलतापूर्वक 'dashboard_data.json' तैयार हो गई है!")

if __name__ == '__main__':
    generate_dashboard_json()
