import os
import json
import requests
import gspread
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials

def send_tg(msg):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={'chat_id': chat_id, 'text': msg})

def main():
    print("1. Aloitetaan...")
    try:
        # 1. Kirjautuminen
        key_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(json.loads(key_json), scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Laru_Tuuli_Data").get_worksheet(0)
        print("2. Google-yhteys OK")

        # 2. Windguru haku (tämä on yleensä helpoin)
        print("3. Haetaan Windguru...")
        wg_res = requests.get("https://www.windguru.cz/int/iapi.php?q=station_data_current&id_station=1336", timeout=10)
        wg_data = wg_res.json()
        w_ws = str(wg_data.get('wind_avg', 0))
        w_wg = str(wg_data.get('wind_max', 0))
        print(f"4. Windguru OK: {w_ws}")

        # 3. Tallennus (kokeillaan tallentaa pelkkä Windguru ensin, jos FMI mättää)
        now = datetime.now(timezone.utc) + timedelta(hours=2)
        row = [now.strftime("%Y-%m-%d %H:%M"), "N/A", "N/A", "N/A", w_ws, w_wg, "N/A"]
        
        sheet.append_row(row)
        success_msg = f"✅ Laru OK: {w_ws} m/s (Pelkkä Windguru testi)"
        print(success_msg)
        send_tg(success_msg)

    except Exception as e:
        # TÄMÄ on se kohta joka kertoo meille nyt totuuden
        err_type = type(e).__name__
        err_msg = str(e)
        final_err = f"❌ Virhetyyppi: {err_type} | Viesti: {err_msg}"
        print(final_err)
        send_tg(final_err)

if __name__ == "__main__":
    main()
