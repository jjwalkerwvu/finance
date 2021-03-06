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
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
from yahoo_csv_reader import yahoo_csv_reader
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
spx=yahoo_csv_reader('/home/jjwalker/Desktop/finance/data/stocks/^SP500TR','^SP500TR')
## load regular spx index:
sp500=yahoo_csv_reader('/home/jjwalker/Desktop/finance/data/stocks/^GSPC','^GSPC')
## get shiller data, either from file or from Shiller's website.
## If you don't put an actual filename, it will pull from Shiller's website.
shiller=shiller_excel_reader('/home/jjwalker/Desktop/finance/data/stocks/ie_data.xls')
## prepare a total return for sp500 based on Shiller dividend data (starts at 1871)
## intersection between shiller's excel sheet and the sp500
ii=sp500.index.intersection(shiller.index)
## union between shiller's excel sheet and the sp500 at correct start/end dates
iu=sp500.index.union(shiller[ii[0]:ii[1]].index)
## MUST USE COLUMN D, NOT DIVIDEND! DIVIDEND COLUMN CORRESPONDS TO INFL. ADJ.
#div=(shiller.D[ii[0]:]/12.0).resample('D').fillna(value=0).cumsum()
div=(shiller.D[ii[0]:]/12.0).resample('D').fillna(value=0)
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
datafile="/home/jjwalker/Desktop/finance/data/bonds/feds200628.csv"
zc=pd.read_csv(datafile,header=7)
zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
zc.set_index('Date',inplace=True)
## the SVENY variable names contain the zero-coupon yield, continuously 
## compounded
## the market price of the 30 year zc bond:
par_val=1000
## calculate market prices right now, before we even start:
pzc=par_val/((1+zc[zc.columns[67:97]]/200)**2)**(range(1,31))
## 30 year STRIPS start date
#strips30_start=pd.Timestamp('1985-12-02')
start_date=pd.to_datetime('1985-12-02')
strips_duration=26
pzc_buy=pzc[pzc.columns[strips_duration-1]]
## change to using the beta, tau, etc. parameters later, but use this for now
pzc_sell=pzc[pzc.columns[strips_duration-2]]

## For a given start date, need to buy 30 zc, sell one year later, repeat
## until desired time frame (in years)

## find the end of the data first then
end_date=zc.index[-1]
## maximum period that we can generate a return for, in days:
max_period=zc.index[-1]-start_date
## desired rolling period, in years:
rolling_period=30
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
sp_roll_array = pd.DatetimeIndex([get_business_day(d).date()+
	relativedelta(years=rolling_period) 
	for d in spx.index[:len(spx[:final_date])]])
sp_tot_return=(spx.Close[sp_roll_array].values)/(spx.Close[:final_date])
## Here is the shiller data; leave the stuff above for comparison.
shiller_roll_array = pd.DatetimeIndex([get_business_day(d).date()+
	relativedelta(years=rolling_period) 
	for d in sp500tr.index[:len(sp500tr[:final_date])]])
shiller_tot_return=((sp500tr.value_tr[shiller_roll_array].values)/
	(sp500tr.value_tr[:final_date]))

## Make the "main array", all days between start_date and final_date
roll_array = pd.DatetimeIndex([get_business_day(d).date() 
	for d in pd.date_range(start_date, final_date, freq='B')])

roll_return=np.zeros((len(roll_array)))

## this is a terrible solution, but works for now
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
	peff=par_val/(1+yeff/200.0)**(2*rem_dur)
	
	roll_return[i]=np.prod((peff.values)/(pzc_buy.loc[buy_date].values))
	
	#roll_return[i]=np.prod((pzc_sell.loc[sell_date].values)/
	#	(pzc_buy.loc[buy_date].values))

## Make a data frame of the rolling returns for simplicity:
zc_return=pd.DataFrame(roll_return,index=roll_array,columns=['zc_return'])
## format the total return of sp500tr:
#tot_return=(spx.Close[start_date:final_date].values/spx.Close[start_date:final_date].values)**(1/rolling_period)-1
## put roll_return and roll_array together into a timeseries
#plt.plot(zc_return,'-k');plt.show()
## CAGR:
plt.figure()
plt.title(str(rolling_period)+'-Year Rolling Return')
spx_cagr=(sp_tot_return**(1.0/rolling_period)-1)*100
zc_cagr=(zc_return**(1.0/rolling_period)-1)*100
shiller_cagr=(shiller_tot_return**(1.0/rolling_period)-1)*100
plt.plot(zc_cagr,'.b',label=str(strips_duration)+'y Annually Rolled Zero')
plt.plot(spx_cagr,'dk',markerfacecolor='k',markeredgecolor='k',
	label='SP500 Total Return');
plt.plot(shiller_cagr[start_date:],'sg',markerfacecolor='g',markeredgecolor='g',
	label='SP500 Total Return, Shiller Dividends')
plt.ylabel('CAGR %')
plt.xlabel('Date')
plt.legend(loc='best')
plt.tight_layout()
#plt.savefig(str(strips_duration)+'y_zc_and_sp500_'+str(rolling_period)+'y_rolling_return.png')
plt.show()
