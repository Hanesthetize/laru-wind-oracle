import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def hae_harmaja_fmi(alku, loppu):
    print(f"Haetaan Harmajan dataa: {alku} - {loppu}...")
    # FMI:n rajapinta vaatii aikaleimat ISO-muodossa
    url = f"https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996&starttime={alku}T00:00:00Z&endtime={loppu}T23:50:00Z&parameters=ws_10min,wd_10min"
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"FMI Virhe: {response.status_code}")
        return pd.DataFrame()

    root = ET.fromstring(response.content)
    data_text = ""
    for elem in root.iter('{http://www.opengis.net/gml/3.2}doubleOrNilReasonTupleList'):
        data_text = elem.text
    
    if not data_text:
        return pd.DataFrame()

    lines = data_text.strip().split('\n')
    rows = [line.split() for line in lines]
    
    df_h = pd.DataFrame(rows, columns=['har_ms', 'har_dir'])
    df_h['har_ms'] = pd.to_numeric(df_h['har_ms'], errors='coerce')
    df_h['har_dir'] = pd.to_numeric(df_h['har_dir'], errors='coerce')
    
    # Luodaan aikaleimat (FMI:n vakio 10min väli)
    times = pd.date_range(start=alku, periods=len(df_h), freq='10min')
    df_h['aika'] = times
    return df_h

# 1. Ladataan Laru-data
try:
    df_laru = pd.read_csv('laru_final_10min.csv', names=['aika', 'laru_ms', 'suunta'])
    df_laru['aika'] = pd.to_datetime(df_laru['aika']).dt.tz_localize(None).dt.floor('10min')
    print(f"Laru-dataa ladattu: {len(df_laru)} riviä.")

    # 2. Haetaan Harmaja-data vertailuksi (vuoden 2024 alku testiksi)
    df_harmaja = hae_harmaja_fmi("2024-01-01", "2024-01-14")

    if not df_harmaja.empty:
        # 3. Yhdistetään datat aikaleiman perusteella
        df_combined = pd.merge(df_laru, df_harmaja, on='aika')
        
        # 4. Lasketaan kerroin (Laru / Harmaja)
        # Suodatetaan pois tyynet hetket ja virheelliset arvot
        df_combined = df_combined[(df_combined['har_ms'] > 3) & (df_combined['laru_ms'] > 0)]
        
        if not df_combined.empty:
            df_combined['kerroin'] = df_combined['laru_ms'] / df_combined['har_ms']
            
            # Ryhmitellään ilmansuunnan mukaan (45 asteen lohkot)
            df_combined['suunta_lohko'] = (df_combined['har_dir'] // 45) * 45
            kertoimet = df_combined.groupby('suunta_lohko')['kerroin'].median()

            print("\n=== LOPULLISET KERTOIMET (Laru vs Harmaja) ===")
            suunnat = {0:'N', 45:'NE', 90:'E', 135:'SE', 180:'S', 225:'SW', 270:'W', 315:'NW'}
            for suunta, kerroin in kertoimet.items():
                print(f"{suunnat.get(suunta, '??')} ({int(suunta)}°): {kerroin:.2f}")
        else:
            print("Ei löytynyt yhteisiä aikaleimoja vertailuun.")
    else:
        print("Harmaja-dataa ei saatu haettua.")

except Exception as e:
    print(f"Virhe: {e}")
