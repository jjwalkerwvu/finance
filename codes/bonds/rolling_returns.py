"""
Created March 19, 2021

@author: Jeffrey J. Walker

rolling_returns.py
	This script returns the rolling returns of an asset given its time 
	series and rolling window period (1 year, 5 year, 30 year, etc.)

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
#from pandas.tseries.holiday import get_calendar, HolidayCalendarFactory,GoodFriday
from pandas.tseries.holiday import USFederalHolidayCalendar
## import the csv reader for FRED data, yahoo, etc.
sys.path.insert(1, '/Users/jeff/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
## yahoo_csv_reader replacement
from yahoo_stock_query import yahoo_stock_query
from shiller_excel_reader import shiller_excel_reader 


## A function to get the nearest business day
def get_business_day(date):
    while date.isoweekday() > 5 or date in cal.holidays():
        date += datetime.timedelta(days=1)
    return date

## Pick the calendar we want to use
cal = USFederalHolidayCalendar()
## possible different approach:
#cal=get_calendar('USFederalCalendar')

## spx total return
## 18 May 2021 - seems to track well with dividends from Shiller, so taking
## this out.
#spx=yahoo_csv_reader('/home/jjwalker/Desktop/finance/data/stocks/^SP500TR','^SP500TR')
## load regular spx index:
#sp500=yahoo_csv_reader('/home/jjwalker/Desktop/finance/data/stocks/^GSPC','^GSPC')
sp500=yahoo_stock_query('^GSPC')
## get shiller data, either from file or from Shiller's website.
## If you don't put an actual filename, it will pull from Shiller's website.
shiller=shiller_excel_reader('/Users/Jeff/Desktop/finance/data/stocks/ie_data.xls')
## prepare a total return for sp500 based on Shiller dividend data (starts at 1871)
## intersection between shiller's excel sheet and the sp500
ii=sp500.index.intersection(shiller.index)
## union between shiller's excel sheet and the sp500 at correct start/end dates
iu=sp500.index.union(shiller[ii[0]:ii[1]].index)
## MUST USE COLUMN D, NOT DIVIDEND! DIVIDEND COLUMN CORRESPONDS TO INFL. ADJ.
#div=(shiller.D[ii[0]:]/12.0).resample('D').fillna(value=0).cumsum()
#div=(shiller.D[ii[0]:]/12.0).resample('D').fillna(value=0,method='pad')
## A super annoying error in python 3, means I have to use some function like
## sum after resample, but before fillna or else it does not do what I want
div=(shiller.D[ii[0]:]/12.0).resample('D').sum().fillna(value=0)
## add sp500 closing price to the dividend with the common index
#sp500_tr=sp500.Close.loc[iu]+div.loc[iu]
## Or, use pd.merge_asof??
#sp500tr=pd.merge_asof(sp500,div,on=div.index)
## simplest method:
sp500tr=pd.concat([sp500.Close[ii[0]:ii[-1]],div],axis=1)
## simple loop for now:
nshares_tr=np.zeros(len(sp500tr))
value_tr=np.zeros(len(sp500tr))
## Start with one share
nshares_tr[0]=1
value_tr[0]=sp500tr.Close[ii[0]]
for i in range(1,len(sp500tr)):
	last_price=sp500tr.Close[:i][~np.isnan(sp500tr.Close[:i])][-1]
	nshares_tr[i]=nshares_tr[i-1]+(nshares_tr[i-1]*sp500tr.D[i])/last_price
	value_tr[i]=nshares_tr[i]*sp500tr.Close[i]	
## add these numpy arrays to the dataframe.
sp500tr['value_tr']=value_tr.tolist()
sp500tr['nshares_tr']=nshares_tr.tolist()
## Should I forward fill the previous sp500 close price to subsequent nans? 
print('SP500 total return from Shiller data now complete.')

## Zero coupon yield curve from FRED:
## read in data; have to use (7)th line as the header, I don't know why
#datafile="/home/jjwalker/Desktop/finance/data/bonds/feds200628.csv"
#zc=pd.read_csv(datafile,header=7)
#zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
#zc.set_index('Date',inplace=True)
url='https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv';
zc=pd.read_csv(url,sep=',',header=7)
zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
zc.set_index('Date',inplace=True)
## the SVENY variable names contain the zero-coupon yield, continuously 
## compounded
## the market price of the 30 year zc bond:
par_val=1000

## bid ask spread, in percentage/100
## Average bid ask spread of STRIPS; 3 ticks (32nds?) 
## (according to Daves and Ehrhardt, 1993) <- check this reference!
## Using 4 ticks to be generous, as in "TIPS-Treasury Bond Puzzle",
## Matthias Fleckenstein, Francis A. Longstaff and Hanno Lustig
## (presented by Rafael A. Porsani)
## I think ticks here assume a bond priced relative to 100, not 1000, but 
## check! It seems low to me; maybe I can turn it into a percentage of the 
## bond? I will check quotes at Etrade later to get an idea
## Brian Sack uses data from 1994-1999, and suggests that 4/32 ($0.125) may be
## narrow oOnly 5% of observations present reconstitution arbitrage 
## opportunity.)
## Quotes from Etrade:
## (I calculate the spread percentage as the difference between the bid and ask
## divided by the average (midpoint). Hence, the calculation goes:
## 2*(ask-bid)/(ask+bid)
## CUSIP: 912834WZ7
## 15 May 2051: bid: 55.694 (%1.978), offer: 56.387 (%1.936), min order:10
## Spread is %1.24 of bid-ask midpoint
## CUSIP: 912803FT5 (Definitely off the run)
## 15 Nov 2050: bid: 56.66 (%1.953), offer: 57.32 (%1.913), min order:25
## Spread is %1.16 of bid-ask midpoint
## Let's go with %1.25 for the spread, instead of 4/32nds for now until I 
## learn more.
## August 19 2021 spreads: 
## 1.2% for May 15 2021 maturity
## 1.16% for November 15 2050 maturity
## September 21 2021 spreads: 
## ~0.5% for May 15 2051 mat.
## October 13 2021 spreads:
## ~0.6% for February 15 2051 mat.
#spread=4/32.0*10
#spread=0.0125
spread=0.005
## I should also consider commissions; interesting article:
## https://www.chicagotribune.com/news/ct-xpm-1985-02-18-8501100081-story.html
## Interactive Brokers current charges: (bills/notes/bonds, does this include
## strips? $5.0 minimum order)
## 0.2 bps for first $1e6 face value and
## 0.01 bps for additional bonds purchased. 
#commission=0.002

## calculate market prices right now, before we even start:
#pzc=par_val/((1+zc[zc.columns[67:97]]/200)**2)**(range(1,31))
## The zero coupon data from the fed is quoted as continuous compounded, so
## we need to convert to semi-annual coupon compound convention for STRIPS
## prices.
pzc=par_val/((1+(np.exp(zc[zc.columns[67:97]]/200)-1))**2)**(range(1,31))
## 30 year STRIPS start date
#strips30_start=pd.Timestamp('1985-12-02')
start_date=pd.to_datetime('1985-12-02')
strips_duration=26
## desired rolling period, in years. If this is more than 30 years, need to
## change things in the code?
rolling_period=30
pzc_buy=pzc[pzc.columns[strips_duration-1]]
## change to using the beta, tau, etc. parameters later, but use this for now
pzc_sell=pzc[pzc.columns[strips_duration-2]]
## risk free total return if we just buy and hold for the duration of the bond,
## adjusted by the spread (only when opening the position)
rf_return=par_val/(pzc[pzc.columns[strips_duration-1]]+
                   spread*pzc[pzc.columns[strips_duration-1]])
## risk free return for the rolling period? Cap it at 30 years, even if 
## rolling period is longer
rf_rolling=par_val/pzc[pzc.columns[
    int((rolling_period>30)*30+(rolling_period<30)*rolling_period)-1]]


## For a given start date, need to buy 30 zc, sell one year later, repeat
## until desired time frame (in years)

## find the end of the data first then
end_date=zc.index[-1]
## maximum period that we can generate a return for, in days:
max_period=zc.index[-1]-start_date
## incremental array to use for each 1 year return period; 
## i.e., add this array as a relative delta to each 30 year start date
## Maybe pd.DateOffset is better?
arr=np.array(range(rolling_period))+1

## final date that we can calculate a return for:
final_date=end_date-relativedelta(years=rolling_period)
## is the rolling period smaller than the max period?
domain_check=final_date>start_date

## Cant figure out a good way to do this with built in functions...
#date_array=pd.bdate_range(start=start_date,end=start_date+relativedelta(years=rolling_period+1),freq='BA',holidays=USFederalHolidayCalendar)

## Quick setup for finding rolling returns for sp500; change later when
## shiller_excel_reader.py is working properly
#sp_roll_array = pd.DatetimeIndex([get_business_day(d).date()+
#	relativedelta(years=rolling_period) 
#	for d in spx.index[:len(spx[:final_date])]])
#sp_tot_return=(spx.Close[sp_roll_array].values)/(spx.Close[:final_date])
## Here is the shiller data; leave the stuff above for comparison.
## add the relative delta inside the get business day function, so we work
## backward from the dates that have a valid date 30 years in the future
shiller_roll_array = (pd.DatetimeIndex([get_business_day(d+
	relativedelta(years=rolling_period)).date() 
	for d in sp500tr[:final_date].index]).unique()).intersection(
    sp500tr.value_tr.index)
## take those dates, and go 30 years backward to map to nearest business day,
## even if there are duplicates
#sp500_dates=pd.DatetimeIndex([get_business_day(d-
#    relativedelta(years=rolling_period)).date()
#    for d in shiller_roll_array])
sp500_dates=pd.DatetimeIndex([(d-relativedelta(years=rolling_period)).date()
    for d in shiller_roll_array])

## Have to make changes to old code to make it work
#shiller_tot_return=((sp500tr.value_tr[shiller_roll_array].values)/
#	(sp500tr.value_tr[:final_date]))
shiller_numerator=sp500tr.value_tr.loc[shiller_roll_array]
shiller_tot_return=shiller_numerator.values/sp500tr.value_tr[sp500_dates]

## Make the "main array", all days between start_date and final_date
roll_array = pd.DatetimeIndex([get_business_day(d).date() 
	for d in pd.date_range(start_date, final_date, freq='B')])
## could I also just use:
#roll_array = pd.DatetimeIndex([get_business_day(d).date() 
#	for d in zc[start_date:final_date].index])    

roll_return=np.zeros((len(roll_array)))

## this is a terrible solution, but works for now
## change this so that we hold the bond for one year exactly, buy next bond
## 5 days after the transaction settles; capital gains would be long term
## 19 August 2021: Trying to incorporate spread into the calculations;
## Assuming that Refet S. Gurkaynak, Brian Sack, and Jonathan H. Wright
## use midpoint of bid ask spread in Fed publication 2006-28; check again!
for i in range(len(roll_array)):
	## best way to make a "yearly" array?
	buy_date=pd.DatetimeIndex([
		get_business_day(roll_array[i]+relativedelta(years=j)) 
		for j in range(rolling_period)])
	
	sell_date=pd.DatetimeIndex([
		get_business_day(
		roll_array[i]+relativedelta(years=j+1)-relativedelta(days=5)) 
		for j in range(rolling_period)])
	
	## Use Svensson model to obtain bond price.
	thold=(sell_date.to_pydatetime()-buy_date.to_pydatetime()).astype(
		'timedelta64[D]').astype(float)/365.25
	rem_dur=strips_duration-thold
	yeff=(zc.BETA0.loc[sell_date]+
			zc.BETA1.loc[sell_date]*(1-np.exp(-rem_dur/zc.TAU1.loc[sell_date])
			)/(rem_dur/zc.TAU1.loc[sell_date])+
			zc.BETA2.loc[sell_date]*((1-np.exp(-rem_dur/zc.TAU1.loc[sell_date])
			)/(rem_dur/zc.TAU1.loc[sell_date])-np.exp(-rem_dur/zc.TAU1.loc[sell_date]))+
			zc.BETA3.loc[sell_date]*((1-np.exp(-rem_dur/zc.TAU2.loc[sell_date])
			)/(rem_dur/zc.TAU2.loc[sell_date])-np.exp(-rem_dur/zc.TAU2.loc[sell_date]))
			)
    ## yeff must be converted from continuous compounding convention to 
    ## semi-annual coupon equivalent compounding convention!	
	peff=par_val/(np.exp(yeff/200.0))**(2*rem_dur)
    #peff=par_val/(1+yeff/200.0)**(2*rem_dur)
    
    ## incorporate bid ask spread of 4/32 into each transaction;
    ## so pay 2/32 more and sell for 2/32 less
    ## The Gurkaynak yield dataset uses midpoint of bid ask spread, so add 
    ## HALF the spread when buying and deduct this value when selling.
    
	roll_return[i]=np.prod((peff.values-peff.values*spread/2)/
                        (pzc_buy.loc[buy_date].values+
                         pzc_buy.loc[buy_date].values*spread/2))
	
	#roll_return[i]=np.prod((pzc_sell.loc[sell_date].values)/
	#	(pzc_buy.loc[buy_date].values))

## Make a data frame of the rolling returns for simplicity:
zc_return=pd.DataFrame(roll_return,index=roll_array,columns=['zc_return'])

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Now, calculate rolling returns over the entire period for both zero coupon
## bonds and sp500

## the number of years between the start date and the end date
## We use this number as a loop counter
total_years=int((end_date-start_date).days//365.25)
## temp fix; shiller data does not update often, so use last valid date of
## Shiller Data as the end_date?


sell_arr=[get_business_day(end_date-relativedelta(years=j)) 
         for j in range(total_years)][::-1]
buy_arr=[get_business_day(end_date-relativedelta(years=j)) 
         for j in range(1,total_years+1)][::-1]

## array for zero coupon returns (of the strip_duration) as measured from the 
## most recent date where we have data
zc_point=(pzc_sell.loc[sell_arr[::-1]]/pzc_buy.loc[buy_arr[::-1]].values)
## And now, the yearly returns, working backward from the current date
zc_pr=[np.prod(zc_point[:i]) for i in range(1,len(zc_point)+1)]
## array that counts the years
pr_years=np.arange(1,total_years+1)
## the cagr for each cumulative year period (1 year, 2 year, etc.)
zc_pr_cagr=(zc_pr**(1.0/pr_years)-1)*100


## What does this correspond to again?
# sp500_point=(sp500tr.value_tr.loc[sell_arr[::-1]]/
#        sp500tr.value_tr.loc[buy_arr[::-1]].values)
# sp500_pr=[np.prod(sp500_point[:i]) for i in range(1,len(sp500_point)+1)]
# sp500_pr_cagr=(sp500_pr**(1.0/pr_years)-1)*100


## The idea for the plot:
#plt.plot(pr_years,zc_pr_cagr,'bd')
#plt.plot(pr_years,sp500_pr_cagr,'sg')

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## format the total return of sp500tr:
#tot_return=(spx.Close[start_date:final_date].values/spx.Close[start_date:final_date].values)**(1/rolling_period)-1
## put roll_return and roll_array together into a timeseries
#plt.plot(zc_return,'-k');plt.show()
## CAGR:
plt.figure()
plt.title(str(rolling_period)+'-Year Rolling Return')
#spx_cagr=(sp_tot_return**(1.0/rolling_period)-1)*100
zc_cagr=(zc_return**(1.0/rolling_period)-1)*100
## include also the zero coupon cagr if held to maturity for duration chosen
rf_cagr=(rf_return**(1.0/strips_duration)-1)*100
## zero coupon cagr, a risk free rate, but for the rolling period
rf_rolling_cagr=(rf_rolling**(1.0/rolling_period)-1)*100
shiller_cagr=(shiller_tot_return**(1.0/rolling_period)-1)*100
plt.plot(zc_cagr,'.b',label=str(strips_duration)+'y Annually Rolled Zero')
#plt.plot(spx_cagr,'dk',markerfacecolor='k',markeredgecolor='k',
#	label='SP500 Total Return');
plt.plot(shiller_cagr[start_date:],'sg',markerfacecolor='g',markeredgecolor='g',
	label='SP500 Total Return, Shiller Dividends')
plt.plot(rf_rolling_cagr[start_date:final_date],'^r',markerfacecolor='r',
	markeredgecolor='r',label=(str(rolling_period)+'y Risk-Free STRIPS'))
plt.ylabel('CAGR %')
plt.xlabel('Date')
plt.legend(loc='best')
plt.tight_layout()
plt.savefig(str(strips_duration)+'y_zc_and_sp500_'+str(rolling_period)+
            'y_rolling_return.png')
plt.show()

## Also plot the "telltale chart", or the ratio of total zc return to spx.
## Might be a good idea to also find the percentage of times that zc beats
## spx for this collection of data
plt.figure()
plt.title(str(strips_duration)+'y STRIPS'+' Total Return Telltale Chart, '+
          str(rolling_period)+'y Rolling Period')
plt.plot(zc_return.zc_return/shiller_tot_return,'ob',
         label=str(strips_duration)+'y rolled zero/SP500')
plt.plot(pd.Series(data=np.ones(len(shiller_tot_return)),
                   index=shiller_tot_return.index),'.k')
plt.xlim(left=zc_return.index[0],right=zc_return.index[-1])
plt.ylabel('STRIPS/SP500 Total Return')
plt.xlabel('Date')
plt.savefig(str(strips_duration)+'y_zc_and_sp500_'+str(rolling_period)+
            'y_rolling_return_telltale_chart.png')
plt.show()

## plot the sp500 cagr minus risk free rate?
## Use the risk free rate corresponding to the investing timeframe 
## (rolling period)
plt.figure()
plt.title(str(rolling_period)+'y ERP')
plt.plot(shiller_cagr-rf_rolling_cagr,'-r')
plt.plot(pd.Series(
    data=np.zeros(len(rf_rolling_cagr)),
    index=rf_rolling_cagr.index),'-k')
plt.xlim(left=zc_return.index[0],right=zc_return.index[-1])
plt.ylabel('SP500 CAGR - '+str(rolling_period)+'y STRIPS CAGR')
plt.xlabel('Date')
plt.savefig('SP500'+str(rolling_period)+
            'y_erp_based_on_STRIPS.png')
plt.show()




