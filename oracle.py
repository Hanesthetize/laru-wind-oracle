import os
import json
import requests
import gspread
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials

# 1. Telegram-viestit
def send_telegram_message(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={'chat_id': chat_id, 'text': message}, timeout=10)
        except Exception as e:
            print(f"Telegram-virhe: {e}")

# 2. Datan hakufunktiot
def get_fmi_data():
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::latest::multipointcoverage&fmisid=101000&parameters=ws_10min,wg_10min,wd_10min"
    try:
        response = requests.get(url, timeout=15)
        root = ET.fromstring(response.content)
        for element in root.iter('{http://www.opengis.net/gml/3.2}doubleOrNilReasonTupleList'):
            values = element.text.strip().split()
            return values[-3], values[-2], values[-1]
    except:
        return "N/A", "N/A", "N/A"

def get_windguru_data():
    url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=1336"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        return str(data.get('wind_avg', 'N/A')), str(data.get('wind_max', 'N/A')), str(data.get('wind_direction', 'N/A'))
    except:
        return "N/A", "N/A", "N/A"

def main():
    try:
        # 3. Yhteys Sheetiin
        creds_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
        if not creds_json:
            raise ValueError("GCP_SERVICE_ACCOUNT_KEY puuttuu!")

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        with open('temp_creds.json', 'w') as f:
            f.write(creds_json)
        
        creds = Credentials.from_service_account_file('temp_creds.json', scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Laru_Oracle_Data").get_worksheet(0)
        
        # 4. Tuplatarkistus
        all_rows = sheet.get_all_values()
        current_time = datetime.now()
        current_hour_prefix = current_time.strftime("%Y-%m-%d %H")

        if all_rows:
            last_row = all_rows[-1]
            if last_row[0].startswith(current_hour_prefix):
                print(f"Tunti {current_hour_prefix} jo hoidettu. Skipataan.")
                return

        # 5. VARSINAINEN DATAN HAKU
        fmi_ws, fmi_wg, fmi_wd = get_fmi_data()
        wg_ws, wg_wg, wg_wd = get_windguru_data()
        
        row = [
            current_time.strftime("%Y-%m-%d %H:%M"),
            fmi_ws, fmi_wg, fmi_wd,
            wg_ws, wg_wg, wg_wd
        ]
        
        # 6. TALLENNUS
        sheet.append_row(row)
        print(f"✅ Tallennus onnistui: {row}")

    except Exception as e:
        # 7. Virheilmoitus Telegramiin
        error_msg = f"❌ Laru-Oracle VIRHE: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)
    finally:
        if os.path.exists('temp_creds.json'):
            os.remove('temp_creds.json')

if __name__ == "__main__":
    main()
