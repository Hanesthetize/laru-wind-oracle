import os
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
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::latest::multipointcoverage&fmisid=101000&parameters=ws_10min,wg_10min,wd_10min"
    res = requests.get(url, timeout=15)
    # TÄSSÄ OLI VIRHE: Jos palautettiin res eikä res.text, tuli se <Response [200]>
    root = ET.fromstring(res.text)
    for elem in root.iter():
        if elem.tag.endswith('doubleOrNilReasonTupleList'):
            raw_data = elem.text.strip().split()
            if len(raw_data) >= 3:
                return raw_data[-3], raw_data[-2], raw_data[-1]
    return "0.0", "0.0", "0.0"

def get_wg():
    url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=1336"
    res = requests.get(url, timeout=15)
    d = res.json()
    return str(d.get('wind_avg', 0)), str(d.get('wind_max', 0)), str(d.get('wind_direction', 0))

def main():
    print("Aloitetaan...")
    try:
        # 1. Creds
        key_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
        if not key_json:
            raise Exception("Key missing")
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
        client = gspread.authorize(creds)
        
        # 2. Sheet
        sheet = client.open("Laru_Oracle_Data").get_worksheet(0)
        
        # 3. Time & Dupe check
        now = datetime.now(timezone.utc) + timedelta(hours=2)
        hour_tag = now.strftime("%Y-%m-%d %H")
        
        last_val = sheet.col_values(1)[-1] if sheet.col_values(1) else ""
        if last_val.startswith(hour_tag):
            print(f"Tunti {hour_tag} jo tehty.")
            return

        # 4. Data
        f_ws, f_wg, f_wd = get_fmi()
        w_ws, w_wg, w_wd = get_wg()
        
        row = [now.strftime("%Y-%m-%d %H:%M"), f_ws, f_wg, f_wd, w_ws, w_wg, w_wd]
        
        # 5. Save
        sheet.append_row(row)
        msg = f"✅ Laru: {now.strftime('%H:%M')} | FMI: {f_ws}m/s | WG: {w_ws}m/s"
        print(msg)
        send_tg(msg)

    except Exception as e:
        err = f"❌ Virhe: {str(e)}"
        print(err)
        send_tg(err)

if __name__ == "__main__":
    main()
