"""
Created on Tuesday March 31 2020

@author: Jeffrey J. Walker

    option_arbitrage_screener.py
        This script looks for arbitrage opportunities in the option chain
		retrieved using the yahoo_option_chain_json.py function.
		At this time, only uses one chain (no calendar spreads) and european
		options! 

"""

import pandas as pd
import numpy as np
#from scipy.interpolate import griddata
from scipy import interpolate
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.tz import *
import time
## import what we need to automatically write output to a folder
import os
import sys
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Be sure that you use a valid ticker symbol!
## Indices have a '^' before their letter symbols!
ticker='^SPX'

## insert the path corresponding to the Yahoo option chain scraper; 
## we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
## insert the path corresponding to bs_analytical solver; we will need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')

from yahoo_option_chain_json import yahoo_option_chain_json
from bs_analytical_solver import bs_analytical_solver

## What is the path to the option chain?
## DO NOT NEED '/' AT THE END!
path='/home/jjwalker/Desktop/finance/data/options'

## Now call the option chain scraper
## call the next calendar month options by default
t_plus_30=pd.to_datetime('today').now()+timedelta(days=30)
input_date=time.mktime(t_plus_30.timetuple())
## Ready to call the option chain scraper/reader
dnow,dexp,St,df_calls,df_puts=yahoo_option_chain_json(path,ticker,input_date)

## time to expiration, from dnow and dexp, in days:
texp=(pd.Timestamp(dexp).tz_localize('US/Eastern')-pd.Timestamp(dnow)
		)/np.timedelta64(1,'D')	

## where to scrape this from?
#y_annual=0.01
## We could assume we are just holding cash, since interest rates are so low
y_annual=0.0
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## find the strikes that calls and puts have in common.
min_common_strike=np.min([np.min(df_calls.strike),np.min(df_puts.strike)])
max_common_strike=np.max([np.max(df_calls.strike),np.max(df_puts.strike)])

## merge on strikes columns? also, there are a lot of columns I do not need

df_join=pd.merge(df_calls,df_puts,how='inner',on='strike',
		left_on=None,right_on=None,
		left_index=False, right_index=False, sort=True,
		suffixes=('_c', '_p'), copy=True, indicator=False)
#df_join=df_join.set_index('strike')

## calls and puts must obey:
## c+K*exp(-rT)=p+S0

## check for buying left side, selling right side.
## In reality you would have to buy the bond as well, which has its own 
## bid/ask...
df_put_sell=df_join[(df_join.ask_c+
	df_join.strike*np.exp(-y_annual*texp/365))<
	(df_join.bid_p+St)]

## difference between left and right sides.
## 
ps_diff=(df_put_sell.bid_p+St-df_put_sell.strike*np.exp(-y_annual*texp/365)-
	df_put_sell.ask_c)

## annualized profit?
ps_profit=ps_diff/(1.0*df_put_sell.ask_c+
	df_put_sell.strike*np.exp(-y_annual*texp/365)-
	1.0*df_put_sell.bid_p-St)

## check for buying right side, selling left side.
## In reality you would have to buy the bond as well, which has its own 
## bid/ask...
df_call_sell=df_join[(df_join.bid_c+
	df_join.strike*np.exp(-y_annual*texp/365))>
	(df_join.ask_p+St)]

## difference between right and left sides
cs_diff=(df_call_sell.bid_c+
	df_call_sell.strike*np.exp(-y_annual*texp/365)-
	df_call_sell.ask_p-St)

