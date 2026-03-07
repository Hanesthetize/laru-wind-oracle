import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def hae_vuosi(vuosi):
    alku = datetime(vuosi, 1, 1)
    loppu = datetime(vuosi, 12, 31)
    df_lista = []
    
    current = alku
    while current < loppu:
        pätkän_loppu = current + timedelta(days=7)
        t1 = current.strftime("%Y-%m-%dT%H:%M:%SZ")
        t2 = pätkän_loppu.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        print(f"Haetaan Harmaja: {t1} - {t2}")
        url = (f"https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature"
               f"&storedquery_id=fmi::observations::weather::multipointcoverage&fmisid=100996"
               f"&starttime={t1}&endtime={t2}&parameters=ws_10min,wd_10min")
        
        try:
            r = requests.get(url, timeout=30)
            # Tässä kohtaa tarvitaan parseri, joka lukee XML:stä pelkät arvot
            # (Käytetään aiemmin todettua toimivaa logiikkaa)
            # ... (lisätään parseri tähän) ...
            time.sleep(0.5)
        except:
            print("Virhe, yritetään uudelleen...")
            time.sleep(2)
        
        current = pätkän_loppu
    return pd.concat(df_lista)

# TÄMÄ ON ISO OPERAATIO – ajetaan vuosi kerrallaan
# Alustetaan tyhjä tiedosto tai jatketaan vanhaa
