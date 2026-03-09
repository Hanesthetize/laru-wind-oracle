import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import csv
import os

def hae_laru_actual():
    """Hakee tuulen nopeuden JA suunnan Larun Windguru-asemalta"""
    print("🌐 Haetaan Windguru (Laru Station 47) dataa...")
    try:
        wg_url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=47"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.windguru.cz/station/47'
        }
        r = requests.get(wg_url, headers=headers, timeout=15)
        res = r.json()
        
        if 'wind_avg' in res and 'wind_direction' in res:
            ws = round(float(res['wind_avg']) * 0.51444, 1) # kts -> m/s
            wd = int(res['wind_direction'])
            print(f"✅ Laru OK: {ws} m/s, {wd}°")
            return ws, wd
    except Exception as e:
        print(f"⚠️ Windguru-virhe: {e}")
    return None, None

def loggaa_kaikki():
    print("📡 Käynnistetään tiedonkeruu...")
    fmi_url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996&parameters=t2m,ws_10min,wg_10min,winddirection"
    
    try:
        r = requests.get(fmi_url, timeout=15)
        root = ET.fromstring(r.content)
        data_node = next((elem for elem in root.iter() if elem.tag.endswith('doubleOrNilReasonTupleList')), None)
        
        if data_node is not None and data_node.text:
            last_obs = data_node.text.strip().split('\n')[-1].split()
            temp, har_ws, har_gust, har_dir = float(last_obs[0]), float(last_obs[1]), float(last_obs[2]), float(last_obs[3])
            
            # HAETAAN LARUN DATA (Nopeus ja Suunta)
            laru_ws, laru_dir = hae_laru_actual()
            
            # AIKA (Suomen aika)
            pvm = datetime.now() + timedelta(hours=2)
            aika_str = pvm.strftime("%Y-%m-%d %H:%M")
            
            file_path = 'history.csv'
            file_exists = os.path.isfile(file_path)
            
            with open(file_path, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    # Päivitetty otsikkorivi
                    writer.writerow(['aika', 'temp', 'har_ws', 'har_gust', 'har_dir', 'laru_ws', 'laru_dir'])
                
                writer.writerow([aika_str, temp, har_ws, har_gust, har_dir, laru_ws, laru_dir])
            
            print(f"🏁 Tallennettu: Harmaja {har_dir}° -> Laru {laru_dir}°")
            
    except Exception as e:
        print(f"💥 Virhe: {e}")

if __name__ == "__main__":
    loggaa_kaikki()
