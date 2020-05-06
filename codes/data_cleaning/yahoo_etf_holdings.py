"""
Created on Wednesday May 6 2020

@author: Jeffrey J. Walker

    yahoo_etf_holdings.py
        This function grabs the top 10 holdings by percentage of an etf 

	Inputs:
		ticker	-	the ticker symbol. ONLY USE ETFS OR YOU WILL GET ERRORS!
							
					
		Do I need an input for the timezone where the function is used?
		Target directory for where to write the option chain csv files?
		
		args/kwargs?
		A flag for whether to write to file or not?
	Output:
		df		- 	Dataframe containing the top 10 holdings of spy, along	
					with market cap

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date
from dateutil.tz import *
import time
## import what we need to automatically write output to a folder
import os
import sys
## import for webscraping
import requests
import lxml.html as lh
import urllib
#import re

def yahoo_quote_lookup(ticker):
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## if statements for different ticker types??
	## might want an option to collect bath month price quotes for futures

	## If just doing a quick quote lookup?
	url_string='https://finance.yahoo.com/quote/'+ticker+'/holdings/'
	r = requests.get(url_string)
	#c=r.content
	## need the date and time if we want to write to a csv file.
	## Get this immediately after pinging the website
	tnow=pd.to_datetime('today').now()
	## the time zone where the code is run, possible check your location to 
	## obtain. Could possibly use as an input, but it might be nice to check
	## the device's location to obtain automatically with this function
	timezone='CET'

	doc = lh.fromstring(r.content)
	tr_elements = doc.xpath('//tr')

	table=[]
	for line in range(len(tr_elements)):
		table_row=[]
		for t in tr_elements[line]:
			table_row.append(t.text_content())
		table.append(table_row)

	df=pd.DataFrame(table[1:], columns=table[0])
	
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## slightly different code to download the (full) data set.
	## url string is something like this?
	#url_string='https://finance.yahoo.com/quote/'+ticker+'/history?p='+ticker

	return df
