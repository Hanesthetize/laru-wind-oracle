import requests
from datetime import datetime
import os

# --- ANALYYSIIN PERUSTUVAT KERTOIMET (82 999 havainnon data) ---
# Kuukausikohtainen peruskerroin (Meren lämpötilaefekti)
KK_BASE = {
    1: 0.68, 2: 0.66, 3: 0.57, 4: 0.61, 5: 0.59, 6: 0.63,
    7: 0.63, 8: 0.58, 9: 0.60, 10: 0.65, 11: 0.69, 12: 0.64
}

# Kellonaikakohtainen korjauskerroin (Aurinko/Lämpö-efekti)
# Suhteutettu keskiarvoon 0.63
HOUR_MOD = {
    0: 0.94, 1: 0.90, 2: 0.90, 3: 0.90, 4: 0.90, 5: 0.78,
    6: 0.89, 7: 0.92, 8: 0.94, 9: 0.98, 10: 1.03, 11: 1.13,
    12: 1.14, 13: 1.16, 14: 1.16, 15: 1.19, 16: 1.11, 17: 1.14,
    18: 1.08, 19: 1.03, 20: 1.00, 21: 0.95, 22: 0.92, 23: 0.90
}

def hae_fmi_ennuste():
    # Harmaja FMISID: 100996
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage&fmisid=100996&parameters=WindSpeedMS,WindDirection"
    # Tähän väliin tulisi FMI:n haku ja parsiminen (pidetään rakenteesi samana)
    # ... (oletetaan että funktio palauttaa listan ennusteita) ...
    pass

def laske_laru_teho(har_ms, suunta, pvm_obj):
    """
    Laskee Larun todellisen tuulen perustuen Harmajan ennusteeseen, 
    kellonaikaan ja kuukauteen.
    """
    # 1. Tarkistetaan onko SW (180-240 astetta)
    if not (180 <= suunta <= 240):
        return round(har_ms * 0.50, 1) # Muilla suunnilla Laru on suojassa
    
    # 2. Peruskerroin kuukauden mukaan
    base = KK_BASE.get(pvm_obj.month, 0.63)
    
    # 3. Aikakorjaus tunnin mukaan
    mod = HOUR_MOD.get(pvm_obj.hour, 1.0)
    
    # 4. Lopullinen laskenta
    ennuste = har_ms * base * mod
    
    return round(ennuste, 1)

# --- ESIMERKKI TULOSTUKSESTA SIVULLE ---
print("--- LARUN ORAAKKELI 2.0 TULOKSET ---")
testi_ajat = [
    (10, 210, datetime(2026, 3, 8, 5, 0)),  # Huomenna aamu (Maaliskuu)
    (10, 210, datetime(2026, 3, 8, 15, 0)), # Huomenna iltapäivä (Maaliskuu)
    (10, 210, datetime(2026, 11, 1, 15, 0)) # Marraskuun iltapäivä vertailuksi
]

for ms, suunta, pvm in testi_ajat:
    tulos = laske_laru_teho(ms, suunta, pvm)
    print(f"{pvm.strftime('%d.%m. klo %H:%M')} | Harmaja {ms} m/s SW -> Laru: {tulos} m/s")
