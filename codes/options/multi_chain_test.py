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

## For now, convert utc timestamp to datetime; put into yahoo_option_chain_multi_exp.py later
dexp=(pd.DatetimeIndex([
	datetime.utcfromtimestamp(date) for date in expiry_dates]))
## texp, in days, float array?
texp=np.array((dexp.tz_localize('US/Eastern')-tnow)/np.timedelta64(1,'D'))

## time to expiration, from dnow and dexp, in days:
#texp=(pd.Timestamp(dexp).tz_localize('US/Eastern')-pd.Timestamp(dnow)
#		)/np.timedelta64(1,'D')	

## A list/array with all the expiration dates/time to expiration:
exp_dates=np.array(df_calls.index.levels[0])
## All possible strikes:
all_strikes=np.unique(df_calls.index.get_level_values(1))
#all_strikes=df_calls.index.levels[1].unique()
## the basic pattern for an expiration, strike:
#df_calls.loc[(exp,strike)]
## get the strike index for a given exp:
#df_calls.loc[exp].index
## get all values of variable for all strikes:
#df_calls[df_calls.index.get_level_values(1)==all_strikes].ask


## Dataframe entries should be "cleaned" with the following conditions:
## (As previously used (successfully?) in my simpler script 'iv_snapshot.py')
## IV constrainted to be >=0 and no Nans
## Volume: no Nans
## Bid and ask are not equal to zero
## how can I fill with nans instead?
test=df_calls.reindex(pd.MultiIndex.from_product(
	[df_calls.index.levels[0],df_calls.index.levels[1].unique()],
	names=['expiration','strike']),fill_value=np.NaN)

## some test arrays:
volume=test.volume.values.reshape(len(df_calls.index.levels[0]),
	len(df_calls.index.levels[1]))
iv=test.impliedVolatility.values.reshape(len(df_calls.index.levels[0]),
	len(df_calls.index.levels[1]))
ask=test.ask.values.reshape(len(df_calls.index.levels[0]),
	len(df_calls.index.levels[1]))
bid=test.bid.values.reshape(len(df_calls.index.levels[0]),
	len(df_calls.index.levels[1]))
## A meshgrid to make 3d plots?
x,y=np.meshgrid(df_calls.index.levels[1],texp)

## How can I make a 2d array using this logic?
## Should I use np.ma.where instead?
## IV cannot be zero.
## Also, we should ensure that the ask/bid price of options has a non-zero
## intrinsic value for (S-k)>0. Otherwise arbitrage is possible.
## How to implement this? Something like:
#ask<np.max(spot_price-all_strikes,0)
#bid<np.max(spot_price-all_strikes,0)
## I was also considering enforcing some kind of monotonicy for ask/bid data
clean_conditions=(np.isnan(volume))|(iv<=0)|(ask<=0)|(bid<=0)
## better attempt with where and making masked array??
#iv_clean=iv[np.ma.masked_where(~np.isnan(volume),volume)].reshape(len(df_calls.index.levels[0]),
#	len(df_calls.index.levels[1]))

## clean all the relevant arrays according to our conditions
ask_clean=np.ma.masked_invalid(np.ma.masked_where(clean_conditions,ask))
bid_clean=np.ma.masked_invalid(np.ma.masked_where(clean_conditions,bid))
iv_clean=np.ma.masked_invalid(np.ma.masked_where(clean_conditions,iv))
xclean=np.ma.masked_invalid(np.ma.masked_where(clean_conditions,x))
yclean=np.ma.masked_invalid(np.ma.masked_where(clean_conditions,y))

##
#fig=plt.figure()
#ax=plt.axes(projection='3d')
#ax.plot_surface(xclean,yclean,iv_clean,cmap='viridis',edgecolor='none');plt.show()
#plt.contour(x,y,iv);plt.show()

## test attempt at a spline interpolation:
spl=splrep(all_strikes[~np.isnan(iv[0,:])],iv[0,:][~np.isnan(iv[0,:])],k=3,
	xb=iv[0,:][~np.isnan(iv[0,:])][0])
yspl=splev(all_strikes,spl)
## two derivatives
#ddy=splev(all_strikes,spl,der=2)
#plt.plot(all_strikes,iv[0,:],'o',all_strikes,yspl);plt.show()

## Maybe a simpler plot to use in the meantime until I get surfaces working?
## color array (try cool and hot colormap?)
#c=np.tile(texp)
plt.scatter(xclean.flatten(),ask_clean.flatten(),
	c=np.log10(yclean.flatten()-np.min(yclean.flatten())),
	cmap=cool,edgecolor='none')
plt.yscale('log')
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.ylabel('Ask Price')
plt.xlabel('Strike')

