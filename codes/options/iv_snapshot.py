"""
Created on Tuesday March 31 2020

@author: Jeffrey J. Walker

    iv_snapshot.py
        This script uses the yahoo_option_chain_json to plot the volatility
		surface and produce an implied probability distribution.
		This script produces several plots as a diagnostic

"""

import pandas as pd
import numpy as np
#from scipy.interpolate import griddata
from scipy import interpolate
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.tz import *
import time
## import what we need to automatically write output to a folder
import os
import sys
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Be sure that you use a valid ticker symbol!
## Indices have a '^' before their letter symbols!
#ticker='^SPX'
#ticker='SPY'
#ticker='TSLA'
ticker='^VIX'
#ticker='^DJX'
#ticker='UBER'
#ticker='AAPL'
#ticker='SNAP'

## insert the path corresponding to the Yahoo option chain scraper; 
## we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
## insert the path corresponding to bs_analytical solver; we will need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')

from yahoo_option_chain_json import yahoo_option_chain_json
from bs_analytical_solver import bs_analytical_solver

## What is the path to the option chain?
## DO NOT NEED '/' AT THE END!
path='/home/jjwalker/Desktop/finance/data/options'

## Now call the option chain scraper
## call the next calendar month, 3rd friday options by default
#t_plus_30=pd.to_datetime('today').now()+timedelta(days=40)
t_plus_30=pd.to_datetime('today').now()+timedelta(days=4)
input_date=time.mktime(t_plus_30.timetuple())
## call the next calendar month, 3rd friday options by default since these have
## greater liquidity
#nearest_monthly=pd.to_datetime('today').now()+timedelta(days=30)
## Ready to call the option chain scraper/reader
dnow,dexp,exp_dates,St,df_calls,df_puts=yahoo_option_chain_json(path,ticker,input_date)

## time to expiration, from dnow and dexp, in days:
texp=(pd.Timestamp(dexp).tz_localize('US/Eastern')-pd.Timestamp(dnow)
		)/np.timedelta64(1,'D')	

## calculate the total time between now and expiration date, and convert to
## annualized percentage; you need to find an appropriate risk free bond
## at the option expiration date; time to maturity equal to dexp-dnow
y_annual=0.003


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## should the data be smoothed in some way (non-invasive way) so that we can
## get a less noisy second derivative of the call/put prices?
## perhaps some kind of interpolation - with a constant step size?
## The standard treatment is to use SABR regression on the implied volatility

## only include data points where there is volume, and a bid and an ask
#plt.plot(df_calls.strike[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))],df_calls.impliedVolatility[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))],'.k');plt.show()
xtemp=np.array(df_calls.strike[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))])
ytemp=np.array((df_calls.ask[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))]+df_calls.bid[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))])/2.0)
iv_temp=np.array(df_calls.impliedVolatility[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))])

## duplicate with puts
## only include data points where there is volume, and a bid and an ask
#plt.plot(df_calls.strike[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))],df_calls.impliedVolatility[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))],'.k');plt.show()
xptemp=np.array(df_puts.strike[~np.isnan(df_puts.volume)&((df_puts.bid!=0)&(df_puts.ask!=0))])
yptemp=np.array((df_puts.ask[~np.isnan(df_puts.volume)&((df_puts.bid!=0)&(df_puts.ask!=0))]+df_puts.bid[~np.isnan(df_puts.volume)&((df_puts.bid!=0)&(df_puts.ask!=0))])/2.0)
ivp_temp=np.array(df_puts.impliedVolatility[~np.isnan(df_puts.volume)&((df_puts.bid!=0)&(df_puts.ask!=0))])

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## implied probability distributions!

## Partial "Analytical" solution for g(K) using calls:
#gtemp=np.zeros(len(xtemp))
#g=np.zeros(len(xnew))
#delta=xnew[1]-xnew[0]
#for i in range(1,len(gtemp)-1):
	## naive, finite-difference approach
    #g[i]=np.exp(y_annual)*(ynew[i+1]-2*ynew[i]+ynew[i-1])/(2*delta**2)
	#solution,second_deriv,delta,gamma,vega,theta,rho=bs_analytical_solver(
	#	S=St,K=xtemp[i],r=y_annual,T=texp/365,sigma=iv_temp[i],o_type='c')
	#gtemp[i]=np.exp(y_annual*texp/365)*second_deriv

## you have to renormalize the implied distribution!
#const=np.trapz(gtemp,xtemp)
#g=gtemp/const        
#plt.plot(xtemp,gtemp,'.k');plt.show()


## Partial "Analytical" solution for g(K) using puts:
## (should theoretically be the same!)
#gptemp=np.zeros(len(xptemp))
#g=np.zeros(len(xnew))
#delta=xnew[1]-xnew[0]
#for i in range(1,len(gptemp)-1):
	## naive, finite-difference approach
    #g[i]=np.exp(y_annual)*(ynew[i+1]-2*ynew[i]+ynew[i-1])/(2*delta**2)
	#solution,second_deriv,delta,gamma,vega,theta,rho=bs_analytical_solver(
	#	S=St,K=xptemp[i],r=y_annual,T=texp/365,sigma=ivp_temp[i],o_type='p')
	#gptemp[i]=np.exp(y_annual*texp/365)*second_deriv

## you have to renormalize the implied distribution!
#const=np.trapz(gptemp,xptemp)
#gp=gptemp/const        
#plt.plot(xptemp,gp,'.k');plt.show()

## probability of the asset to be between two price limits:
#k1=2450
#k2=2550
#prob=np.trapz(gp[(xptemp>=k1)&(xptemp<=k2)],
#	xptemp[(xptemp>=k1)&(xptemp<=k2)])
## probability of the asset to be below some price limit:
#prob=np.trapz(gp[(xptemp>=0)&(xptemp<=k1)],xptemp[(xptemp>=0)&(xptemp<=k1)])
## probability of the asset to be greater the spot price
#prob=np.trapz(gp[(xptemp>=St)&(xptemp<=np.max(xptemp))],
#	xptemp[(xptemp>=St)&(xptemp<=np.max(xptemp))])


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
#tck=interpolate.splrep(x[keep_array],ytemp[keep_array],s=0)
#npoints=1e2
#xnew=np.linspace(df_calls.Strike.iloc[0],df_calls.Strike.iloc[-1],npoints)
#xnew=np.linspace(x[0],x[-1],npoints)
#ynew=interpolate.splev(xnew,tck,der=0)
#ynew=np.interp(xnew,x[keep_array],ytemp[keep_array])
#plt.plot(xnew,ynew,'.k');plt.show()

## is hermite polynomial interpolation an option?
#np.polynomial.hermite.hermfit(x[keep_array],y,deg=2)


## linear interpolation of the "cleaned" data, do separately for puts and 
## calls
npoints=1e4
xnew=np.linspace(xtemp[0],xtemp[-1],npoints)
ynew=np.interp(xnew,xtemp,ytemp)
iv_new=np.interp(xnew,xtemp,iv_temp)
#plt.plot(xnew,ynew,'.k');plt.show()
#plt.plot(xnew,iv_new,'.k');plt.show()
## make the implied distribution function from the interpolated calls data?
gnew=np.zeros(len(xnew))
#g=np.zeros(len(xnew))
#delta=xnew[1]-xnew[0]
for i in range(1,len(gnew)-1):
	## naive, finite-difference approach
    #g[i]=np.exp(y_annual)*(ynew[i+1]-2*ynew[i]+ynew[i-1])/(2*delta**2)
	solution,second_deriv,delta,gamma,vega,theta,rho=bs_analytical_solver(
		S=St,K=xnew[i],r=y_annual,T=texp/365,sigma=iv_new[i],o_type='c')
	gnew[i]=np.exp(y_annual*texp/365)*second_deriv

## you have to renormalize the implied distribution!
const=np.trapz(gnew,xnew)
g=gnew/const        
#plt.plot(xnew,gnew,'.k');plt.show()

## for puts:
xpnew=np.linspace(xptemp[0],xptemp[-1],npoints)
ypnew=np.interp(xpnew,xptemp,yptemp)
ivp_new=np.interp(xpnew,xptemp,ivp_temp)
## make the implied distribution function from the interpolated puts data?
gpnew=np.zeros(len(xpnew))
#g=np.zeros(len(xnew))
#delta=xnew[1]-xnew[0]
for i in range(1,len(gpnew)-1):
	solution,second_deriv,delta,gamma,vega,theta,rho=bs_analytical_solver(
		S=St,K=xpnew[i],r=y_annual,T=texp/365,sigma=ivp_new[i],o_type='p')
	gpnew[i]=np.exp(y_annual*texp/365)*second_deriv

## you have to renormalize the implied distribution!
const=np.trapz(gpnew,xpnew)
gp=gpnew/const        

## Let's test with a log normal distribution?
#xnew=np.linspace(-5,5,1e3)
#sigma=1.0
#mu=0.0
#ynew=(1/sigma/np.sqrt(2*np.pi))*np.exp(-0.5*((xnew-mu)/sigma)**2)

## probability of the asset to be between two price limits, using interpolated
## distributionfunction
#k1=2450
#k1_ask=df_puts.ask[np.abs(df_puts.strike-k1)==np.min(np.abs(df_puts.strike-k1))].values
#k2=2550
## k1 with an offset; what the strike price has to be to break even?
## can also have a desired profit? dollar amount or multiple?
#dprofit=1000.0/100
## version using multiple:
#dprofit=10*k1_ask
#k1_adj=k1-dprofit-df_puts.ask[np.abs(df_puts.strike-k1)==np.min(np.abs(df_puts.strike-k1))].values
#prob=np.trapz(gp[(xptemp>=k1)&(xptemp<=k2)],
#	xptemp[(xptemp>=k1)&(xptemp<=k2)])
## probability of the asset to be below some price limit:
#prob=np.trapz(gp[(xpnew>=0)&(xpnew<=k1)],xpnew[(xpnew>=0)&(xpnew<=k1)])
## probability of the asset to be greater the spot price
#prob=np.trapz(gp[(xpnew>=St)&(xptemp<=np.max(xpnew))],
#	xpnew[(xpnew>=St)&(xpnew<=np.max(xpnew))])

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Some plots for now; put into a separate script/function later?
## plot the last price and retrieved time!
plt.figure()
plt.subplot(211)
title=('IV for Underlying: '+ticker+'='+str(St)+', retrieved:'+
	dnow.strftime('%Y-%b-%d %H:%M')+', '+
	dexp.strftime('%Y-%b-%d')+' Expiry')
#plt.title(title)
plt.plot(df_calls.strike,100*df_calls.impliedVolatility,'.c',label=ticker+
	' calls, raw data')
plt.plot(df_puts.strike,100*df_puts.impliedVolatility,'.m',label=ticker+
	' puts, raw data')
## plot little circles corresponding to iv minimum?
## there may be multiple values of the same iv minimum
#if length(np.min(iv_temp))==1:
#plt.plot(xtemp[iv_temp==np.min(iv_temp)],100*np.min(iv_temp),'ok',
#	markerfacecolor="None",markeredgecolor='k',label='Min IV, calls')
#plt.plot(xptemp[ivp_temp==np.min(ivp_temp)],100*np.min(ivp_temp),'ok',
#	markerfacecolor="None",markeredgecolor='k',label='Min IV, puts')
#print(str(xptemp[ivp_temp==np.min(ivp_temp)]))
#print(str(100*np.min(ivp_temp)))
plt.ylabel('Implied Volatility, %')
plt.xlabel('Strike Price')
## plot the range, with the abosolute min and max strikes included in the
## dataset.
plt.xlim(left=np.min([np.min(df_calls.strike),np.min(df_puts.strike)]),
	right=np.max([np.max(df_calls.strike),np.max(df_puts.strike)]))
#plt.ylim(top=,bottom=)
plt.legend(loc='best')
plt.tight_layout()
#plt.ylim(top=,bottom=)
plt.subplot(212)
#title=('Implied Probability Distribution')
#plt.title(title)
## Not sure if I should plot the computed distribution, or the normalized 
## distribution?
plt.plot(xnew,gnew,'-c',label=ticker+' calls, interpolated')
plt.plot(xpnew,gpnew,'-m',label=ticker+' puts, interpolated')
## print, or find suitable plot to show the implied expected value of the 
## underlying
## use g and gp, or gnew and gpnew?
Stc_exp=np.trapz(gnew*xnew,xnew)
gc_exp=gnew[np.abs(Stc_exp-xnew)==np.min(np.abs(Stc_exp-xnew))]
#print(str(gc_exp))
## get nearest g value to the expect value of the security at t=expiration
Stp_exp=np.trapz(gpnew*xpnew,xpnew)
gp_exp=gpnew[np.abs(Stp_exp-xpnew)==np.min(np.abs(Stp_exp-xpnew))]
plt.plot(Stc_exp,gc_exp,'oc',markerfacecolor="None",markeredgecolor='c',
	label='E['+ticker+']={:.2f} from Calls'.format(Stc_exp))
plt.plot(Stp_exp,gp_exp,'om',markerfacecolor="None",markeredgecolor='m',
	label='E['+ticker+']={:.2f} from Puts'.format(Stp_exp))
plt.ylabel('Implied Probability Density')
plt.xlabel('Strike Price')
plt.legend(loc='best')
plt.tight_layout()
plt.xlim(left=np.min([np.min(df_calls.strike),np.min(df_puts.strike)]),
	right=np.max([np.max(df_calls.strike),np.max(df_puts.strike)]))
#plt.ylim(top=,bottom=)
write_path=path+dnow.strftime("/%Y/%m/%d")
## save in the same path where you got the file?
if not os.path.exists(write_path):
	os.makedirs(write_path)
plt.savefig(write_path+'/'+ticker+'_at_time_'+dnow.strftime('%Y_%b_%d_%H_%M')+
	'_exp_'+dexp.strftime('%Y_%b_%d')+'_iv_snapshot.png')

## Make plots for theta, gamma, vega?? Fan plots for volatility term structure?

#plt.plot(df_calls.strike,df_calls.lastPrice,'dc',markeredgecolor='c')
#plt.plot(df_puts.strike,df_puts.lastPrice,'sm',markeredgecolor='m')
#plt.show()

## plot bid ask midpoint
#plt.plot(df_calls.strike,(df_calls.ask+df_calls.bid)/2,'.k');plt.show()
## plot the call bid/ask and put bid/ask for each strike
#plt.figure()
#plt.plot(df_calls.strike,df_calls.ask,'vc',label='Call Ask',markeredgecolor='c')
#plt.plot(df_calls.strike,df_calls.bid,'^c',label='Call Bid',markeredgecolor='c')
#plt.title(dexp.strftime("%Y %b %d") +' Expiry Option Chain Call Prices')
#plt.xlabel('Strike Price')
#plt.ylabel('Calls Prices, $')
## Make a legend
#plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
#plt.tight_layout()
## concatenate the date and time for this figure?
#plt.savefig(ticker+'call_prices.png')
#
#plt.figure()
#plt.plot(df_calls.strike,df_calls.ask,'vm',label='Put Ask',markeredgecolor='m')
#plt.plot(df_calls.strike,df_calls.bid,'^m',label='Put Bid',markeredgecolor='m')
#plt.title(dexp.strftime("%Y %b %d") +' Expiry Option Chain Put Prices')
#plt.xlabel('Strike Price')
#plt.ylabel('Puts Prices, $')
## Make a legend
#plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
#plt.tight_layout()
#plt.savefig(ticker+'put_prices.png')


