import pandas as pd
import numpy as np

# --- ASETUKSET ---
# Julkaistu Google Sheets CSV-linkki (Harmaja-historia välilehti)
SHEETS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8xHuFTU9k_mF6sDi2F6ElNcvBYzqovZfV2TyzirxlI8wZtc82TXC553WdqmC_Cp5oJ-TJI5fE2JeI/pub?gid=1608576699&single=true&output=csv"

def aja_analyysi():
    # 1. LADATAAN LARU-DATA (GitHubista)
    print("1/3 Ladataan Laru-dataa (377k riviä)...")
    try:
        # Luetaan data, pakotetaan aika-sarake tekstiksi korjausta varten
        df_laru = pd.read_csv('laru_final_10min.csv', names=['aika', 'laru_ms', 'suunta'], dtype={'aika': str})
        
        # KORJAUS: Lisätään puuttuva välilyönti (esim. 2019-01-0100:08 -> 2019-01-01 00:08)
        df_laru['aika'] = df_laru['aika'].str[:10] + " " + df_laru['aika'].str[10:]
        
        # Muunnos ajaksi ja pyöristys 10 minuuttiin
        df_laru['aika'] = pd.to_datetime(df_laru['aika'], errors='coerce')
        df_laru = df_laru.dropna(subset=['aika'])
        df_laru['aika'] = df_laru['aika'].dt.tz_localize(None).dt.floor('10min')
        
        print(f"   -> Laru-data valmis: {len(df_laru)} riviä.")
    except Exception as e:
        print(f"Virhe Laru-datan luvussa: {e}")
        return

    # 2. LADATAAN HARMAJA-DATA (Sheetsistä)
    print("\n2/3 Haetaan Harmaja-dataa Sheetsistä...")
    try:
        # dayfirst=True hoitaa suomalaiset pp.kk.vvvv muodot
        df_har = pd.read_csv(SHEETS_URL)
        
        # Nimetään sarakkeet Sheetsin rakenteen mukaan (Aika, Nopeus, Suunta)
        df_har.columns = ['aika', 'har_ms', 'har_dir'] + list(df_har.columns[3:])
        
        # Puhdistetaan ja muunnetaan aika
        df_har['aika'] = pd.to_datetime(df_har['aika'], dayfirst=True, errors='coerce')
        df_har = df_har.dropna(subset=['aika'])
        df_har['aika'] = df_har['aika'].dt.floor('10min')
        
        # Varmistetaan että numerot ovat numeroita
        df_har['har_ms'] = pd.to_numeric(df_har['har_ms'], errors='coerce')
        df_har['har_dir'] = pd.to_numeric(df_har['har_dir'], errors='coerce')
        
        print(f"   -> Harmaja-data valmis: {len(df_har)} riviä.")
    except Exception as e:
        print(f"Virhe Sheets-datan luvussa: {e}")
        return

    # 3. YHDISTETÄÄN JA LASKETAAN VERTAILU
    print("\n3/3 Lasketaan korrelaatiota...")
    
    # Etsitään ne hetket, jolloin molemmilla on dataa samalle 10min pätkälle
    df_merged = pd.merge(df_laru, df_har, on='aika')
    
    if df_merged.empty:
        print("!!! VIRHE: Aikaleimat eivät kohdanneet.")
        print("Vinkki: Tarkista onko Sheetsissä ja CSV:ssä samat vuodet/päivät.")
        return

    # Suodatetaan pois tyynet (Harmaja > 3 m/s) ja virheelliset nollat
    mask = (df_merged['har_ms'] > 3) & (df_merged['laru_ms'] > 0)
    df_final = df_merged[mask].copy()

    if not df_final.empty:
        # Lasketaan kerroin: Kuinka paljon Larussa on tuulta suhteessa Harmajaan
        df_final['kerroin'] = df_final['laru_ms'] / df_final['har_ms']
        
        # Ryhmitellään 45 asteen lohkoihin Harmajan suunnan mukaan
        df_final['lohko'] = (df_final['har_dir'] // 45) * 45
        
        # Lasketaan mediaanikerroin per suunta (mediaani on vakaampi kuin keskiarvo)
        kertoimet = df_final.groupby('lohko')['kerroin'].median()

        print("\n" + "="*45)
        print("   ORAAKKELIN KERTOIMET (Laru / Harmaja) ")
        print("   (Data perustuu " + str(len(df_final)) + " yhteiseen havaintoon)")
        print("="*45)
        
        suunnat = {0:'N ', 45:'NE', 90:'E ', 135:'SE', 180:'S ', 225:'SW', 270:'W ', 315:'NW'}
        
        for lohko, kerroin in kertoimet.items():
            s_nimi = suunnat.get(int(lohko), '??')
            print(f" {s_nimi} ({str(int(lohko)).zfill(3)}°): {kerroin:.2f}")
        
        print("="*45)
        print("Tulkinta: 1.00 = sama tuuli, 0.50 = Larussa puolet vähemmän.")
    else:
        print("Ei tarpeeksi tuulista dataa (>3m/s) vertailuun.")

if __name__ == "__main__":
    aja_aja_analyysi = aja_analyysi()
