"""
Created on Sunday, July 11, 2021

@author: Jeffrey J. Walker

    spx_chain.py
        This is a script based on the earlier multi_chain_test.py, but 
        adapted specifically for spx options, to get implied interest rate,
        implied dividends and then spx risk neutral probability distribution.
        The method:
        1.) Get all spx option chains
        2.) Match the option chains that correspond to expiration dates of all
            futures contracts within the next year
        3.) With forward prices from these option chains, use put-call parity
            to obtain risk free rates across all strikes!
        4.) Get the overnight rate from nyfed:
    
            (If nearest term expiration is more than one night, assume that 
             we roll at the overnight rate for the required number of nights
             until expiration of nearest term spx options)
        5.) Now, use cubic spline to interpolate (1-3 day rate) out to 
            interest rate corresponding to furthest ES future contract 
            available (~1 year). 
            This interest rate can be used to price other options/get RNDs.
            Interpolate forwards
        6.) Get implied dividend rate for spx options
        7.) Now, get RND for spx; Use interpolated forward price to get c(k=0)
            and p(k->infty) values, needed for monotonic interp. method.
        Consider including the scraping of bond prices from 
        wsj_bond_scraper.py for zero-coupon yields and adding this to the 
        saved dataframe(?)
		A good test would be to plot 3d volatility surfaces and start to 
		think about about Malz and Tiang methods for computing implied prob.

"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
from matplotlib.colors import LogNorm
## I wanted to use scipy.interpolate.CubicSpline, but I cannot get it to import
#from scipy.interpolate import splev, splrep
from scipy.interpolate import interp1d
from scipy.interpolate import CubicSpline
## for monotonic interpolation:
from scipy.interpolate import PchipInterpolator
#from scipy.interpolate import Akima1DInterpolator
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.tz import *
import calendar
import time
import os
import sys
import json
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/Users/Jeff/Desktop/finance/codes/data_cleaning')
from yahoo_option_chain_multi_exp import yahoo_option_chain_multi_exp
from YieldCurve import FedFundsFutures
## insert the path corresponding to bs_analytical solver; we may need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/Users/Jeff/Desktop/finance/codes/options')
from bs_analytical_solver import bs_analytical_solver
from implied_volatility import implied_volatility
## Want to execute in python shell? then use:
#execfile('/home/jjwalker/Desktop/finance/codes/options/multi_chain_test.py')

#ticker='^XSP'
ticker='^SPX'
#ticker='GME'
## days until expiry
#dte=150
## What is the path to the option chain?
## DO NOT NEED '/' AT THE END!
path='/Users/Jeff/Desktop/finance/data/options'
#t_plus_30=pd.to_datetime('today').now()+timedelta(days=dte)
#input_date=time.mktime(t_plus_30.timetuple())

## read from a specific file
#filename=path+'/2021/04/23/2021_04_23_13_55_^SPX_full_chain.txt'
#filename=path+'/2021/04/16/2021_04_16_17_11_^SPX_full_chain.txt'

#tnow,expiry_dates,spot_price,df=yahoo_option_chain_multi_exp(filename,ticker,scrape=False)
tnow,expiry_dates,spot_price,df=yahoo_option_chain_multi_exp(path,ticker,
                                                             scrape=True)

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Not sure how to best structure this, since the time when prices are queried
## is important (want to get futures prices as close in time as possible to
## when we get option prices)
## GET FUTURES PRICES FROM YAHOO FINANCE

## futures quarterly expiration codes:
futures_months=[3,6,9,12]
futures_codes=['H','M','U','Z']

closest_month=min(futures_months,key=lambda x:(tnow.month-x)>0)

## es futures expiration month and year as integers
exp_months=(futures_months[futures_months.index(closest_month):]+
              futures_months[:futures_months.index(closest_month)])
exp_years=([tnow.year]*len(
    futures_months[futures_months.index(closest_month):])+
    [tnow.year+1]*len(
    futures_months[:futures_months.index(closest_month)]))

## es futures expiration month and year as strings; needed for querying yahoo
query_months=(futures_codes[futures_months.index(closest_month):]+
              futures_codes[:futures_months.index(closest_month)])
query_years=([str(tnow.year)[-2:]]*len(
    futures_months[futures_months.index(closest_month):])+
    [str(tnow.year+1)[-2:]]*len(
    futures_months[:futures_months.index(closest_month)]))

es_prices=np.zeros(len(futures_months))
## Will need to insert the forward price corresponding to nearest term spx
## option expiration
es_expiry_dates=np.array([])

## Need expiration dates!
## third friday of the month at index open, which for es futures is 9:30am
c = calendar.Calendar(firstweekday=calendar.SUNDAY)

# loop to extract the next year's futures prices
for i in range(len(futures_months)):
    es_url=('https://query2.finance.yahoo.com/v10/finance/quoteSummary/ES'+
            query_months[i]+query_years[i]+'.CME?modules=price')
    #print(es_url)
    json_data=pd.read_json(es_url)
    es_prices[i]=json_data.quoteSummary.result[0]['price']['regularMarketPrice']['raw']
    datetime.utcfromtimestamp(json_data.quoteSummary.result[0]['price']
                     ['regularMarketTime'])
    
    monthcal = c.monthdatescalendar(exp_years[i],exp_months[i])
    third_friday = [day for week in monthcal for day in week if \
                    day.weekday() == calendar.FRIDAY and \
                    day.month == exp_months[i]][2]
    ## third_friday is a datetime.date object, which is why I have to do all 
    ## the weird shuffling below with combining a datetime.date and 
    ## datetime.time, then adding 9.5 (corresponding to 9:30 am market open)
    es_expiry_dates=np.append(es_expiry_dates,
        datetime.combine(third_friday,datetime.min.time())+
        timedelta(hours=9.5))

## convert es_expiry_dates to pandas datetime.
## I think I can localize here?
es_expiry_dates=pd.to_datetime(es_expiry_dates).tz_localize('US/Eastern')
## And now get the time to expiry of the next 4 quarterly es futures contracts
## in days
es_texp=np.array((es_expiry_dates-tnow)/np.timedelta64(1,'D'))

## get the (maximum?) overnight rate from marketwatch
headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'}
url='https://www.marketwatch.com/investing/InterestRate/USDR-TU1?countryCode=MR'
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
soup=BeautifulSoup(webpage, 'html5lib')
## the maximum overnight rate (guarunteed rate)
dr=float(soup.find('td',{"class": "table__cell u-semi"}).get_text().replace(
    '%',''))

## What about the secured overnight funding rate?
## When should sofr be used? - SOFR arrangements must be collateralized
#sofr_url='https://www.marketwatch.com/investing/interestrate/ussofr-fds?countrycode=mr'
#req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
#webpage = urlopen(req).read()
#soup=BeautifulSoup(webpage, 'html5lib')
#sofr=float(soup.find('td',{"class": "table__cell u-semi"}).get_text().replace(
#    '%',''))

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Continue with option chain cleaning after getting futures quotes.
## In this version, Do I want to include only strikes where there are valid 
## strikes for puts and calls?
## Do reindexing and cleaning in here:
## Do I need to add the 16 hour time delta?
df.expiration=(df.expiration.apply(lambda d: datetime.utcfromtimestamp(d))+
               timedelta(hours=16))	
## Last trade dates may have NaN entries, so clean these outside of here?
#df.lastTradeDate_c=df.lastTradeDate_c.apply(lambda d: datetime.utcfromtimestamp(d))+timedelta(hours=16)
#df.lastTradeDate_p=df.lastTradeDate_p.apply(lambda d: datetime.utcfromtimestamp(d))+timedelta(hours=16)
df.set_index(['expiration','strike'],inplace=True)
df=df.reindex(pd.MultiIndex.from_product(
	[df.index.levels[0],df.index.levels[1].unique()],
	names=['expiration','strike']),fill_value=np.NaN)

## write path for plots
write_path=path+tnow.strftime("/%Y/%m/%d")

## recalculate tnow if necessary:
timezone='CET'
#tnow=pd.to_datetime('today').now().tz_localize(timezone).tz_convert('US/Eastern')
## For now, convert utc timestamp to datetime; put into yahoo_option_chain_multi_exp.py later
#dexp=(pd.DatetimeIndex([
#	datetime.utcfromtimestamp(date) for date in df.index.levels[0]]))
#exp_dates=np.array(df_calls.index.levels[0])
dexp=np.array(df.index.levels[0])
## texp, in days, float array?
#tnow=tnow.tz_localize('US/Eastern')
texp=np.array((df.index.levels[0].tz_localize('US/Eastern')-tnow)/np.timedelta64(1,'D'))

## A list/array with all the expiration dates/time to expiration:
## All possible strikes:
#all_strikes=np.unique(df.index.get_level_values(1))
all_strikes=df.index.levels[1].unique()
## the basic pattern for an expiration, strike:
#df_calls.loc[(exp,strike)]
## get the strike index for a given exp:
#df_calls.loc[exp].index
## get all values of variable for all strikes:
#df_calls[df_calls.index.get_level_values(1)==all_strikes].ask

## Nearest "term" forward is the forward price constructed from the nearest 
## term spx option chain; 
## assume the dividend is zero?? How to address this as dividends are paid??
## We can assume that we can roll at the overnight rate
## F_nearest should be very close to the spot_price.
F_nearest=spot_price*np.exp((dr/100)*texp[0]/365.24)

## find option expirations that match the futures expirations;
## just take the date component of the timestamp
## OR: (LAZY)
## Find nearest value of texp to each entry in es_texp; this will be an spx 
## option chain corresponding to quarterly expiration.
## replace texp with es_texp?
trep_index=np.array([])
for i in range(len(es_texp)):
    es_expiry_dates[i].date()
    ## cap the expiration date on texp:
    trep_index=np.append(trep_index,np.where(
        abs(es_texp[i]-texp)==min(abs(es_texp[i]-texp)))[0][0])
trep_index=trep_index.astype(int)
## replace some of the option chain dates with the more correct dates, from
## futures quotes
texp[trep_index]=es_texp

## interpolate futures dates up until approx. 1 year
forward_cs=CubicSpline(np.insert(es_texp,0,texp[0]),
                       np.insert(es_prices,0,F_nearest),bc_type='clamped')
tcap=texp[texp<=es_texp[-1]]
## An easy to use index that only contains option strikes for the available
## futures prices (~1 year)
tcap_index=np.arange(len(tcap))
F_interp=forward_cs(texp[texp<=es_texp[-1]])
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Get discount rates using one of my YieldCurve class
ff_data=FedFundsFutures.get_fedfunds_futures(write_path=path,
                                             write_to_file=True)
## Use simple, linear interpolation to fill in interest rates for all option
## expirys.
## I used extrapolation for the fill value in order to suppress errors for now,
## but this can get you into trouble later!
ff_yield_interp=interp1d(ff_data.market_df.t_settlement.values*365.24,
                         ff_data.market_df.implied_yield.values,
                         fill_value="extrapolate")

## resulting interest rate will already be continuously compounding and in 
## (decimal) form, ready to use as a discount rate.
rintp=ff_yield_interp(texp)

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Dataframe entries should be "cleaned" with the following conditions:
## (As previously used (successfully?) in my simpler script 'iv_snapshot.py')
## IV constrainted to be >=0 and no Nans
## Volume: no Nans
## Bid and ask are not equal to zero
## how can I fill with nans instead?
#test=df_calls.reindex(pd.MultiIndex.from_product(
#	[df_calls.index.levels[0],df_calls.index.levels[1].unique()],
#	names=['expiration','strike']),fill_value=np.NaN)

## some test arrays:
open_interest_c=df.openInterest_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
open_interest_p=df.openInterest_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
volume_c=df.volume_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
volume_p=df.volume_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
iv_c=df.impliedVolatility_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
iv_p=df.impliedVolatility_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
ask_c=df.ask_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
ask_p=df.ask_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
bid_c=df.bid_c.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
bid_p=df.bid_p.values.reshape(len(df.index.levels[0]),
	len(df.index.levels[1]))
## A meshgrid to make 3d plots?
x,y=np.meshgrid(df.index.levels[1],texp)

## How can I make a 2d array using this logic?
## Should I use np.ma.where instead?
## IV cannot be zero.
## Also, we should ensure that the ask/bid price of options has a non-zero
## intrinsic value for (S-k)>0. Otherwise arbitrage is possible.
## How to implement this? Something like: ask_c<np.max(spot_price-x,0)
unfair_call=((ask_c<(spot_price-x))&(x<spot_price))
unfair_put=((ask_p<(x-spot_price))&(x>spot_price))
## I was also considering enforcing some kind of monotonicy for ask/bid data
clean_conditions_c=((np.isnan(volume_c))|(iv_c<=0)|(ask_c<=0)|(bid_c<=0)|
                    (np.isnan(open_interest_c))|(unfair_call))
clean_conditions_p=((np.isnan(volume_p))|(iv_p<=0)|(ask_p<=0)|(bid_p<=0)|
                    (np.isnan(open_interest_p))|(unfair_call))

## special clean condition to keep only the strikes where there is valid data
## for puts and calls
clean_all=clean_conditions_c|clean_conditions_p

## clean all the relevant arrays according to our conditions
ask_clean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,ask_c))
bid_clean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,bid_c))
iv_clean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,iv_c))
oi_clean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,
                                                   open_interest_c))
xclean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,x))
yclean_c=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_c,y))
##
ask_clean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,ask_p))
bid_clean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,bid_p))
iv_clean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,iv_p))
oi_clean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,
                                                   open_interest_p))
xclean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,x))
yclean_p=np.ma.masked_invalid(np.ma.masked_where(clean_conditions_p,y))
## Arrays cleaned for puts and calls, together, which only keeps the strikes
## for which there is valid data
## call data
ask_all_c=np.ma.masked_invalid(np.ma.masked_where(clean_all,ask_c))
bid_all_c=np.ma.masked_invalid(np.ma.masked_where(clean_all,bid_c))
iv_all_c=np.ma.masked_invalid(np.ma.masked_where(clean_all,iv_c))
oi_all_c=np.ma.masked_invalid(np.ma.masked_where(clean_all,
                                                   open_interest_c))
## put data
ask_all_p=np.ma.masked_invalid(np.ma.masked_where(clean_all,ask_p))
bid_all_p=np.ma.masked_invalid(np.ma.masked_where(clean_all,bid_p))
iv_all_p=np.ma.masked_invalid(np.ma.masked_where(clean_all,iv_p))
oi_all_p=np.ma.masked_invalid(np.ma.masked_where(clean_all,
                                                   open_interest_p))
x_all=np.ma.masked_invalid(np.ma.masked_where(clean_all,x))
y_all=np.ma.masked_invalid(np.ma.masked_where(clean_all,y))

## Put call parity to obtain implied interest rates/forwards from these chains
## Basic Formula: r_imp=(np.log((F_interp-k)/(c-p+k-k)))/T
## Loop over the dates for which we have futures prices or interpolated 
## futures prices and compute the implied interest rates.
r_imp=np.zeros(len(trep_index))
div_imp=np.zeros(len(r_imp))
for i in range(len(trep_index)):
    ## compute average value of c-p+k, based on bid-ask spread midpoint
    call_put=((ask_all_c[i,:][~ask_all_c[i,:].mask].data+
            bid_all_c[i,:][~bid_all_c[i,:].mask].data)/2-
           (ask_all_p[i,:][~ask_all_p[i,:].mask].data+
            bid_all_p[i,:][~bid_all_p[i,:].mask].data)/2)
    ## Alternative: buy c-p or sell c-p
    call_put_buy=(ask_all_c[i,:][~ask_all_c[i,:].mask].data+
                  bid_all_p[i,:][~bid_all_p[i,:].mask].data)
    call_put_sell=(bid_all_c[i,:][~bid_all_c[i,:].mask].data+
                  ask_all_p[i,:][~ask_all_p[i,:].mask].data)
    ## Get the linear regression of this line; 
    ## then use exp(r_imp*T)(beta*k+alpha)+k to get r_imp,
    ## satisfied by r_imp=-np.log(-beta)/T
    ## as per this page: 
    ## https://quant.stackexchange.com/questions/48781/implied-interest-rate-using-put-call-parity
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        x_all[i,:][~x_all[i,:].mask].data,call_put)
    ## pick a value for the strike price that is guaranteed to have (F-k)>0
    k=all_strikes[0]
    ## Pick lowest available strike
    #k=x_all[i,:][~x_all[i,:].mask].data[0]
    ## put it all together.
    ## Divide tcap by 365 because it is given in days.
    #r_imp[i]=np.log((F_interp[i]-k)/(denom-k))/(tcap[i]/365.25)
    #r_imp[i]=-np.log(-slope)/(tcap[i]/365.25)
    r_imp[i]=np.log((es_prices[i]-k)/(intercept+slope*k))/(es_texp[i]/365.25)
    div_imp[i]=-np.log((intercept+slope*k+
                        k*np.exp(-r_imp[i]*es_texp[i]/365.25))
                       /spot_price)/(es_texp[i]/365.25)
    
#np.log((F_interp[1]-x_all[1,:][~x_all[1,:].mask].data)/((ask_all_c[1,:][~ask_all_c[1,:].mask].data+bid_all_c[1,:][~bid_all_c[1,:].mask].data)/2-(ask_all_p[1,:][~ask_all_p[1,:].mask].data+bid_all_p[1,:][~bid_all_p[1,:].mask].data)/2))/texp[1]

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## 2022 Jan 7: Now that I have a reliable method to obtain risk-free rates, I
## can now solve for forward price and implied dividends!

fprice=np.zeros(len(texp))
div_imp=np.zeros(len(texp))
for i in range(len(df.index.levels[0])):
    ## Do our best to compute the forward.
    near_atm=(x_all[i,:].data<=1.1*spot_price)&(
        x_all[i,:].data>=0.9*spot_price)
    fprice_vector=x_all[i,:].data[near_atm]+np.exp(rintp[i]*texp[i]/365.24)*(
        (ask_all_c[i,:].data[near_atm]+bid_all_c[i,:].data[near_atm]-
         bid_all_p[i,:].data[near_atm]-ask_all_p[i,:].data[near_atm])/2)
    
    fprice[i]=fprice_vector[~np.isnan(fprice_vector)].mean()
    div_imp[i]=-365.24/texp[i]*np.log(fprice[i]*np.exp(-rintp[i]*texp[i]/365.24)/spot_price)
    

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Compute IV manually; vectorize in the future.

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

## Now that iv interpolation is complete, we use second derivative of BS
## model
ask_iv_calc_c=np.zeros((len(df.index.levels[0]),len(df.index.levels[1])))
bid_iv_calc_c=np.zeros((len(df.index.levels[0]),len(df.index.levels[1])))
for i in range(len(df.index.levels[0])):
    for j in range(len(df.index.levels[1])):
        if (np.ma.is_masked(ask_clean_c[i,j]) and 
            np.ma.is_masked(xclean_c[i,j]))==False:
            try:
                ask_iv_calc_c[i,j]=implied_volatility(
                    ask_clean_c[i,j],
                    spot_price,
                    xclean_c[i,j],
                    rintp[i],
                    texp[i]/365.24,
                    iv_clean_c[i,j],
                    o_type='c')
                
                bid_iv_calc_c[i,j]=implied_volatility(
                    bid_clean_c[i,j],
                    spot_price,
                    xclean_c[i,j],
                    rintp[i],
                    texp[i]/365.24,
                    iv_clean_c[i,j],
                    o_type='c')
            except:
                ask_iv_calc_c[i,j]=np.nan
        else:
            ask_iv_calc_c[i,j]=np.nan
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## multiplier to extend the new basis beyond all_strikes[-1]
mb=3
spacing=int(mb*all_strikes[-1])+1
new_basis=np.linspace(0,mb*all_strikes[-1],num=spacing)   
iv_interp_c=np.zeros((len(df.index.levels[0]),len(new_basis)))
iv_interp_p=np.zeros((len(df.index.levels[0]),len(new_basis)))
#
call_interp=np.zeros((len(df.index.levels[0]),len(new_basis)))
cumul_dist_c=np.zeros((len(df.index.levels[0]),len(new_basis)))
for i in range(len(df.index.levels[0])):
    ## Further cleaning; maybe some of this can be done outside the loop?
    ## get rid of any masked elements:
    # u=xclean_c[i,:][~iv_clean_c[i,:].mask].data
    # v=iv_clean_c[i,:][~iv_clean_c[i,:].mask].data
    u=xclean_c[i,:][~np.isnan(ask_iv_calc_c[i,:])]
    v=ask_iv_calc_c[i,:][~np.isnan(ask_iv_calc_c[i,:])]
    ## Have to do this for the clamping, for now
    ## Inserting 0 should always work, since 0 is almost never a strike
    #u=np.insert(u,0,0)
    #u=np.append(u,all_strikes[-1]+100)
    #v=np.insert(v,0,v[0])
    #v=np.append(v,v[-1])
    cs=CubicSpline(u,v,bc_type='clamped')
    iv_interp_c[i,:][(new_basis>=u[0])&(new_basis<=u[-1])]=cs(
        new_basis[(new_basis>=u[0])&(new_basis<=u[-1])])
    ## make sure the iv is constant outside the data region.
    iv_interp_c[i,:][new_basis<u[0]]=v[0]
    iv_interp_c[i,:][new_basis>u[-1]]=v[-1]
    for j in range(len(new_basis)):
        call_interp[i,j],second_der,delta,gamma,vega,theta,rho=(
            bs_analytical_solver(
                spot_price, 
                new_basis[j], 
                rintp[i], 
                texp[i]/365.24, 
                iv_interp_c[i,j], 
                o_type='c'))
        call_interp[i,j],second_der,delta,gamma,vega,theta,rho=(
            bs_analytical_solver(
                spot_price, 
                new_basis[j], 
                rintp[i], 
                texp[i]/365.24, 
                iv_interp_c[i,j], 
                o_type='c'))
    temp=1+np.exp(rintp[i]*texp[i]/365.24)*np.diff(call_interp[i,:])/np.diff(
        new_basis)
    temp=np.append(temp,1)
    cumul_dist_c[i,:]=temp
    print('Finished iteration: '+str(i))
    ## now for puts
    
    
x_interp,y_interp=np.meshgrid(new_basis,texp)
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Monotonic interpolation of calls and puts to get cumulative risk neutral
## distribution function.

## set up solution arrays
call_m_interp=np.zeros((len(df.index.levels[0]),len(new_basis)))
call_deriv=np.zeros((len(df.index.levels[0]),len(new_basis)))
put_interp=np.zeros((len(df.index.levels[0]),len(new_basis)))
put_deriv=np.zeros((len(df.index.levels[0]),len(new_basis)))
## array for IMPLIED INTEREST RATE!!!
## based off calls
r_c=np.zeros(len(df.index.levels[0]))
## based off puts
r_p=np.zeros(len(df.index.levels[0]))
## plan: calls have no extrinsic value at k=0, and c=0 for k -> infty
## puts have no extrinsic value for k -> infty, and p=0 for k=0
for i in range(len(df.index.levels[0])):
    u=xclean_c[i,:][~ask_clean_c[i,:].mask].data
    v=ask_clean_c[i,:][~ask_clean_c[i,:].mask].data
    ## Here is where we need to insert endpoings for the call data
    ## In the limit of k=0, call options have little or no extrinsic value;
    ## May want to rethink this at a later date just to confirm!
    ## My solution to the endpoint problem for now.
    ## Inserting 0 should always work with this command, since 0 is almost 
    ## never a strike
    u=np.insert(u,0,0)
    ## Append the last element of the new basis?
    u=np.append(u,new_basis[-1])
    ## At strike k=0, call option has no extrinsic value
    v=np.insert(v,0,spot_price)
    ## As strike price goes to infinity, call option extrinsic value goes to 0
    ## but market makers would never sell for less than 0.05
    v=np.append(v,0.05)
    ## use a minus sign so that v is monotonically increasing instead of 
    ## decreasing; multiply by -1 later.
    call_mint=PchipInterpolator(x=u,y=v)
    call_m_interp[i,:]=call_mint(new_basis)
    ## get first derivative of the monotonic interpolation
    call_deriv[i,:]=call_mint(new_basis,nu=1)
    
    ## find the forward price, get interest rate (NO DIVIDENDS??)
    f_price=new_basis[call_deriv[i,:]>=
                      (call_deriv[i,:][0]-call_deriv[i,:][-1]/2)][0]
    r_c[i]=np.log(f_price/spot_price)
    


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Various plots
## Maybe a simpler plot to use in the meantime until I get surfaces working?
## color array (try cool and hot colormap?)
#c=np.tile(texp)
plt.figure()
plt.subplot(1,2,1)
plt.title(ticker+' Calls')
plt.scatter(xclean_c.flatten(),ask_clean_c.flatten(),
	c=yclean_c.flatten(),
	cmap='cool',edgecolor='none',norm=LogNorm())
cbar=plt.colorbar(orientation="horizontal")
cbar.set_label('DTE')
plt.yscale('log')
## use zero bound for strikes
plt.xlim(0)
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.ylabel('Ask Premium')
plt.xlabel('Strike')
## subplot for puts?
plt.subplot(1,2,2)
plt.title(ticker+' Puts')
plt.scatter(xclean_p.flatten(),ask_clean_p.flatten(),
	c=yclean_p.flatten(),
	cmap='hot',edgecolor='none',norm=LogNorm())
cbar=plt.colorbar(orientation="horizontal")
cbar.set_label('DTE')
plt.yscale('log')
## use zero bound for strikes
plt.xlim(0)
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.xlabel('Strike')
## Need to put colorbars somewhere...
plt.tight_layout()
## save in the same path where you got the file?
if not os.path.exists(write_path):
	os.makedirs(write_path)
plt.savefig(write_path+'/'+ticker+'_at_time_'+tnow.strftime('%Y_%b_%d_%H_%M')+
	'_premia.png')
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Implied Volatility Plots!!!
## Find the strike where the minimum iv occurs; I thought this would correspond
## to the forward price, but now I'm not so sure
iv_min_c=np.zeros(len(texp))
arr_elements=np.zeros(len(texp))
for i in range(len(texp)):
    iv_min_c[i]=np.min(iv_clean_c[i,:])
    arr_elements[i]=xclean_c[i,:][iv_clean_c[i,:]==iv_min_c[i]].data[0]
    
iv_max=(np.max(iv_clean_c)*(np.max(iv_clean_c)>np.max(iv_clean_p))+
	np.max(iv_clean_p)*(np.max(iv_clean_c)<=np.max(iv_clean_p)))
plt.figure()
plt.subplot(1,2,1)
plt.title(ticker+' Calls')
plt.scatter(xclean_c.flatten(),iv_clean_c.flatten(),
	c=yclean_c.flatten(),
	cmap='cool',edgecolor='none',norm=LogNorm())
cbar=plt.colorbar(orientation="horizontal")
cbar.set_label('DTE')
## use zero bound for strikes
plt.xlim(left=0)
plt.ylim(bottom=0,top=iv_max)
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.ylabel('Implied Volatility')
plt.xlabel('Strike')
## subplot for puts?
plt.subplot(1,2,2)
plt.title(ticker+' Puts')
plt.scatter(xclean_p.flatten(),iv_clean_p.flatten(),
	c=yclean_p.flatten(),
	cmap='hot',edgecolor='none',norm=LogNorm())
cbar=plt.colorbar(orientation="horizontal")
cbar.set_label('DTE')
## use zero bound for strikes
plt.xlim(left=0)
plt.ylim(bottom=0,top=iv_max)
## use the same y limits for puts and calls
plt.grid(b=True, which='major', color='k', linestyle=':',linewidth=2)
plt.grid(b=True, which='minor', color='k', linestyle=':')
plt.xlabel('Strike')
plt.tight_layout()
## save in the same path where you got the file?
if not os.path.exists(write_path):
	os.makedirs(write_path)
plt.savefig(write_path+'/'+ticker+'_at_time_'+tnow.strftime('%Y_%b_%d_%H_%M')+
	'_iv.png')
plt.show()

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## 3d surface plot
fig=plt.figure()
ax=plt.axes(projection='3d')
ax.plot_surface(x_interp,y_interp,iv_interp_c,cmap='viridis',edgecolor='none')
plt.show()
#ax.set_xlim(left=0,right=5000)
#ax.set_ylim(bottom=700)
#plt.contour(x_interp,y_interp,iv_interp_c);plt.show()

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Open interest by strike price?
plt.figure();
# Maybe bar chart is good?
i=1
plt.title('Days to Expiry: %.2f' %texp[i])
plt.bar(x_all[i,:][~oi_all_c[i,:].mask].data,
        oi_all_c[i,:][~oi_all_c[i,:].mask].data)
# Let's have a negative sign in front of put open interest
plt.bar(x_all[i,:][~oi_all_p[i,:].mask].data,
        -oi_all_p[i,:][~oi_all_c[i,:].mask].data)
# It would be great to plot the spot and forward prices!
plt.xlabel('Strike Price')
plt.ylabel('Open Interest')
