"""
Created on Saturday March 21 2020

@author: Jeffrey J. Walker

    yahoo_option_chain_json.py
        This function obtains the options chain for a particular stock symbol.
		
		This seems to only fetch the nearest expiration date options chain, 
		can we modify this and use a function input to find nearest calendar
		date expiration to the input date? Perhaps this can be built into a
		class method if this function morphs into a class.

		Should the risk-free rate be scraped from some location when this 
		function runs, or should that functionality be given to the script
		that calls this function?
		Maybe a reasonable method is to find the yield to maturity for a zero
		coupon bond with a maturity date closest to the expiration date of the
		option?
		A simpler, but less accurate alternative would be to just use the 
		yield curve

	Inputs
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
import json
#from json import loads
## import this library to save the file directly to json format
import urllib

def yahoo_option_chain_json(write_path,ticker,input_date):

	## Maybe query the "default" option chain first, and from there scan the
	## json string to find expiration dates. Then use that information to get
	## the closest expiration date to the user-input date.
	url_string='https://query1.finance.yahoo.com/v7/finance/options/'+ticker
	
	
	## need the date and time if we want to write to a csv file.
	## Get this immediately after pinging the website
	tnow=pd.to_datetime('today').now()
	## the time zone where the code is run, possible check your location to 
	## obtain. Could possibly use as an input, but it might be nice to check
	## the device's location to obtain automatically with this function
	timezone='CET'
	## target directory? Currently an input to the function, but maybe have 
	## some default if this is not specified by the user.
	#target_dir='/home/jjwalker/Desktop/finance/data/options'
	target_dir=write_path

	## use this???
	bs_json = pd.io.json.read_json(url_string)
	## found through trial and error, hopefully all yahoo option chains 
	## look like this
	entries=bs_json['optionChain']['result'][0].keys()
	## We should keep the expiry dates, maybe output the array of expiry dates
	expiry_dates=bs_json['optionChain']['result'][0][entries[1]]
	## now that all of the expiry dates are known, get the closest date to 
	## the user input! Then make another query.
	## closest date is whichever entry in expiry date has the smallest 
	## difference to the user input date.
	exp_array=np.array(expiry_dates)*1.0
	## Now the procedure to convert closest date to unix time. 
	## This ends up being a float using my method.
	## Convert to datetime later.
	## Error checking, in case an input date has not been given:
	if 'input_date' in locals():
		closest_date=exp_array[
			((exp_array-input_date)**2)==np.min((exp_array-input_date)**2)]
	else:
		closest_date=exp_array[0]
	## the actual time of day when the option expires; try 4pm EDT, although  
	## the holder of the option has until 5pm to exercise the option, 5:30 pm 
	## according to the nasdaq? Double check!
	## exp_time variable should eventually go to the top of this script?
	exp_date=datetime.utcfromtimestamp(closest_date)+timedelta(hours=16)
	## modify the original url string to include the nearest date in the query
	url_string=url_string+'?date='+str(int(closest_date[0]))
	## Can/should I print out all of the expiration dates?
	print("Expiry Dates:\n")
	for expiry in expiry_dates:	
		if expiry==closest_date:
			print(pd.Timestamp(datetime.utcfromtimestamp(expiry)
				).tz_localize('US/Eastern').strftime("%Y %b %d")+
				"<--Closest Expiry to Input Date")
		else:
			print(pd.Timestamp(datetime.utcfromtimestamp(expiry)
				).tz_localize('US/Eastern').strftime("%Y %b %d"))

	## some commented lines here describe how to append multiple expiration
	## dates to one file
	#temp=bs_json['optionChain']['result'][0]['options']
	## replace bs_json_alt with whatever the updated option chain json is
	## called
	#temp.append(bs_json_alt['optionChain']['result'][0]['options'])
	## and now:
	## bs_json['optionChain']['result'][0]['options'][0] is the first chain;
	## bs_json['optionChain']['result'][0]['options'][1] is the appended chain
	## len(bs_json['optionChain']['result'][0]['options']) tells you how many
	## chains there are in total!

	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## Now, perform the necessary work to write to file.
	## convert local time to utc.
	#tnow=?
	tnow.tz_localize(timezone).tz_convert('utc')
	## in practice though, we will just assume all times (for stock purposes) 
	## to be in eastern time, so just convert our local time to that
	tnow=tnow.tz_localize(timezone).tz_convert('US/Eastern')
	## the time to expiration is today's date subtracted from the future date;
	## get the result in units of days!
	## Maybe texp belongs in a script or function where this function is 
	## called from
	texp=(pd.Timestamp(exp_date).tz_localize('US/Eastern')-pd.Timestamp(tnow)
		)/np.timedelta64(1,'D')		
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
	
	## If there is going to be a loop over expiry dates to get volatility term
	## structure, this would be the place to put it.

	## convert tnow, the time at which the data was retrieved, into a string
	## for a filename.
	tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
	
	## save the data into two dataframes; put tnow and expiration date into
	## a second header above the column names
	## INCLUDE THE CURRENT SPOT PRICE OF THE ASSET AS WELL!
	## Maybe include a vix-like calculation?
	#date_header=('Date Retrieved,'+
	#			tnow.strftime("%Y-%m-%d %H:%M:%S.%f")+','+
	#			'Date of Expiry,'+
	#			exp_date.strftime("%Y-%m-%d %H:%M:%S.%f"))

	#date_header_list=['Date_Retrieved', 
	#					tnow.strftime("%Y-%m-%d %H:%M:%S.%f"),
	#					'Date_of_expiry', 
	#					exp_date.strftime("%Y-%m-%d %H:%M:%S.%f")]

	
	filename=path+'/'+tnow_str+'_'+ticker+'_'+exp_date.strftime("%Y_%m_%d")+'_exp'	

	#df_calls = df_calls.append(date_header_list, ignore_index=True).append(
	#	df_calls, ignore_index=True)
	#bs_json.to_csv(filename+'.csv')	
	## Why not just write the json (a pandas.core.frame.DataFrame object) to 
	## file?
	## write this to file much earlier?
	## This looks like the best method; writes to file easily and the option
	## chain can be read the same way as in this function!
	urllib.urlretrieve(url_string,filename+'.txt')
	## still have to put tnow into this data object!
	## Need to insert tnow into the dataframe?
	## urllib.urlretrieve works great, but for multiple expiration dates, when
	## contcatenation has been done, use something like this:
	#bs_json.to_json(path+'/'+tnow_str+'_'+ticker+'_full_chain'+'.txt')
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## read the file we have just created!
	bs_json = pd.io.json.read_json(filename+'.txt')
	## how to read the file if it was written with the .to_json pd method?
	#bs_json=pd.read_json(path+'/'+tnow_str+'_'+ticker+'_full_chain'+'.txt')

	
	strikes=bs_json['optionChain']['result'][0][entries[2]]
	quote=bs_json['optionChain']['result'][0][entries[4]]
	## could also use midpoint of bid ask?
	spot_price=quote['regularMarketPrice']
	## this is the latest market time, which may not correspond to the time	
	## when this function is run (i.e., if you run the function when market
	## is closed, you will the last market time of the underlying
	market_time=bs_json['optionChain']['result'][0]['quote'][
		'regularMarketTime']
	
	## ready to extract the option chain data.
	option_chain=bs_json['optionChain']['result'][0][entries[5]]
	## This should also work:
	#option_chain=bs_json['optionChain']['result'][0]['options']
	## these are lists of dictionaries!
	puts_list=option_chain[0]['puts']
	## model for json with multiple expiration dates?
	#bs_json['optionChain']['result'][0]['options'][0]['puts']
	calls_list=option_chain[0]['calls']
	## is this even needed?
	#exp_date=option_chain[0]['expirationDate']
	## convert these lists of dictionaries into a dictionary of lists?
	#puts_dict = reduce(lambda d, src: d.update(src) or d, dicts, {})
	
	## making the dataframes is as simple as this.
	df_calls=pd.DataFrame(calls_list)
	df_puts=pd.DataFrame(puts_list)

	
	
	
	## Don't forget, exp_date is output as a unix time
	return tnow,exp_date,expiry_dates,spot_price,df_calls,df_puts


