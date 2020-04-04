"""
Created on Thursday April 2, 2020

@author: Jeffrey J. Walker

    hedging_optimizer.py
        This script looks for the best priced options to hedge a long 
		position, with option data retrieved using the 
		yahoo_option_chain_json.py function.
		

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
## Be sure that you use a valid ticker symbol, no indices!
## This will be the stock you are long on.
ticker='SPY'
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

## pick an appropriate time horizon.
t_plus_30=pd.to_datetime('today').now()+timedelta(days=42)
input_date=time.mktime(t_plus_30.timetuple())
## Ready to call the option chain scraper/reader
dnow,dexp,St,df_calls,df_puts=yahoo_option_chain_json(path,ticker,input_date)

## time to expiration, from dnow and dexp, in days:
texp=(pd.Timestamp(dexp).tz_localize('US/Eastern')-pd.Timestamp(dnow)
		)/np.timedelta64(1,'D')	

## where to scrape this from?
#y_annual=0.01
## We could assume we are just holding cash, since interest rates are so low
y_annual=0.01
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Now use the option chain to find the best combination of options to hedge
## the stock/security

## number of shares you want to protect:
nshares=100

## only include data points where there is a bid and an ask
xptemp=np.array(df_puts.strike[((df_puts.bid!=0)&(df_puts.ask!=0))])
yptemp=np.array((df_puts.ask[((df_puts.bid!=0)&(df_puts.ask!=0))]))
ivp_temp=np.array(df_puts.impliedVolatility[((df_puts.bid!=0)&(df_puts.ask!=0))])
delta_temp=np.zeros(len(xptemp))
gamma_temp=np.zeros(len(xptemp))

## Simplest hedge is hedging delta; try doing just this before trying other
## things.
## May consider also hedging gamma
for i in range(1,len(xptemp)-1):
	solution,second_deriv,delta,gamma,vega,theta,rho=bs_analytical_solver(
		S=St,K=xptemp[i],r=y_annual,T=texp/365,sigma=ivp_temp[i],o_type='p')
	gamma_temp[i]=gamma	
	delta_temp[i]=delta

## The optimization requires Integer Programming.
## Canonical Form:
## Maximize C^{T}*X
## Subject to
## A*X>=B, where X>=0 and is restricted to natural numbers

## Make dataframe, then save to csv to handle with octave or R





