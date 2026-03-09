import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import csv
import os

def hae_laru_actual():
    """Hakee tuulen nopeuden JA suunnan Larun Windguru-asemalta"""
    try:
        wg_url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=47"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(wg_url, headers=headers, timeout=15)
        res = r.json()
        
        if 'wind_avg' in res and 'wind_direction' in res:
            # Muutetaan knots -> m/s
            ws = round(float(res['wind_avg']) * 0.51444, 1)
            wd = int(res['wind_direction'])
            return ws, wd
    except Exception as e:
        print(f"Windguru error: {e}")
    return None, None

def loggaa_kaikki():
    fmi_url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996&parameters=t2m,ws_10min,wg_10min,winddirection"
    
    try:
        r = requests.get(fmi_url, timeout=15)
        root = ET.fromstring(r.content)
        data_node = next((elem for elem in root.iter() if elem.tag.endswith('doubleOrNilReasonTupleList')), None)
        
        if data_node is not None and data_node.text:
            last_obs = data_node.text.strip().split('\n')[-1].split()
            
            # FMI tiedot (Harmaja)
            temp = float(last_obs[0]) if last_obs[0] != 'NaN' else "nan"
            har_ws = float(last_obs[1])
            har_gust = float(last_obs[2])
            har_dir = float(last_obs[3])
            
            # Laru toteuma (Windguru)
            laru_ws, laru_dir = hae_laru_actual()
            
            # Meidän nykyinen ennustekaava vertailuun
            if 180 <= har_dir <= 240:
                laru_pred = round(har_ws * 0.57, 1)
            else:
                laru_pred = round(har_ws * 0.45, 1)

            # Aika
            aika_str = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            
            # JÄRJESTYS: aika, temp, har_ws, har_gust, har_dir, laru_ws, laru_dir, laru_pred
            row = [aika_str, temp, har_ws, har_gust, har_dir, laru_ws, laru_dir, laru_pred]
            
            file_path = 'history.csv'
            file_exists = os.path.isfile(file_path)
            
            with open(file_path, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    # Otsikot täsmälleen datan mukaan
                    writer.writerow(['aika', 'temp', 'har_ws', 'har_gust', 'har_dir', 'laru_ws', 'laru_dir', 'laru_pred'])
                writer.writerow(row)
                
            print(f"✅ Tallennettu: Laru {laru_ws}m/s, Suunta {laru_dir}")
            
    except Exception as e:
        print(f"❌ Virhe logituksessa: {e}")

if __name__ == "__main__":
    loggaa_kaikki()
