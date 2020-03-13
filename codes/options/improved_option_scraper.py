#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 19:12:10 2019

@author: jeffreywalker

    improved_option_chain_scraper.py
        This script obtains the options chain for a particular stock symbol.
        Turn this into a function later
"""

import matplotlib.pyplot as plt
import requests
import lxml.html as lh
import pandas as pd
import numpy as np
## import everything we need for datetime operations
import datetime
## or this?
#from datetime import *
from datetime import datetime
from datetime import date
from dateutil.tz import *
import time
## import what we need to automatically write output to a folder
import os
import sys
## import 
## import the analytical solver to calculate the greeks for each option chain!
#from bs_analytical_solver import bs_analytical_solver

## keep in mind, structure of the table may differ for different securities!
## note also, that etfs like spy pay dividends

## put call parity for european options:
# c + k*exp(-rT) = p + s, OR:
# c - p + k*exp(-rT) = s, OR:
# c*exp(rT) - p*exp(rT) + k = f 
# s - the spot price (1 share)
# k - the strike price
# c - european call (1 share)
# p - european put (1 share)
# r - risk free rate
# T - time to expiration 
# f=s*exp(rT) - the forward price

## the full put call inequality for american options:
# s - k <= c_a - p_a <= s - k*exp(-rT)
# s - the spot price
# k - strike price
# c_a - american call
# p_a - american put
# r - risk free rate
# T - time to expiration


## the time zone where the code is run, possible check your location to obtain
timezone='CET'
## do this automatically??
## Need to figure out how to get this working
#timezone=datetime.datetime.now(tzlocal()).tzname()
## No need to put in a string to define the time zone for stocks, options
## since these are all know to occur in the 'US/Eastern' time zone.

## the yield of the risk-free rate
y=0.02

# the ticker to use?
ticker='spy'
# the url:
url_string='https://www.marketwatch.com/investing/fund/SPY/options?countrycode=US&showAll=True'
# another url example:
#https://www.marketwatch.com/investing/stock/uber/options?countrycode=US&showAll=True
# so stock or fund matters!

#soup = BeautifulSoup(url_string, 'html.parser')
r = requests.get(url_string)
c=r.content

doc = lh.fromstring(r.content)
tr_elements = doc.xpath('//tr')

col=[];
for t in tr_elements[4]:
    name=t.text_content()
    col.append((name,[]))   
## remove the symbol column? or not?

## prepare the columns for calls
df_col=['Symbolc']
for element in col[1:7]:
    df_col.append(element[0].replace('.','')+"c")
df_col.append('Strike')
df_col.append('Symbolp')
## prepare the columns for puts
for element in col[9:]:
    df_col.append(element[0].replace('.','')+"p")
## get rid of any spaces!
i=0
for name in df_col:
    df_col[i]=name.replace(' ', '_')
    i=i+1
## prepare a dictionary based on the column names we just generated.
chain_dict={i:[] for i in df_col}

counter=0
option_list=[]
strike_equal_spot=[]
new_table=[]
exp_date=[]
for element in tr_elements:
    table_row=element.text_content().split()
    ## have to get rid of commas for each element in table_row, somehow
	## I have the problem where open interest is sometimes
	## empty, and does not split into 15 columns like it should
	#table_row=element.text_content().replace("\r\n","").split("\t")
	#table_row=[i.strip(' ') for i in table_row]
    option_list.append(table_row)
    if 'Expires' in table_row:
        new_table.append(counter)       
        exp_date.append(element.text_content().replace("\r\n","").strip())
    if 'Current' in table_row:
        strike_equal_spot.append(counter)
        ## I think this command works to remove the rows where the current
        ## strike price is listed
        option_list.remove(table_row)
    counter=counter+1

## This should make a list of the second table, including all calls and puts
## for the option chain.
## Do this for the second table, and try to generalize to additional tables
## for the given stock symbol.     
table2=option_list[new_table[1]+2:new_table[2]-1]
## it looks like option_list[3] gives the expiration date; check for the 
## others!
## This variable will be a title for a plot
exp_date2=exp_date[1]
## populate the table column names:
for i in range(new_table[1]+2,new_table[2]):
	for j in range(len(option_list[i])):
		col[j][1].append(option_list[i][j])


## Here is a plot for table2 for the complete option chain
## make the dictionary
chain_dict={df_col[i]:col[i][1] for i in range(len(df_col))}
## make the dataframe
#option_chain=pd.DataFrame.from_dict(chain_dict)
## drop the symbol columns.
#option_chain=option_chain.drop(['Symbolc', 'Symbolp'], axis=1)
## make everything numeric??
#option_chain.astype('float')

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


