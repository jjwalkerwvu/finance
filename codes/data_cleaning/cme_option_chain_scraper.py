"""
Created on Tuesday May 12, 2020

@author: Jeffrey J. Walker

    cme_option_chain_scraper.py
        This function is an attempt to get the option chain from cme's website
		

		Should the risk-free rate be scraped from some location when this 
		function runs, or should that functionality be given to the script
		that calls this function?

	Inputs
		path	- 	the target directory, where the option chain will be 
					written. 	
					args or kwargs for write to file flag?
		ticker	-	the ticker symbol.
					Stocks are just the letters	
					Indices include '^' in front of the letters.	
		
		
		
		Do I need an input for the timezone where the function is used?
		Target directory for where to write the option chain csv files?

		A flag for whether to write option chain data to file or not?
"""

import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
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
import re

def cme_option_chain_scraper(ticker):
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## if statements for different ticker types??
	## might want an option to collect bath month price quotes for futures

	## example url for cme:
	url_string='https://www.cmegroup.com/trading/interest-rates/stir/30-day-federal-fund_quotes_globex_options.html?optionExpiration=K0#optionExpiration=K0&optionProductId=6316&strikeRange=ALL'
	## here is a link to the list for all commodities in json?
	#url_string='https://www.cmegroup.com/CmeWS/mvc/ProductSlate/V2/List'
	## here is the link for xlst tranformer, see cmegroup_scraper.m:
	#'http://www.cmegroup.com/CmeWS/mvc/xsltTransformer.do?xlstDoc=/XSLT/md/blocks-records.xsl&url=/da/BlockTradeQuotes/V1/Block/BlockTrades?exchange=XCBT,XCME,XCEC,DUMX,XNYM&foi=OPT&subGroup=16&tradeDate=',5242020,'&sortCol=time&sortBy=desc&_=1417532611358?xlstDoc=/XSLT/md/blocks-records.xsl&url=/da/BlockTradeQuotes/V1/Block/BlockTrades?exchange=XCBT,XCME,XCEC,DUMX,XNYM&foi=OPT&subGroup=16&tradeDate=',5242020,'&sortCol=time&sortBy=desc&_=1417532611358'
	
	## do we need to "trick" cme that we are using a brower?
	session=requests.Session()

	#cme officially forbids scraping
    #so a header must be used to disguise as a browser
    #technically speaking, the website should be able to detect that too
    #those tech guys just turn a blind eye, thx fellas
    session.headers.update(
            {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'})
	
	response=session.get(url_string)

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
	## how do we get more than one table??
	tr_elements = doc.xpath('//tr')

	table=[]
	for line in range(len(tr_elements)):
		table_row=[]
		for t in tr_elements[line]:
			table_row.append(t.text_content())
		table.append(table_row)

	df=pd.DataFrame(table[1:], columns=table[0])
	
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	

	return df
