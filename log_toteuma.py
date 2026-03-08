import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import csv
import os

# Meidän kertoimet (Maaliskuu) - Käytetään ennusteen vertailuun
KK_BASE = {1: 0.68, 2: 0.66, 3: 0.57, 4: 0.61, 5: 0.59, 6: 0.63, 7: 0.63, 8: 0.58, 9: 0.60, 10: 0.65, 11: 0.69, 12: 0.64}

def laske_laru_teho(har_ms, suunta, pvm_obj):
    """Laskee mitä meidän nykyinen mallimme ennustaisi Larulle näillä Harmajan arvoilla"""
    if not (180 <= suunta <= 240): 
        return round(har_ms * 0.45, 1)
    base = KK_BASE.get(pvm_obj.month, 0.63)
    return round(har_ms * base, 1)

def hae_laru_actual():
    """Hakee todellisen datan Larun Windguru-asemalta (Station 47)"""
    print("🌐 Haetaan Windguru (Laru Station 47) dataa...")
    try:
        wg_url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=47"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(wg_url, headers=headers, timeout=15).json()
        if 'wind_avg' in res:
            # Muunnetaan solmut (kts) -> m/s
            ws = round(float(res['wind_avg']) * 0.51444, 1)
            print(f"✅ Laru Actual OK: {ws} m/s")
            return ws
    except Exception as e:
        print(f"⚠️ Windguru-virhe: {e}")
    return None

def loggaa_kaikki():
    print("📡 Käynnistetään tiedonkeruu...")
    
    # 1. HAETAAN HARMAJAN TOTEUMA (FMI)
    # Haetaan viimeisimmät havainnot Harmajasta (fmisid=100996)
    fmi_url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996&parameters=t2m,ws_10min,wg_10min,winddirection"
    
    try:
        r = requests.get(fmi_url, timeout=15)
        r.raise_for_status()
        
        root = ET.fromstring(r.content)
        data_node = None
        
        # Etsitään XML-puusta se kohta, jossa varsinainen data on
        for elem in root.iter():
            if elem.tag.endswith('doubleOrNilReasonTupleList'):
                data_node = elem
                break
        
        if data_node is not None and data_node.text and len(data_node.text.strip()) > 0:
            # Otetaan listan viimeinen (tuorein) havaintorivi
            all_rows = data_node.text.strip().split('\n')
            last_obs = all_rows[-1].split()
            
            # Parametrit: t2m (0), ws_10min (1), wg_10min (2), winddirection (3)
            temp = float(last_obs[0])
            har_ws = float(last_obs[1])
            har_gust = float(last_obs[2])
            har_dir = float(last_obs[3])
            
            print(f"✅ FMI Data saatu: Harmaja {har_ws} m/s, {har_dir}°, Lämpö {temp}°C")
            
            # 2. HAETAAN LARUN TODELLINEN MITTARIARVO (Windguru)
            laru_actual = hae_laru_actual()
            
            # 3. LASKETAAN ORACLE-ENNUSTE VERTAILUA VARTEN
            # Käytetään Suomen aikaa (UTC + 2h)
            pvm = datetime.now() + timedelta(hours=2)
            laru_predicted = laske_laru_teho(har_ws, har_dir, pvm)
            aika_str = pvm.strftime("%Y-%m-%d %H:%M")
            
            # 4. TALLENNUS HISTORY.CSV -TIEDOSTOON
            file_path = 'history.csv'
            file_exists = os.path.isfile(file_path)
            
            print(f"📝 Tallennetaan rivi tiedostoon {file_path}...")
            with open(file_path, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    # Otsikkorivi jos tiedostoa ei vielä ole
                    writer.writerow(['aika', 'temp', 'har_ws', 'har_gust', 'har_dir', 'laru_actual', 'laru_predicted'])
                
                writer.writerow([aika_str, temp, har_ws, har_gust, har_dir, laru_actual, laru_predicted])
            
            print(f"🏁 VALMIS! Rivi lisätty onnistuneesti.")
        else:
            print("❌ Virhe: FMI palautti tyhjän datalistan. Yritä uudelleen myöhemmin.")

    except Exception as e:
        print(f"💥 KRIITTINEN VIRHE LOKITUKSESSA: {e}")

if __name__ == "__main__":
    loggaa_kaikki()
