import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sys

# KERTOIMET (Maaliskuu) - Larun teho suhteessa Harmajaan
KK_BASE = {1: 0.68, 2: 0.66, 3: 0.57, 4: 0.61, 5: 0.59, 6: 0.63, 7: 0.63, 8: 0.58, 9: 0.60, 10: 0.65, 11: 0.69, 12: 0.64}

def laske_laru_teho(har_ms, suunta, pvm_obj):
    # Jos tuuli ei ole optimisuunnasta (180-240), vaimennus on rajumpaa
    if not (180 <= suunta <= 240): 
        return round(har_ms * 0.45, 1)
    
    base = KK_BASE.get(pvm_obj.month, 0.63)
    return round(har_ms * base, 1)

def paivita_ennuste():
    print("🚀 Käynnistetään ennusteen päivitys V2.3 (Skaalatut puuskat)...")
    
    # Haetaan Nopeus, Suunta ja Puuska
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage&fmisid=100996&parameters=WindSpeedMS,WindDirection,WindGust"
    
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        
        data_node = next((e for e in root.iter() if e.tag.endswith('doubleOrNilReasonTupleList')), None)
        
        if data_node is None or not data_node.text:
            print("❌ Virhe: Dataa ei löytynyt XML:stä.")
            return

        values = data_node.text.strip().split('\n')
        ennusteet = []
        nykyhetki = datetime.now()

        for i, val in enumerate(values):
            parts = val.split()
            if len(parts) < 3: continue 
            
            har_ms = float(parts[0])
            har_dir = float(parts[1])
            har_gust = float(parts[2])
            
            ennuste_aika = nykyhetki + timedelta(hours=i)
            
            # SKAALAUS: Ajetaan molemmat Laru-kertoimen läpi
            laru_ms = laske_laru_teho(har_ms, har_dir, ennuste_aika)
            laru_gust = laske_laru_teho(har_gust, har_dir, ennuste_aika)
            
            ennuste_aika_str = ennuste_aika.strftime("%d.%m. klo %H:%M")
            
            ennusteet.append({
                "aika_str": ennuste_aika_str,
                "har_ms": har_ms,
                "laru_ms": laru_ms,
                "har_dir": har_dir,
                "gust_ms": laru_gust # Skaalattu puuska
            })
            
        with open('ennuste.json', 'w') as f:
            json.dump(ennusteet, f, indent=4)
            
        print(f"✅ VALMIS: Päivitetty {len(ennusteet)} tuntia skaalatuilla puuskilla.")

    except Exception as e:
        print(f"❌ VIRHE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    paivita_ennuste()
