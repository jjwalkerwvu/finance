"""
Created December 1, 2020

@author: Jeffrey J. Walker

market_timing.py
	This script attempts to use a rules-based system for timing financial 
	markets based on yield curve inversion, and evaluate the results.

	The idea is to buy leveraged instruments, like long-dated zero coupon
	bonds, options on the short end of the curve (euro-dollar futures), and 	
	possibly some middle of the curve bonds like 10 year note.
	
	These purchases are made when the the 10 year minus 2 year yield goes 
	negative, and subsequently goes back to zero; this is the point where we
	buy in.
	Then, we hold these instruments, perhaps even DCA into these investments,
	until the Fed Funds rate drops by a large amount - something I still need 
	to quantify satisfactorily.
	Some ideas (not all are mutually exclusive) for when to sell:
		- 	Fed rate has decreased, and has remained constant for 2 or more 
			quarters (within some tolerance)
		-	Fed rate drops by a larger amount than the most recent increase?
			This makes sense, because the fed usually has to drop the short
			rate "all at once"
		-	A local maximum in the Fed funds rate is observed, then wait until
			the rate drops faster than the most recent increase and wait until
			Fed funds stays constant for 1-2 quarters?
		-	When reaching a profit target on certain instruments (100% for
			STRIPS, 500-1000% Eurodollar options, etc.)
		- 	Definitely sell bonds when fed funds rate goes to zero, you are 
			done, you have probably done quite well on the investment if this
			happens. This most recently happend on March 15, 2020; a great
			time to sell bonds and buy stocks
		-	Some examples:
			* 
			* December 16 2008: Fed Funds to 0, SPX to 913.18
			* March 16 2020: Fed Funds to 0, SPX to 2381.63
			

	Approaches to consider:
		1.) Bond and bond derivative basket only, never hold SPX?
		2.) Buy back into stock market after selling bonds and derivatives?
			Likewise, sell stocks and move to bonds after yield curve
			inversion
		3.) Hold "safe" bond portfolio after moving out of speculative 
			instruments, maybe short term notes, and DCA into bonds as 
			interest rates rise again

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
from pandas.tseries.holiday import USFederalHolidayCalendar

def get_business_day(date):
    while date.isoweekday() > 5 or date in cal.holidays():
        date += datetime.timedelta(days=1)
    return date

## Want to execute in python shell? then use:
#execfile('/home/jjwalker/Desktop/finance/codes/bonds/market_timing.py')

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
## the market price of the 30 year zc bond:
par_val=1000
p30=par_val/(1+zc30/100)**30

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

## data for spx: (or use ^GSPC)
## EVEN BETTER! Use sp500TR, the sp500 total return index which assumes 
## dividend reinvestment!
#spx=yahoo_csv_reader('/home/jjwalker/Desktop/finance/data/stocks/^SP500TR','^SP500TR')
spx=yahoo_csv_reader('/home/jjwalker/Desktop/finance/data/stocks/^GSPC','^GSPC')
## SPX daily return, in case we need it:
#spx_drf=spx.Close[1:].values/(spx.Close[:-1])




## DCA inputs:
## starting cash; make this zero if you want to start by dca'ing first 
## iteration of list
cash=0
## DCA investing amount, dollars
dca_inv=200
## initial number of spx shares:
nshares=0
## Dates to use for dollar cost averaging; set to the first of the month
## Find a start date; Ideally this would be a treasury auction date?
#start_date='1985-12-02' 	# this start date is the first month that 30 year 
							# STRIPS data is available
start_date='1979-06-01'
## suitable end date; need to error check for weekend, does not seem to work
## automatically
#end_date='2019-12-02'
#end_date='2020-08-03' ## Use latest Possible date:
end_date='2020-08-01'
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


## FED funds rate:
## monthly data; still usefull for looking at major jumps in policy
fedfunds_monthly_path='/home/jjwalker/Desktop/finance/data/us_economic_data/FEDFUNDS'
## Daily data is usefull for checking when the rate reaches a target level for
## a given day.
fedfunds_path='/home/jjwalker/Desktop/finance/data/us_economic_data/DFF'
fedfunds=fred_csv_reader(fedfunds_path)
fedfunds_monthly=fred_csv_reader(fedfunds_monthly_path)
## I think back fill is the best way to display the monthly data, in a daily format
fedfunds_bfill=fedfunds_monthly.resample('D').bfill()
## this may be helpful
fedfunds_diff=fedfunds_bfill.diff()



## Construct the recession prediction indicator, the 10y-2y yield
## or use 10y - 3mo?
#yc_indicator=yc['10']-yc['0.25']
yc_10y_minus_2y=yc['10']-yc['2']
## I think dropping NANs here is ok and appropriate, and only go from 
## start_date to end_date. 
#pd.merge(left=df_with_millions, left_on='date_column',
#         right=df_with_seven_thousand, right_on='date_column')
yc_10y_minus_2y=yc_10y_minus_2y[start_date:end_date].dropna()
## May want to also restructure this to include dates where bonds and stocks 
## both have data
loop_index=yc_10y_minus_2y.index.intersection(spx.index)
yc_10y_minus_2y=yc_10y_minus_2y[loop_index]
## find whether yield curve starts off inverted or not for the time period
## you are investigating.
thresh=0
prev_check=yc_10y_minus_2y[0]<0
## maybe check this? How to initialize for any time period?
uninversion=False
uninv_days=0
## maximum wait time before reallocating, or "giving up" in days; 2 or 3 years 
max_wait=3*365
## The flag for when to sell stocks and buy bonds:
exit_stocks=False
## The flag for when to sell bonds and buy stocks again
exit_bonds=True
## flag for if we are buying bonds for dca part of loop
buy_bonds=False
## flag for if we are buying stocks for dca part of loop
buy_stocks=True
## array for uninversion time stamps:
uninvert_dates=np.array([])

## Additional variables for "FEDFUNDS" logic
## get the most recent decrease and increase before starting the main loop?
temp=fedfunds_diff.FEDFUNDS[:yc_10y_minus_2y.index[0]]
## if you want the date for when it occurs, it is temp.index[temp>0][-1]
mrff_increase=temp[temp>0][-1] 
mrff_increase_date=temp.index[temp>0][-1]
## the value:
mrff_increase_value=fedfunds_bfill.FEDFUNDS[mrff_increase_date]
## Same, for decrease:
mrff_decrease=temp[temp<0][-1]
mrff_decrease_date=temp.index[temp<0][-1]
mrff_decrease_value=fedfunds_bfill.FEDFUNDS[mrff_decrease_date]
## threshold for considering the effective fed funds rate "constant"; so it
## is permitted to be +/- 0.25%
const_thresh=0.25


for i in range(1,len(yc_10y_minus_2y)):
	## date for each step:
	loop_date=yc_10y_minus_2y.index[i]
	## Every step in loop?
	## compute the "inversion" logic each pass through the loop?
	prev_check=yc_10y_minus_2y[i-1]<0
	inv_check=yc_10y_minus_2y[i]<0
	## need to know whether to use 10y zc or 30y zc; if false, use 10y zc
	## if true, use my preferred levered bond, the 30y zc when buying bonds
	thirty_zcb=loop_date>=pd.to_datetime("1985-12-02")
	## Yield curve has just inverted if the statement below is true	
	if (inv_check==True and prev_check==False) and exit_bonds==True:
		## if there is an inversion, continue investing in stocks? 
		inversion=True
		uninversion=False
		## Use first inversion before exit_bonds=True?
		#print(str(uninversion))
		#if (inversion==True and uninversion==False):
		#	print('First Inversion: '+yc_10y_minus_2y.index[i].strftime('%Y-%b-%d'))
	#inversion=inv_check*~prev_inv
		
	
	## Check to see when the yield curve uninverts; only care about it the 
	## first time it uninverts after an inversion, hence the or statement
	if ((inv_check==False and prev_check==True) and uninversion==False):
		
		uninversion=True
		## keep an array of all these timestamps
		uninvert_dates=np.append(uninvert_dates,loop_date)
		uninv_days=0
		## print the first day of the uninversion?
		print('Uninversion on date: '+loop_date.strftime('%Y-%b-%d')+
			' buy bonds at price: ' + str(p30[loop_date])+	
			', SPX sell price: '+str(spx['Close'][loop_date]))
		exit_bonds=False
		exit_stocks=True
		buy_bonds=True
		buy_stocks=False

	
	#if (inversion==True and uninversion==True):
	#	print('First uninversion: '+yc_10y_minus_2y.index[i].strftime('%Y-%b-%d'))
	#	inversion=False

	## the yield curve has just uninverted, and so the clock starts; count
	## the number of days 
	uninv_days=uninv_days+uninversion*(
			(yc_10y_minus_2y.index[i]-yc_10y_minus_2y.index[i-1])).days
	

	## fed funds logic; only care about fed funds logic if the yield curve
	## has inverted up to 2 (3?) years ago.
	## The plan: wait until the most recent fed funds rate change has: 
	## 1.) decreased by a larger amount than the most previous increase
	## 2.) stayed constant for one business quarter (3 months)
	## 3.) or if the fed funds rate hits zero, then we are also done
	## Cut our losses if the fed funds rate increases by more a larger
	## amount than the most recent decrease
	## Do we need additional logic? want continually decreasing fedfunds, 
	## with a threshold
	## Maybe we need to think in terms of decrease cycle; if fedfunds is 	
	## continually decreasing (within some reasonable threshold)

	## most recent fedfunds increase or decrease:
	if fedfunds_diff.FEDFUNDS[loop_date]>0.01:
		mrff_increase=fedfunds_diff.FEDFUNDS[loop_date]
		mrff_increase_date=loop_date
	if fedfunds_diff.FEDFUNDS[loop_date]<-0.01:
		mrff_decrease=fedfunds_diff.FEDFUNDS[loop_date]
		mrff_decrease_value=fedfunds_bfill.FEDFUNDS[loop_date]
		mrff_decrease_date=loop_date
	
	## wait until local max, last change was a larger decrease than the
	## last increase, and current rate is unchanged for 1 business quarter
	if (exit_bonds==False and
		(uninv_days<=max_wait) and 
		(mrff_decrease_date>mrff_increase_date) and #(abs(mrff_decrease)>mrff_increase) and
		((loop_date-mrff_decrease_date).days>=90)):
		## put this requirement here so we do not calculate it every iteration
		temp=fedfunds_bfill.FEDFUNDS[mrff_decrease_date:loop_date]
		## easier to use the "negative" of the desired condition	
		if ((temp>(mrff_decrease_value+const_thresh))&
			(temp<(mrff_decrease_value-const_thresh))).sum()==0: 
			## 		
			exit_bonds=True
			## Trying something here	
			#mrff_decrease=0
			print('Exit Bonds at price: '+str(p30[loop_date])+ ' on date: '+
				loop_date.strftime('%Y-%b-%d')+
				', SPX buy in price: '+str(spx['Close'][loop_date]))

	## The fed funds equal to 0 case; where the threshold is 0.15% or lower	
	## (Or max wait time has elapsed and we exit the trade)
	if (uninv_days>=max_wait or 
		fedfunds['DFF'][yc_10y_minus_2y.index[i]]<=0.15) and exit_bonds==False:
		exit_bonds=True
		#mrff_decrease=0
		## sell the bonds here
		## amount of time that has elapsed since bonds were purchased
		#tb=
		print('Exit Bonds at price: '+str(p30[loop_date])+ ' on date: '+
			loop_date.strftime('%Y-%b-%d')+
			', SPX buy in price: '+str(spx['Close'][loop_date]))
	## The fed funds has dropped since the last increase (local max) and has
	## stayed constant for 1 business quarter (3 months)
	
	## Asset allocation update part of the loop
	## Sell all bonds and buy back into stocks if either condition below is
	## true on the exact day it occurs
	## Also include condition that this must be at least second loop iteration?
	if (exit_bonds==True) and (nshares==0):
		## sell bonds and buy stocks again according to dca rules		
		buy_bonds=False
		buy_stocks=True
		exit_stocks=False
		## liquidate bond position; requires some finesse on account of the
		## various maturities in the portfolio

		#cash=0
	
		## lump sum into stocks; need to get dates in common with stocks and bonds before
		## activating this line
		nshares=np.floor(cash/spx['Close'][loop_date])
		cash=cash-nshares*spx['Close'][loop_date]

	## if we intend to exit our stock position, lump sum into bonds on the 
	## exact day that it occurs
	if (exit_stocks==True) and (nshares!=0):
		buy_bonds=True
		buy_stocks=False
		## liquidate stock position, easy peasy
		cash=cash+nshares*spx['Close'][loop_date]	
		nshares=0	
		## lump sum into bonds; 10 year zero coupon before 1985 December, 
		## 30 year zero coupon afterward
	 

	## DCA part of loop.
	## DCA according to some rules on the first day of the month or some other
	## Frequency
	if np.datetime64(loop_date.strftime('%Y-%m-%d')) in first_bday_of_month:
		cash=cash+dca_inv	
		#print('You are dca\'ing at date: '+loop_date.strftime('%Y-%m-%d'))
		if buy_stocks==True:
			dca_shares=np.floor(cash/spx['Close'][loop_date])
			## update cash position
			cash=cash-dca_shares*spx['Close'][loop_date]
			## update total shares
			nshares=nshares+dca_shares
		#if buy_bonds==True:
			#thirty_zcb

## total everything up to get value of portfolio		
vs=nshares*spx['Close'][loop_date]
## something more complicated if we have any bonds
vb=0
vtot=vs+vb+cash
print("Total market value of portfolio: "+str(vtot))
