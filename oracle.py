import os
import json
import requests
import gspread
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials

def send_tg(msg):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          json={'chat_id': chat_id, 'text': msg}, timeout=10)
        except:
            print("Telegram fail")

def get_fmi():
    try:
        url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::latest::multipointcoverage&fmisid=101000&parameters=ws_10min,wg_10min,wd_10min"
        res = requests.get(url, timeout=15)
        # Käytetään contentia (bytes), se on XML-parserille varmempi
        root = ET.fromstring(res.content)
        for elem in root.iter():
            if elem.tag.endswith('doubleOrNilReasonTupleList'):
                # Tämä oli se logiikka joka toimi kerran!
                raw_data = elem.text.strip().split()
                if len(raw_data) >= 3:
                    return str(raw_data[-3]), str(raw_data[-2]), str(raw_data[-1])
    except Exception as e:
        print(f"FMI virhe: {e}")
    return "0.0", "0.0", "0.0"

def get_wg():
    try:
        url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=1336"
        res = requests.get(url, timeout=15)
        d = res.json()
        # Varmistetaan että otetaan oikeat kentät
        return str(d.get('wind_avg', 0)), str(d.get('wind_max', 0)), str(d.get('wind_direction', 0))
    except Exception as e:
        print(f"WG virhe: {e}")
    return "0.0", "0.0", "0.0"

def main():
    try:
        # Kirjautuminen
        key_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
        client = gspread.authorize(creds)
        
        # TIEDOSTON NIMI (Tämä oli se kivi kengässä)
        sheet = client.open("Laru_Tuuli_Data").get_worksheet(0)
        
        # Aika (Suomen aika UTC+2)
        now = datetime.now(timezone.utc) + timedelta(hours=2)
        
        # Haetaan data
        f_ws, f_wg, f_wd = get_fmi()
        w_ws, w_wg, w_wd = get_wg()
        
        # Rivin koostumus
        row = [now.strftime("%Y-%m-%d %H:%M"), f_ws, f_wg, f_wd, w_ws, w_wg, w_wd]
        
        # Tallennus
        sheet.append_row(row)
        
        # Telegram-viesti
        msg = f"✅ Laru: {now.strftime('%H:%M')}\nFMI: {f_ws} m/s\nWG: {w_ws} m/s"
        send_tg(msg)
        print("Valmis!")

    except Exception as e:
        err_msg = f"❌ Virhe: {str(e)}"
        print(err_msg)
        send_tg(err_msg)

if __name__ == "__main__":
    main()
