import json
import requests
from datetime import datetime

# 1. LATAA KERTOIMET (varmista että tiedosto on samassa kansiossa)
def lataa_kertoimet():
    try:
        with open('coeffs.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ coeffs.json ei löytynyt, käytetään oletuskertoimia.")
        return None

COEFFS = lataa_kertoimet()

def laske_laru_ennuste(har_ws, har_dir, pvm_str):
    """
    Laskee Laru-ennusteen käyttäen dynaamista matriisia.
    har_ws: Harmajan nopeus (m/s)
    har_dir: Harmajan suunta (deg)
    pvm_str: Ennustehetken aikaleima (ISO-muoto)
    """
    try:
        dt = datetime.fromisoformat(pvm_str.replace('Z', '+00:00'))
        kk = str(dt.month)
        tunti = str(dt.hour)
        # Ryhmitys 10 asteen sektoreihin (esim. 213 -> 210)
        sektori = str(int(har_dir // 10) * 10)

        # Haetaan kerroin matriisista
        if COEFFS and kk in COEFFS and sektori in COEFFS[kk] and tunti in COEFFS[kk][sektori]:
            kerroin = COEFFS[kk][sektori][tunti]
        else:
            # Fallback jos dataa puuttuu juuri tältä tunnilta/suunnalta
            kerroin = 0.55 
            
        return round(har_ws * kerroin, 1)
    except Exception as e:
        print(f"Laskentavirhe: {e}")
        return round(har_ws * 0.55, 1)

# --- INTEGRAATIO ENNUSTELISTAN MUODOSTUKSEEN ---
# Kun looppaat FMI:n ennustedataa läpi:
# for row in fmi_data:
#    ws_har = row['windspeed']
#    dir_har = row['direction']
#    aika = row['time']
#    
#    ws_laru = laske_laru_ennuste(ws_har, dir_har, aika)
#    print(f"Harmaja: {ws_har}m/s -> Laru: {ws_laru}m/s")
