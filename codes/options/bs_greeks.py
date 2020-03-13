'''
A simple function that calculates the greeks for a european option, given 
inputs:

K		- the strike price of the option
S		- the price of the underlying stock
T		- Time to expiry, days?
sigma 	- historical volatility, write notes here on how this is calculated!
		  (standard deviation of the stock's returns?)
r		- the interest rate, as a ratio (not percentage!)
otype	- type of options, use 'c' for call and 'p' for put

'''

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## importations and declarations
import numpy as np
import matplotlib as plt
import scipy as sp
from scipy.special import erf

## in the future, can make a class and then we can have different methods;
## this could be for european options?
def bs_greeks(K,S,T,sigma,r,otype):
	## stuff happens
	if otype=='c' or otype=='p':
		## I think we have to divide the time by the number of trading days
		## to get a value in units of years?
		#T=T/252
		d1=1/sigma/np.sqrt(T)*(np.log(S/K)+(r+sigma**2/2)*(T))
		d2=d1-sigma*np.sqrt(T)
		if otype=='c':
			

			delta=1.0/2*(1+sp.special.erf(d1/np.sqrt(2)))
			gamma=1.0/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)/(S*sigma*np.sqrt(T))
			vega=S*1.0/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)*np.sqrt(T)
			theta=(-S*sigma/2/np.sqrt(T)*(1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2))-
					r*K*np.exp(-r*T)*1.0/2*(1+sp.special.erf(d2/np.sqrt(2))))
			rho=K*T*np.exp(-r*T)*1.0/2*(1+sp.special.erf(d2/np.sqrt(2)))
			## might as well compute the value as well?
			value=0
		else:
			delta=1.0/2*(1+sp.special.erf(d1/np.sqrt(2)))-1
			## gamma and vega are the same for a put option
			gamma=1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)/(S*sigma*np.sqrt(T))
			vega=S*1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)*np.sqrt(T)
			theta=(-S*sigma/2/np.sqrt(T)*(1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2))+
					r*K*np.exp(-r*T)*1.0/2*(1+sp.special.erf(-d2/np.sqrt(2))))
			rho=-K*T*np.exp(-r*T)*1.0/2*(1+sp.special.erf(-d2/np.sqrt(2)))
			## might as well compute the value as well?
			value=0
	else:
		print('otype must be (c)all or (p)ut')

	return delta,gamma,vega,theta,rho
