"""
Created on Saturday March 14 2020

@author: Jeffrey J. Walker

    yahoo_option_chain_scraper.py
        This function obtains the options chain for a particular stock symbol.
        Turn this into a function later?
		
		This seems to only fetch the nearest expiration date options chain, 
		can we modify this and use a function input to find nearest calendar
		date expiration to the input date?

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
import re

## import the analytical solver to calculate the greeks for each option chain!
#from bs_analytical_solver import bs_analytical_solver

## keep in mind, structure of the table may differ for different securities!
## note also, that etfs like spy pay dividends

## the full put call inequality for american options:
# s - k <= c_a - p_a <= S - k*exp(-rT)
# s - the spot price
# k - strike price
# c_a - american call
# p_a - american put
# r - risk free rate
# T - time to expiration

def yahoo_option_chain_scraper(write_path,ticker):

	## the yield of the risk-free rate; scrape this from somewhere too or use 
	## as a constant for now?
	#y=0.02

	## Do not forget, we should also return, and write to file, the current
	## spot price of the asset!
	## I do not know how to grab the price of the asset from the option chain
	## page, so here is a workaround:
	#url_string='https://finance.yahoo.com/quote/'+ticker
	#r = requests.get(url_string)
	#doc = lh.fromstring(r.content)
	#tr_elements = doc.xpath('//tr')
	#bid=tr_elements[2].text_content()
	#ask=tr_elements[3].text_content()
	#price=(bid+ask)/2.0
	## (Because this takes time, the spot price may not be the same when we
	## access the option chain

	## the ticker to use?
	## do some error checking here?
	#ticker='SPY'
	## the url; this defaults to the nearest expiration date.
	## Maybe need to have a desired expiration date as an input?
	url_string='https://finance.yahoo.com/quote/'+ticker+'/options/'
	## Here is another example, with a unix date at the end, May 15 2020
	#url_string='https://query1.finance.yahoo.com/v7/finance/options/'+ticker+'?date=1589500800'
	r = requests.get(url_string)
	## Is this line even needed?
	#c=r.content
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


	doc = lh.fromstring(r.content)
	tr_elements = doc.xpath('//tr')

	## find out the next table element number that corresponds to puts;
	## this number is the cutoff for reading calls data.
	header=tr_elements[0].text_content()
	for line in range(len(tr_elements)):
		if tr_elements[line].text_content()==header:
			puts_begin=line
		
	## now reuse the header variable, fill with the column names
	header=tr_elements[0].text_content().split()

	call_cols=[]
	i=0
	for t in tr_elements[0]:
		i+=1
		name=t.text_content()
		## get rid of spaces.
		## If there are no spaces, this statement does no harm.
		name=name.replace(" ", "_")
		## also get rid of '%' special character.
		name=name.replace("%", "Percent")
		call_cols.append(name)
    	#print '%d:"%s"'%(i,name)
    	#call_cols.append((name,[]))
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## Now that we have all of the column names, we are ready to get the data
	## for calls
	option_list=[]
	for line in range(1,puts_begin):
		i=0
		table_row=[]
		## need an additional loop to populate each table row.
		for t in tr_elements[line]:
			value=t.text_content()
			table_row.append(value)
		option_list.append(table_row)	

	## simple way to make a dictionary?
	#chain_dict={i:[option_list[]] for i in call_cols}
	## or just use the list.
	df_calls=pd.DataFrame(option_list, columns=call_cols)
	
	## get rid of any weird symbols, like ',','%'; 
	## Do not have to worry about having only dashes as entries; these will 
	## become nans when columns[2:] are forced to numeric values.
	df_calls[df_calls.columns[2:]]=df_calls[df_calls.columns[2:]].replace(
		{',':''},regex=True)
	df_calls[df_calls.columns[2:]]=df_calls[df_calls.columns[2:]].replace(
		{'%':''},regex=True)

	## convert the relevant string values to numeric
	df_calls[df_calls.columns[2:]]=df_calls[df_calls.columns[2:]].apply(
		pd.to_numeric,errors='coerce')
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## Now do puts
	option_list=[]
	for line in range(puts_begin+1,len(tr_elements)):
		i=0
		table_row=[]
		## need an additional loop to populate each table row.
		for t in tr_elements[line]:
			value=t.text_content()
			table_row.append(value)
		option_list.append(table_row)	

	
	## simple way to make a dictionary?
	#chain_dict={i:[option_list[]] for i in call_cols}
	## or just use the list.
	## the columns for puts are the same for calls.
	df_puts=pd.DataFrame(option_list, columns=call_cols)

	## get rid of any weird symbols, like ',','%'; 
	## Do not have to worry about having only dashes as entries; these will 
	## become nans when columns[2:] are forced to numeric values.
	df_puts[df_puts.columns[2:]]=df_puts[df_puts.columns[2:]].replace(
		{',':''},regex=True)
	df_puts[df_puts.columns[2:]]=df_puts[df_puts.columns[2:]].replace(
		{'%':''},regex=True)

	## convert the relevant string values to numeric
	df_puts[df_puts.columns[2:]]=df_puts[df_puts.columns[2:]].apply(
		pd.to_numeric,errors='coerce')
	
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## A little snippet of code that I will use to get the time to expiration  
	## in days

	## the actual time of day when the option expires; try 4pm EDT, although  
	## the holder of the option has until 5pm to exercise the option, 5:30 pm 
	## according to the nasdaq? Double check!

	## exp_time variable should eventuall go to the top of this script?
	#exp_time=' 16' ## 4pm?
	exp_time='16:00'

	## This test date is how the dates are usually formatted on marketwatch.com.
	#test_date='September 4, 2020'+exp_time
	
	## We should get the expiry date from the dataframe, calls or puts
	#exp_string=df_calls[df_calls.columns[0]][0]
	## remove the ticker; This does not work for spx or other index options!
	## Maybe better to split based on the year, which is known from tnow?
	## Anything before the tens place of the year corresponds to characters
	## relating to the ticker, but not necessarily containing the ticker 
	## exactly 
	#exp_string=exp_string.split(ticker)[1]
	## turn the exp_string into a datetime.
	## first two digits are the expiration year; '20' is assumed for the 
	## thousands and hundreds place for now.
	#exp_year='20'+exp_string[:2]
	#exp_month=exp_string[2:4]
	#exp_day=exp_string[4:6]
	#exp_date=pd.to_datetime(exp_year+'-'+exp_month+'-'+exp_day+'-'+exp_time)
	
	## We should get the expiry date from the dataframe, calls or puts
	exp_string=df_calls[df_calls.columns[0]][0]
	## Here is a better way, ASSUMING YAHOO FINANCE WILL ALWAYS USE THE
	## CONTRACT NAME FORMAT: "ticker info"+"exp date"+"c or p"+"strike"
	temp=re.findall(r'\d+', exp_string)
	## temp should have two components; the first one is for the date and 
	## second is for the strike.
	exp_year='20'+temp[0][:2]
	exp_month=temp[0][2:4]
	exp_day=temp[0][4:6]
	exp_date=pd.to_datetime(exp_year+'-'+exp_month+'-'+exp_day+'-'+exp_time)

	#test_date = datetime.now()+exp_time
	#date_dt = datetime.datetime.strptime(test_date, '%B %d, %Y, %H')

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
	
	return tnow,exp_date,df_calls,df_puts


