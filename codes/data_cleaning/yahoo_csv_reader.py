"""
Created on Friday March 13

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
	args/kwargs? include if I want to also the scraping of balance sheets...
	

"""

import pandas as pd
import numpy as np
import datetime
import sys

def yahoo_csv_reader(filename):
	## The first thing we must do is figure out what kind of document it is by
	## the filename, csv not included!

	## strings that end with =F are futures contracts!
	'=F' in filename

	## strings that begin with ^ are indices or treasury yields;
	'^' in filename
	
	## Treasuries begin with ^T
	'^T' in filename

	## option for balance sheet?
	## use arg or kwarg?

	## All other strings correspond to regular stocks, as far as I know
	## load up stock data:
	df=pd.read_csv(filename+'.csv',header=0)
	df['Date'] = pd.to_datetime(df.Date,infer_datetime_format=True)
	df=df.rename(columns={'Date':'date'})
	df=df.set_index('date')
	df[df[1:]]=df[df.columns[1:]].apply(pd.to_numeric,errors='coerce')

	## return the data as a data frame with the chosen format
	return df
