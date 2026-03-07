import requests
import pandas as pd
import xml.etree.ElementTree as ET

def hae_ja_tallenna(alku, loppu, tiedosto):
    print(f"Haetaan Harmaja: {alku} - {loppu}...")
    url = (
        "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0"
        "&request=getFeature"
        "&storedquery_id=fmi::observations::weather::multipointcoverage"
        "&fmisid=100996"
        f"&starttime={alku}T00:00:00Z"
        f"&endtime={loppu}T23:50:00Z"
        "&parameters=ws_10min,wd_10min"
    )
    
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Virhe: {r.status_code}")
        return

    root = ET.fromstring(r.content)
    data_text = ""
    # Etsitään FMI:n XML-rakenteesta ne varsinaiset numerot
    for elem in root.iter('{http://www.opengis.net/gml/3.2}doubleOrNilReasonTupleList'):
        data_text = elem.text
    
    if data_text:
        lines = data_text.strip().split('\n')
        rows = [line.split() for line in lines]
        df = pd.DataFrame(rows, columns=['har_ms', 'har_dir'])
        
        # Luodaan aikaleimat (tammikuun 2024 alku on 4464 kpl 10min pätkiä koko kuukaudelle)
        # Käytetään dynaamista pituutta, ettei tule virhettä
        df['aika'] = pd.date_range(start=alku, periods=len(df), freq='10min')
        
        df.to_csv(tiedosto, index=False)
        print(f"Tallennettu: {tiedosto} ({len(df)} riviä)")
    else:
        print("Dataa ei löytynyt XML-vastauksesta.")

# Haetaan tammikuu 2024 testiksi
hae_ja_tallenna("2024-01-01", "2024-01-31", "harmaja_history.csv")
