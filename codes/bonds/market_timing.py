"""
Created December 1, 2020

@author: Jeffrey J. Walker

market_timing.py
	This script attempts to use a rules-based system for timing financial 
	markets based on yield curve inversion, and evaluate the results.
	May want to start the timer when yield curve inverts, not wait until it
	uninverts

	The idea is to buy leveraged instruments, like long-dated zero coupon
	bonds, options on the short end of the curve (euro-dollar futures), and 	
	possibly some middle of the curve bonds like 10 year note.
	
	These purchases are made when the the 10 year minus 2 year yield goes 
	negative, and subsequently goes back to zero; this is the point where we
	buy in.
	Then, we hold these instruments, perhaps even DCA into these investments,
	until the Fed Funds rate drops by a large amount - something I still need 
	to quantify satisfactorily.


	Explanation of the various pieces of data and how they are put together:
	
	The Fed Funds TARGET rate is the "indicator" for when to exit the bond 
	position. 
	For the data, I use DFEDTAR from Fred:
	https://fred.stlouisfed.org/series/DFEDTAR 
	Note that this data is discontinued as of 2008, so I use the rates (upper
	limit) from the following link for my data:
	https://www.federalreserve.gov/monetarypolicy/openmarket.htm
	Note that where this data overlaps with DFEDTAR from Fred, the DEFEDTAR 
	data corresponds to the upper target range.
	I do not care about the daily or monthly effective rate, I just care about
	the policy, which is given by these rates. 
	For pre-1982 data, I (will) use monthly fed funds effective rate, put into
	0.25% increments (with ceiling function) to hopefully get close enough to
	the "policy" number at that time; more historical research is necessary 
	for this procedure though because I read that the Fed did not start 
	publicly announcing its target rate until 1979.

	The zero coupon yield curves are contained in the file feds200628.csv
	Download this file again from website to get updated yields: 
	https://www.federalreserve.gov/pubs/feds/2006/200628/200628abs.html
	(specifically this link, if you want to use pd.read_csv)
	https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv
	(pd.read_csv(url,sep=",",header=7)

	Try using pd.read_csv with the following url??
	I think the numbers after period1 and period2 may be unix time stamps?
	^GSPC data from url: https://query1.finance.yahoo.com/quote/%5EGSPC/history?period1=-1325635200&period2=1613520000&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true

	Monthly dividends taken from Shiller's website:
	http://www.econ.yale.edu/~shiller/data.htm

	April 3, 2021 - Needed additions:
		- 	Find the total return factor from start to end dates, with no 
			additional money added to the portfolio
		- 	the portfolio gets marked to market every day within the main 
			loop, so we can keep track relative to a performance benchmark
			(here, it's the sp500)
		-	Compare also to a 60/40 quarterly or monthly rebalance portfolio
		-	Include another portfolio for bonds only during this time period
		- 	allow for coupon-bearing bond option
		-	set up ability to contribute 10% to Eurodollar futures, following
			a good methodology?
		-	Make separate script to show an idealized and/or real example of
			a business cycle including fed funds rate, unemployment, inflation
		


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
## Need the federal holiday calendar for ease
from pandas.tseries.holiday import get_calendar, HolidayCalendarFactory,GoodFriday
from pandas.tseries.holiday import USFederalHolidayCalendar
## insert the path corresponding to bond_price; we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/bonds')
#from bond_price import bond_price
## import the csv reader for FRED data, yahoo, etc.
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
from yahoo_csv_reader import yahoo_csv_reader
#from shiller_excel_reader import shiller_excel_reader 


## A function to get the nearest business day
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
## calculate market prices right now, before we even start:
pzc=par_val/(1+zc[zc.columns[67:97]]/100.0)**range(1,31)
## 30 year STRIPS start date
strips30_start=pd.Timestamp('1985-12-02')
## Duration of zero-coupon bond that you want to buy when yield curve inverts?
## My thought was to use 30 year STRIPS, but the lack of issuance between
## February 18, 2002 until February 9, 2006 suggests using 26 for the sake of 
## continuity.
## Default: does not allow lower duration 10 years as an input
strips_duration=10
pzc_buy=pzc[pzc.columns[strips_duration-1]]

## regular yield curve data from FRED:
#filename='/home/jjwalker/Desktop/finance/data/bonds/fredgraph_01_may_2020'
filename='/home/jjwalker/Desktop/finance/data/bonds/fredgraph_2020_dec_31'
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
## Trying a different start date?

## suitable end date; need to error check for weekend, does not seem to work
## automatically
#end_date='2019-12-02'
#end_date='2020-08-03' ## Use latest Possible date:
end_date='2020-08-31'
cal = USFederalHolidayCalendar()
#cal=get_calendar('USFederalCalendar')
first_bday_of_month = [get_business_day(d).date() 
	for d in pd.date_range(start_date, end_date, freq='BMS')]
## Stop gap solution to get rid of good friday (1988 April 1, 1994 April 1)
## problem.
## 1983 April 1
first_bday_of_month[46]=first_bday_of_month[46]+timedelta(days=3)
## 1988 April 1
first_bday_of_month[106]=first_bday_of_month[106]+timedelta(days=3)
## 1994 April 1
first_bday_of_month[178]=first_bday_of_month[178]+timedelta(days=3)
## 2007 January 2
first_bday_of_month[331]=first_bday_of_month[331]+timedelta(days=1)
## And now, initialize some variables for bonds:
## Array of purchase dates
bond_purch=np.array([])
## Number of bonds corresponding to each purchase date
nbonds=np.array([])


## prepare dividends; may also consider total return index for post-1988
## (post-1988 "index" now complete)
shiller_data=pd.read_excel('/home/jjwalker/Desktop/finance/data/stocks/ie_data.xls',
	sheetname='Data',header=7)
## Switch to doing it this way with the line below:
## If you don't put an actual filename, it will pull from Shiller's website.
#shiller=shiller_excel_reader('/home/jjwalker/Desktop/finance/data/stocks/ie_data.xls')
## if start date is 1979-06-01 and end date is 2020-08-31, then use 
## iloc[1301:1796] as the range; each value corresponds to payment received 
## on the respective month
div=shiller_data.D[1301:1796]
div=pd.DataFrame(div.values,index=first_bday_of_month)
div.index=pd.to_datetime(div.index)


## FED funds rate:
## I want to use the target rate! The one that the fed has announced since 1979
#fedfunds_target='/home/jjwalker/Desktop/finance/data/us_economic_data/fedfunds_target'
## monthly data; still usefull for looking at major jumps in policy
fedfunds_monthly_path='/home/jjwalker/Desktop/finance/data/us_economic_data/FEDFUNDS'
## The target rate, from https://fred.stlouisfed.org/series/DFEDTAR and 
## https://www.federalreserve.gov/monetarypolicy/openmarket.htm
fedfunds_target_path='/home/jjwalker/Desktop/finance/data/us_economic_data/fedfunds_target'
fedfunds_monthly=fred_csv_reader(fedfunds_monthly_path)
fedfunds_target=fred_csv_reader(fedfunds_target_path)
## to bin the pre-1982 monthly data to nearest 0.25%:
## (use ceiling, not round or floor!)
ffm=np.ceil(4*fedfunds_monthly)/4
## start of fed funds monthly data:
ffm_start=ffm.index[0]
## end of fed funds monthly data is one day before start of fed funds target data
## fedfunds_target starts at date: 1982-09-27
ffm_end=fedfunds_target.index[0]-relativedelta(days=1)
## rename columns:
fedfunds_target.rename(columns={fedfunds_target.columns[0]:ffm.columns[0]},
	inplace=True)
## Now merge the datasets; use merge instead of join because there should be
## no elements in common.
#fedfunds_result=ffm[ffm_start:ffm_end].merge(fedfunds_target,how='outer')
fedfunds_result=pd.concat([ffm[ffm_start:ffm_end],fedfunds_target])
## I think forward fill is the best way to display the monthly data, in a daily format
fedfunds_ffill=fedfunds_result.resample('D').ffill()
## this may be helpful
fedfunds_diff=fedfunds_ffill.diff()




## Construct the recession prediction indicator, the 10y-2y yield
## or use 10y - 3mo?
#yc_indicator=yc['10']-yc['0.25']
yc_indicator=yc['10']-yc['2']
## What about using the zero coupon yield curve??
#yc_indicator=zc.SVENY10-zc.SVENY02
## The start of whichever indicator you use; need the start of it for later:
yc_start=yc_indicator[~np.isnan(yc_indicator)].index[0]
## I think dropping NANs here is ok and appropriate, and only go from 
yc_indicator=yc_indicator[start_date:end_date].dropna()
## May want to also restructure this to include dates where bonds and stocks 
## both have data
loop_index=yc_indicator.index.intersection(spx.index)
yc_indicator=yc_indicator[loop_index]
## find whether yield curve starts off inverted or not for the time period
## you are investigating.
thresh=0
prev_check=yc_indicator[0]<0
## maybe check this? How to initialize for any time period?
uninversion=False
uninv_days=0
## maximum wait time before reallocating, or "giving up" in days; 2 or 3 years 
max_wait=3*365
## Consider also a wait time, say 1 business quarter of inversion before 
## entering the trade
#invert_wait=90
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
## timestamps for selling bonds, buying back into stocks array:
fed_signal_dates=np.array([])

## Additional variables for "FEDFUNDS" logic
## get the most recent decrease and increase before starting the main loop?
temp=fedfunds_diff.FEDFUNDS[:yc_indicator.index[0]]
## if you want the date for when it occurs, it is temp.index[temp>0][-1]
mrff_increase=temp[temp>0][-1] 
mrff_increase_date=temp.index[temp>0][-1]
## the value:
mrff_increase_value=fedfunds_ffill.FEDFUNDS[mrff_increase_date]
## Same, for decrease:
mrff_decrease=temp[temp<0][-1]
mrff_decrease_date=temp.index[temp<0][-1]
mrff_decrease_value=fedfunds_ffill.FEDFUNDS[mrff_decrease_date]
## The number of days that the fed target rate should be constant before  
## triggering signal; My thinking is that the default should be 1-2 business 
## quarters (90-180 days)
fed_const_days=180	## maybe better performance with 210, but a bit "overfit"
## threshold for considering the effective fed funds rate "constant"; so it
## is permitted to be +/- 0.25%?
const_thresh=0.0
## start with last cycle complete? CHECK TO MAKE SURE!
## Either go through the data and check to see, or write some code to do it
## automatically
cycle_complete=True
## last cycle end date?
## Need to back out to start of time series and end at the start_date 
## (selected earlier)
#for i in range(1,len(fedfunds_ffill.FEDFUNDS)):
#	loop_date=fedfunds_ffill.index[i]
#	
cycle_end=pd.Timestamp("1977-04-01")
cycle_end_dates=np.array([cycle_end])
cycle_start_dates=np.array([])

## initialize arrays for the market_timing portfolio, and the buy and hold
## benchmark
buy_and_hold=np.zeros(len(yc_indicator))
bah_shares=0
bah_cash=0
portfolio=np.zeros(len(yc_indicator))
## initial value of bonds
bond_m2m=0

for i in range(1,len(yc_indicator)):
	## date for each step:
	loop_date=yc_indicator.index[i]
	## Every step in loop?
	## compute the "inversion" logic each pass through the loop?
	prev_check=yc_indicator[i-1]<0
	inv_check=yc_indicator[i]<0
	## need to know whether to use 10y zc or 30y zc; if false, use 10y zc
	## if true, use my preferred levered bond, the 30y zc when buying bonds
	thirty_zcb=loop_date>=strips30_start
	## Yield curve has just inverted if the statement below is true	
	if (inv_check==True and prev_check==False) and exit_bonds==True:
		## if there is an inversion, continue investing in stocks? 
		inversion=True
		uninversion=False
		## Use first inversion before exit_bonds=True?
		#print(str(uninversion))
		#if (inversion==True and uninversion==False):
		#	print('First Inversion: '+yc_indicator.index[i].strftime('%Y-%b-%d'))
	#inversion=inv_check*~prev_inv
		
	
	## Check to see when the yield curve uninverts; only care about it the 
	## first time it uninverts after an inversion, hence the or statement
	## May also want to include a wait time before exit_stocks=True, like 
	## having one quarter of yield curve inversion before liquidation
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
	#	print('First uninversion: '+yc_indicator.index[i].strftime('%Y-%b-%d'))
	#	inversion=False

	## the yield curve has just uninverted, and so the clock starts; count
	## the number of days 
	uninv_days=uninv_days+uninversion*(
			(yc_indicator.index[i]-yc_indicator.index[i-1])).days
	

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

	## New idea:
	## if cycle_complete=True, and we observe a local max or const fed funds
	## for 180 days, and we have decreased at least 0.25 since (last local max
	## or fed funds const), begin new cutting cycle.
	## Cycle continues as long as the rate keeps decreasing from the level of
	## the cycle start until: fedfunds constant for 2 quarters, fed to 0 or 3 years.

	## most recent fedfunds increase or decrease:
	temp=fedfunds_diff.FEDFUNDS[mrff_increase_date:loop_date]
	mrff_increase=temp[temp>=0.01][-1] 
	mrff_increase_date=temp.index[temp>=0.01][-1]
	mrff_increase_value=fedfunds_ffill.FEDFUNDS[mrff_increase_date]
	## decrease:
	temp=fedfunds_diff.FEDFUNDS[mrff_decrease_date:loop_date]
	mrff_decrease=temp[temp<0][-1]
	mrff_decrease_date=temp.index[temp<0][-1]
	mrff_decrease_value=fedfunds_ffill.FEDFUNDS[mrff_decrease_date]

	## test if Fed Funds is constant for a 90 day interval or maybe 180?
	## The constant test for when a cycle ends
	#fed_const_end=abs(fedfunds_diff.FEDFUNDS[
	#	loop_date-relativedelta(days=fed_const_days):loop_date].sum())<=const_thresh
	## New approach: fedfunds must be constant for the entire interval for 
	## this to work
	fed_const_end=(fedfunds_diff.FEDFUNDS[
		(loop_date-relativedelta(days=fed_const_days)):loop_date]!=0).sum()==0

	## test for cycle start, constant fed funds before a recent decrease?
	fed_const_start=((abs(fedfunds_diff.FEDFUNDS[
		loop_date-relativedelta(days=(fed_const_days+1)):
		loop_date-relativedelta(days=1)].sum()
		)<=const_thresh) and (mrff_decrease_date>cycle_end))

	## A new cutting cycle begins when fed funds target rate decreases,
	## either from a local max or after two quarters of a constant rate
	## foll
	if (((mrff_decrease_date>mrff_increase_date) or (fed_const_start)) and 
		(cycle_complete and (mrff_decrease_date>cycle_end))):
		##
		local_max=True
		#cycle_start=yc_indicator.index[i]
		cycle_start=loop_date
		cycle_complete=False
		cycle_start_dates=np.append(cycle_start_dates,cycle_start)
		#print('Cutting cycle started on: '+ cycle_start.strftime('%Y-%b-%d')) 

	## Test for end of cycle; cycle must not have been complete, and the fed
	## has been constant for 2 business quarters
	if ((cycle_complete==False) and fed_const_end):
		#cycle_end=yc_indicator.index[i]
		cycle_end=loop_date
		cycle_complete=True
		cycle_end_dates=np.append(cycle_end_dates,cycle_end)
	
	## The conditions for exiting bonds and/or Eurodollar futures
	if (exit_bonds==False and
		(uninv_days<=max_wait) and 
		(cycle_complete and prev_cycle_check==False)): 
		##		
		exit_bonds=True
		#cycle_complete=True
		#cycle_end=yc_indicator.index[i]
		## Trying something here	
		#mrff_decrease=0
		#print('Most recent decrease date: '+mrff_decrease_date.strftime('%Y-%b-%d'))
		print('Exit Bonds at price: '+str(p30[loop_date])+ ' on date: '+
			loop_date.strftime('%Y-%b-%d')+
			', SPX buy in price: '+str(spx['Close'][loop_date]))

	## The fed funds equal to 0 case; where the threshold is 0.15% or lower	
	## (Or max wait time has elapsed and we exit the trade)
	if ((uninv_days>=max_wait or 
		fedfunds_ffill['FEDFUNDS'][yc_indicator.index[i]]<=0.25) and 
		exit_bonds==False):
		##
		exit_bonds=True
		#cycle_complete=True
		#cycle_end=yc_indicator.index[i]
		#mrff_decrease=0
		print('Exit Bonds at price: '+str(p30[loop_date])+ ' on date: '+
			loop_date.strftime('%Y-%b-%d')+
			', SPX buy in price: '+str(spx['Close'][loop_date]))
	
	## previous cycle check?
	## I need this because otherwise, cycle_complete=True will end the cycle
	## prematurely
	prev_cycle_check=cycle_complete
	
	## Asset allocation update part of the loop
	## Sell all bonds and buy back into stocks if either condition below is
	## true on the exact day it occurs
	## Also include condition that this must be at least second loop iteration?
	if ((exit_bonds==True) and (nbonds.size!=0)) and (nshares==0):
		## record the fed signal.
		fed_signal_dates=np.append(fed_signal_dates,loop_date)
		## sell bonds and buy stocks again according to dca rules		
		buy_bonds=False
		buy_stocks=True
		exit_stocks=False
		## liquidate bond position; requires some finesse on account of the
		## various maturities in the portfolio
		## use floor function for now? Try linear or "exponential" interpolation later
		## Or better, just use the Svenson approximation!
		## Here's how you might do it if you have something between 29 and 30 yr dur.: 
		## rexp=np.log(pzc.loc[loop_date].SVEN30/pzc.loc[loop_date].SVEN29)/1.0
		## price=(pzc.loc[loop_date].SVENY30)*np.exp(rexp*(1-tremaining))
		#print(str(bond_purch))
		#print(str(nbonds))
		telapsed=np.array(
			(pd.to_datetime(loop_date)-pd.to_datetime(bond_purch)
			).astype('timedelta64[D]')).astype(float)/365.25
		#print(telapsed)
		
		#remaining_duration=((strips_duration-np.floor(telapsed))*(
		#	bond_purch>=strips30_start)+
		#	(10-np.floor(telapsed))*(bond_purch<strips30_start))-1
		#cash=np.sum(pzc.loc[loop_date].iloc[remaining_duration].values*nbonds)
		#print(cash)

		## alternate (improved) attempt; remove the floor function, allow 
		## telapsed to be a float. Dont need the minus 1?
		rem_dur=((strips_duration-telapsed)*(bond_purch>=strips30_start)+
			(10-telapsed)*(bond_purch<strips30_start))
		## plug remaining_duration into equation 22 from Gurkayanka; an array
		yeff=(zc.BETA0.loc[loop_date]+
			zc.BETA1.loc[loop_date]*(1-np.exp(-rem_dur/zc.TAU1.loc[loop_date])
			)/(rem_dur/zc.TAU1.loc[loop_date])+
			zc.BETA2.loc[loop_date]*((1-np.exp(-rem_dur/zc.TAU1.loc[loop_date])
			)/(rem_dur/zc.TAU1.loc[loop_date])-np.exp(-rem_dur/zc.TAU1.loc[loop_date]))+
			zc.BETA3.loc[loop_date]*((1-np.exp(-rem_dur/zc.TAU2.loc[loop_date])
			)/(rem_dur/zc.TAU2.loc[loop_date])-np.exp(-rem_dur/zc.TAU2.loc[loop_date]))
			)
		## value of the basket of bonds; new method checks out, gives similar
		## but slightly higher result than old method above (mar 29, 2021)
		peff=par_val/(1+yeff/100.0)**(rem_dur)
		cash=np.sum(peff*nbonds)

		
		## Print cost basis!
		## clear the bond arrays
		bond_purch=np.array([])
		nbonds=np.array([])
		
		## lump sum into stocks; need to get dates in common with stocks and bonds before
		## activating this line
		nshares=np.floor(cash/spx['Close'][loop_date])
		cash=cash-nshares*spx['Close'][loop_date]
		## print out the return on bonds vs spx from uninversion to end of fed
		## cutting cycle
		## current price of 10 year bond purchased on the last uninvert date:
		trem=10-(loop_date-uninvert_dates[-1]).days/365.25
		## plug into equation 22 from Gurkayanka
		yrem=(zc.BETA0.loc[loop_date]+
			zc.BETA1.loc[loop_date]*(1-np.exp(-trem/zc.TAU1.loc[loop_date])
			)/(trem/zc.TAU1.loc[loop_date])+
			zc.BETA2.loc[loop_date]*((1-np.exp(-trem/zc.TAU1.loc[loop_date])
			)/(trem/zc.TAU1.loc[loop_date])-np.exp(-trem/zc.TAU1.loc[loop_date]))+
			zc.BETA3.loc[loop_date]*((1-np.exp(-trem/zc.TAU2.loc[loop_date])
			)/(trem/zc.TAU2.loc[loop_date])-np.exp(-trem/zc.TAU2.loc[loop_date]))
			)
		pbond=par_val/(1+yrem/100.0)**(trem)
		br=((pbond-
			pzc['SVENY10'].loc[uninvert_dates[-1]])/
			pzc['SVENY10'].loc[uninvert_dates[-1]])
		## old method		
		ty=pzc.loc[loop_date].iloc[
			int(9-np.floor((loop_date-uninvert_dates[-1]).days/365.25))]
		print('Underestimate: '+str(ty)+', Svenson approximation: '+str(pbond))
		#br=((ty-
		#	pzc['SVENY10'].loc[uninvert_dates[-1]])/
		#	pzc['SVENY10'].loc[uninvert_dates[-1]])
		## new method		
		print('Bond return: '+str(br*100)+ '% on date: '+loop_date.strftime('%Y-%b-%d'))
		print('SP500 return: '+str(100*(
			spx.Close[loop_date]-spx.Close[uninvert_dates[-1]])/
			spx.Close[uninvert_dates[-1]]) +'%')

	## if we intend to exit our stock position, lump sum into bonds on the 
	## exact day that it occurs
	if (exit_stocks==True) and (nshares!=0):
		buy_bonds=True
		buy_stocks=False
		## liquidate stock position, easy peasy
		cash=cash+nshares*spx['Close'][loop_date]	
		nshares=0	
		## lump sum into bonds; 10 year zero coupon before 1985 December, 
		## 30 year zero coupon thereafter
		bond_purch=np.append(bond_purch,loop_date)
		ntemp=np.floor(cash/(
				pzc['SVENY10'][loop_date]*(loop_date<strips30_start)+
				np.nan_to_num(pzc_buy[loop_date])*(loop_date>=strips30_start)))
		nbonds=np.append(nbonds,ntemp)
		## update cash position
		cash=cash-ntemp*(
				pzc['SVENY10'][loop_date]*(loop_date<strips30_start)+
				np.nan_to_num(pzc_buy[loop_date])*(loop_date>=strips30_start))
		#if loop_date<strips30_start:	
		## buy 10 year "STRIPS"
		#else:
		## buy 30 year STRIPS
	 

	## DCA part of loop.
	## DCA according to some rules on the first day of the month or some other
	## Frequency
	if np.datetime64(loop_date.strftime('%Y-%m-%d')) in first_bday_of_month:
		## not sure if this works for dividends, but simplest use for now
		## Apparently Shiller dividend data is annualized? not sure why I have 
		## to divide by 12
		cash=cash+dca_inv+nshares*div.loc[loop_date][0]/12.0	

		## the benchmark portfolio just buys stock (DCA) and reinvests dividends
		bah_cash=bah_cash+dca_inv+bah_shares*div.loc[loop_date][0]/12.0	
		temp_shares=np.floor(bah_cash/spx['Close'][loop_date])		
		bah_cash=bah_cash-temp_shares*spx['Close'][loop_date]
		bah_shares=bah_shares+temp_shares
		## End of benchmark commands here
		
		#print('cash = '+str(cash))
		#print('number of shares: '+str(nshares))
		#print(loop_date.strftime('%Y-%m-%d'))
		#print('You are dca\'ing at date: '+loop_date.strftime('%Y-%m-%d'))
		if buy_stocks==True:
			## get cash from dividends here?
			dca_shares=np.floor(cash/spx['Close'][loop_date])
			## update cash position
			cash=cash-dca_shares*spx['Close'][loop_date]
			## update total shares
			nshares=nshares+dca_shares
		if buy_bonds==True:
			bond_purch=np.append(bond_purch,loop_date)
			## Need to get price for ANY duration STRIPS, not just 10/30
			ypurch=(zc.BETA0.loc[loop_date]+
				zc.BETA1.loc[loop_date]*(1-np.exp(
				-strips_duration/zc.TAU1.loc[loop_date]))/
				(strips_duration/zc.TAU1.loc[loop_date])+
				zc.BETA2.loc[loop_date]*((1-np.exp(
				-strips_duration/zc.TAU1.loc[loop_date]))/
				(strips_duration/zc.TAU1.loc[loop_date])-
				np.exp(-strips_duration/zc.TAU1.loc[loop_date]))+
				zc.BETA3.loc[loop_date]*((1-np.exp(
				-strips_duration/zc.TAU2.loc[loop_date]))/
				(strips_duration/zc.TAU2.loc[loop_date])-
				np.exp(-strips_duration/zc.TAU2.loc[loop_date])))
			## 
			ppurch=par_val/(1+ypurch/100.0)**strips_duration
			ntemp=np.floor(cash/(
				pzc['SVENY10'][loop_date]*(loop_date<strips30_start)+
				np.nan_to_num(ppurch)*(loop_date>=strips30_start)))
			#ntemp=np.floor(cash/(
			#	pzc['SVENY10'][loop_date]*(loop_date<strips30_start)+
			#	np.nan_to_num(pzc['SVENY30'][loop_date])*(loop_date>=strips30_start)))
			nbonds=np.append(nbonds,ntemp)
			## update cash position
			#cash=cash-ntemp*(
			#	pzc['SVENY10'][loop_date]*(loop_date<strips30_start)+
			#	np.nan_to_num(pzc['SVENY30'][loop_date])*(loop_date>=strips30_start))
			cash=cash-ntemp*(
				pzc['SVENY10'][loop_date]*(loop_date<strips30_start)+
				np.nan_to_num(ppurch)*(loop_date>=strips30_start))
	
	## Mark the portfolio to market for every day in the loop; include also
	## a total return for a dca SP500 portfolio with reinvested dividends
	## Not sure that this if statement is the most robust, maybe fix later
	if bond_purch.size>0:
		telapsed=np.array((
			(pd.to_datetime(loop_date)-pd.to_datetime(bond_purch)
			).astype('timedelta64[D]')/365.25).astype(float))
		#print(telapsed)
		rem_dur=((strips_duration-telapsed)*(bond_purch>=strips30_start)+
			(10-telapsed)*(bond_purch<strips30_start))
		## plug remaining_duration into equation 22 from Gurkayanka; an array
		yeff=(zc.BETA0.loc[loop_date]+
			zc.BETA1.loc[loop_date]*(1-np.exp(-rem_dur/zc.TAU1.loc[loop_date])
			)/(rem_dur/zc.TAU1.loc[loop_date])+
			zc.BETA2.loc[loop_date]*((1-np.exp(-rem_dur/zc.TAU1.loc[loop_date])
			)/(rem_dur/zc.TAU1.loc[loop_date])-np.exp(-rem_dur/zc.TAU1.loc[loop_date]))+
			zc.BETA3.loc[loop_date]*((1-np.exp(-rem_dur/zc.TAU2.loc[loop_date])
			)/(rem_dur/zc.TAU2.loc[loop_date])-np.exp(-rem_dur/zc.TAU2.loc[loop_date]))
			)
		## value of the basket of bonds; new method checks out, gives similar
		## but slightly higher result than old method above (mar 29, 2021)
		peff=par_val/(1+yeff/100.0)**(rem_dur)
		bond_m2m=np.sum(peff*nbonds)
	else:
		bond_m2m=0
	## compute the total value of the portfolio now
	portfolio[i]=cash+spx['Close'][loop_date]*nshares+bond_m2m
	## total value of the benchmark
	buy_and_hold[i]=bah_cash+spx['Close'][loop_date]*bah_shares

## Use the last element of the portfolio array to get the value at the end
print("Total market value of portfolio: "+str(portfolio[-1]))
## print the total of the buy and hold benchmark:
print('DCA into SP500 and hold benchmark: '+str(buy_and_hold[-1]))
## The return of this strategy from the start; equivalent to putting the money
## in at the start and never adding more (dividends are reinvested)
#stock_portion=

## plot cycle start/end dates on fed funds/yc_indicator plot with green/red 
## circles
plt.plot(fedfunds_ffill.FEDFUNDS,'-k')
plt.plot(fedfunds_ffill.FEDFUNDS.loc[cycle_end_dates],'s',markerfacecolor='r',
	markeredgecolor='r')
plt.plot(fedfunds_ffill.FEDFUNDS.loc[cycle_start_dates],'>',markerfacecolor='g',
	markeredgecolor='g')
for xc in uninvert_dates:
	plt.axvline(x=xc,color='k',linestyle='-')
## save this fed funds figure??

## plot performance of the portfolio and the benchmark (use log plot!)
plt.figure()
plt.title('Market Timing using '+str(strips_duration)+
	'y STRIPS at first Uninversion')
plt.plot(yc_indicator.index,(portfolio),label='Market Timing: $'+
	str(int(round(portfolio[-1]))))
plt.plot(yc_indicator.index,buy_and_hold,label='Time in the SP500 (Only) $'+
	str(int(round(buy_and_hold[-1]))))
## plot some vertical lines; x=first uninversions
for xc in uninvert_dates:
	plt.axvline(x=xc,color='r',linestyle='-')
## plot the fed signal dates, when we sell bonds and go to stocks
for xc in fed_signal_dates:
	plt.axvline(x=xc,color='g',linestyle=':')
plt.yscale('log')
## Make a legend
plt.legend(loc='best')
plt.ylabel('Dollar Amount')
plt.xlabel('Date')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
plt.savefig('market_timing_'+str(strips_duration)+'y_STRIPS'+'.png')
plt.show()

