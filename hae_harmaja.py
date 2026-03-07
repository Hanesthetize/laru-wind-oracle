import requests
import pandas as pd
import xml.etree.ElementTree as ET

def lataa_vuosi_harmaja(vuosi):
    print(f"Ladataan Harmajan data vuodelta {vuosi}...")
    # Haetaan dataa 2 viikon pätkissä, koska FMI rajoittaa kertahakua
    pätkät = [("01-01", "01-14"), ("01-15", "01-31")] # Tähän voi lisätä koko vuoden
    kaikki_data = []

    for alku, loppu in pätkät:
        alku_iso = f"{vuosi}-{alku}T00:00:00Z"
        loppu_iso = f"{vuosi}-{loppu}T23:50:00Z"
        url = f"https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996&starttime={alku_iso}&endtime={loppu_iso}&parameters=ws_10min,wd_10min"
        
        r = requests.get(url)
        if r.status_code == 200:
            # Tässä kohtaa parsimme XML:n ja lisäämme listaan
            print(f"Pätkä {alku} - {loppu} ladattu.")
            # (Lisää parsimislogiikka tähän)
    
    # Lopuksi tallennus
    # pd.DataFrame(kaikki_data).to_csv('harmaja_data.csv', index=False)
