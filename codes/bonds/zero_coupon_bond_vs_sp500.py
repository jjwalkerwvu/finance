"""
Created on Monday, October 4, 2020

@author: Jeffrey J. Walker

zero_coupon_bond_vs_sp500.py

	This script loads the zero coupon yield curves contained in feds200628.csv
	and performs an annual rolldown. 
	Download this file again from website: 
		https://www.federalreserve.gov/pubs/feds/2006/200628/200628abs.html
	(if you want to add additional dates beyond october 2020)
	Obviously, actual market data would be nice, but the authors have 
	constructed these curves from market data so have eliminated much of the
	work.

	Maybe I can use the author's method to construct zero-coupon equivalent
	yield curves from live market data?

	Basic idea: 
	start from when 30 year zero coupon bond data is available in this data 
	set; use this as the start date for the first time through this exercise
	
	After 1 year has elapsed since the start date, sell the zero coupon bond,
	(which is now a 29 year bond,) and buy another 30 year bond at the current
	30 year zero coupon bond yield with the proceeds. 
	The idea is to always maintain 30 years to maturity position in the long 
	bond.

	Plot the value of the bond portfolio as it compounds, alongside the sp500
	(semi-log plot probably best). Need to get a dividend reinvested plot of
	sp500 to compare
	

	*Try random starting dates to check the performance; also start dates 
	progressively later in time, like 1987, 1988, etc. to see how the 
	performance evolves with start date

	*Find the sharpe, information, or other similiar kind of ratio for the 30 
	year bond and for the sp500

	*What to use for the risk free rate?

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
## insert the path corresponding to bond_price; we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/bonds')
#from bond_price import bond_price
## import the csv reader for FRED data
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
from yahoo_csv_reader import yahoo_csv_reader

## Want to execute in python shell? then use:
#execfile('/home/jjwalker/Desktop/finance/codes/bonds/zero_coupon_bond_vs_sp500.py')

## regular yield curve data from FRED:
filename='/home/jjwalker/Desktop/finance/data/bonds/fredgraph_01_may_2020'
yc=fred_csv_reader(filename)
## change some column names:
yc.rename(columns={'DGS1MO':'0.083','DGS3MO':'0.25','DGS6MO':'0.5','DGS1':'1',
	'DGS2':'2','DGS3':'3','DGS5':'5','DGS7':'7','DGS10':'10','DGS20':'20',
	'DGS30':'30',},inplace=True)
## restructure the dataframe, sort the columns numerically
## However, this sorts alphabetically instead of numerically
#yc.sort_index(axis=1,ascending=True,inplace=True)
## FINALLY found the way to do this:
yc=yc[np.argsort(yc.columns.astype(float))]
## standard us treasury maturities
xtemp = np.array(yc.columns.astype(float))

## Load spx for comparison: (or use ^GSPC)
## EVEN BETTER! Use sp500TR, the sp500 total return index which assumes 
## dividend reinvestment!
spx=yahoo_csv_reader('/home/jjwalker/Desktop/finance/data/stocks/^SP500TR','^SP500TR')
## SPX daily return, in case we need it:
spx_drf=spx.Close[1:].values/(spx.Close[:-1])

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
## daily return:
p30_drf=p30[1:].values/p30[:-1]
## 29 year zero coupon, what a 30 year zero becomes after 1 year
zc29=zc['SVENY29']
## the market price of the bond:
p29=1000/(1+zc29/100)**29
## daily return:
p29_drf=p29[1:].values/p29[:-1]
## daily annual rolldown return?? p29 offset from p30 by one year
#aroll=p29[1:]/p30[:-1]

## Find a start date; Ideally this would be a treasury auction date?
start_date='3/2/1985'
## suitable end date
end_date='3/2/2020'
## we start rolling from the date: 1981 Oct?
date_array=pd.date_range(start_date,end_date,freq='BAS-feb')
## yield array for each year for 30 year zero coupon bond
#y30=zc['SVENY30'].loc[date_array].values
## price array from the yield data, assuming $1000 par value of bond:
#p30=1000/(1+y30/100)**30
## yield array for each year for 29 year zero coupon bond
#y29=zc['SVENY29'].loc[date_array].values
## price array from the yield data, assuming $1000 par value of bond:
#p29=1000/(1+y29/100)**29

## initial capital, dollars:
p0=1000
## initial number of bonds, 30 year zero coupon bonds:
#n0=np.floor(p0/(1000/(1+y30[0]/100)**30))
n0=np.floor(p0/p30.loc[date_array][0])
n=np.zeros(len(p30.loc[date_array]))
n[0]=n0
## initial value of cash in portfolio; must equal p0-n0*p30[0]!
c=np.zeros(len(n))
c[0]=p0-n0*p30.loc[date_array][0]
## return factor by year:
#r30=p29[1:]/p30[:-1]
## or, more general:
r30=p29.loc[date_array][1:].values/p30.loc[date_array][:-1]
## and for spx:
spx_1y=spx['Close'].loc[date_array][1:].values/spx['Close'].loc[date_array][:-1]
## the cumulative return:
#np.prod(r30)

## loop through the array of yearly dates provided.
for i in range(1,len(date_array)):
	n[i]=np.floor((c[i-1]+n[i-1]*p29.loc[date_array][i])/p30.loc[date_array][i])
	#print(str(n))
	c[i]=c[i-1]+n[i-1]*p29.loc[date_array][i]-n[i]*p30.loc[date_array][i]

final_value=c[-1]+n[-1]*p30.loc[date_array][-1]

## interesting thing we can plot:
start_index=22 # or use start date, if spx_1y has a datetime index
spx_1yt=[np.prod(spx_1y[start_index:i]) for i in range(start_index+1,len(spx_1y))]
r30_1yt=[np.prod(r30[start_index:i]) for i in range(start_index+1,len(spx_1y))]
## sharpe/information/sortino ratio:
r30_std=np.std(r30[start_index:])
r30_mean=np.mean(r30[start_index:])
spx_1y_std=np.std(spx_1y[start_index:])
spx_1y_mean=np.mean(spx_1y[start_index:])

plt.figure()
title='Annual Returns Since ' + spx_1y.index[start_index].strftime("%Y %b")
plt.title(title)
plt.plot(spx_1yt,'-b',label='SP500 Dividends Reinvested');
plt.plot(r30_1yt,'-g',label='30y Zero-Coupon Rolled Annually')
plt.xlabel('Years')
plt.ylabel('Return Factor')
plt.legend(loc='best')
plt.tight_layout()
plt.savefig('TR500_vs_30yr_us_bond_from_'+spx_1y.index[start_index].strftime("%Y")+'.png')


