"""
Created on Monday March 16 2020

@author: Jeffrey J. Walker

    option_test_script.py
        This script uses the yahoo_option_chain_scraper to plot the volatility
		surface and produce an implied probability distribution.

"""

import pandas as pd
import numpy as np
#from scipy.interpolate import griddata
from scipy import interpolate
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date
from dateutil.tz import *
import time
## import what we need to automatically write output to a folder
import os
import sys
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Be sure that you use a valid ticker symbol!
## Indices have a '^' before their letter symbols!
ticker='^SPX'
#ticker='SPY'

## insert the path corresponding to the Yahoo option chain scraper; 
## we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
## insert the path corresponding to bs_analytical solver; we will need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')

from yahoo_option_chain_scraper import yahoo_option_chain_scraper
from bs_analytical_solver import bs_analytical_solver

## What is the path to the option chain?
## DO NOT NEED '/' AT THE END!
path='/home/jjwalker/Desktop/finance/data/options'

## Now call the option chain scraper
dnow,dexp,df_calls,df_puts=yahoo_option_chain_scraper(path,ticker)

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

## A relatively simple interpolation scheme, using splines
## FIGURE THIS OUT FOR SIMPLE LINEAR INTERPOLATION!
## only include Strikes, Bids, and Asks where there is volume!
xtemp=np.array(df_calls.Strike[~np.isnan(df_calls.Volume)])
## bid-ask midpoint
ytemp=np.array((df_calls.Ask[~np.isnan(df_calls.Volume)]+
	df_calls.Bid[~np.isnan(df_calls.Volume)])/2.0)
## Implied Volatility for all of the valid, non-nan strikes:
iv_temp=np.array(df_calls.Implied_Volatility[~np.isnan(df_calls.Volume)])
#ytemp=np.array((df_calls.Ask+df_calls.Bid)/2.0)
## find the first non-nan! This should also be the largest value!
y=np.array(np.max(ytemp))
## remove any "anomalous points"; call prices have to decrease with increasing
## strike price!
keep_array=[0]
#keep_array=[]
for i in range(1,len(ytemp)):
	#print(str(i))
	if (np.sum(ytemp[i]<y)==y.size)&(
		np.sum(ytemp[i]>ytemp[i:])==(len(ytemp[i:])-1)): 
		#print(str(y[i])+'<'+str(y[i-1])+' at index:'+str(i))
		keep_array.append(i)
		#y.append(ytemp[i])
		y=np.append(y,ytemp[i])
		## Why do I end up with len(y)>len(ytemp[keep_array])?

## put into numerical order:
#keep_array.sort()
x=xtemp[keep_array]
#y=y[keep_array]
iv=iv_temp[keep_array]

## Partial "Analytical" solution for g(K):
St=243.68
gtemp=np.zeros(len(x))
#g=np.zeros(len(xnew))
#delta=xnew[1]-xnew[0]
for i in range(1,len(gtemp)-1):
	## naive, finite-difference approach
    #g[i]=np.exp(y_annual)*(ynew[i+1]-2*ynew[i]+ynew[i-1])/(2*delta**2)
	solution,second_deriv,delta,gamma,vega,theta,rho=bs_analytical_solver(
		S=St,K=xtemp[i],r=y_annual,T=texp/365,sigma=iv_temp[i]/100.0,o_type='c')
	gtemp[i]=np.exp(y_annual*texp)*second_deriv

## you have to renormalize the implied distribution!
const=np.trapz(gtemp,x)
g=gtemp/const
           
plt.plot(x,g,'.k');plt.show()

## probability of the asset to be between two price limits:
k1=2450
k2=2550
prob=np.trapz(g[(x>=2450)&(x<=np.max(x))],x[(x>=2450)&(x<=np.max(x))])

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
tck=interpolate.splrep(x[keep_array],ytemp[keep_array],s=0)
npoints=1e2
#xnew=np.linspace(df_calls.Strike.iloc[0],df_calls.Strike.iloc[-1],npoints)
xnew=np.linspace(x[0],x[-1],npoints)
#ynew=interpolate.splev(xnew,tck,der=0)
ynew=np.interp(xnew,x[keep_array],ytemp[keep_array])
plt.plot(xnew,ynew,'.k');plt.show()

## is hermite polynomial interpolation an option?
#np.polynomial.hermite.hermfit(x[keep_array],y,deg=2)


## linear interpolation
npoints=1e3
xnew=np.linspace(df_calls.Strike.iloc[0],df_calls.Strike.iloc[-1],npoints)
xp=np.array(df_calls.Strike)
fp=np.array((df_calls.Ask+df_calls.Bid)/2.0)
ynew=np.interp(xnew,xp,fp)
plt.plot(xnew,ynew,'.k');plt.show()

## Let's test with a log normal distribution?
#xnew=np.linspace(-5,5,1e3)
#sigma=1.0
#mu=0.0
#ynew=(1/sigma/np.sqrt(2*np.pi))*np.exp(-0.5*((xnew-mu)/sigma)**2)


## Get the risk-neutral probability distribution function, g(K)
g=np.zeros(len(xnew))
delta=xnew[1]-xnew[0]
for i in range(1,len(g)-1):
    g[i]=np.exp(y_annual)*(ynew[i+1]-2*ynew[i]+ynew[i-1])/(2*delta**2)

            
plt.plot(xnew,g,'.k');plt.show()
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Some plots for now; put into a separate script/function later?
plt.plot(df_calls.Strike,df_calls.Last_Price,'.k');plt.show()
## plot the last price
plt.figure()
plt.plot(df_calls.Strike,df_calls.Last_Price,'dc')
plt.plot(df_calls.Strike,df_calls.Last_Price,'sm')

## plot bid ask midpoint
plt.plot(df_calls.Strike,(df_calls.Ask+df_calls.Bid)/2,'.k');plt.show()
## plot the call bid/ask and put bid/ask for each strike
plt.figure()
plt.plot(df_calls.Strike,df_calls.Ask,'vc',label='Call Ask')
plt.plot(df_calls.Strike,df_calls.Bid,'^c',label='Call Bid')
plt.title('Date: Option Chain Call Prices')
plt.xlabel('Strike Price')
plt.ylabel('Price, $')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
## concatenate the date and time for this figure?
plt.savefig(ticker+'call_prices.png')
#
plt.figure()
plt.plot(df_calls.Strike,df_calls.Ask,'vm',label='Put Ask')
plt.plot(df_calls.Strike,df_calls.Bid,'^m',label='Put Bid')
plt.title('Date: Option Chain Put Prices')
plt.xlabel('Strike Price')
plt.ylabel('Price, $')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
#plt.savefig('put_prices.png')


g=np.zeros((len(df_calls)))
delta=df_calls.Strike[1]-df_calls.Strike[0]
for i in range(1,len(df_calls)-1):
    #g[i]=np.exp(0.02*1/365)*(
    #        option_chain.Lastc[i+1]
    #        -2*option_chain.Lastc[i]
    #        +option_chain.Lastc[i-1])/delta**2
	
	## my bumbling attempt to handle non-uniform delta size; have to fix 
	## this somehow, maybe with interpolation?
	#delta[i]=df_calls.Strike[
    g[i]=np.exp(y_annual)*(
            (df_calls.Ask[i+1]+df_calls.Bid[i+1])/2
            -(df_calls.Ask[i]+df_calls.Bid[i])
            +(df_calls.Ask[i-1]+df_calls.Ask[i-1])/2)/delta**2

plt.plot(df_calls.Strike,g,'.k');plt.show()
plt.title('Date: Implied Distribution')
plt.xlabel('Strike Price')
plt.ylabel('Implied Distribution')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
#plt.savefig('implied_distribution.png')
