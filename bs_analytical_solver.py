'''
bs_analytical_solver.py

28 April 2019
Author: Jeffrey J. Walker


This function uses the Black Scholes formula to calculate prices for
European call and put options, based on the inputs:

Also, this function calculates the greeks

Inputs:
	S 		- The spot price of the option
	K 		- The strike price of the option
	r		- The risk free rate, yearly
	T 		- The time to expiration (in years)
	sigma 	- The sqrt of the variance of the underlying stock price, usually
			  given as a percentage, yearly
	o_type 	- The type of option; 'c' for call, 'p' for put. I have this set
			  up to use calls by default, in case user does not put anything
			  in
	
Outputs:
	solution 	- The value of the option, put or call
	delta		- 
	gamma	 	-
	vega 		- This seems to output a percentage, why?
	theta 		- This is given in units of /year, so to get in units of days
				  (or other unit), use:
				  theta(/day)=theta(/year)*(1/365)(year/day)
	rho		   	- This seems to output a percentage, why?
'''

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## importations and declarations
import numpy as np
import scipy as sp
from scipy.special import erf

def bs_analytical_solver(S,K,r,T,sigma,o_type):

	## place holder in case I need to include t as a separate input, maybe to 
	## vectorize this function
	t=0

	if o_type=='c':
		## fix this later to include puts, this is just the formula for calls.
		## VECTORIZE!!!
		d1=1/sigma/np.sqrt(T-t)*(np.log(S/K)+(r+sigma**2/2)*(T-t))
		d2=d1-sigma*np.sqrt(T-t)
		solution=1.0/2*(1+sp.special.erf(d1/np.sqrt(2)))*S-1.0/2*(1
			+sp.special.erf(d2/np.sqrt(2)))*K*np.exp(-r*(T-t))

		delta=1.0/2*(1+sp.special.erf(d1/np.sqrt(2)))
		gamma=1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)/(
				S*sigma*np.sqrt(T-t))
		vega=S*1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)*np.sqrt(T-t)
		
		theta=(-S/np.sqrt(2*np.pi)*sigma*np.exp(-(d1**2)/2)/(2.0*np.sqrt(T-t))-
				r*K*np.exp(-r*(T-t))*1.0/2*(1+sp.special.erf(d2/np.sqrt(2))))
		rho=K*(T-t)*np.exp(-r*(T-t))*1.0/2*(1+sp.special.erf(d2/np.sqrt(2)))

	else:	
		## Now, the put solution, based on put-call parity
		d1=1/sigma/np.sqrt(T-t)*(np.log(S/K)+(r+sigma**2/2)*(T-t))
		d2=d1-sigma*np.sqrt(T-t)

		solution=1.0/2*(1+sp.special.erf(-d2/np.sqrt(2)
				))*K*np.exp(-r*(T-t))-1.0/2*(
				1+sp.special.erf(-d1/np.sqrt(2)))*S
		delta=1.0/2*(1+sp.special.erf(d1/np.sqrt(2)))-1.0
		gamma=1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)/(
				S*sigma*np.sqrt(T-t))
		vega=S*1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)*np.sqrt(T-t)
		theta=(-S*1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)*sigma/2.0/np.sqrt(T-t)+
				r*K*np.exp(-r*(T-t))*1.0/2*(1+sp.special.erf(-d2/np.sqrt(2))))
		rho=-K*(T-t)*np.exp(-r*(T-t))*1.0/2*(1+sp.special.erf(-d2/np.sqrt(2)))
		
	## wait, are vega and rho returned as percentages? why?
	return solution,delta,gamma,vega,theta,rho
