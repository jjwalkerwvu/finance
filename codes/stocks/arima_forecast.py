"""
Created on Sunday April 5, 2020

@author: Jeffrey J. Walker

    arima_forecast.py
        This script loads a stock, and uses the arima model to make a 
		forecast. Please note, you can not make useful stock price
		predictions with arima, this is for entertainment purposes only!
		And to practice making predictions with arima.
	
"""

import pandas as pd
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import datetime
import os
import sys
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.stattools import adfuller

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Be sure that you use a valid ticker symbol, no indices!
## This will be the stock you are long on.
ticker='^SPX'
## insert the path corresponding to the Yahoo option chain scraper; 
## we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from yahoo_csv_reader import yahoo_csv_reader

## the path:
path='/home/jjwalker/Desktop/finance/data/stocks/'

df=yahoo_csv_reader(path+ticker,ticker)


## ADF test: Null hypothesis is that the time series has unit root
adftest=adfuller(df.Close,autolag='AIC')
dfResults = pd.Series(adftest[0:4], index=['ADF Test Statistic','P-Value','# Lags Used','# Observations Used'])
## critical values come from
#adfResults[4].items()
## p-values from adfResults[1]
## The more negative the test statistic, the more likely we are to reject the
## NULL HYPOTHESIS that there is unit root.
## If the test statistic is less than the critical value, we reject Null
## hypothesis
#adfResults[0]<=adfResults[4].items()

X=df.Close
#X=df.Close.values
size=int(len(X)*0.7)
train,test=X[0:size],X[size:len(X)]
start_index=size
end_index=-1
#history=[x for x in train]

model=ARIMA(train,order=(0,1,0))
model_fit=model.fit()
#model_fit.summary()
forecast=model_fit.predict(start=0,end=100)


