"""
Created on Thursday, October 29, 2020

@author: Jeffrey J. Walker

    multi_chain_test.py
        This is a test script for the yahoo_option_chain_multi_exp.py function
		Want to make sure it works properly, including the scraping of bond 
		prices from wsj_bond_scraper.py for zero-coupon yields and adding this
		to the saved dataframe(?)
		A good test would be to plot 3d volatility surfaces and start to 
		think about about Malz and Tiang methods for computing implied prob.

"""

import pandas as pd
import numpy as np
## I wanted to use scipy.interpolate.CubicSpline, but I cannot get it to import
from scipy.interpolate import splev, splrep
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.tz import *
import time
import os
import sys
import json
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from yahoo_option_chain_multi_exp import yahoo_option_chain_multi_exp
## insert the path corresponding to bs_analytical solver; we may need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')

## Want to execute in python shell? then use:
#execfile('/home/jjwalker/Desktop/finance/codes/options/multi_chain_test.py')

#ticker='^XSP'
ticker='^SPX'
#ticker='GME'
## days until expiry
dte=150
## What is the path to the option chain?
## DO NOT NEED '/' AT THE END!
path='/home/jjwalker/Desktop/finance/data/options'
#t_plus_30=pd.to_datetime('today').now()+timedelta(days=dte)
#input_date=time.mktime(t_plus_30.timetuple())

tnow,expiry_dates,spot_price,df_calls,df_puts=yahoo_option_chain_multi_exp(path,ticker)

## time to expiration, from dnow and dexp, in days:
#texp=(pd.Timestamp(dexp).tz_localize('US/Eastern')-pd.Timestamp(dnow)
#		)/np.timedelta64(1,'D')	

## A list/array with all the expiration dates/time to expiration:
exp_dates=df_calls.index.get_level_values(0)
## All possible strikes:
all_strikes=np.unique(df_calls.index.get_level_values(1))
#all_strikes=df_calls.index.levels[1].unique()
## the basic pattern for an expiration, strike:
#df_calls.loc[(exp,strike)]
## get the strike index for a given exp:
#df_calls.loc[exp].index
## get all values of variable for all strikes:
#df_calls[df_calls.index.get_level_values(1)==all_strikes].ask

## how can I fill with nans instead?
test=df_calls.reindex(pd.MultiIndex.from_product(
	[df_calls.index.levels[0],df_calls.index.levels[1].unique()],
	names=['expiration','strike']),fill_value=np.NaN)
	
## a test array:
iv=test.impliedVolatility.values.reshape(len(df_calls.index.levels[0]),
	len(df_calls.index.levels[1]))
## A meshgrid for this:
x,y=np.meshgrid(df_calls.index.levels[1],df_calls.index.levels[0])

##
fig=plt.figure()
ax=plt.axes(projection='3d')
ax.plot_surface(x,y,-iv,cmap='viridis',edgecolor='none');plt.show()
#plt.contour(x,y,iv);plt.show()
