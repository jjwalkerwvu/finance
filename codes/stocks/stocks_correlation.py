"""
25 Jan 2020

@author: jeffreywalker

	This script reads in the data sets for two different stocks or other
	instrument and finds the correlation between the two. 

	The script works using data taken from yahoo finance, so assume that 
	kind of file structure.

	Also makes a plot.
"""
## import the libraries that you need.
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt

## path where the various data files are located.
path='/home/jjwalker/Desktop/finance/data/stocks/'
## load data for each ticker
ticker1='shanghai_index'
ticker2='AMSC'

## read in all the data frames you would like to check
stock1=pd.read_csv(path+ticker1+'.csv')
## need to convert each to numeric?
## Assuming the files came from yahoo finance, the lines below should work.
stock1[stock1.columns[1:]]=stock1[stock1.columns[1:]].apply(pd.to_numeric, errors='coerce')
##
stock2=pd.read_csv(path+ticker2+'.csv')
stock2[stock2.columns[1:]]=stock2[stock2.columns[1:]].apply(pd.to_numeric, errors='coerce')
## in the case of american vs asian markets, need to shift asian markets up 1
## row, to account for the fact that asian markets close before american 
## markets. (To maintain causality)
#stock2=stock2.shift(-1,axis=0)



## set indices for each security?
stock1['Date'] = pd.to_datetime(stock1.Date,infer_datetime_format=True)
stock1=stock1.set_index('Date')
stock1=stock1.rename(columns={'Close':ticker1+'_close'})
#stock1[~stock1[ticker1+'_close'].isnull()]
## fill in nans in the case that yahoo finance gives columns with null string.
## EXTREMELY ANNOYING THAT .DROPNA() DOES NOT WORK HERE WHEN THE MANUAL SAYS
## IT SHOULD.
stock1=stock1[stock1[ticker1+'_close']!='null']
## A few commands to adjust the closing date for asian markets?
## Is this necessary?
## SHANGHAI CLOSES AT UTC+8:00, SO IT CLOSES BEFORE EUROPE AND USA.

##
stock2['Date'] = pd.to_datetime(stock2.Date,infer_datetime_format=True)
stock2=stock2.set_index('Date')
stock2=stock2.rename(columns={'Close':ticker2+'_close'})

## concatenate the close price for the two (or more) securities and find the correlation.
close_price=pd.concat([stock1[ticker1+'_close'],stock2[ticker2+'_close']],axis=1)
## get rid of any nans??
close_price=close_price.dropna()
## choose a startdate?
start_date=pd.to_datetime('2018-09-30')
## calculate pearson correlation coefficient, easy peasy:
corr_coef=close_price[close_price.index>start_date].corr(method='pearson')
## if that does not work, then try numpy version:
#corr=np.corrcoef(close_price[ticker1+'_close'].astype(np.float),close_price[ticker2+'_close'].astype(np.float))

## quick and dirty plot, in % growth:
plt.plot(close_price[ticker1+'_close']/close_price[ticker1+'_close'][0],'.r')
plt.plot(close_price[ticker2+'_close']/close_price[ticker2+'_close'][0],'.g')




