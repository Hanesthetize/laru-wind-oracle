import pandas as pd
import numpy as np

# 1. Ladataan data
df = pd.read_csv('laru_final_10min.csv', names=['aika', 'laru_ms', 'suunta'])
df['aika'] = pd.to_datetime(df['aika'])

# 2. Analysoidaan suhde (tässä vaiheessa simuloidaan Harmaja-vertausta, 
# kunnes saadaan FMI-haku rullaamaan)

print(f"Ladattu {len(df)} mittausta vuodesta {df['aika'].min().year} alkaen.")

# Lasketaan keskiarvot suunnittain
df['suunta_ryhma'] = (df['suunta'] // 20) * 20
yhteenveto = df.groupby('suunta_ryhma')['laru_ms'].mean()

print("\nAlustava katsaus Larun keskituuliin suunnittain (0=Pohjoinen, 180=Etelä):")
print(yhteenveto)
