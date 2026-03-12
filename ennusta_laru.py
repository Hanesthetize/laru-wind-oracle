import json
import os
import requests
from datetime import datetime, timedelta

# --- ASETUKSET ---
COEFFS_FILE = 'coeffs.json'

def lataa_kertoimet():
    if os.path.exists(COEFFS_FILE):
        try:
            with open(COEFFS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Virhe kertoimien lukemisessa: {e}")
            return None
    return None

COEFFS = lataa_kertoimet()

def hae_kerroin(pvm_obj_utc, suunta):
    """
    Muuttaa UTC-ajan Suomen ajaksi (+2h tai +3h) ja hakee kertoimen.
    """
    if not COEFFS:
        return 0.55

    # MUUTOS TÄSSÄ: FMI:n ennusteet ovat UTC-aikaa. 
    # Lisätään 2 tuntia (talviaika), jotta se vastaa coeffs.json -tiedoston tunteja.
    # (Huom: Jos haluat täydellisen, käytä pytz-kirjastoa kesä/talviaikaan)
    suomen_aika = pvm_obj_utc + timedelta(hours=2)
    
    kk = str(suomen_aika.month)
    tunti = str(suomen_aika.hour)
    sektori = str(int(suunta // 10) * 10)

    try:
        return COEFFS[kk][sektori][tunti]
    except KeyError:
        return 0.55

def laske_ennuste():
    # Testi-aika (FMI:n formaatissa UTC-aikaa)
    testi_aika = "2026-03-11T13:51:00Z" 
    har_ws = 7.79
    har_gust = 9.5
    har_dir = 227

    dt_utc = datetime.fromisoformat(testi_aika.replace('Z', '+00:00'))
    
    # Haetaan kerroin (koodi hoitaa UTC -> Suomi muunnoksen)
    kerroin = hae_kerroin(dt_utc, har_dir)
    
    laru_ws = round(har_ws * kerroin, 1)
    laru_gust = round(har_gust * kerroin, 1)

    print("--- LARU ORAAKKELI 2.1 (Paikallisaika-korjattu) ---")
    print(f"Ennuste (UTC):  {dt_utc.strftime('%H:%M')}")
    print(f"Hakuperuste (FI): {(dt_utc + timedelta(hours=2)).hour}:00")
    print(f"Harmaja:        {har_ws} m/s")
    print(f"Kerroin:        {kerroin}")
    print(f"---")
    print(f"📍 LARU ENNUSTE: {laru_ws} m/s")
    print(f"🌪️ PUUSKA:       {laru_gust} m/s")

if __name__ == "__main__":
    laske_ennuste()
