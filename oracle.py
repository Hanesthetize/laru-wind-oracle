import os
import json
import requests
import gspread
import numpy as np
from fmiopendata.wfs import download_stored_query
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials

def send_tg(msg):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={'chat_id': chat_id, 'text': msg}, timeout=10)
        except Exception as e:
            print(f"Telegram-virhe: {e}")

def paivita_oraakkeli():
    try:
        # 1. TUNNUKSET
        google_secrets_raw = os.environ.get("GOOGLE_CREDENTIALS")
        if not google_secrets_raw:
            return
            
        google_secrets = json.loads(google_secrets_raw)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(google_secrets, scopes=scopes)
        gc = gspread.authorize(creds)

        # 2. SHEETS
        sh = gc.open("Laru_Tuuli_Data").sheet1

        # 3. HARMAJA (FMI)
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

        # 4. LARU (WINDGURU)
        l_ws, l_wd = None, None
        wg_url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=47"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.windguru.cz/station/47'}
        wg_res = requests.get(wg_url, headers=headers, timeout=10).json()
        if 'wind_avg' in wg_res:
            l_ws = float(wg_res['wind_avg'])
            l_wd = float(wg_res['wind_direction'])

        # 5. TALLENNUS
        now = datetime.now(timezone.utc) + timedelta(hours=2)
        now_str = now.strftime("%Y-%m-%d %H:%M")
        uusi_rivi = [now_str, h_ws, h_wd, l_ws, l_wd]
        
        sh.append_row(uusi_rivi)
        
        # 6. TELEGRAM-VIESTI
        msg = f"✅ Laru Päivitetty {now.strftime('%H:%M')}\nFMI (Harmaja): {h_ws} m/s\nWG (Laru): {l_ws} m/s"
        send_tg(msg)
        print(f"Valmis: {uusi_rivi}")

    except Exception as e:
        err_msg = f"❌ Oraakkeli-virhe: {e}"
        print(err_msg)
        send_tg(err_msg)

if __name__ == "__main__":
    paivita_oraakkeli()
