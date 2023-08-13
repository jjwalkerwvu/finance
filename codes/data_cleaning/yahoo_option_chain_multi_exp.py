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

## Make optional arguments: write_path, read_path;
#(path,ticker,scrape=True)
## include path and ticker; 
## if optional scrape variable set to False, then treat path as a file to 
## read from instead of write to, test that the path can be opened (try bock),
## and ticker must still be specified, but is just a dummy in such a case  
def yahoo_option_chain_multi_exp(input_path,ticker,scrape=True):
	
	## the time zone where the code is run, possible check your location to 
	## obtain. Could possibly use as an input, but it might be nice to check
	## the device's location to obtain automatically with this function
    timezone='CET'
	## target directory? Currently an input to the function, but maybe have 
	## some default if this is not specified by the user.
	#target_dir='/home/jjwalker/Desktop/finance/data/options'
    target_dir=input_path
	
	## If the optional scrape flag has False selected, then read from file
	## (input_path must contain a properly formated option chain.)
    if scrape==False:
        try:
			## Here is how to open it back up again.
			#bs_json=pd.io.json.read_json(input_path)
            bs_json=pd.read_json(input_path)
			
			#pframes=[pd.DataFrame(
			#	chain['optionChain']['result'][0]['options'][0]['puts']) 
			#	for chain in bs_json[0].iloc[:]]
			#cframes=[pd.DataFrame(
			#	chain['optionChain']['result'][0]['options'][0]['calls']) 
			#	for chain in bs_json[0].iloc[:]]
            pframes=[pd.DataFrame(chain[0]['options'][0]['puts']) 
                                  for chain in bs_json[1][:]]
            cframes=[pd.DataFrame(chain[0]['options'][0]['calls'] )
                                  for chain in bs_json[1][:]]
            
            df_puts=pd.concat(pframes)
            df_calls=pd.concat(cframes)
			## merge on strike:
            df=df_calls.merge(df_puts,how='outer',on=['expiration','strike'],suffixes=('_c','_p'))
			#df.expiration=df.expiration.apply(lambda d: datetime.utcfromtimestamp(d))	
			#df.lastTradeDate_c=df.lastTradeDate_c.apply(lambda d: datetime.utcfromtimestamp(d))
			#df.lastTradeDate_p=df.lastTradeDate_p.apply(lambda d: datetime.utcfromtimestamp(d))
			#df.set_index(['expiration','strike'],inplace=True)
			#df=df.reindex(pd.MultiIndex.from_product(
			#	[df.index.levels[0],df.index.levels[1].unique()],
			#	names=['expiration','strike']),fill_value=np.NaN)	
		
			## Need expiry dates as an output
			#expiry_dates=bs_json[0].iloc[0]['optionChain']['result'][0]['expirationDates']
            expiry_dates=bs_json[1][0][0]['expirationDates']

			## Also need spot price as an output
			#spot_price=bs_json[0].iloc[0]['optionChain']['result'][0]['quote'][
			#	'regularMarketPrice']
            spot_price=bs_json[1][0][0]['quote']['regularMarketPrice']
			## The time when the data was queried; this should be in eastern time
			## so no need for any conversions.
			#tquery=bs_json[0].iloc[0]['optionChain']['result'][0]['quote']['regularMarketTime']
            tquery=bs_json[1][0][0]['quote']['regularMarketTime']
            ## not really tnow, this was the time when the data was queried. 
			## Using this as the output for tnow.
			## Might be interesting to get the market time for all the other 
			## chains (.iloc[0] to highest row number) to see how different the 
			## times are. It takes some time to access each chain, causing a delay
            tnow=pd.to_datetime(datetime.utcfromtimestamp(tquery))
		
		## throw error if the file does not exist
        except: #FileNotFoundError
            print('File not found, check filename, directory')
            tnow=''
            expiry_dates=''
            spot_price=''
            df=''
		
		
		
	
	## If no datafile is given, query the data from yahoo website
    else:

		## First get expiry dates.
		## use query1.stuff or query2?
        url_string=('https://query1.finance.yahoo.com/v7/finance/options/'+ticker)
		#bs_json = pd.io.json.read_json(url_string)
        bs_json = pd.read_json(url_string)
		## found through trial and error, hopefully all yahoo option chains 
		## look like this
        entries=bs_json['optionChain']['result'][0].keys()
		## We should keep the expiry dates, maybe output the array of expiry 
		## dates
		#expiry_dates=bs_json['optionChain']['result'][0][entries[1]]
        expiry_dates=bs_json['optionChain']['result'][0]['expirationDates']
        
		## Kelly's idea:
		## initialize an empty dataframe with len(expiry_dates) number of rows;
		## each row will contain the json result for a given expiry date
		## or, append to list?
		## Is this fastest, or is there a better way?
        option_chain_multi=[]

        for date in expiry_dates:
            url_date=url_string+'?date='+str(date)
			#option_chain_multi.append(pd.io.json.read_json(url_date))
            option_chain_multi.append(pd.read_json(url_date))

	
		## Near here:
		## Get the risk free rate?
		## (scrape wallstreetjournal? 
		## 'https://www.wsj.com/market-data/bonds/treasuries'

		## need the date and time if we want to write to a csv file.
		## Get this immediately after pinging the website.
        tnow=pd.to_datetime('today').now()
	
		## now make a dataframe, and save it
        option_chain=pd.DataFrame(np.squeeze(option_chain_multi))	
        #option_chain=pd.concat(option_chain_multi).reset_index()
		##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		## Now, perform the necessary work to write to file.
		## convert local time to utc.
		#tnow=?
        #tnow=tnow.tz_localize(timezone).tz_convert('utc')
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
		## convert tnow, the time at which the data was retrieved, into a 
		## string for a filename.
        tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
	
        filename=path+'/'+tnow_str+'_'+ticker+'_full_chain'+'.txt'
	
        option_chain.to_json(filename)
		##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		## Clean up the data for output variables of this function!
		#strikes=bs_json['optionChain']['result'][0][entries[2]]
		## could also use midpoint of bid ask?
		#spot_price=option_chain[0][0]['optionChain']['result'][0]['quote'][
		#	'regularMarketPrice']
        #spot_price=option_chain.iloc[0]['result'][0]['quote'][
        #    'regularMarketPrice']
        spot_price=option_chain[1][0][0]['quote']['regularMarketPrice']

	

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
		#index=pd.MultiIndex.from_product([map(str,expiry_dates),strike],
		#	names=[expiry_dates,strike])

		## I should make it so that the index level after expiry dates is strike
		## price
        df_puts=pd.concat(pframes,ignore_index=True)
		## is now a good time to convert expiration column to pandas datetime?
		#df_puts.set_index(['expiration','strike'],inplace=True)
		#df_puts = pd.concat(pframes, keys=expiry_dates,names=['expiry_date','strike'])
		## do the same for calls:
        df_calls=pd.concat(cframes,ignore_index=True)
		#df_calls.set_index(['expiration','strike'],inplace=True)

		## New method: Make one dataframe for calls and puts
		## merge on strike:
        df=df_calls.merge(df_puts,how='outer',on=['expiration','strike'],suffixes=('_c','_p'))
		## Hmm, having problems with this too...
		#df.expiration=df.expiration.apply(lambda d: datetime.utcfromtimestamp(d))	
		## Last trade dates may have NaN entries, so clean these outside of here?
		#df.lastTradeDate_c=df.lastTradeDate_c.apply(lambda d: datetime.utcfromtimestamp(d))
		#df.lastTradeDate_p=df.lastTradeDate_p.apply(lambda d: datetime.utcfromtimestamp(d))
		#df.set_index(['expiration','strike'],inplace=True)
		#df=df.reindex(pd.MultiIndex.from_product(
		#	[df.index.levels[0],df.index.levels[1].unique()],
		#	names=['expiration','strike']),fill_value=np.NaN)


		## old method:
		#df_calls = pd.concat(cframes, keys=expiry_dates)
		## should I join the two dataframes, calls and puts?
		## can index the different expiration dates by key:
		## (You will likely use this functionality in scripts that call this
		## function) 
		#df_keys.loc[expiry_dates[0]] 

		## should I put into the dataframe: tnow, time to expiration for each
		## option, and the spot price?
		## Need also risk-free rate from scraped bond data for each expiry
		## (separate bond-scraper from this function?)


		## should expiry dates be transformed to a regular datetime?
		#datetime.utcfromtimestamp(expiry_dates)+timedelta(hours=16)

    return tnow,expiry_dates,spot_price,df

