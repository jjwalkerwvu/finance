"""
Created on Monday March 16 2020

@author: Jeffrey J. Walker

    option_test_script.py
        This script uses the yahoo_option_chain_scraper to plot the volatility
		surface and produce an implied probability distribution.

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
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Be sure that you use a valid ticker symbol!
## Indices have a '^' before their letter symbols!
#ticker='^SPX'
ticker='SPY'

## insert the path corresponding to the Yahoo option chain scraper; 
## we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
## insert the path corresponding to bs_analytical solver; we will need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')

from yahoo_option_chain_scraper import yahoo_option_chain_scraper
from bs_analytical_solver import bs_analytical_solver

## What is the path to the option chain?
## DO NOT NEED '/' AT THE END!
path='/home/jjwalker/Desktop/finance/data/options'

## Now call the option chain scraper
dnow,dexp,df_calls,df_puts=yahoo_option_chain_scraper(path,ticker)

## calculate the total time between now and expiration date, and convert to
## annualized percentage:
y_annual=0.003

## should the data be smoothed in some way (non-invasive way) so that we can
## get a less noisy second derivative of the call/put prices?
## perhaps some kind of interpolation - with a constant step size?

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Some plots for now; put into a separate script/function later?
plt.plot(df_calls.Strike,df_calls.Last_Price,'.k');plt.show()
## plot the last price
plt.figure()
plt.plot(df_calls.Strike,df_calls.Last_Price,'dc')
plt.plot(df_calls.Strike,df_calls.Last_Price,'sm')

## plot bid ask midpoint
plt.plot(df_calls.Strike,(df_calls.Ask+df_calls.Bid)/2,'.k');plt.show()
## plot the call bid/ask and put bid/ask for each strike
plt.figure()
plt.plot(df_calls.Strike,df_calls.Ask,'vc',label='Call Ask')
plt.plot(df_calls.Strike,df_calls.Bid,'^c',label='Call Bid')
plt.title('Date: Option Chain Call Prices')
plt.xlabel('Strike Price')
plt.ylabel('Price, $')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
## concatenate the date and time for this figure?
plt.savefig(ticker+'call_prices.png')
#
plt.figure()
plt.plot(df_calls.Strike,df_calls.Ask,'vm',label='Put Ask')
plt.plot(df_calls.Strike,df_calls.Bid,'^m',label='Put Bid')
plt.title('Date: Option Chain Put Prices')
plt.xlabel('Strike Price')
plt.ylabel('Price, $')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
#plt.savefig('put_prices.png')


g=np.zeros((len(df_calls)))
delta=df_calls.Strike[1]-df_calls.Strike[0]
for i in range(1,len(df_calls)-1):
    #g[i]=np.exp(0.02*1/365)*(
    #        option_chain.Lastc[i+1]
    #        -2*option_chain.Lastc[i]
    #        +option_chain.Lastc[i-1])/delta**2
	
	## my bumbling attempt to handle non-uniform delta size; have to fix 
	## this somehow, maybe with interpolation?
	#delta[i]=df_calls.Strike[
    g[i]=np.exp(y_annual)*(
            (df_calls.Ask[i+1]+df_calls.Bid[i+1])/2
            -(df_calls.Ask[i]+df_calls.Bid[i])
            +(df_calls.Ask[i-1]+df_calls.Ask[i-1])/2)/delta**2

plt.plot(df_calls.Strike,g,'.k');plt.show()
plt.title('Date: Implied Distribution')
plt.xlabel('Strike Price')
plt.ylabel('Implied Distribution')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
#plt.savefig('implied_distribution.png')
