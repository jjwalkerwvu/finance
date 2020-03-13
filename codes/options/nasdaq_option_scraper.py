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
from datetime import datetime
from datetime import date
import requests
import lxml.html as lh
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

## the yield of the risk-free rate
y=0.02

# the ticker to use?
ticker='spy'
# the url:
url_string='https://www.marketwatch.com/investing/fund/SPY/options?countrycode=US&showAll=True'
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
    
table2=option_list[new_table[1]+2:new_table[2]-1]
