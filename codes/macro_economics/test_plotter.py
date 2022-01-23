"""
March 3, 2020

Short script to plot US public debt to gdp ratio

test_plotter.py
"""

import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt

## path for the recession dates?
path_economics='/home/jjwalker/Desktop/finance/data/us_economic_data/'
file1='GDP'
file2='nonfinancial_corporate_business_debt_securities_and_loans'

## gdp is given in billions
gdp=pd.read_csv(path_economics+file1+'.csv',header=0)
gdp['DATE'] = pd.to_datetime(gdp.DATE,infer_datetime_format=True)
gdp=gdp.set_index('DATE')
## and also, the column is read in as a string, so turn into numerical value
gdp[gdp.columns[0]]=pd.to_numeric(gdp[gdp.columns[0]])*1e9

## corporate debt is given in billions
corp_debt=pd.read_csv(path_economics+file2+'.csv',header=0)
corp_debt['DATE'] = pd.to_datetime(corp_debt.DATE,infer_datetime_format=True)
corp_debt=corp_debt.set_index('DATE')
corp_debt=corp_debt.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
corp_debt[corp_debt.columns[0]]=pd.to_numeric(corp_debt[corp_debt.columns[0]])*1e9

## Should input the csv with the recession dates?
## The dataframe that contains the dates for recessions
recessions=pd.read_csv(path_economics+'fred_recession_dates.csv',header=0)
recessions['DATE'] = pd.to_datetime(recessions.DATE,infer_datetime_format=True)
## rename the first column
recessions=recessions.set_index('DATE')
recessions=recessions.rename(columns={recessions.columns[0]:"recession"})

plt.figure()
title='US Corporate Debt to GDP Ratio'
plt.title(title)
plt.plot(corp_debt[corp_debt.columns[0]]/gdp[gdp.columns[0]],'.k',label='US Corp Debt/GDP')
## Make gray shaded regions for the recession periods
## confine ourselves to the 0-100% range?
#plt.ylim([0,1])
plt.legend(loc='best')
plt.ylabel('%')
plt.xlabel('Date')
plt.tight_layout()
#plt.savefig('test.png')


