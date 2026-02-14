import os
import json
import requests
import pandas as pd
import gspread
from fmiopendata.wfs import download_stored_query
from datetime import datetime, timedelta, timezone
import numpy as np
from google.oauth2.service_account import Credentials

# 1. TUNNUKSET GITHUB SECRETSISTÄ
# Haetaan JSON-avain, jonka tallensit GitHubin asetuksiin
google_secrets_raw = os.environ.get("GOOGLE_CREDENTIALS")
google_secrets = json.loads(google_secrets_raw)

# Määritellään oikeudet
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(google_secrets, scopes=scopes)
gc = gspread.authorize(creds)

# Avaa Sheet (Varmista, että olet jakanut Sheetin service accountin sähköpostille!)
SHEET_NAME = "Laru_Tuuli_Data"
sh = gc.open(SHEET_NAME).sheet1

def paivita_oraakkeli():
    try:
        # --- 2. HARMAJA (FMI) ---
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        obs = download_stored_query("fmi::observations::weather::multipointcoverage",
                                    args=["place=Harmaja", 
                                          f"starttime={start_time.isoformat(timespec='seconds').replace('+00:00', 'Z')}", 
                                          f"endtime={end_time.isoformat(timespec='seconds').replace('+00:00', 'Z')}"])
        
        h_ws, h_wd = None, None
        times = sorted(obs.data.keys())
        for ts in reversed(times):
            asema = list(obs.data[ts].keys())[0]
            vals = obs.data[ts][asema]
            ws_val = vals.get('Wind speed', {}).get('value')
            wd_val = vals.get('Wind direction', {}).get('value')
            if ws_val is not None and not np.isnan(ws_val):
                h_ws, h_wd = float(ws_val), float(wd_val)
                break

        # --- 3. LARU (WINDGURU) ---
        l_ws, l_wd = None, None
        wg_url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=47"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.windguru.cz/station/47'}
        wg_res = requests.get(wg_url, headers=headers, timeout=10).json()
        if 'wind_avg' in wg_res:
            l_ws = float(wg_res['wind_avg'])
            l_wd = float(wg_res['wind_direction'])

        # --- 4. TALLENNUS ---
        # Suomen aika (UTC+2 talvella)
        now_str = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        uusi_rivi = [now_str, h_ws, h_wd, l_ws, l_wd]
        
        sh.append_row(uusi_rivi)
        print(f"Päivitetty: {uusi_rivi}")

    except Exception as e:
        print(f"Virhe: {e}")

if __name__ == "__main__":
    paivita_oraakkeli()
