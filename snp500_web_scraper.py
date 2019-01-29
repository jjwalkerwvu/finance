# snp500_web_scraper.py

# this is my attempt at a script to pull s and p 500 FROM THE INTERNET

import pandas as pd

data = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')


table = data[0]
table.head()

sliced_table = table[1:]
header = table.iloc[0]

corrected_table = sliced_table.rename(columns=header)
#corrected_table


