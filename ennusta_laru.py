import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sys
import os

# --- ASETUKSET ---
# Varmista, että coeffs.json on samassa kansiossa kuin tämä skripti
COEFFS_FILE = 'coeffs.json'

def lataa_kertoimet():
    """Lataa historialliset kertoimet JSON-tiedostosta."""
    if os.path.exists(COEFFS_FILE):
        try:
            with open(COEFFS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Virhe kertoimien lukemisessa: {e}")
            return None
    else:
        print(f"⚠️ {COEFFS_FILE} ei löytynyt! Käytetään oletuskerrointa 0.55.")
        return None

# Ladataan kertoimet globaaliksi muuttujaksi kerran käynnistyksessä
COEFFS = lataa_kertoimet()

def hae_suomen_aika_offset(pvm_utc):
    """
    Laskee onko annettu UTC-aika Suomen kesä- vai talviajassa.
    Kesäaika alkaa maaliskuun viimeisenä sunnuntaina ja päättyy lokakuun viimeisenä.
    """
    vuosi = pvm_utc.year
    
    # Maaliskuun viimeinen sunnuntai
    maalis_loppu = datetime(vuosi, 3, 31, 1)
    alku = maalis_loppu - timedelta(days=(maalis_loppu.weekday() + 1) % 7)
    
    # Lokakuun viimeinen sunnuntai
    loka_loppu = datetime(vuosi, 10, 31, 1)
    loppu = loka_loppu - timedelta(days=(loka_loppu.weekday() + 1) % 7)
    
    if alku <= pvm_utc < loppu:
        return 3 # Kesäaika (UTC+3)
    else:
        return 2 # Talviaika (UTC+2)

def hae_kerroin(pvm_obj_utc, suunta):
    """
    Etsii matriisista tarkan kertoimen kuukauden, tunnin ja suunnan perusteella.
    Muuntaa UTC-ajan ensin Suomen paikalliseksi ajaksi.
    """
    if not COEFFS:
        return 0.55

    # Korjataan aika Suomen paikalliseksi ajaksi kertoimen hakua varten
    offset = hae_suomen_aika_offset(pvm_obj_utc)
    suomen_aika = pvm_obj_utc + timedelta(hours=offset)
    
    kk = str(suomen_aika.month)
    tunti = str(suomen_aika.hour)
    # Ryhmitellään suunta 10 asteen sektoreihin (esim. 227 -> 220)
    sektori = str(int(suunta // 10) * 10)

    try:
        # Haetaan polulla: Kuukausi -> Sektori -> Tunti
        return COEFFS[kk][sektori][tunti]
    except KeyError:
        # Jos tarkkaa osumaa ei löydy (harvinainen suunta/aika), palautetaan perusarvo
        return 0.55

def paivita_ennuste():
    print("🚀 Käynnistetään Laru Oraakkeli V3.1 (Paikallisaika-korjattu)...")
    
    # Harmajan FMI-tunnus: 100996
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
        
        # FMI:n harmonie-ennuste alkaa yleensä nykyhetkestä (UTC)
        nykyhetki_utc = datetime.utcnow()

        for i, val in enumerate(values):
            parts = val.split()
            if len(parts) < 3: continue 
            
            har_ms = float(parts[0])
            har_dir = float(parts[1])
            har_gust = float(parts[2])
            
            # Ennustehetki UTC-muodossa
            ennuste_aika_utc = nykyhetki_utc + timedelta(hours=i)
            
            # Haetaan dynaaminen kerroin (hoitaa sisäisesti UTC -> FI muunnos)
            kerroin = hae_kerroin(ennuste_aika_utc, har_dir)
            
            # Lasketaan Laru-lukemat
            laru_ms = round(har_ms * kerroin, 1)
            laru_gust = round(har_gust * kerroin, 1)
            
            # Viestiin näkyvä aika Suomen ajassa
            offset = hae_suomen_aika_offset(ennuste_aika_utc)
            naytto_aika = ennuste_aika_utc + timedelta(hours=offset)
            aika_str = naytto_aika.strftime("%d.%m. klo %H:%M")
            
            ennusteet.append({
                "aika_str": aika_str,
                "har_ms": har_ms,
                "laru_ms": laru_ms,
                "har_dir": har_dir,
                "gust_ms": laru_gust,
                "kerroin": kerroin
            })
            
        with open('ennuste.json', 'w') as f:
            json.dump(ennusteet, f, indent=4)
            
        print(f"✅ VALMIS: Päivitetty {len(ennusteet)} tuntia historiallisella matriisilla.")

    except Exception as e:
        print(f"❌ VIRHE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    paivita_ennuste()
