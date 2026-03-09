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
            ws = round(float(res['wind_avg']) * 0.51444, 1) # kts -> m/s
            wd = int(res['wind_direction'])
            return ws, wd
    except:
        pass
    return None, None

def loggaa_kaikki():
    fmi_url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996&parameters=t2m,ws_10min,wg_10min,winddirection"
    
    try:
        r = requests.get(fmi_url, timeout=15)
        root = ET.fromstring(r.content)
        data_node = next((elem for elem in root.iter() if elem.tag.endswith('doubleOrNilReasonTupleList')), None)
        
        if data_node is not None and data_node.text:
            last_obs = data_node.text.strip().split('\n')[-1].split()
            # FMI arvot
            temp = float(last_obs[0])
            har_ws = float(last_obs[1])
            har_gust = float(last_obs[2])
            har_dir = float(last_obs[3])
            
            # Laru toteuma
            laru_ws, laru_dir = hae_laru_actual()
            
            # Laru ennuste (nykyinen 0.57 kerroin tai blokki)
            if 180 <= har_dir <= 240:
                laru_pred = round(har_ws * 0.57, 1)
            else:
                laru_pred = round(har_ws * 0.45, 1)

            aika_str = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            
            file_path = 'history.csv'
            # JÄRJESTYS: aika, temp, har_ws, har_gust, har_dir, laru_ws, laru_dir, laru_pred
            row = [aika_str, temp, har_ws, har_gust, har_dir, laru_ws, laru_dir, laru_pred]
            
            # Jos tiedosto on vanha ja siinä on väärä määrä sarakkeita, se kannattaa ehkä resetoida
            file_exists = os.path.isfile(file_path)
            
            with open(file_path, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['aika', 'temp', 'har_ws', 'har_gust', 'har_dir', 'laru_ws', 'laru_dir', 'laru_pred'])
                writer.writerow(row)
                
            print(f"✅ Logattu: Laru actual {laru_ws} m/s ({laru_dir}°) | Predicted {laru_pred} m/s")
            
    except Exception as e:
        print(f"❌ Virhe: {e}")

if __name__ == "__main__":
    loggaa_kaikki()
