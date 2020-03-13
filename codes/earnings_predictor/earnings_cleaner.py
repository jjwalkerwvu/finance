"""
October 18,2019

earnings_cleaner.py

	This script opens up the csv files with the data needed for the earnings
	predictor and collates all the data in the correct order.

	This script works with the csv files:


@author Jeffrey J. Walker
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
## useful for selecting previous or next business day
from pandas.tseries.offsets import BDay

## the ticker
ticker='cni'
## path where the various data files are located.
path='/home/jjwalker/Desktop/finance/earnings_predictor/'

## earnings data/relevant stock data
earnings=pd.read_csv(path+ticker+'_earnings.csv',header=0)
earnings['date'] = pd.to_datetime(earnings.date,infer_datetime_format=True)
earnings=earnings.set_index('date')
## Also put earnings dates into datetime format?
#earnings['quarter_end']=pd.to_datetime(earnings.quarter_end,infer_datetime_format=True)
#earnings=earnings.rename(columns={'old_name':'new_name'})
## and also, the column is read in as a string, so turn into numerical value
#bond_1.y1=pd.to_numeric[]=\(bond_1.y1)
## make a new column for the price change in percent:
earnings['price_change']=np.nan
earnings['spy_price_change']=np.nan
## price data:
stock_price=pd.read_csv(path+ticker+'_price.csv',header=0)
stock_price['Date'] = pd.to_datetime(stock_price.Date,infer_datetime_format=True)
stock_price=stock_price.rename(columns={'Date':'date'})
stock_price=stock_price.set_index('date')
## and also, the column is read in as a string, so turn into numerical value
#bond_1.y1=pd.to_numeric(bond_1.y1)

## load spy historical data.
spy_price=pd.read_csv(path+'spy_price.csv',header=0)
spy_price['Date'] = pd.to_datetime(spy_price.Date,infer_datetime_format=True)
spy_price=spy_price.rename(columns={'Date':'date'})
spy_price=spy_price.set_index('date')

## go through price data and fill in the open, close, min and max prices for 
## the stock before and after the earnings report release
## going until the n-1 timestep is just a temporary fix; missing some price 
## data when this is was first written
for date in earnings.index[:-1]:
	## if the earnings announcement was after market close on the specified
	## day, we need to grab price data from the next trading day.
	if earnings.announcement_time[date]=='after_close':
		next_date=date+BDay(1)
		## price before earnings
		earnings.price_before_open[date]=stock_price.Open[date]
		earnings.price_before_max[date]=stock_price.High[date]
		earnings.price_before_min[date]=stock_price.Low[date]
		earnings.price_before_close[date]=stock_price.Close[date]
		earnings.volume_before[date]=stock_price.Volume[date]
		## price after earnings
		earnings.price_after_open[date]=stock_price.Open[next_date]
		earnings.price_after_max[date]=stock_price.High[next_date]
		earnings.price_after_min[date]=stock_price.Low[next_date]
		earnings.price_after_close[date]=stock_price.Close[next_date]
		earnings.volume_after[date]=stock_price.Volume[next_date]
		## spy price before earnings
		earnings.spy_price_before_open[date]=spy_price.Open[date]
		earnings.spy_price_before_max[date]=spy_price.High[date]
		earnings.spy_price_before_min[date]=spy_price.Low[date]
		earnings.spy_price_before_close[date]=spy_price.Close[date]
		earnings.spy_volume_before[date]=spy_price.Volume[date]
		## spy price after earnings
		earnings.spy_price_after_open[date]=spy_price.Open[next_date]
		earnings.spy_price_after_max[date]=spy_price.High[next_date]
		earnings.spy_price_after_min[date]=spy_price.Low[next_date]
		earnings.spy_price_after_close[date]=spy_price.Close[next_date]
		earnings.spy_volume_after[date]=spy_price.Volume[next_date]
		## input values for the price change, for now just in percent:
		earnings.price_change[date]=(earnings.price_after_open[date]-
			earnings.price_before_close[date])/(
			earnings.price_before_close[date])*100
		## input values for spy?
	
	## if not after_close, then it has to be before_open, which means that 
	## we need the previous trading day.
	## could make another elseif statement to handle errors	
	else:
		prev_date=date-BDay(1)
		## if there was a holiday, just get the next closest date.
		## this seemed like the simplest solution.
		try:
			earnings.price_before_open[date]=stock_price.Open[prev_date]
		except:
			prev_date=date-BDay(2)	
		## price before earnings
		earnings.price_before_open[date]=stock_price.Open[prev_date]
		earnings.price_before_max[date]=stock_price.High[prev_date]
		earnings.price_before_min[date]=stock_price.Low[prev_date]
		earnings.price_before_close[date]=stock_price.Close[prev_date]
		earnings.volume_before[date]=stock_price.Volume[prev_date]
		## price after earnings
		earnings.price_after_open[date]=stock_price.Open[date]
		earnings.price_after_max[date]=stock_price.High[date]
		earnings.price_after_min[date]=stock_price.Low[date]
		earnings.price_after_close[date]=stock_price.Close[date]
		earnings.volume_after[date]=stock_price.Volume[date]
		## spy price before earnings
		earnings.spy_price_before_open[date]=spy_price.Open[prev_date]
		earnings.spy_price_before_max[date]=spy_price.High[prev_date]
		earnings.spy_price_before_min[date]=spy_price.Low[prev_date]
		earnings.spy_price_before_close[date]=spy_price.Close[prev_date]
		earnings.spy_volume_before[date]=spy_price.Volume[prev_date]
		## spy price after earnings
		earnings.spy_price_after_open[date]=spy_price.Open[date]
		earnings.spy_price_after_max[date]=spy_price.High[date]
		earnings.spy_price_after_min[date]=spy_price.Low[date]
		earnings.spy_price_after_close[date]=spy_price.Close[date]
		earnings.spy_volume_after[date]=spy_price.Volume[date]
	
	## price changes are set up to work the same whether before or after 
	## market open
	## May consider using price_before_open and comparing to result from
	## price after open.		
	## input values for the price change, for now just in percent:
	earnings.price_change[date]=(earnings.price_after_open[date]-
		earnings.price_before_close[date])/(
		earnings.price_before_close[date])*100
	## input values for spy?	
	print(str(date))
	

## print the dataframe to csv

earnings.to_csv(path+ticker+'_test.csv')

## will need this command later, but 
#price_change_percent=(earnings.price_after_open-earnings.price_before_close)/(earnings.price_before_close)*100


