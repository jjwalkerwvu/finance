"""
Created March 5, 2021

@author: Jeffrey J. Walker

wheat_analysis.py
	load wheat prices (from FRED) and Oceanic Nino Index

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
#import json
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
## insert the path corresponding to bond_price; we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
## import the csv reader for FRED data
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
from shiller_excel_reader import shiller_excel_reader 

## I think I can get sunspot cycle data from here:
sunspot_url='https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json'
sunspot_df = pd.read_json(sunspot_url)
sunspot_df['time-tag'] = pd.to_datetime(sunspot_df['time-tag'],
                                        infer_datetime_format=True)
sunspot_df=sunspot_df.set_index('time-tag')
# the number of sunspots number is sunspot_df.ssn, or better, sunspot_df.smoothed_ssn
# Need to break it into cycles



## import various wheat prices
filename='/Users/jeff/Desktop/finance/data/commodities/WPU0121'
wt=fred_csv_reader(filename)

## Chicago six markets
wholesale_wheat='/Users/jeff/Desktop/finance/data/commodities/M04F1AUS16980M260NNBR'
six_markets=fred_csv_reader(wholesale_wheat)

# Great Britian wheat prices
gb_wheat_url='/Users/jeff/Desktop/finance/data/commodities/M04002GBM523NNBR'
gb_wheat=fred_csv_reader(gb_wheat_url)

# Get inflation data from shiller data
shiller=shiller_excel_reader('/Users/Jeff/Desktop/finance/data/stocks/ie_data.xls')
wheat_cpi=pd.concat([wt.WPU0121,shiller.CPI],axis=1).dropna()
chi_wheat_cpi=pd.concat([six_markets.M04F1AUS16980M260NNBR,shiller.CPI],axis=1).dropna()
gb_wheat_cpi=pd.concat([gb_wheat.M04002GBM523NNBR,shiller.CPI],axis=1).dropna()


oni=pd.read_csv('/home/jjwalker/Desktop/finance/data/commodities/monthly_oni.csv',header=0)
oni['PeriodNum'] = pd.to_datetime(oni.PeriodNum,infer_datetime_format=True)
## This rename is not really needed.
#df=df.rename(columns={'DATE':'date'})
oni=oni.set_index('PeriodNum')
oni=oni[oni.columns].apply(pd.to_numeric,errors='coerce')

# Plot wheat price, adjusted by CPI (Shiller Data)
plt.figure();
plt.plot(50*wheat_cpi.WPU0121/wheat_cpi.CPI,'.',label='CPI Adjusted Wheat Price');
plt.plot(sunspot_df.smoothed_ssn)
# We can also try chi_wheat_cpi
plt.plot(10*chi_wheat_cpi.M04F1AUS16980M260NNBR/chi_wheat_cpi.CPI)


# get cycle start/end dates.

# Here is an imperfect way.
# start_dates=sunspot_df.smoothed_ssn['1867':].resample('11YS').first().index
# end_dates=start_dates[1:]


# better: list start and end dates manually for now.
start_dates=pd.to_datetime(['1855-12',
                            '1867-03',
                            '1878-12',
                            '1890-03',
                            '1902-01',
                            '1913-07',
                            '1923-08',
                            '1933-09',
                            '1944-02',
                            '1954-04',
                            '1964-10',
                            '1976-03',
                            '1986-09',
                            '1996-08',
                            '2008-12',
                            '2019-12'])
# 22 year cycle??
# start_dates=pd.to_datetime(['1855-12',
#                             '1867-03',
#                             '1890-03',
#                             '1902-01',
#                             '1923-08',
#                             '1944-02',
#                             '1964-10',
#                             '1986-09',
#                             '2008-12'])
end_dates=start_dates[1:]

wheat_series=wheat_cpi.WPU0121/wheat_cpi.CPI
chi_wheat_series=chi_wheat_cpi.M04F1AUS16980M260NNBR/chi_wheat_cpi.CPI

plt.figure()
for i in range(len(start_dates)-1):
    # Subtract off the lowest price, to bring the "baseline" down to zero for
    # visibility
    plt.plot(50*wheat_series[start_dates[i]:end_dates[i]].values/
             wheat_series[start_dates[i]:end_dates[i]].min()-50,'y')
    plt.plot(50*chi_wheat_series[start_dates[i]:end_dates[i]].values/
             chi_wheat_series[start_dates[i]:end_dates[i]].min()-50,'r')
    plt.plot(sunspot_df.smoothed_ssn[start_dates[i]:end_dates[i]].values,'k')

