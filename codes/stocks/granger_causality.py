"""
17 Oct 2020

@author: jeffreywalker

	This script reads in data sets for the fed balance sheet and spx and
	performs the correlation and Granger causality
"""
## import the libraries that you need.
import sys
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt	
## needed for Granger causality test
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.stattools import adfuller
#from statsmodels.tsa.stattools import kpss
## import the csv reader for Yahoo finance data
# insert at 1, 0 is the script path (or '' in REPL)
## import the csv reader for FRED data
sys.path.insert(1, '/Users/jeff/Desktop/finance/codes/data_cleaning')
from yahoo_csv_reader import yahoo_csv_reader
from fred_csv_reader import fred_csv_reader
from yahoo_stock_query import yahoo_stock_query


## path where the various data files are located.
spx_path='/Users/jeff/Desktop/finance/data/stocks/'
fed_path='/Users/jeff/Desktop/finance/data/us_economic_data/'



fed_bs=fred_csv_reader(fed_path+'WALCL')
#spx=yahoo_csv_reader(spx_path+'^GSPC','^GSPC')
spx=yahoo_stock_query('^GSPC')

## Want to execute in python shell? then use:
#execfile('/home/jjwalker/Desktop/finance/codes/stocks/granger_causality.py')

## concatenate the close price for the two (or more) securities and find the correlation.
common_values=pd.concat([fed_bs.WALCL,spx.Close],axis=1)
## get rid of any nans?? Or, resample based on WALCL?
common_values.dropna(inplace=True)
## choose a startdate?
start_date=pd.to_datetime('2009-01-02')
## calculate pearson correlation coefficient, easy peasy:
corr_coef=common_values[common_values.index>start_date].corr(method='pearson')

## BEFORE RUNNING ADF TEST, YOU NEED TO DO KPSS TEST!
## May also be a good idea to take log of quantities before testing for trend
## KPSS test: Null hypothesis is that the time series is stationary around a 
## deterministic trend
## If we reject the null hypothesis, then we can test for unit root

## ADF test: Null hypothesis is that the time series has unit root
adf_test=adfuller(spx.Close,autolag='AIC')
adf_results = pd.Series(adf_test[0:4], index=['ADF Test Statistic','P-Value','# Lags Used','# Observations Used'])
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


#x=[common_values.WALCL.values/np.max(common_values.WALCL),common_values.Close.values/np.max(common_values.Close)]
#x=np.column_stack((common_values.WALCL.values/np.max(common_values.WALCL),
#	common_values.Close.values/np.max(common_values.Close)))
x=np.column_stack((
	np.diff(common_values.WALCL.values)/np.max(
	np.diff(common_values.WALCL.values)),
	np.diff(common_values.Close.values)/np.max(
	np.diff(common_values.Close.values))))

## number of max lags?
nmlags=4

## Null hypothesis of granger causality test is that x[0] DOES NOT granger 
## cause x[1].
## I think this means that small p-values suggest we reject the null hypothesis
gc_res=grangercausalitytests(x,nmlags)
## dictionary keys of the results are just the number of lags, so 1,2,3, etc.

## find lag with highest F-test, then print the following? (restricted model?)
print(gc_res[4][1][0].summary())

## Might also want to go the other way, to make sure that spx does not granger
## cause the fed balance sheet





