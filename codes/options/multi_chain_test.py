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

#tnow,expiry_dates,spot_price,df=yahoo_option_chain_multi_exp(path,ticker)

## recalculate tnow if necessary:
timezone='CET'
tnow=pd.to_datetime('today').now().tz_localize(timezone).tz_convert('US/Eastern')
## For now, convert utc timestamp to datetime; put into yahoo_option_chain_multi_exp.py later
#dexp=(pd.DatetimeIndex([
#	datetime.utcfromtimestamp(date) for date in df.index.levels[0]]))
#exp_dates=np.array(df_calls.index.levels[0])
dexp=np.array(df.index.levels[0])
## texp, in days, float array?
texp=np.array((df.index.levels[0].tz_localize('US/Eastern')-tnow)/np.timedelta64(1,'D'))

## time to expiration, from dnow and dexp, in days:
#texp=(pd.Timestamp(dexp).tz_localize('US/Eastern')-pd.Timestamp(dnow)
#		)/np.timedelta64(1,'D')	

## A list/array with all the expiration dates/time to expiration:
## All possible strikes:
#all_strikes=np.unique(df.index.get_level_values(1))
all_strikes=df.index.levels[1].unique()
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
#test=df_calls.reindex(pd.MultiIndex.from_product(
#	[df_calls.index.levels[0],df_calls.index.levels[1].unique()],
#	names=['expiration','strike']),fill_value=np.NaN)

## some test arrays:
volume_c=df.volume_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
volume_p=df.volume_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
iv_c=df.impliedVolatility_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
iv_p=df.impliedVolatility_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
ask_c=df.ask_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
ask_p=df.ask_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
bid_c=df.bid_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
bid_p=df.bid_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
## A meshgrid to make 3d plots?
x,y=np.meshgrid(df.index.levels[1],texp)

## How can I make a 2d array using this logic?
## Should I use np.ma.where instead?
## IV cannot be zero.
## Also, we should ensure that the ask/bid price of options has a non-zero
## intrinsic value for (S-k)>0. Otherwise arbitrage is possible.
## How to implement this? Something like:
#ask<np.max(spot_price-all_strikes,0)
#bid<np.max(spot_price-all_strikes,0)
## I was also considering enforcing some kind of monotonicy for ask/bid data
clean_conditions_c=(np.isnan(volume_c))|(iv_c<=0)|(ask_c<=0)|(bid_c<=0)
clean_conditions_p=(np.isnan(volume_p))|(iv_p<=0)|(ask_p<=0)|(bid_p<=0)
## better attempt with where and making masked array??
#iv_clean=iv[np.ma.masked_where(~np.isnan(volume),volume)].reshape(len(df_calls.index.levels[0]),
#	len(df_calls.index.levels[1]))

## clean all the relevant arrays according to our conditions
ask_clean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,ask_c))
bid_clean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,bid_c))
iv_clean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,iv_c))
xclean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,x))
yclean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,y))
##
ask_clean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,ask_p))
bid_clean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,bid_p))
iv_clean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,iv_p))
xclean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,x))
yclean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,y))

##
#fig=plt.figure()
#ax=plt.axes(projection='3d')
#ax.plot_surface(xclean,yclean,iv_clean,cmap='viridis',edgecolor='none');plt.show()
#plt.contour(x,y,iv);plt.show()

## test attempt at a spline interpolation:
#spl=splrep(all_strikes[~np.isnan(iv[0,:])],iv[0,:][~np.isnan(iv[0,:])],k=3,
#	xb=iv[0,:][~np.isnan(iv[0,:])][0])
#yspl=splev(all_strikes,spl)
## two derivatives
#ddy=splev(all_strikes,spl,der=2)
#plt.plot(all_strikes,iv[0,:],'o',all_strikes,yspl);plt.show()

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Maybe a simpler plot to use in the meantime until I get surfaces working?
## color array (try cool and hot colormap?)
#c=np.tile(texp)
plt.figure()
plt.subplot(1,2,1)
plt.title(ticker+' Calls')
plt.scatter(xclean_c.flatten(),ask_clean_c.flatten(),
	c=np.log10(yclean_c.flatten()-np.min(yclean_c.flatten())),
	cmap='cool',edgecolor='none')
plt.yscale('log')
## use zero bound for strikes
plt.xlim(0)
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.ylabel('Ask Premium')
plt.xlabel('Strike')
## subplot for puts?
plt.subplot(1,2,2)
plt.title(ticker+' Puts')
plt.scatter(xclean_p.flatten(),ask_clean_p.flatten(),
	c=np.log10(yclean_p.flatten()-np.min(yclean_p.flatten())),
	cmap='hot',edgecolor='none')
plt.yscale('log')
## use zero bound for strikes
plt.xlim(0)
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.xlabel('Strike')
## Need to put colorbars somewhere...
plt.tight_layout()
## save in the same path where you got the file?
write_path=path+tnow.strftime("/%Y/%m/%d")
if not os.path.exists(write_path):
	os.makedirs(write_path)
plt.savefig(write_path+'/'+ticker+'_at_time_'+tnow.strftime('%Y_%b_%d_%H_%M')+
	'_premia.png')
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Implied Volatility Plots!!!
iv_max=(np.max(iv_clean_c)*(np.max(iv_clean_c)>np.max(iv_clean_p))+
	np.max(iv_clean_p)*(np.max(iv_clean_c)<=np.max(iv_clean_p)))
plt.figure()
plt.subplot(1,2,1)
plt.title(ticker+' Calls')
plt.scatter(xclean_c.flatten(),iv_clean_c.flatten(),
	c=np.log10(yclean_c.flatten()-np.min(yclean_c.flatten())),
	cmap='cool',edgecolor='none')
## use zero bound for strikes
plt.xlim(left=0)
plt.ylim(bottom=0,top=iv_max)
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.ylabel('Implied Volatility')
plt.xlabel('Strike')
## subplot for puts?
plt.subplot(1,2,2)
plt.title(ticker+' Puts')
plt.scatter(xclean_p.flatten(),iv_clean_p.flatten(),
	c=np.log10(yclean_p.flatten()-np.min(yclean_p.flatten())),
	cmap='hot',edgecolor='none')
## use zero bound for strikes
plt.xlim(left=0)
plt.ylim(bottom=0,top=iv_max)
## use the same y limits for puts and calls
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.xlabel('Strike')
## Need to put colorbars somewhere...
plt.tight_layout()
## save in the same path where you got the file?
write_path=path+tnow.strftime("/%Y/%m/%d")
if not os.path.exists(write_path):
	os.makedirs(write_path)
plt.savefig(write_path+'/'+ticker+'_at_time_'+tnow.strftime('%Y_%b_%d_%H_%M')+
	'_iv.png')
plt.show()

