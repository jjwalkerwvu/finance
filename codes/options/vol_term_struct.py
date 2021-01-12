"""
Created on Tuesday March 31 2020

@author: Jeffrey J. Walker

    vol_term_struct.py
        This script uses the yahoo_option_chain_multi_exp.py function to get
		The volatility term structure surface.

"""

import pandas as pd
import numpy as np
#from scipy.interpolate import griddata
from scipy import interpolate
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
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

from yahoo_option_chain_multi_exp import yahoo_option_chain_multi_exp
from bs_analytical_solver import bs_analytical_solver

## What is the path to the option chain?
## DO NOT NEED '/' AT THE END!
path='/home/jjwalker/Desktop/finance/data/options'

dnow,expiry_dates,St,df_calls,df_puts=yahoo_option_chain_multi_exp(
	path,ticker)
## Make a directory (if it does not exist)
write_path=path+dnow.strftime("/%Y/%m/%d")
## save in the same path where you got the file?
if not os.path.exists(write_path):
	os.makedirs(write_path)


plt.plot(df_calls.loc[:].impliedVolatility[df_calls.loc[:].strike==3000].index.get_level_values(level=0),100*df_calls.loc[:].impliedVolatility[df_calls.loc[:].strike==3000].values,'.k');
plt.show()
plt.savefig(write_path+'/'+ticker+'_at_time_'+dnow.strftime('%Y_%b_%d_%H_%M')+
	'_exp_'+dexp.strftime('%Y_%b_%d')+'_atm_iv_snapshot.png')

## let's make a volatility surface plot.
## use Viridis for color scheme?
ax=plt.axes(projection='3d')
Z=df_calls.loc[:].impliedVolatility[:].values
X=df_calls.loc[:].impliedVolatility[:].index.get_level_values(level=0).values
Y=df_calls.loc[:].impliedVolatility[:].index.get_level_values(level=1).values


