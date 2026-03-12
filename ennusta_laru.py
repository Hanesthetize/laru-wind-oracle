import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sys
import os
import csv
import time

# --- ASETUKSET ---
COEFFS_FILE = 'coeffs.json'
LOG_FILE = 'ennuste_vertailu.csv'

def lataa_kertoimet():
    if os.path.exists(COEFFS_FILE):
        try:
            with open(COEFFS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Virhe kertoimien lukemisessa: {e}")
    return None

def hae_suomen_aika_offset(pvm_utc):
    vuosi = pvm_utc.year
    maalis_loppu = datetime(vuosi, 3, 31, 1)
    alku = maalis_loppu - timedelta(days=(maalis_loppu.weekday() + 1) % 7)
    loka_loppu = datetime(vuosi, 10, 31, 1)
    loppu = loka_loppu - timedelta(days=(loka_loppu.weekday() + 1) % 7)
    return 3 if alku <= pvm_utc < loppu else 2

def hae_kerroin(coeffs, pvm_obj_utc, suunta):
    if not coeffs: return 0.55
    offset = hae_suomen_aika_offset(pvm_obj_utc)
    suomen_aika = pvm_obj_utc + timedelta(hours=offset)
    kk, tunti = str(suomen_aika.month), str(suomen_aika.hour)
    sektori = str(int(suunta // 10) * 10)
    try:
        return coeffs[kk][sektori][tunti]
    except KeyError:
        return 0.55

def hae_fmi_kaikki_data(fmisid=None, latlon=None):
    """Hakee datan käyttäen FMISID:tä tai koordinaatteja."""
    base_url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage"
    
    if fmisid:
        url = f"{base_url}&fmisid={fmisid}"
    else:
        url = f"{base_url}&latlon={latlon}"
    
    url += "&parameters=WindSpeedMS,WindDirection,WindGust,Temperature,Pressure,TotalCloudCover"
    
    try:
        print(f"🔍 Haetaan: {url}")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        
        if not r.content: return None
            
        root = ET.fromstring(r.content)
        data_node = next((e for e in root.iter() if e.tag.endswith('doubleOrNilReasonTupleList')), None)
        
        if data_node is not None and data_node.text:
            return data_node.text.strip().split('\n')
    except Exception as e:
        print(f"❌ Virhe haussa: {e}")
    return None

def paivita_ennuste():
    print("🚀 Käynnistetään Laru Oraakkeli V4.2 (LatLon Edition)...")
    
    coeffs = lataa_kertoimet()
    
    # Haetaan datat: Harmaja (ID), Kaisaniemi (LatLon) ja Laru (LatLon)
    har_rows = hae_fmi_kaikki_data(fmisid=100996)       # Harmaja
    kai_rows = hae_fmi_kaikki_data(latlon="60.175,24.944") # Kaisaniemi
    lar_rows = hae_fmi_kaikki_data(latlon="60.155,24.878") # Laru
    
    if not (har_rows and kai_rows and lar_rows):
        print("❌ Keskeytetään: Dataa ei saatu riittävästi.")
        if not har_rows: print("- Harmaja puuttuu")
        if not kai_rows: print("- Kaisaniemi puuttuu")
        if not lar_rows: print("- Lauttasaari puuttuu")
        return

    ennusteet = []
    log_rivit = []
    nykyhetki_utc = datetime.utcnow()

    # Käydään läpi seuraavat 24 tuntia
    maksimi_tunnit = min(24, len(har_rows), len(kai_rows), len(lar_rows))
    
    for i in range(maksimi_tunnit):
        h = har_rows[i].split()
        k = kai_rows[i].split()
        l = lar_rows[i].split()
        
        if len(h) < 6 or len(k) < 6 or len(l) < 1: continue
        
        h_ws, h_dir, h_gust = float(h[0]), float(h[1]), float(h[2])
        h_temp, h_pres, h_cloud = float(h[3]), float(h[4]), float(h[5])
        k_temp = float(k[3])
        l_fmi_ws = float(l[0])
        
        delta_t = round(k_temp - h_temp, 1)
        
        ennuste_aika_utc = nykyhetki_utc + timedelta(hours=i)
        kerroin = hae_kerroin(coeffs, ennuste_aika_utc, h_dir)
        
        oraakkeli_ws = round(h_ws * kerroin, 1)
        oraakkeli_gust = round(h_gust * kerroin, 1)
        
        offset = hae_suomen_aika_offset(ennuste_aika_utc)
        aika_str = (ennuste_aika_utc + timedelta(hours=offset)).strftime("%d.%m. %H:%M")

        ennusteet.append({
            "aika_str": aika_str,
            "har_ms": h_ws,
            "laru_ms": oraakkeli_ws,
            "laru_fmi_ms": l_fmi_ws,
            "har_dir": h_dir,
            "delta_t": delta_t,
            "cloud": h_cloud,
            "gust_ms": oraakkeli_gust
        })

        if i == 0:
            log_rivit.append([
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                h_ws, h_dir, h_gust, h_temp, h_pres, h_cloud, delta_t, l_fmi_ws, oraakkeli_ws
            ])

    with open('ennuste.json', 'w') as f:
        json.dump(ennusteet, f, indent=4)

    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Aika', 'Har_WS', 'Har_Dir', 'Har_Gust', 'Har_Temp', 'Har_Pres', 'Har_Cloud', 'DeltaT', 'Laru_FMI_WS', 'Oraakkeli_WS'])
        writer.writerows(log_rivit)

    print(f"✅ VALMIS: Päivitetty {len(ennusteet)} tuntia ja lokitettu vertailu.")

if __name__ == "__main__":
    paivita_ennuste()
