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
	solution 			- 	The value of the option, put or call
	second_derivative	-	The second derivative of the solution computed at
							the input values
	delta				- 	How the value of the option changes with respect  
							to the asset price
	gamma	 			- 	(d^2 V)/(d S^2)
	vega 				- 	This seems to output a percentage, why?
	theta 				- 	This is given in units of /year, so to get in 
							units of days (or other unit), use:
				  			theta(/day)=theta(/year)*(1/365)(year/day)
	rho		   			- 	This seems to output a percentage, why?
'''

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## importations and declarations
import numpy as np
import scipy as sp
from scipy.special import erf

## consider turning this into a class, include a method for finding implied 
## volatility? or is there an easier way?
def bs_analytical_solver(S,K,r,T,sigma,o_type):

	## MAKE SURE S, K, R, T, SIGMA ARE FLOATING POINT VALUES!
	S=1.0*S
	K=1.0*K
	r=1.0*r
	T=1.0*T
	sigma=1.0*sigma


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

		second_derivative=(1/np.pi)*((
							1/(sigma*np.sqrt(T-t)))*np.exp(-(d1**2)/2)-
							d1*np.exp(-(d1**2)/2)*(
							K/S/(sigma*np.sqrt(T-t)))**2)

		delta=1.0/2*(1+sp.special.erf(d1/np.sqrt(2)))
		gamma=1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)/(
				S*sigma*np.sqrt(T-t))
		vega=S*1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)*np.sqrt(T-t)
		
		theta=(-S/np.sqrt(2*np.pi)*sigma*np.exp(-(d1**2)/2)/(2.0*np.sqrt(T-t))
				-r*K*np.exp(-r*(T-t))*1.0/2*(1+sp.special.erf(d2/np.sqrt(2))))
		rho=K*(T-t)*np.exp(-r*(T-t))*1.0/2*(1+sp.special.erf(d2/np.sqrt(2)))

    ## might want to ONLY accept the string 'p'
	else:	
		## Now, the put solution, based on put-call parity
		d1=1/sigma/np.sqrt(T-t)*(np.log(S/K)+(r+sigma**2/2)*(T-t))
		d2=d1-sigma*np.sqrt(T-t)

		solution=1.0/2*(1+sp.special.erf(-d2/np.sqrt(2)
				))*K*np.exp(-r*(T-t))-1.0/2*(
				1+sp.special.erf(-d1/np.sqrt(2)))*S
		
		## currently I am only using the second derivative of the call price;
		## put the second derivative of the put solution at a later time.
		second_derivative=0

		delta=1.0/2*(1+sp.special.erf(d1/np.sqrt(2)))-1.0
		gamma=1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)/(
				S*sigma*np.sqrt(T-t))
		vega=S*1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)*np.sqrt(T-t)
		theta=(-S*1/np.sqrt(2*np.pi)*np.exp(-(d1**2)/2)*sigma/2.0/np.sqrt(T-t)
				+r*K*np.exp(-r*(T-t))*1.0/2*(1+sp.special.erf(-d2/np.sqrt(2)))
				)
		rho=-K*(T-t)*np.exp(-r*(T-t))*1.0/2*(1+sp.special.erf(-d2/np.sqrt(2)))
		
	## wait, are vega and rho returned as percentages? why?
	return solution,second_derivative,delta,gamma,vega,theta,rho
