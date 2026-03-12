import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sys
import os
import csv

# --- ASETUKSET ---
COEFFS_FILE = 'coeffs.json'
LOG_FILE = 'ennuste_vertailu.csv'

def hae_fmi_kaikki_data(fmisid=None, paikka=None):
    """
    Hakee laajan setin parametreja: Tuuli, Suunta, Puuska, Lämpötila, Paine, Pilvisyys.
    """
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage"
    if fmisid: url += f"&fmisid={fmisid}"
    else: url += f"&place={paikka}"
    
    # Lisätty: Temperature, Pressure, TotalCloudCover
    url += "&parameters=WindSpeedMS,WindDirection,WindGust,Temperature,Pressure,TotalCloudCover"
    
    try:
        r = requests.get(url, timeout=20)
        root = ET.fromstring(r.content)
        data_node = next((e for e in root.iter() if e.tag.endswith('doubleOrNilReasonTupleList')), None)
        if data_node:
            return data_node.text.strip().split('\n')
    except Exception as e:
        print(f"Virhe FMI-haussa: {e}")
    return None

def paivita_ennuste():
    print("🚀 Käynnistetään Laru Oraakkeli V4.1 (Petri Edition)...")
    
    # Haetaan laaja data: Harmaja, Kaisaniemi (lämpövertailu) ja Lauttasaari
    har_rows = hae_fmi_kaikki_data(fmisid=100996)       # Harmaja (Meri)
    kai_rows = hae_fmi_kaikki_data(fmisid=100971)       # Kaisaniemi (Manner)
    lar_rows = hae_fmi_kaikki_data(paikka="lauttasaari,helsinki") # Laru FMI-arvaus
    
    if not har_rows or not kai_rows or not lar_rows:
        print("❌ Dataa ei saatu riittävästi.")
        return

    ennusteet = []
    log_rivit = []
    nykyhetki_utc = datetime.utcnow()

    # Käydään läpi seuraavat 24 tuntia
    for i in range(min(24, len(har_rows), len(kai_rows))):
        h = har_rows[i].split() # Harmaja: [ws, dir, gust, temp, pres, cloud]
        k = kai_rows[i].split() # Kaisaniemi: [ws, dir, gust, temp, pres, cloud]
        l = lar_rows[i].split() # Laru FMI: [ws, dir, gust, temp, pres, cloud]
        
        if len(h) < 6 or len(k) < 6: continue
        
        # Luetaan arvot
        h_ws, h_dir, h_gust = float(h[0]), float(h[1]), float(h[2])
        h_temp, h_pres, h_cloud = float(h[3]), float(h[4]), float(h[5])
        k_temp = float(k[3])
        l_fmi_ws = float(l[0])
        
        # Lämpötilaero: Manner - Meri (Positiivinen = Manner lämpimämpi = Merituulipotentiaali)
        delta_t = round(k_temp - h_temp, 1)
        
        # Meidän Oraakkeli (vanha matriisi vielä pohjana)
        ennuste_aika_utc = nykyhetki_utc + timedelta(hours=i)
        from __main__ import hae_kerroin # Varmistetaan että funktio löytyy
        kerroin = hae_kerroin(ennuste_aika_utc, h_dir)
        oraakkeli_ws = round(h_ws * kerroin, 1)

        # Muotoillaan aika näyttöä varten
        from __main__ import hae_suomen_aika_offset
        offset = hae_suomen_aika_offset(ennuste_aika_utc)
        aika_str = (ennuste_aika_utc + timedelta(hours=offset)).strftime("%d.%m. %H:%M")

        # JSON Web-sivulle
        ennusteet.append({
            "aika_str": aika_str,
            "har_ms": h_ws,
            "laru_ms": oraakkeli_ws,
            "laru_fmi_ms": l_fmi_ws,
            "har_dir": h_dir,
            "delta_t": delta_t,
            "cloud": h_cloud
        })

        # LOKIIN (Petrin RandomForestia varten)
        if i == 0:
            # Aika, WS, Dir, Gust, Temp, Pres, Cloud, DeltaT, Laru_FMI, Oraakkeli
            log_rivit.append([
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                h_ws, h_dir, h_gust, h_temp, h_pres, h_cloud, delta_t, l_fmi_ws, oraakkeli_ws
            ])

    # Tallennukset
    with open('ennuste.json', 'w') as f:
        json.dump(ennusteet, f, indent=4)

    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Aika', 'Har_WS', 'Har_Dir', 'Har_Gust', 'Har_Temp', 'Har_Pres', 'Har_Cloud', 'DeltaT', 'Laru_FMI_WS', 'Oraakkeli_WS'])
        writer.writerows(log_rivit)

    print(f"✅ VALMIS: Petrin speksin mukainen data kerätty (DeltaT: {log_rivit[0][7]}°C)")

# --- APUFUNKTIOT (Pidetään samassa tiedostossa) ---
def hae_suomen_aika_offset(pvm_utc):
    vuosi = pvm_utc.year
    maalis_loppu = datetime(vuosi, 3, 31, 1)
    alku = maalis_loppu - timedelta(days=(maalis_loppu.weekday() + 1) % 7)
    loka_loppu = datetime(vuosi, 10, 31, 1)
    loppu = loka_loppu - timedelta(days=(loka_loppu.weekday() + 1) % 7)
    return 3 if alku <= pvm_utc < loppu else 2

def hae_kerroin(pvm_obj_utc, suunta):
    coeffs = lataa_kertoimet()
    if not coeffs: return 0.55
    offset = hae_suomen_aika_offset(pvm_obj_utc)
    suomen_aika = pvm_obj_utc + timedelta(hours=offset)
    kk, tunti = str(suomen_aika.month), str(suomen_aika.hour)
    sektori = str(int(suunta // 10) * 10)
    try: return coeffs[kk][sektori][tunti]
    except: return 0.55

def lataa_kertoimet():
    if os.path.exists(COEFFS_FILE):
        with open(COEFFS_FILE, 'r') as f: return json.load(f)
    return None

if __name__ == "__main__":
    paivita_ennuste()
