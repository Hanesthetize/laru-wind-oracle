import os
import json
import requests
import pandas as pd
import gspread
import datetime # Käytetään tätä tuplatarkistukseen
from fmiopendata.wfs import download_stored_query
from datetime import datetime, timedelta, timezone
import numpy as np
from google.oauth2.service_account import Credentials

# 1. UUSI TOIMINTO: Telegram-viestit
def send_telegram_message(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={'chat_id': chat_id, 'text': message}, timeout=10)
        except Exception as e:
            print(f"Telegram-virhe: {e}")

def main():
    try:
        # 2. Yhteys Sheetiin
        creds_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
        if not creds_json:
            raise ValueError("GCP_SERVICE_ACCOUNT_KEY puuttuu!")

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        with open('temp_creds.json', 'w') as f:
            f.write(creds_json)
        
        creds = Credentials.from_service_account_file('temp_creds.json', scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Laru_Oracle_Data").get_worksheet(0)
        
        # 3. UUSI TOIMINTO: Tuplatarkistus
        all_rows = sheet.get_all_values()
        current_time = datetime.now()
        current_hour_prefix = current_time.strftime("%Y-%m-%d %H")

        if all_rows:
            last_row = all_rows[-1]
            if last_row[0].startswith(current_hour_prefix):
                print(f"Tunti {current_hour_prefix} jo hoidettu. Skipataan.")
                return

        # 4. SINUN ALKUPERÄINEN DATAN HAKUSI TÄHÄN
        # (Koska en näe koko fmiopendata-pätkääsi, oletan että se tuottaa 'row' muuttujan)
        # Esimerkki siitä, miten se jatkuu:
        
        # ... (tässä kohtaa koodisi hakee datan fmiopendatalla) ...
        
        # row = [current_time.strftime("%Y-%m-%d %H:%M"), fmi_arvo, wg_arvo]
        # sheet.append_row(row)
        
        print("✅ Tallennus onnistui!")

    except Exception as e:
        # 5. UUSI TOIMINTO: Virheilmoitus Telegramiin
        error_msg = f"❌ Laru-Oracle VIRHE: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)
    finally:
        if os.path.exists('temp_creds.json'):
            os.remove('temp_creds.json')

if __name__ == "__main__":
    main()
