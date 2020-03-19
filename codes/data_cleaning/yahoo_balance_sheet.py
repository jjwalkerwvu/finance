"""
Created on Wednesday March 18

@author: Jeffrey J. Walker

    yahoo_balance_sheet.py
        This function is designed to quickly grab some information about the
		balance sheet of a given company.

	Inputs
		ticker	-	the ticker symbol.
					Stocks are just the letters	
					Indices include '^' in front of the letters.	
					
		Do I need an input for the timezone where the function is used?
		Target directory for where to write the option chain csv files?

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

def yahoo_balance_sheet(ticker):

	url_string='https://finance.yahoo.com/quote/'+ticker+'balance_sheet/'
	r = requests.get(url_string)
	c=r.content
	## need the date and time if we want to write to a csv file.
	## Get this immediately after pinging the website
	tnow=pd.to_datetime('today').now()
	## the time zone where the code is run, possible check your location to 
	## obtain. Could possibly use as an input, but it might be nice to check
	## the device's location to obtain automatically with this function
	timezone='CET'

	doc = lh.fromstring(r.content)
	tr_elements = doc.xpath('//tr')

	## return an appropriately formatted dataframe?
	return df
