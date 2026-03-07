import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json

# 1. ORAAKKELIN KERTOIMET (Laskettu datasta)
# Nämä ovat ne "pyhät luvut", joita hienosäädämme myöhemmin
KERTOIMET = {
    0: 0.94, 45: 0.97, 90: 0.50, 135: 0.66, 
    180: 0.58, 225: 0.63, 270: 0.50, 315: 1.03
}

def hae_fmi_ennuste():
    # Haetaan Harmajan ennuste (WindSpeedMS, WindDirection, WindGust)
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::harmonie::surface::point::multipointcoverage&fmisid=100996&parameters=WindSpeedMS,WindDirection,WindGust"
    
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        
        data_text = ""
        for elem in root.iter():
            if 'doubleOrNilReasonTupleList' in elem.tag:
                data_text = elem.text
                break
        
        if not data_text: return None

        lines = data_text.strip().split('\n')
        rows = [line.split() for line in lines]
        
        df = pd.DataFrame(rows, columns=['har_ms', 'har_dir', 'har_gust'])
        df = df.apply(pd.to_numeric)
        
        # Luodaan aikaleimat tunnin välein tästä hetkestä
        df['aika'] = pd.date_range(start=datetime.now().replace(minute=0, second=0, microsecond=0), 
                                   periods=len(df), freq='h')
        return df
    except Exception as e:
        print(f"Virhe ennusteen haussa: {e}")
        return None

def laske_laru_ennuste(df):
    def hae_kerroin(suunta):
        lohko = round(suunta / 45) * 45
        if lohko >= 360: lohko = 0
        return KERTOIMET.get(lohko, 0.6)

    df['kerroin'] = df['har_dir'].apply(hae_kerroin)
    
    # Lasketaan Larun keskituuli ja pidetään puuska mukana (tässä voisi olla oma kerroin puuskalle!)
    df['laru_ms'] = (df['har_ms'] * df['kerroin']).round(1)
    df['laru_gust'] = (df['har_gust'] * df['kerroin']).round(1) # Alustava arvio puuskalle
    
    # Muutetaan aika tekstiksi JSONia varten
    df['aika_str'] = df['aika'].dt.strftime('%d.%m. klo %H:%M')
    
    return df

# AJO
df_ennuste = hae_fmi_ennuste()
if df_ennuste is not None:
    ennuste = laske_laru_ennuste(df_ennuste)
    
    # Tallennetaan JSON-tiedostona webbisivua varten
    tulos_json = ennuste[['aika_str', 'har_ms', 'laru_ms', 'har_dir', 'laru_gust']].head(48).to_dict(orient='records')
    
    with open('ennuste.json', 'w') as f:
        json.dump(tulos_json, f, indent=4)
    
    print("Ennuste päivitetty tiedostoon ennuste.json")
    print(ennuste[['aika_str', 'har_ms', 'laru_ms', 'har_dir']].head(10))
