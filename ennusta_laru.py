import pandas as pd
from datetime import datetime

# --- ORAAKKELIN UUDET AIVOT (Dataan perustuvat kertoimet) ---
KK_KERTOIMET = {
    1: 0.68, 2: 0.66, 3: 0.57, 4: 0.61, 5: 0.59, 6: 0.63,
    7: 0.63, 8: 0.58, 9: 0.60, 10: 0.65, 11: 0.69, 12: 0.64
}

TUNTI_KERTOIMET = {
    0: 0.59, 1: 0.57, 2: 0.57, 3: 0.57, 4: 0.57, 5: 0.49,
    6: 0.56, 7: 0.58, 8: 0.59, 9: 0.62, 10: 0.65, 11: 0.71,
    12: 0.72, 13: 0.73, 14: 0.73, 15: 0.75, 16: 0.70, 17: 0.72,
    18: 0.68, 19: 0.65, 20: 0.63, 21: 0.60, 22: 0.58, 23: 0.57
}

def laske_laru_ennuste(har_ms, suunta, aika_str):
    # Muutetaan aika objektiksi
    aika = datetime.strptime(aika_str, "%Y-%m-%d %H:%M")
    
    # Tarkistetaan onko suunta SW (180-240)
    if not (180 <= suunta <= 240):
        return har_ms * 0.50 # Muilla suunnilla Laru on katveessa (vakiokerroin)
    
    # Lasketaan dynaaminen kerroin
    kk_kerroin = KK_KERTOIMET.get(aika.month, 0.63)
    tunti_kerroin = TUNTI_KERTOIMET.get(aika.hour, 0.60)
    
    # Normalisoidaan tunti-kerroin (verrataan sitä keskiarvoon 0.63)
    suhteellinen_teho = tunti_kerroin / 0.63
    
    lopullinen_ennuste = har_ms * kk_kerroin * suhteellinen_teho
    return round(lopullinen_ennuste, 1)

# --- TESTIAJO ---
ennusteet = [
    {"aika": "2026-03-08 05:00", "har": 10, "dir": 210}, # Huomenna aamulla
    {"aika": "2026-03-08 15:00", "har": 10, "dir": 210}  # Huomenna iltapäivällä
]

print("🔍 ENNUSTE-TESTI (SW-tuuli 10 m/s Harmajassa):")
for e in ennusteet:
    tulos = laske_laru_ennuste(e['har'], e['dir'], e['aika'])
    print(f"Klo {e['aika'][-5:]} -> Laru ennuste: {tulos} m/s")
