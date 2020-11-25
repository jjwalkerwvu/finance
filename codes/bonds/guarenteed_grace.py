"""
Created November 25, 2020

@author: Jeffrey J. Walker

guaranteed_grace.py

	A simple script that computes a portfolio of someone who buys 30 year 
	zero coupon bonds using $200 per month; what is the value at t=2019?
	Any returns are reinvested, and we check the value of the portfolio at 
	2019.
	If $200 is not enough money to buy a bond in a month, she waits until 
	she has accrued enough cash to buy in.
	If we encounter Nan, just build up cash and buy the next month.
	Grace will have to wait until 1985 to buy in

	So called "guarenteed_grace", because she will have guarenteed returns.

	Compare with results from:
	https://www.reddit.com/r/financialindependence/comments/c02ml4/timing_the_market_the_absolute_worst_vs_absolute/
	https://imgur.com/gallery/BlK4jzM
	


"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime as dt
## insert the path corresponding to bond_price; we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/bonds')
#from bond_price import bond_price
## import the csv reader for FRED data
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
from yahoo_csv_reader import yahoo_csv_reader
## Need the federal holiday calendar for ease
from pandas.tseries.holiday import USFederalHolidayCalendar

def get_business_day(date):
    while date.isoweekday() > 5 or date in cal.holidays():
        date += dt.timedelta(days=1)
#    return date

## Want to execute in python shell? then use:
#execfile('/home/jjwalker/Desktop/finance/codes/bonds/guaranteed_grace.py')

## Zero coupon yield curve from FRED:
## read in data; have to use (7)th line as the header, I don't know why
datafile="/home/jjwalker/Desktop/finance/data/bonds/feds200628.csv"
zc=pd.read_csv(datafile,header=7)
zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
zc.set_index('Date',inplace=True)
## the SVENY variable names contain the zero-coupon yield, continuously 
## compounded
## get the variables needed: 
## 1 year zero coupon (for annual Sortino/information/Sharpe ratio)
zc01=zc['SVENY01']
## 30 year zero coupon, the instrument we are interested in
zc30=zc['SVENY30']
## the market price of the bond:
p30=1000/(1+zc30/100)**30


## Find a start date; Ideally this would be a treasury auction date?
start_date='1985-12-02'
## suitable end date
end_date='2019-12-02'
cal = USFederalHolidayCalendar()

first_bday_of_month = [get_business_day(d).date() 
	for d in pd.date_range(start_date, end_date, freq='BMS')]

## cash array
c=np.zeros(len(first_bday_of_month))

#date_array=pd.date_range(start_date,end_date, freq='BMS')
