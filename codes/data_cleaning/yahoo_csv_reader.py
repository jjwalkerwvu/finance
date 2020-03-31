"""
Created on Friday March 13 2020

@author: Jeffrey J. Walker

	yahoo_csv_reader.py
		This function reads csv files downloaded from yahoo finance and 
		automatically puts them into a useful format based on the security 
		type (stock, bond yield, futures contract, option, etc.)

	Inputs:
		filename	-	filename, must be a string! 
						The filename should include the directory?
						Make sure to error check

		ticker		-	the ticker symbol.
						Stocks are just the letters	
						Indices include '^' in front of the letters.
						Is this variable even needed?
	args/kwargs? include if I want to also the scraping of balance sheets...
	

"""

import pandas as pd
import numpy as np
import datetime
import sys

def yahoo_csv_reader(filename,ticker):
	## The first thing we must do is figure out what kind of document it is by
	## the filename, csv not included!
	## Wait, this seems unnecessary, they are all formatted the same?

	## strings that end with =F are futures contracts!
	#'=F' in ticker

	## strings that begin with ^ are indices or treasury yields;
	#'^' in ticker
	
	## Treasuries begin with ^T
	#'^T' in ticker

	## option for balance sheet?
	## use arg or kwarg?

	## All other strings correspond to regular stocks, as far as I know
	## load up stock data:
	df=pd.read_csv(filename+'.csv',header=0)
	df['Date'] = pd.to_datetime(df.Date,infer_datetime_format=True)
	## This rename is not really needed.
	#df=df.rename(columns={'Date':'date'})
	df=df.set_index('Date')
	df=df[df.columns].apply(pd.to_numeric,errors='coerce')
	
	## If you want to read an option chain, saved as a json:
	#bs_json=pd.io.json.read_json(filename+'.txt')
	#strikes=bs_json['optionChain']['result'][0][entries[2]]
	#quote=bs_json['optionChain']['result'][0][entries[4]]
	## could also use midpoint of bid ask?
	#spot_price=quote['regularMarketPrice']
	## this is the latest market time, which may not correspond to the time	
	## when this function is run (i.e., if you run the function when market
	## is closed, you will the last market time of the underlying
	#market_time=bs_json['optionChain']['result'][0]['quote'][
	#	'regularMarketTime']
	## ready to extract the option chain data.
	#option_chain=bs_json['optionChain']['result'][0][entries[5]]
	## these are lists of dictionaries!
	#puts_list=option_chain[0]['puts']
	#calls_list=option_chain[0]['calls']
	## is this even needed?
	#exp_date=option_chain[0]['expirationDate']
	## convert these lists of dictionaries into a dictionary of lists?
	#puts_dict = reduce(lambda d, src: d.update(src) or d, dicts, {})
	## making the dataframes is as simple as this.
	#df_calls=pd.DataFrame(calls_list)
	#df_puts=pd.DataFrame(puts_list)


	## return the data as a data frame with the chosen format
	return df
