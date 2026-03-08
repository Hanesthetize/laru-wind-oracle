import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sys

# --- ANALYYSIIN PERUSTUVAT KERTOIMET ---
KK_BASE = {1: 0.68, 2: 0.66, 3: 0.57, 4: 0.61, 5: 0.59, 6: 0.63, 7: 0.63, 8: 0.58, 9: 0.60, 10: 0.65, 11: 0.69, 12: 0.64}
HOUR_MOD = {0: 0.94, 1: 0.90, 2: 0.90, 3: 0.90, 4: 0.90, 5: 0.78, 6: 0.89, 7: 0.92, 8: 0.94, 9: 0.98, 10: 1.03, 11: 1.13, 12: 1.14, 13: 1.16, 14: 1.16, 15: 1.19, 16: 1.11, 17: 1.14, 18: 1.08, 19: 1.03, 20: 1.00, 21: 0.95, 22: 0.92, 23: 0.90}

def laske_laru_teho(har_ms, suunta, pvm_obj):
    if not (180 <= suunta <= 240):
        return round(har_ms * 0.50, 1)
    base = KK_BASE.get(pvm_obj.month, 0.63)
    mod = HOUR_MOD.get(pvm_obj.hour, 1.0)
    return round(har_ms * base * mod, 1)

def paivita_ennuste():
    print("🚀 Haetaan ennuste FMI:ltä...")
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage&fmisid=100996&parameters=WindSpeedMS,WindDirection"
    
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        
        root = ET.fromstring(r.content)
        
        # JOUSTAVA HAKU: Etsitään elementti, joka loppuu tähän nimeen (ignoraa nimiavaruudet)
        data_node = None
        for elem in root.iter():
            if elem.tag.endswith('doubleOrNilReasonTupleList'):
                data_node = elem
                break
        
        if data_node is None or not data_node.text:
            print("❌ Virhe: Datapistettä 'doubleOrNilReasonTupleList' ei löytynyt XML:stä.")
            return

        values = data_node.text.strip().split('\n')
        print(f"✅ Löydetty {len(values)} ennustetuntia.")
        
        ennusteet = []
        nykyhetki = datetime.now()

        for i, val in enumerate(values):
            parts = val.split()
            if len(parts) < 2: continue
            
            har_ms = float(parts[0])
            har_dir = float(parts[1])
            ennuste_aika = nykyhetki + timedelta(hours=i)
            laru_ms = laske_laru_teho(har_ms, har_dir, ennuste_aika)
            
            ennusteet.append({
                "aika_str": ennuste_aika.strftime("%d.%m. klo %H:%M"),
                "har_ms": har_ms,
                "laru_ms": laru_ms,
                "har_dir": har_dir,
                "laru_gust": round(laru_ms * 1.3, 1)
            })
            
        with open('ennuste.json', 'w') as f:
            json.dump(ennusteet, f, indent=4)
        print(f"💾 Tiedosto ennuste.json päivitetty onnistuneesti!")

    except Exception as e:
        print(f"❌ Virhe prosessoinnissa: {e}")
        sys.exit(1)

if __name__ == "__main__":
    paivita_ennuste()
