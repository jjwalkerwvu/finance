"""
Created on Saturday March 14 2020

@author: Jeffrey J. Walker

    yahoo_quote_lookup.py
        This function is designed to quickly grab the price of a security.
		Maybe also allow an option to download the 

	Inputs
		ticker	-	the ticker symbol.
					Stocks are just the letters	
					Indices include '^' in front of the letters.	
					
		Do I need an input for the timezone where the function is used?
		Target directory for where to write the option chain csv files?
		
		args/kwargs?
		A flag for whether to write to file or not?
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
#import re

def yahoo_quote_lookup(ticker):
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## if statements for different ticker types??
	## might want an option to collect bath month price quotes for futures

	## If just doing a quick quote lookup?
	url_string='https://finance.yahoo.com/quote/'+ticker
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

	previous_close=tr_elements[0].text_content()
	price_open=tr_elements[1].text_content()
	bid=tr_elements[2].text_content()
	ask=tr_elements[3].text_content()
	volume=tr_elements[6].text_content()
	
	## set price to the midpoint?
	price=(bid+ask)/2.0
	
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## slightly different code to download the (full) data set.
	## url string is something like this?
	#url_string='https://finance.yahoo.com/quote/'+ticker+'/history?p='+ticker

	return price
