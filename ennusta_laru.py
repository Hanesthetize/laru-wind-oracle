import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# 1. ORAAKKELIN KERTOIMET (Laskettu datasta)
KERTOIMET = {
    0: 0.94,   # N
    45: 0.97,  # NE
    90: 0.50,  # E
    135: 0.66, # SE
    180: 0.58, # S
    225: 0.63, # SW
    270: 0.50, # W
    315: 1.03, # NW
    360: 0.94  # N (toinen pää)
}

def hae_fmi_ennuste():
    print("Haetaan tuorein ennuste Harmajalle...")
    # FMI Ennustemalli (Harmaja FMISID: 100996)
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage&fmisid=100996&parameters=WindSpeedMS,WindDirection"
    
    r = requests.get(url)
    if r.status_code != 200: return None

    root = ET.fromstring(r.content)
    data_text = ""
    for elem in root.iter():
        if 'doubleOrNilReasonTupleList' in elem.tag:
            data_text = elem.text
            break
    
    if not data_text: return None

    lines = data_text.strip().split('\n')
    rows = [line.split() for line in lines]
    
    df = pd.DataFrame(rows, columns=['har_ms', 'har_dir'])
    df['har_ms'] = pd.to_numeric(df['har_ms'])
    df['har_dir'] = pd.to_numeric(df['har_dir'])
    
    # Luodaan aikaleimat (ennuste alkaa tästä hetkestä tunnin välein)
    df['aika'] = pd.date_range(start=datetime.now(), periods=len(df), freq='H')
    return df

def laske_laru_ennuste(df):
    def hae_kerroin(suunta):
        # Etsitään lähin 45 asteen lohko
        lohko = round(suunta / 45) * 45
        if lohko == 360: lohko = 0
        return KERTOIMET.get(lohko, 0.6) # Oletus 0.6 jos ei löydy

    df['kerroin'] = df['har_dir'].apply(hae_kerroin)
    df['laru_ms'] = (df['har_ms'] * df['kerroin']).round(1)
    return df[['aika', 'har_ms', 'har_dir', 'laru_ms']]

# AJETAAN ENNUSTE
ennuste_data = hae_fmi_ennuste()
if ennuste_data is not None:
    lopputulos = laske_laru_ennuste(ennuste_data)
    print("\n--- LÄHIAIJOJEN LARU-ENNUSTE ---")
    # Tulostetaan seuraavat 12 tuntia
    print(lopputulos.head(12).to_string(index=False))
else:
    print("Ennustetta ei saatu haettua.")
