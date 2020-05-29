"""
Created on Tuesday May 26 2020

@author: Jeffrey J. Walker

    yahoo_option_chain_multi_exp.py
        This function obtains the option chain for multiple expiration dates.

		Is it possible to obtain the performance of the underlying for the 
		previous year? (in order to find the historical volatility if I want
		to make my own iv calculations)

	Inputs:
		path		- 	the target directory, where the option chain will be 
						written. args or kwargs for write to file flag?
						Should there be a default path if none given?
		ticker		-	the ticker symbol.
						Stocks are just the letters	
						Indices include '^' in front of the letters.	
		input_date	- 	user inputs a date? If not given, use the nearest 
						expiry date? Should this be unix or datetime format?
						Right now I use unix time format, but maybe do a check
						and convert to unix format if input_date is not in
						unix format.
						Can I make this function accept multiple input dates?
						Get closest expiry date to each one in list or 
						datetime array

	Outputs:

"""

import pandas as pd
import numpy as np
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.tz import *
import time
import os
import sys
import json

def yahoo_option_chain_multi_exp(write_path,ticker):
	
	## the time zone where the code is run, possible check your location to 
	## obtain. Could possibly use as an input, but it might be nice to check
	## the device's location to obtain automatically with this function
	timezone='CET'
	## target directory? Currently an input to the function, but maybe have 
	## some default if this is not specified by the user.
	#target_dir='/home/jjwalker/Desktop/finance/data/options'
	target_dir=write_path

	## First get expiry dates.
	url_string=('https://query1.finance.yahoo.com/v7/finance/options/'+ticker)
	bs_json = pd.io.json.read_json(url_string)
	## found through trial and error, hopefully all yahoo option chains 
	## look like this
	entries=bs_json['optionChain']['result'][0].keys()
	## We should keep the expiry dates, maybe output the array of expiry 
	## dates
	expiry_dates=bs_json['optionChain']['result'][0][entries[1]]

	## Kelly's idea:
	## initialize an empty dataframe with len(expiry_dates) number of rows;
	## each row will contain the json result for a given expiry date
	## or, append to list?
	## Is this fastest, or is there a better way?
	option_chain_multi=[]

	for date in expiry_dates:
		url_date=url_string+'?date='+str(date)
		option_chain_multi.append(pd.io.json.read_json(url_date))

	## need the date and time if we want to write to a csv file.
	## Get this immediately after pinging the website
	tnow=pd.to_datetime('today').now()
	
	## now make a dataframe, and save it
	option_chain=pd.DataFrame(option_chain_multi)	
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## Now, perform the necessary work to write to file.
	## convert local time to utc.
	tnow.tz_localize(timezone).tz_convert('utc')
	## in practice though, we will just assume all times (for stock purposes) 
	## to be in eastern time, so just convert our local time to that
	tnow=tnow.tz_localize(timezone).tz_convert('US/Eastern')
	## the time to expiration is today's date subtracted from the future date;
	## get the result in units of days!
	## Maybe texp belongs in a script or function where this function is 
	## called from
	#texp=(pd.Timestamp(exp_date).tz_localize('US/Eastern')-pd.Timestamp(tnow)
	#	)/np.timedelta64(1,'D')		
	## code to check the current date, and make a folder for today's date if 
	## it does not exist.
	## this next line can be the default if no path is given?
	#path=os.getcwd()+time.strftime("/%Y/%m/%d")
	## in future, change target_dir to the path variable, given as an input to
	## the function
	path=target_dir+tnow.strftime("/%Y/%m/%d")
	## the line below is apparently for python 3!
	#os.makedirs(path, exist_ok=True)
	## Workaround for python 2
	if not os.path.exists(path):
		os.makedirs(path)
	## convert tnow, the time at which the data was retrieved, into a string
	## for a filename.
	tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
	
	filename=path+'/'+tnow_str+'_'+ticker+'_full_chain'+'.txt'
	
	option_chain.to_json(filename)
	#strikes=bs_json['optionChain']['result'][0][entries[2]]
	## could also use midpoint of bid ask?
	spot_price=option_chain[0][0]['optionChain']['result'][0]['quote'][
		'regularMarketPrice']

	

	## How to best make a dataframe from the option_chain? (clean it up)
	#option_chain[0][0]['optionChain']['result'][0]['options'][0]['puts']
	
	## Maybe this is the best way to concatenate the dataframes?
	## DO NOT INCLUDE OPTION CHAINS THAT HAVE NO DATA!
	pframes=[pd.DataFrame(
		chain['optionChain']['result'][0]['options'][0]['puts']) 
		for chain in option_chain_multi]
	## set index to strike for each dataframe in list? What is best way?
	#for df in pframes:
	#	if 'strike' in df.columns:
	#		df.set_index(['expiration','strike'],inplace=True)

	
	cframes=[pd.DataFrame(
		chain['optionChain']['result'][0]['options'][0]['calls']) 
		for chain in option_chain_multi]
	
	## make a multi index first?
	#strike=df_calls.strike.unique()
	#index=pd.MultiIndex.from_product([map(str,expiry_dates),strike],names=[expiry_dates,strike])

	## I should make it so that the index level after expiry dates is strike
	## price
	df_puts=pd.concat(pframes,ignore_index=True)
	## is now a good time to convert expiration column to pandas datetime?
	df_puts.set_index(['expiration','strike'],inplace=True)
	#df_puts = pd.concat(pframes, keys=expiry_dates,names=['expiry_date','strike'])
	## do the same for calls:
	df_calls=pd.concat(cframes,ignore_index=True)
	df_calls.set_index(['expiration','strike'],inplace=True)
	## old method:
	#df_calls = pd.concat(cframes, keys=expiry_dates)
	## should I join the two dataframes?
	## can index the different expiration dates by key:
	## (You will likely use this functionality in scripts that call this
	## function) 
	#df_keys.loc[expiry_dates[0]] 

	## should I put into the dataframe: tnow, time to expiration for each
	## option, and the spot price?

	## should expiry dates be transformed to a regular datetime?
	#datetime.utcfromtimestamp(expiry_dates)+timedelta(hours=16)

	## test code to ensure I can read the option_chain json dataframe in!
	## will be used in other codes that call the files produced from this
	## function
	#attempt=pd.read_json(filename)
	## example for a single expiration date, use to generalize in an external
	## script:
	#df_attempt=pd.DataFrame(attempt[0].iloc[35]['optionChain']['result'][0]
	#	['options'][0]['puts'])	

	return tnow,expiry_dates,spot_price,df_calls,df_puts

