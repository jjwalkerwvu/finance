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
	If we encounter Nan, just build up cash and buy the next month?
	Or figure out why there are nans? (good friday problem)
	Grace will have to save cash and wait until 1985 to buy in

	So called "guarenteed_grace", because she will have guarenteed returns.

	Compare with results from:
	https://www.reddit.com/r/financialindependence/comments/c02ml4/timing_the_market_the_absolute_worst_vs_absolute/
	https://imgur.com/gallery/BlK4jzM

	It looks like the spreadsheet goes from June 1979 to June 2019, so use
	this as the date range.
	


"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
## insert the path corresponding to bond_price; we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/bonds')
#from bond_price import bond_price
## import the csv reader for FRED data
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
from yahoo_csv_reader import yahoo_csv_reader
## Need the federal holiday calendar for ease
from pandas.tseries.holiday import get_calendar, HolidayCalendarFactory,GoodFriday
#from pandas.tseries.holiday import USFederalHolidayCalendar

def get_business_day(date):
    while date.isoweekday() > 5 or date in cal.holidays():
        date += datetime.timedelta(days=1)
    return date

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
par_val=1000
p30=par_val/(1+zc30/100)**30


## Find a start date; Ideally this would be a treasury auction date?
start_date='1985-12-02'
## suitable end date; need to error check for weekend, does not seem to work
## automatically
#end_date='2019-12-02'
end_date='2020-08-03'
cal = USFederalHolidayCalendar()
#cal=get_calendar('USFederalCalendar')


first_bday_of_month = [get_business_day(d).date() 
	for d in pd.date_range(start_date, end_date, freq='BMS')]

## Stop gap solution to get rid of good friday (1988 April 1, 1994 April 1)
## problem.
## 1988 April 1
first_bday_of_month[28]=first_bday_of_month[28]+timedelta(days=3)
## 1994 April 1
first_bday_of_month[100]=first_bday_of_month[100]+timedelta(days=3)


## cash; start with initial pool of money
#c=0
## alternate option: begin with five years of stashed money, excepting 
## month of december 1985.
## so this is 5*12*200+6*200
c=12000+1200-200
## invested amount; set at 200 for now
inv=200
## array with maturity dates of bonds, number of bonds;
## Just automatically initialize with 30 years to maturity for now
mdate=np.array(first_bday_of_month)+relativedelta(years=30)
nbonds=np.zeros(len(first_bday_of_month))
## As we loop through the dates, if a maturity date now falls at or before
## the current date in the loop, convert the bond to cash


for i in range(0,len(first_bday_of_month)):
	## if a bond has matured, add to cash pool
	#if mdate<first_bday_of_month[i]
	c+=np.sum(nbonds[mdate<first_bday_of_month[i]])*par_val
	nbonds[mdate<first_bday_of_month[i]]=0

	## increment the cash pool by 200; the portion of income applied to 
	## investing
	c+=inv

	## after cashing bonds, buy new bonds with cash from pool
	## if there is not enough cash to buy a new bond, try again next iteration 
	
	nbonds[i]=np.floor(c/p30.loc[first_bday_of_month[i]])
	c=c-nbonds[i]*p30.loc[first_bday_of_month[i]]
	
## find the number of years to maturity for each bond, to the nearest year.
## simple to use the end_date, but need to use a datetime object
ytm=((mdate-first_bday_of_month[-1]).astype('timedelta64[D]')/365.25).astype(int)
## get rid of <0?
ytm[ytm<0]=0
## get the yields at the end date, the SVENY variables;
## first element in resulting the array is SVENY01, second is SVENY02, etc.
## meaning, first element has one year to maturity, etc.
## 67 is SVENY01, 97 is SVENY30
end_yields=zc.loc[end_date][67:97].values
end_prices=par_val/(1+end_yields/100)**range(1,31)
#mat_price=np.tile(ytm,30).reshape(len(ytm),len(end_prices))
mat_price=np.zeros(len(ytm))
for i in range(0,len(ytm)):
	if ytm[i]>0:
		mat_price[i]=end_prices[ytm[i]-1]
		
## compute the value of the bond portfolio.
val=np.sum(nbonds*mat_price)+c
print("Value of Portfolio: "+str(val))

