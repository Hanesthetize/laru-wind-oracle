import json
import os
import requests
from datetime import datetime

# --- ASETUKSET ---
# Varmista, että coeffs.json on samassa kansiossa kuin tämä skripti
COEFFS_FILE = 'coeffs.json'

def lataa_kertoimet():
    """Lataa dynaamiset kertoimet JSON-tiedostosta."""
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

def hae_kerroin(pvm_obj, suunta):
    """
    Etsii matriisista tarkan kertoimen kuukauden, tunnin ja suunnan perusteella.
    """
    if not COEFFS:
        return 0.55

    kk = str(pvm_obj.month)
    tunti = str(pvm_obj.hour)
    # Ryhmitellään suunta 10 asteen sektoreihin (esim. 227 -> 220)
    sektori = str(int(suunta // 10) * 10)

    try:
        # Haetaan polulla: Kuukausi -> Sektori -> Tunti
        return COEFFS[kk][sektori][tunti]
    except KeyError:
        # Jos tarkkaa osumaa ei löydy (harvinainen suunta/aika), palautetaan turva-arvo
        return 0.55

def laske_ennuste():
    """
    Hakee Harmajan datan (esimerkki API-kutsusta) ja laskee Laru-ennusteen.
    Tämä on runko, jota voit muokata FMI-integraatiosi mukaan.
    """
    # TÄHÄN: FMI API-kutsu tai muu datalähde
    # Esimerkkiarvot (Testi 3: 11.3. klo 13:51, Harmaja 7.79 m/s, suunta 227)
    testi_aika = "2026-03-11T13:51:00Z"
    har_ws = 7.79
    har_gust = 9.5
    har_dir = 227

    # Muunnos datetime-olioksi
    dt = datetime.fromisoformat(testi_aika.replace('Z', '+00:00'))
    
    # Haetaan tarkka kerroin historiasta
    kerroin = hae_kerroin(dt, har_dir)
    
    # Lasketaan Laru-lukemat
    laru_ws = round(har_ws * kerroin, 1)
    laru_gust = round(har_gust * kerroin, 1)

    print("--- LARU ORAAKKELI 2.0 ---")
    print(f"Aika:      {dt.strftime('%d.%m. klo %H:%M')}")
    print(f"Harmaja:   {har_ws} m/s (suunta {har_dir} deg)")
    print(f"Kerroin:   {kerroin} (Matriisipohjainen)")
    print(f"---")
    print(f"📍 LARU ENNUSTE: {laru_ws} m/s")
    print(f"🌪️ PUUSKA:       {laru_gust} m/s")

if __name__ == "__main__":
    laske_ennuste()
