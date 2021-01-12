"""
Created on Monday May 25 2020

@author: Jeffrey J. Walker

    iv_term_structure.py
		This is a script that uses the yahoo_option_chain_json function to 
		obtain volatility term structure.

		This is meant as a test bed until I come up with a better solution for
		getting term structure from option chains, like building a devoted
		class or something else.
"""

import pandas as pd
import numpy as np
#from scipy.interpolate import griddata
from scipy import interpolate
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.tz import *
import time
## import what we need to automatically write output to a folder
import os
import sys
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Be sure that you use a valid ticker symbol!
## Indices have a '^' before their letter symbols!
ticker='^SPX'

## insert the path corresponding to the Yahoo option chain scraper; 
## we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
## insert the path corresponding to bs_analytical solver; we will need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')

from yahoo_option_chain_json import yahoo_option_chain_json
from bs_analytical_solver import bs_analytical_solver

## What is the path to the option chain?
## DO NOT NEED '/' AT THE END!
path='/home/jjwalker/Desktop/finance/data/options'

## Now call the option chain scraper
## should call the next calendar month, 3rd friday options by default
t_plus_30=pd.to_datetime('today').now()+timedelta(days=30)
input_date=time.mktime(t_plus_30.timetuple())
## Ready to call the option chain scraper/reader
dnow,dexp,exp_dates,St,df_calls,df_puts=yahoo_option_chain_json(path,ticker,input_date)

## time to expiration, from dnow and dexp, in days:
texp=(pd.Timestamp(dexp).tz_localize('US/Eastern')-pd.Timestamp(dnow)
		)/np.timedelta64(1,'D')	

## calculate the total time between now and expiration date, and convert to
## annualized percentage; you need to find an appropriate risk free bond
## at the option expiration date; time to maturity equal to dexp-dnow
y_annual=0.003


## ready to scrape all expiration dates?
for exp_date in exp_dates:
	_,_,_,_,_,_=yahoo_option_chain_json(path,ticker,exp_date)

