"""
October 30,2019

stock_daily_returns.py

	This script opens a csv file for a given ticker and plots the daily 
	return.
	This is a generalization of the daily_returns.py or 
	spy_daily_returns.py scripts.
	
	The goal is to output a probability distribution function for the daily
	returns.


@author Jeffrey J. Walker
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
## for normal distribution
import scipy.stats as stats
from scipy.special import erf
from scipy.special import erfc

## path where the various data files are located; may need to change
path='/home/jjwalker/Desktop/finance/earnings_predictor/'
## Tickers should be in all caps, but right now I have files saved in lower
## case.
ticker='spx'
## might be good to put nbin variable, the divisor of the total number of
## observation periods (typically days)
nbin=1

## load up stock data:
price=pd.read_csv(path+ticker+'_price.csv',header=0)
price['Date'] = pd.to_datetime(price.Date,infer_datetime_format=True)
price=price.rename(columns={'Date':'date'})
price=price.set_index('date')
## need to set values to numeric 

## get daily returns; these can be the open to close, but better might be
## previous close to current close.
## These are given as percentage gain/loss
daily_return=(price.Close.values[1:]-price.Close.values[:-1])/(price.Close.values[:-1])*100

## construct dataframe for the daily return to include the dates?

sorted_return=np.sort(daily_return)
## Number of measurements
N=len(sorted_return)
## M is more arbitrary? (Number of bins, require N>>nbin)
## number of observations per bin (N/nbin) is input at the beginning of the
## script now.
#nbin=100 ## I think this is actually number of observations per bin
M=int(N/nbin)
## might want to check that M*nbin=N; If not, figure out how to fairly split
## up the remainder among the M bins
return_min=sorted_return[0]
return_max=sorted_return[-1]
dreturn=(return_max-return_min)/M
## the cumulative distribution function?
F=1.0*np.array(range(0,M))/M
## initialize pdf; include endpoints or no?
pdf=np.zeros(M)
## initialize cdf
cdf=np.zeros(M)
x=np.zeros(M)



## simple loop; just count the number of measurements between boundries of bin
for i in range(1,M-1):
	pdf[i]=1.0*np.sum((sorted_return>=(return_min+(i-1)*dreturn))&(sorted_return<(return_min+i*dreturn)))/N
	## We also have to approximate the daily return that accompanies the pdf;
	## place this in the center of "the bin"
	x[i]=.5*(return_min+(i-1)*dreturn)+.5*(return_min+i*dreturn)
	## also compute the cdf
	cdf[i]=np.trapz(pdf[1:i],x[1:i])

## This pdf needs to be properly normalized?
const=np.trapz(pdf[1:-1],x[1:-1])
pdf=pdf/const
## same thing for the cdf; use the same integration constant.
cdf=cdf/const



## compute the stuff we need for guassian comparison
## the center:
mu=np.mean(sorted_return)
std=np.std(sorted_return)
#norm_returns=stats.norm.pdf(sorted_return,mu,std)
norm_returns=1/np.sqrt(2*np.pi*std**2)*np.exp(-((sorted_return-mu)**2/2.0/std**2))
#norm_cdf=0.5*erfc(-sorted_return/np.sqrt(2))
norm_const=np.trapz(norm_returns,sorted_return)
## will this help with underflow problems??
## (historical data give norm_const=1.00000244...)
norm_returns=norm_returns/norm_const

## compute the stuff we need for a lorentzian comparison
## find max value of the pdf that we found:
pdf_max=np.max(pdf)
cauchy_scale=1.0/(pdf_max*np.pi)
## find what value of x corresponds to this maximum value, this is the
## location parameter
x0=x[pdf>=pdf_max]
cauchy_returns=1.0/(np.pi*cauchy_scale*(1+((sorted_return-x0)/cauchy_scale)**2))
## cumulative distribution:
cauchy_cdf=1/np.pi*np.arctan((sorted_return-x0)/cauchy_scale)+0.5


plt.figure()
plt.subplot(211)
title=(ticker+' Daily Returns from '+price.index[0].strftime('%Y-%b-%d')
		+' to '+price.index[-1].strftime('%Y-%b-%d'))
plt.title(title)
plt.plot(x[1:-1],pdf[1:-1],'.r',label=ticker+' Daily Returns PDF')
## plot the cumulative distribution function for the daily returns!
plt.plot(x[1:-1],cdf[1:-1],'.-b',label=ticker+' Daily Returns CDF')
plt.plot(sorted_return,norm_returns,'.-k',label='Normal Distribution')
## for fun, let's plot a Cauchy distribution:
plt.plot(sorted_return,cauchy_returns,'.-g',label='Cauchy Distribution')
plt.xlim(left=return_min,right=return_max)
plt.ylim(top=1,bottom=0)
plt.xlabel('Daily Return (%)')
plt.ylabel('Probability Density')
plt.legend(loc='best')
plt.tight_layout()
plt.subplot(212)
plt.title('Log[Daily Returns PDF]')
plt.plot(x[1:-1],np.log(pdf[1:-1]),'.r',label='Log['+ticker+ ' Daily Returns PDF]')
## include only subset of data to show difference between tails?
plt.plot(sorted_return,np.log(norm_returns),'.-k',
		label='log[Normal Distribution]')
## for fun, let's plot a Cauchy distribution:
plt.plot(sorted_return,np.log(cauchy_returns),'.-g',
		label='log[Cauchy Distribution]')
plt.xlim(left=return_min,right=return_max)
plt.ylim(top=0,bottom=-10)
plt.xlabel('Daily Return (%)')
plt.ylabel('log[Probability Density]')
plt.legend(loc='best')
plt.tight_layout()
##
plt.savefig(ticker+'_daily_returns.png')

## Might be a fun idea to estimate the frequency of various-% moves, compare
## the actual historical data to guassian prediction.
percent_move=np.array([0.25,0.5,1,2,3,4,5,6,7,8,9,10])
## these will be the probabilities for moves...?
probability=np.zeros(len(percent_move))
norm_probability=np.zeros(len(percent_move))
cauchy_probability=np.zeros(len(percent_move))
for i in range(0,len(percent_move)):
	probability[i]=(np.max(cdf[x<=-percent_move[i]])+
					(1-np.max(cdf[x<=percent_move[i]])))
	## find for gaussian
	norm_tail_left=(np.trapz((norm_returns[sorted_return<=-percent_move[i]]),sorted_return[sorted_return<=-percent_move[i]]))
	norm_tail_right=1-(np.trapz((norm_returns[sorted_return<=percent_move[i]]),sorted_return[sorted_return<=percent_move[i]]))
	norm_probability[i]=norm_tail_left+norm_tail_right
	## find for cauchy
	## find for gaussian
	cauchy_tail_left=(np.trapz((cauchy_returns[sorted_return<=-percent_move[i]]),sorted_return[sorted_return<=-percent_move[i]]))
	cauchy_tail_right=1-(np.trapz((cauchy_returns[sorted_return<=percent_move[i]]),sorted_return[sorted_return<=percent_move[i]]))
	cauchy_probability[i]=cauchy_tail_left+cauchy_tail_right

## frequency of events should just be the probability multiplied by the 
## total amount of time elapsed?
seconds_per_century=1.0*60*60*24*365.25*100
## events per century is the frequency of the data set (in days) times:
##(price.index[-1]-price.index[0]).total_seconds()/seconds_per_century 
probability_frequency=probability*((price.index[-1]-price.index[0]).total_seconds()/86400)*(price.index[-1]-price.index[0]).total_seconds()/seconds_per_century
norm_frequency=norm_probability*((price.index[-1]-price.index[0]).total_seconds()/86400)*(price.index[-1]-price.index[0]).total_seconds()/seconds_per_century
cauchy_frequency=cauchy_probability*((price.index[-1]-price.index[0]).total_seconds()/86400)*(price.index[-1]-price.index[0]).total_seconds()/seconds_per_century

plt.figure()
title=''
plt.title(title)
#plt.plot(percent_move,probability,'rd',label='SPX Historical Data')
#plt.plot(percent_move,np.abs(probability/norm_probability),'sk',label='Ratio')
plt.plot(percent_move,probability_frequency,'rd',label=ticker+' Historical Data')
plt.plot(percent_move,norm_frequency,'sk',label='Normal Model Frequency')
plt.legend(loc='best')
plt.xlabel('Daily Return (%)')
#plt.ylabel('Probability of Move')
#plt.ylabel('Ratio of Historical Data to Gaussian Approximation')
plt.tight_layout()
plt.savefig(ticker+'_daily_move_probability.png')
	



