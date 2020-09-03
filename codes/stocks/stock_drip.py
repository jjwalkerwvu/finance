"""
8 August 2020

@author: Jeffrey J. Walker


	This script does an (approximate) dividend reinvestment, to find roi 
	given a stock chart and dividend file.
"""

## import the libraries that you need.
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt

## Need this line to import the yahoo csv reader
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from yahoo_csv_reader import yahoo_csv_reader

## path where the various data files are located.
path='/home/jjwalker/Desktop/finance/data/stocks/'
## load data for each ticker
ticker1='NSC'
#ticker2='AMSC'
div_data=ticker+'_div'
## Start date?

stock=yahoo_csv_reader(path+ticker1,ticker1)
div=yahoo_csv_reader(path+div_data,ticker1)
## make sure we have sorted by index!
div.sort(inplace=True)

## initial number of shares or initial investment.
## initial investment
p0=1e4
## initial shares:
n0=np.floor(p0/stock.Close[stock.index==div.index[0]])#n0=10.0
## number of shares grows with time, can be fractional.
## just use the paid date for when these get added to the principal.
#start_date=
n=np.zeros((len(div))
n[0]=n0
for i in range(len(div)-1):
	n[i+1]=n[i]+n[i]*div.Dividends[i]/stock.Close[stock.index==div.index[i]]



