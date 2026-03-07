import pandas as pd
import requests
from datetime import datetime

# 1. Ladataan Laru-data
df_laru = pd.read_csv('laru_final_10min.csv', names=['aika', 'laru_ms', 'suunta'])
df_laru['aika'] = pd.to_datetime(df_laru['aika']).dt.floor('10min')

# 2. Haetaan Harmaja-data (esimerkki yhdelle kuukaudelle testiksi)
# Oikeassa ajossa haetaan pidempi pätkä
def hae_fmi_data(alku, loppu):
    url = f"https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996&starttime={alku}&endtime={loppu}&parameters=ws_10min,wd_10min"
    # Tähän tulee XML-parsiminen, mutta pidetään logiikka tässä:
    print(f"Hetaan Harmajan dataa väliltä {alku} - {loppu}...")
    return pd.DataFrame() # Palauttaa vertailudatan

print("Analysoidaan korrelaatiota...")
# Tässä kohtaa skripti vertaa laru_ms vs harmaja_ms eri suunnilla
