import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import csv
import os

# Meidän kertoimet (Maaliskuu)
KK_BASE = {1: 0.68, 2: 0.66, 3: 0.57, 4: 0.61, 5: 0.59, 6: 0.63, 7: 0.63, 8: 0.58, 9: 0.60, 10: 0.65, 11: 0.69, 12: 0.64}

def laske_laru_teho(har_ms, suunta, pvm_obj):
    if not (180 <= suunta <= 240): 
        return round(har_ms * 0.45, 1)
    base = KK_BASE.get(pvm_obj.month, 0.63)
    return round(har_ms * base, 1)

def hae_laru_actual():
    """Hakee todellisen datan Larun Windguru-asemalta (Station 47)"""
    try:
        wg_url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=47"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.windguru.cz/station/47'}
        res = requests.get(wg_url, headers=headers, timeout=10).json()
        if 'wind_avg' in res:
            # Muunnetaan kts -> m/s
            ws = round(float(res['wind_avg']) * 0.51444, 1)
            return ws
    except:
        return None
    return None

def loggaa_kaikki():
    print("📡 Kerätään vertailudataa (Harmaja vs Laru Mittari)...")
    
    # 1. HARMAJA TOTEUMA (FMI)
    fmi_url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996&parameters=t2m,ws_10min,wg_10min,winddirection"
    
    try:
        r = requests.get(fmi_url, timeout=30)
        root = ET.fromstring(r.content)
        data_node = next((e for e in root.iter() if e.tag.endswith('doubleOrNilReasonTupleList')), None)
        
        if data_node and data_node.text:
            last_obs = data_node.text.strip().split('\n')[-1].split()
            temp, har_ws, har_gust, har_dir = map(float, last_obs)
            
            # 2. LARU TOTEUMA (Windguru)
            laru_actual = hae_laru_actual()
            
            # 3. LARU ENNUSTE (Mitä meidän koodi laskisi Harmajasta juuri nyt)
            pvm = datetime.now()
            laru_predicted = laske_laru_teho(har_ws, har_dir, pvm)
            
            aika_str = pvm.strftime("%Y-%m-%d %H:%M")
            
            # 4. TALLENNUS
            file_exists = os.path.isfile('history.csv')
            with open('history.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['aika', 'temp', 'har_ws', 'har_gust', 'har_dir', 'laru_actual', 'laru_predicted'])
                
                writer.writerow([aika_str, temp, har_ws, har_gust, har_dir, laru_actual, laru_predicted])
            
            print(f"✅ Logattu! Harmaja: {har_ws} | Mittari: {laru_actual} | Oracle: {laru_predicted}")

    except Exception as e:
        print(f"❌ Lokitusvirhe: {e}")

if __name__ == "__main__":
    loggaa_kaikki()
