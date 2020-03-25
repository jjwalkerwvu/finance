'''
implied_volatility.py

1 September 2019
Author: Jeffrey J. Walker

This is a function that uses the function bs_analytical_solver to find the
implied volatility for a given price of an option.
This is for european calls and puts, and american calls ONLY

Inputs:
	o_price	- The current market price of the option, put or call.
	S 		- The spot price of the option
	K 		- The strike price of the option
	r		- The risk free rate, yearly
	T 		- The time to expiration (in years)
	sigma 	- The sqrt of the variance of the underlying stock price, usually
			  given as a percentage, yearly
	o_type 	- The type of option; 'c' for call, 'p' for put. I have this set
			  up to use calls by default, in case user does not put anything
			  in

'''

import numpy as np
import scipy as sp
import scipy.optimize as optimize
#from bs_analytical_solver import bs_analytical_solver
## insert the path corresponding to bs_analytical solver; we will need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')
from bs_analytical_solver import bs_analytical_solver

def implied_volatility(o_price,S,K,r,T,sigma,o_type):
	#print('working')
	## bisect requires that f(a) and f(b) have different signs.
	## here is some logic to ensure that f(a) and f(b) have different signs.
	bs_val,second_deriv,delta,gamma,vega,theta,rho=bs_analytical_solver(
			S,K,r,T,sigma,o_type)
	o_greater=(o_price-bs_val)>0
	## wrapper function to work with optimize.bisect?
	def f(sigma,S,K,r,T,o_type,o_price):
		bs_val,second_deriv,delta,gamma,vega,theta,rho=bs_analytical_solver(
			S,K,r,T,sigma,o_type)
		return bs_val-o_price
	#optimize.bisect(f,a,b,args=(),xtol=2e-12,rtol=8.881784197001252e-16,maxiter=100,full_optput=False, disp=True)
		
	## look in an interval where we have almost zero volatility (but not
	## zero, otherwise bs_analytical_solver will throw divide by 0 error)
	## and some absurdly large implied volatility	
	#iv=optimize.bisect(f,a=1e-6,b=1e3,args=(S,K,r,T,o_type,o_price))	

	if (bs_val-o_price)>0:		
		iv=optimize.bisect(f,a=sigma/10.0,b=sigma,args=(S,K,r,T,o_type,o_price))	
	else:
		iv=optimize.bisect(f,a=sigma,b=10.0*sigma,args=(S,K,r,T,o_type,o_price))

	return iv
		
