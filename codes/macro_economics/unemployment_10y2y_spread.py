#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 21:46:25 2021

@author: jeff

    unemployment_10y2y_spread.py
        A quick script to look at unemployment and the 10y 2y spread
    
    
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime
sys.path.insert(1, '/Users/jeff/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader

## Unrate data
unrate=fred_csv_reader('/Users/jeff/Desktop/finance/data/us_economic_data/fred_unemployment')

## Zero coupon yield curve from FRED:
## read in data; have to use (7)th line as the header, I don't know why
## Zero coupon bond data should be good enough, and easier to get.
## Also, this gives more data than FRED 10y 2y spread
url='https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv';
zc=pd.read_csv(url,sep=',',header=7)
zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
zc.set_index('Date',inplace=True)


## Try a simple correlation first.
## concat both dataframes.
df_concat=pd.concat([zc.SVENY10-zc.SVENY02,unrate.UNRATE],axis=1)
df_concat.rename(columns={df_concat.columns[0]:'yield_spread',"UNRATE":"unrate"},inplace=True)
## scheme to make sure the yield spread has no Nans?
df_concat.yield_spread=df_concat.yield_spread.fillna(method='ffill')
## choose a startdate?
start_date=pd.to_datetime('1985')
corr_coef=df_concat[df_concat.index>start_date].corr(method='pearson')
print(corr_coef)