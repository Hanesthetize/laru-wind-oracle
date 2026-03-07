import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# --- ANALYYSIIN PERUSTUVAT KERTOIMET (82 999 havainnon data) ---
KK_BASE = {
    1: 0.68, 2: 0.66, 3: 0.57, 4: 0.61, 5: 0.59, 6: 0.63,
    7: 0.63, 8: 0.58, 9: 0.60, 10: 0.65, 11: 0.69, 12: 0.64
}

HOUR_MOD = {
    0: 0.94, 1: 0.90, 2: 0.90, 3: 0.90, 4: 0.90, 5: 0.78,
    6: 0.89, 7: 0.92, 8: 0.94, 9: 0.98, 10: 1.03, 11: 1.13,
    12: 1.14, 13: 1.16, 14: 1.16, 15: 1.19, 16: 1.11, 17: 1.14,
    18: 1.08, 19: 1.03, 20: 1.00, 21: 0.95, 22: 0.92, 23: 0.90
}

def laske_laru_teho(har_ms, suunta, pvm_obj):
    if not (180 <= suunta <= 240):
        return round(har_ms * 0.50, 1)
    base = KK_BASE.get(pvm_obj.month, 0.63)
    mod = HOUR_MOD.get(pvm_obj.hour, 1.0)
    return round(har_ms * base * mod, 1)

def paivita_ennuste():
    print("🚀 Haetaan tuore ennuste FMI:ltä...")
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage&fmisid=100996&parameters=WindSpeedMS,WindDirection"
    
    try:
        r = requests.get(url)
        root = ET.fromstring(r.content)
        
        # Etsitään aikaleimat ja arvot
        namespaces = {'gml': 'http://www.opengis.net/gml/3.2'}
        points_node = root.find('.//gml:doubleOrNilReasonTupleList', namespaces)
        times_node = root.find('.//gml:positions', namespaces)
        
        if points_node is None or times_node is None:
            print("❌ Virhe: FMI-dataa ei voitu lukea.")
            return

        values = points_node.text.strip().split('\n')
        # Aikaleimat ovat muodossa "lat lon epoch", otetaan vain epoch
        times_raw = times_node.text.strip().split('\n')
        
        ennusteet = []
        for i in range(len(values)):
            parts = values[i].split()
            har_ms = float(parts[0])
            har_dir = float(parts[1])
            
            # Lasketaan aika (FMI antaa 1h välein)
            aika = datetime.utcnow() + timedelta(hours=i)
            # Muotoillaan tekstiksi HTML:ää varten
            aika_str = aika.strftime("%d.%m. klo %H:%M")
            
            laru_ms = laske_laru_teho(har_ms, har_dir, aika)
            
            ennusteet.append({
                "aika_str": aika_str,
                "har_ms": har_ms,
                "har_dir": har_dir,
                "laru_ms": laru_ms
            })
            
        # Tallennetaan JSON-tiedostoksi HTML-sivua varten
        with open('ennuste.json', 'w') as f:
            json.dump(ennusteet, f, indent=4)
        
        print(f"✅ Ennuste päivitetty! ({len(ennusteet)} tuntia)")

    except Exception as e:
        print(f"❌ Virhe päivityksessä: {e}")

if __name__ == "__main__":
    paivita_ennuste()
