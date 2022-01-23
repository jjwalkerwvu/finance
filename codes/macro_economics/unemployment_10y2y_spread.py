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
#import scipy as sp
import matplotlib.pyplot as plt
import sys
import datetime
## stuff for granger causality
from statsmodels.tsa.stattools import kpss
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.filters.hp_filter import hpfilter
sys.path.insert(1, '/Users/jeff/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader

## Unrate data
unrate=fred_csv_reader('/Users/jeff/Desktop/finance/data/us_economic_data/fred_unemployment')
## calculate trend unemployment using a Hodrick-Prescott filter
unrate_cycle,unrate_trend=hpfilter(x=unrate.values,lamb=1e5)
unrate_cycle_series=pd.Series(data=unrate_cycle,index=unrate.index)

## African american unemployment
aa_unrate=fred_csv_reader('/Users/jeff/Desktop/finance/data/us_economic_data/african_american_unemployment')

## Just putting here for now; long run data for bonds (since 1871)
## Maybe use if you want an even longer comparison between 10y-2y spread to
## unemployment
bond_history=pd.read_csv('/Users/jeff/Desktop/finance/data/us_economic_data/constant-maturity-treasu.csv')
bond_history['DateTime']=pd.to_datetime(bond_history['DateTime'],infer_datetime_format=True)
bond_history.set_index('DateTime',inplace=True)
long10y2y_spread=bond_history['US10Y Yield']-bond_history['US02Y Yield']

## Zero coupon yield curve from FRED:
## read in data; have to use (7)th line as the header, I don't know why
## Zero coupon bond data should be good enough, and easier to get.
## Also, this gives more data than FRED 10y 2y spread
url='https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv';
zc=pd.read_csv(url,sep=',',header=7)
zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
zc.set_index('Date',inplace=True)

# Could also use gs10 an gs1 data; these go back to 1953.
gs1=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS1')
gs10=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS10')

df_cmts=pd.concat([gs1.GS1-gs10.GS10,unrate.UNRATE],axis=1)




## Try a simple correlation first.
## concat both dataframes.
# df_concat=pd.concat([zc.SVENY10-zc.SVENY02,unrate.UNRATE,
#                      aa_unrate[aa_unrate.columns[0]]],axis=1)
df_concat=pd.concat([long10y2y_spread,unrate.UNRATE],axis=1)
df_concat.rename(columns={df_concat.columns[0]:'yield_spread',
                          "UNRATE":"unrate",
                          aa_unrate.columns[0]:"aa_unrate"},inplace=True)
## scheme to make sure the yield spread has no Nans?
#df_concat.yield_spread=df_concat.yield_spread.fillna(method='ffill')
df_concat.dropna(inplace=True)
## choose a startdate?
#start_date=pd.to_datetime('1985')
#start_date=pd.to_datetime('1971')
## 1952 is definitely after yield curve control
start_date=pd.to_datetime('1952')

corr_coef=df_concat[df_concat.index>start_date].corr(method='pearson')
print(corr_coef)

## cross correlation would also be good to look at
# xcorr=np.correlate(df_concat.yield_spread[df_concat.index>start_date].values-
#         np.mean(df_concat[df_concat.index>start_date].yield_spread.values),
#         df_concat[df_concat.index>start_date].unrate.values-
#         np.mean(df_concat[df_concat.index>start_date].unrate.values),'full')

## for some reason, matplotlib works the way I want?
## use a start date
plt.figure()
plt.xcorr(df_concat.yield_spread[df_concat.index>start_date].values-
        np.mean(df_concat[df_concat.index>start_date].yield_spread.values),
        df_concat[df_concat.index>start_date].unrate.values-
        np.mean(df_concat[df_concat.index>start_date].unrate.values),
        maxlags=250)
plt.title('Cross Correlation between Yield Spread And Unemployment Rate')
plt.xlabel('Lags (Months)')
plt.show()
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Cyclically averaged unemployment
## This is an attempt to "detrend" unemployment cycles, or "collapse" them into
## a form of normalized unemployment.
## The 10y-2y yield spread, by its nature, cannot vary as greatly, so this is
## an attempt to see if there is a closer correlation this way.

## So what is the idea? maybe detrend according to trough to trough in 
## unemployment

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Granger Causality tests here
## ADF test: Null hypothesis is that the time series has unit root
adf_test=adfuller(unrate.UNRATE,autolag='AIC')
adf_results = pd.Series(adf_test[0:4], index=['ADF Test Statistic','P-Value',
                                        '# Lags Used','# Observations Used'])
## critical values come from
#adf_test[4].items()
## p-values from adfResults[1]
## The more negative the test statistic, the more likely we are to reject the
## NULL HYPOTHESIS that there is unit root.
## Also, a high p-value suggests unit root
## If the test statistic is less than the critical value, we reject Null
## hypothesis
#adfResults[0]<=adfResults[4].items()
## If you have unit root, need to difference the time series??
## Go to within 1%?


## Website which may help
#https://towardsdatascience.com/granger-causality-and-vector-auto-regressive-model-for-time-series-forecasting-3226a64889a6
## If there is no unit root, we can perform the Granger Causality Test
## Testing whether yield spread Granger causes unemployment rate
x=np.column_stack((np.diff(df_concat.yield_spread.values),
	np.diff(df_concat.unrate.values)))

## number of max lags?
nmlags=4

## Null hypothesis of granger causality test is that x[0] DOES NOT granger 
## cause x[1].
## I think this means that small p-values suggest we reject the null 
## hypothesis;
## What is the critical value?
gc_res=grangercausalitytests(x,nmlags)
## dictionary keys of the results are just the number of lags, so 1,2,3, etc.

## find lag with highest F-test, then print the following? (restricted model?)
print(gc_res[4][1][0].summary())

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Quick plot
plt.plot(unrate,'.',label='Unrate')
plt.plot(aa_unrate,'.',label='AA Unrate')
#plt.plot(zc.SVENY10-zc.SVENY02,'.',label='10y - 2y Note yield')
plt.plot(long10y2y_spread,'.',label='Long 10y - 2y Note yield')
plt.plot(long10y2y_spread.dropna()*0,'k')
plt.title('Unemployment And Term Structure')
plt.xlabel('Date')
plt.ylabel('Yield (%)')
plt.legend(loc='best')
plt.show()






