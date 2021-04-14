"""
Created on Wednesday March 24 2021

@author: Jeffrey J. Walker

	shiller_excel_reader.py
		This function reads the excel file from Shiller's website and extracts
		the data into a useable dataframe.

		The url:
		http://www.econ.yale.edu/~shiller/ie_data.xls

		Should I have an option to read straight from the url?

	Inputs:
		filename	-	filename, must be a string! 
						The filename should include the directory?
						Make sure to error check!
						If there is no filename given, default to retrieving
						excel data from the url
	

"""

import pandas as pd
import numpy as np
import datetime
import sys

def shiller_excel_reader(filename):
	## is it a TypeError exception?
	## if you want to read from file:
	## (Were I usually keep it:
	## '/home/jjwalker/Desktop/finance/data/stocks/ie_data.xls'
	try:
		df=pd.read_excel(filename,sheetname='Data',header=7)
	except:
		print('Shiller Data not found in filename specified. Using website data instead.')
		## access website or read from file and put into desired format
		df=pd.read_excel('http://www.econ.yale.edu/~shiller/ie_data.xls',
			sheetname='Data',header=7)
	## Either one or the other in the try block above should have worked, so
	## continue

	## convert Date to string:
	df['Date']=df['Date'].apply(str)
	## need to make this replacement first, due to the fact that October 
	## is listed as .1 instead of .10 in the excel file.
	## Must be an easier way to do this, maybe ask Kelly how to do these regex
	## calls more efficient (fewer commands)
	df['Date']=df['Date'].replace(r'\.1','-10',regex=True)
	df['Date']=df['Date'].replace(r'-101','-11',regex=True)
	df['Date']=df['Date'].replace(r'-102','-12',regex=True)
	## replace decimal with dash in order to convert column to datetime
	df['Date']=df['Date'].replace('\.','-',regex=True)
	df['Date']=pd.to_datetime(df.Date)
	#df['Date'] = pd.to_datetime(df.Date,infer_datetime_format=True)
	df=df.set_index('Date')
	## is this necessary?
	#df=df[df.columns].apply(pd.to_numeric,errors='coerce')
	
	## prepare dividends; may also consider total return index for post-1988
	#shiller_data=pd.read_excel('/home/jjwalker/Desktop/finance/data/stocks/ie_data.xls',
	#	sheetname='Data',header=7)
	#shiller_data['Date'] = pd.to_datetime(shiller_data.Date,infer_datetime_format=True)
	## if start date is 1979-06-01 and end date is 2020-08-31, then use 
	## iloc[1301:1796] as the range; each value corresponds to payment received 
	## on the respective month
	#div=shiller_data.D[1301:1796]
	#div=pd.DataFrame(div.values,index=first_bday_of_month)
	#div.index=pd.to_datetime(div.index)


	## return the data as a data frame with the chosen format
	return df
