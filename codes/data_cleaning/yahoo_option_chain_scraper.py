"""
Created on Saturday March 14

@author: Jeffrey J. Walker

    yahoo_option_chain_scraper.py
        This script obtains the options chain for a particular stock symbol.
        Turn this into a function later?
"""

import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date
import requests
import lxml.html as lh
#import re
import pandas as pd
import numpy as np
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

#def yahoo_option_chain_scraper(filename)

## the yield of the risk-free rate; scrape this from somewhere too or use as a
## constant for now?
y=0.02

# the ticker to use?
ticker='SPY'
# the url:
url_string='https://finance.yahoo.com/quote/'+ticker+'/options/'
# another url example:
#https://www.marketwatch.com/investing/stock/uber/options?countrycode=US&showAll=True
# so stock or fund matters!
#url='https://www.nasdaq.com/market-activity/stocks/tsla/option-chain'
## or:
#url='https://old.nasdaq.com/symbol/tsla/option-chain'

#soup = BeautifulSoup(url_string, 'html.parser')
r = requests.get(url_string)
c=r.content

doc = lh.fromstring(r.content)
tr_elements = doc.xpath('//tr')

## From Yahoo finance, the columns of the table for calls comes from 
## tr_elements[0].text_content()

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
	name.replace(" ", "_")
	## also get rid of '%' special character.
	name.replace("%", "Percent")
	call_cols.append(name)
    #print '%d:"%s"'%(i,name)
    #call_cols.append((name,[]))
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## A little snippet of code that I will use to get the time to expiration in 
## days

## the actual time of day when the option expires; try 4pm, although the 
## holder of the option has until 5pm to exercise the option, 5:30 pm 
## according to the nasdaq.
## exp_time variable should eventuall go to the top of this script?
exp_time=' 16' ## 4pm
## This test date is how the dates are usually formatted on marketwatch.com.
test_date='September 4, 2020'+exp_time
date_dt = datetime.datetime.strptime(test_date, '%B %d, %Y, %H')

## get the time right now, as the code is run.
tnow=pd.to_datetime('today').now()
## convert local time to utc
#tnow.tz_localize(timezone).tz_convert('utc')
## in practice though, we will just assume all times (for stock purposes) to
## be in eastern time, so just convert our local time to that
tnow=tnow.tz_localize(timezone).tz_convert('US/Eastern')

## the time to expiration is today's date subtracted from the future date;
## get the result in units of days!
texp=(pd.Timestamp(date_dt).tz_localize('US/Eastern')-pd.Timestamp(tnow))/np.timedelta64(1,'D')

## code to check the current date, and make a folder for today's date if it
## does not exist.
path=os.getcwd()+time.strftime("/%Y/%m/%d")
#os.makedirs(path, exist_ok=True)
## and when saving a file, for example:
#plt.savefig(path+'implied_distribution.png')
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#return df_calls,df_puts


