"""
Created on Saturday March 21 2020

@author: Jeffrey J. Walker

    yahoo_option_chain_json.py
        This function obtains the options chain for a particular stock symbol.
        Turn this into a function later?
		
		This seems to only fetch the nearest expiration date options chain, 
		can we modify this and use a function input to find nearest calendar
		date expiration to the input date?

		Should the risk-free rate be scraped from some location when this 
		function runs, or should that functionality be given to the script
		that calls this function?

	Inputs
		path		- 	the target directory, where the option chain will be 
						written. args or kwargs for write to file flag?
						Should there be a default path if none given?
		ticker		-	the ticker symbol.
						Stocks are just the letters	
						Indices include '^' in front of the letters.	
		input_date	- 	user inputs a date? If not given, use the nearest 
						expiry date? Should this be unix or datetime format?
		
		
		Do I need an input for the timezone where the function is used?
		Target directory for where to write the option chain csv files?

		A flag for whether to write option chain data to file or not?
"""

import pandas as pd
import numpy as np
from functools import reduce
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.tz import *
import time
## import what we need to automatically write output to a folder
import os
import sys
## import for webscraping
#import requests
#import lxml.html as lh
#import re
import json
#from json import loads

def yahoo_option_chain_json(write_path,ticker,input_date):

	## Maybe query the "default" option chain first, and from there scan the
	## json string to find expiration dates. Then use that information to get
	## the closest expiration date to the user-input date.
	url_string='https://query1.finance.yahoo.com/v7/finance/options/'+ticker
	
	#r = requests.get(url_string)
	## need the date and time if we want to write to a csv file.
	## Get this immediately after pinging the website
	tnow=pd.to_datetime('today').now()
	## the time zone where the code is run, possible check your location to 
	## obtain. Could possibly use as an input, but it might be nice to check
	## the device's location to obtain automatically with this function
	timezone='CET'
	## target directory? Maybe make this an input to the function?
	#target_dir='/home/jjwalker/Desktop/finance/data/options'
	target_dir=write_path

	## use this???
	bs_json = pd.io.json.read_json(url_string)
	## found through trial and error, hopefully all yahoo option chains 
	## look like this
	entries=bs_json['optionChain']['result'][0].keys()
	expiry_dates=bs_json['optionChain']['result'][0][entries[1]]
	## now that all of the expiry dates are known, get the closest date to 
	## the user input! Then make another query.
	## closest date is whichever entry in expiry date has the smallest 
	## difference to the user input date.
	exp_array=np.array(expiry_dates)*1.0
	## closest date in unix time. This ends up being a float.
	## Convert to datetime later
	closest_date=exp_array[
			((exp_array-input_date)**2)==np.min((exp_array-input_date)**2)]
	## the actual time of day when the option expires; try 4pm EDT, although  
	## the holder of the option has until 5pm to exercise the option, 5:30 pm 
	## according to the nasdaq? Double check!
	## exp_time variable should eventuall go to the top of this script?
	#exp_time=' 16' ## 4pm?
	#exp_time='16:00'
	exp_date=datetime.utcfromtimestamp(closest_date)+timedelta(hours=16)
	## modify the original url string to include the nearest date in the query
	url_string=url_string+'?date='+str(int(closest_date[0]))
	
	
	bs_json = pd.io.json.read_json(url_string)
	strikes=bs_json['optionChain']['result'][0][entries[2]]
	quote=bs_json['optionChain']['result'][0][entries[4]]
	## could also use midpoint of bid ask?
	spot_price=quote['regularMarketPrice']
	option_chain=bs_json['optionChain']['result'][0][entries[5]]
	## these are lists of dictionaries!
	puts_list=option_chain[0]['puts']
	calls_list=option_chain[0]['calls']
	## is this even needed?
	#exp_date=option_chain[0]['expirationDate']
	## convert these lists of dictionaries into a dictionary of lists?
	#puts_dict = reduce(lambda d, src: d.update(src) or d, dicts, {})
	
	## making the dataframes is as simple as this.
	df_calls=pd.DataFrame(calls_list)
	df_puts=pd.DataFrame(puts_list)
	
	## convert the relevant string values to numeric
	#df_puts[df_puts.columns[2:]]=df_puts[df_puts.columns[2:]].apply(
	#	pd.to_numeric,errors='coerce')


	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

	## get the time right now, as the code is run.
	#tnow=pd.to_datetime('today').now()
	## convert local time to utc
	tnow.tz_localize(timezone).tz_convert('utc')
	## in practice though, we will just assume all times (for stock purposes) 
	## to be in eastern time, so just convert our local time to that
	tnow=tnow.tz_localize(timezone).tz_convert('US/Eastern')

	## the time to expiration is today's date subtracted from the future date;
	## get the result in units of days!
	## Maybe texp belongs in a script or function where this function is 
	## called from
	#texp=(pd.Timestamp(date_dt).tz_localize('US/Eastern')-pd.Timestamp(tnow)
	#	)/np.timedelta64(1,'D')
	texp=(pd.Timestamp(exp_date).tz_localize('US/Eastern')-pd.Timestamp(tnow)
		)/np.timedelta64(1,'D')	
	
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## code to check the current date, and make a folder for today's date if 
	## it does not exist.
	path=os.getcwd()+time.strftime("/%Y/%m/%d")
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
	
	## save the data into two dataframes; put tnow and expiration date into
	## a second header above the column names
	## INCLUDE THE CURRENT SPOT PRICE OF THE ASSET AS WELL!
	date_header=('Date Retrieved,'+
				tnow.strftime("%Y-%m-%d %H:%M:%S.%f")+','+
				'Date of Expiry,'+
				exp_date.strftime("%Y-%m-%d %H:%M:%S.%f"))

	date_header_list=['Date_Retrieved', 
						tnow.strftime("%Y-%m-%d %H:%M:%S.%f"),
						'Date_of_expiry', 
						exp_date.strftime("%Y-%m-%d %H:%M:%S.%f")]

	## replace colons and periods with underscores if making a file?
	#date_dt = datetime.datetime.strptime(datetime.now(), '%B %d, %Y, %H')
	filename=path+'/'+tnow_str+'_'+ticker	

	#s = pd.Series(date_header, index=df.columns)
	#df_calls = df_calls.append(date_header_list, ignore_index=True).append(
	#	df_calls, ignore_index=True)
	df_calls.to_csv(filename+'_Calls'+'.csv',header=date_header)	
	
	return tnow,exp_date,spot_price,df_calls,df_puts


