import os
import json
import requests
import gspread
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials

def get_fmi():
    # Tämä on se alkuperäinen haku joka toimi
    url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::latest::multipointcoverage&fmisid=101000&parameters=ws_10min,wg_10min,wd_10min"
    res = requests.get(url)
    root = ET.fromstring(res.content)
    for elem in root.iter():
        if elem.tag.endswith('doubleOrNilReasonTupleList'):
            raw_data = elem.text.strip().split()
            if len(raw_data) >= 3:
                return raw_data[-3], raw_data[-2], raw_data[-1]
    return "0.0", "0.0", "0.0"

def get_wg():
    # Alkuperäinen Windguru-haku
    url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=1336"
    res = requests.get(url)
    d = res.json()
    return str(d.get('wind_avg', 0)), str(d.get('wind_max', 0)), str(d.get('wind_direction', 0))

def main():
    # Haetaan avain GitHub Secretsistä
    key_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
    
    # Tarkistetaan ettei avain ole tyhjä ennen kuin jatketaan
    if not key_json:
        print("❌ Virhe: GCP_SERVICE_ACCOUNT_KEY on tyhjä!")
        return

    # Kirjautuminen
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
    client = gspread.authorize(creds)

    # Avataan se OIKEA tiedosto
    sheet = client.open("Laru_Tuuli_Data").get_worksheet(0)

    # Aika
    now = datetime.now(timezone.utc) + timedelta(hours=2)
    
    # Haetaan datat
    f_ws, f_wg, f_wd = get_fmi()
    w_ws, w_wg, w_wd = get_wg()

    # Rivin lisäys
    row = [now.strftime("%Y-%m-%d %H:%M"), f_ws, f_wg, f_wd, w_ws, w_wg, w_wd]
    sheet.append_row(row)
    
    print(f"✅ Onnistui: {f_ws} m/s")

if __name__ == "__main__":
    main()
