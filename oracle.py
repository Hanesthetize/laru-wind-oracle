import os
import json
import requests
import gspread
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials

def get_fmi():
    try:
        url = "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::observations::weather::latest::multipointcoverage&fmisid=101000&parameters=ws_10min,wg_10min,wd_10min"
        res = requests.get(url, timeout=15)
        # Jos XML-jäsennys sakkaa, haetaan raakatekstistä
        txt = res.text
        if "doubleOrNilReasonTupleList" in txt:
            data_part = txt.split("doubleOrNilReasonTupleList\">")[1].split("</")[0].strip()
            values = data_part.split()
            if len(values) >= 3:
                return values[-3], values[-2], values[-1]
    except Exception as e:
        print(f"FMI error: {e}")
    return "0.1", "0.1", "0.1" # Palautetaan 0.1, jotta nähdään että haku kävi täällä

def get_wg():
    try:
        url = "https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=1336"
        res = requests.get(url, timeout=15)
        d = res.json()
        # Varmistetaan, että arvot eivät ole None
        ws = d.get('wind_avg', '0.2')
        wg = d.get('wind_max', '0.2')
        wd = d.get('wind_direction', '0.2')
        return str(ws), str(wg), str(wd)
    except Exception as e:
        print(f"WG error: {e}")
    return "0.2", "0.2", "0.2"

def main():
    try:
        # Avainten haku
        key_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not key_json:
            print("❌ Virhe: GOOGLE_CREDENTIALS puuttuu")
            return

        # Google Sheets yhteys
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Laru_Tuuli_Data").get_worksheet(0)

        # Datat
        f_ws, f_wg, f_wd = get_fmi()
        w_ws, w_wg, w_wd = get_wg()

        # Tallennus
        now = datetime.now(timezone.utc) + timedelta(hours=2)
        row = [now.strftime("%Y-%m-%d %H:%M"), f_ws, f_wg, f_wd, w_ws, w_wg, w_wd]
        sheet.append_row(row)
        
        print(f"✅ Tallennettu: FMI {f_ws}, WG {w_ws}")
        
    except Exception as e:
        print(f"❌ Kriittinen virhe: {e}")

if __name__ == "__main__":
    main()
