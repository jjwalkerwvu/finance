"""
Created on Sunday August 2 2020

@author: Jeffrey J. Walker

    risk_neutral_european.py
        This is a function that finds the implied probability distributions
		for a security with european-style options. Some additional cleaning
		is necessary to produce the risk-neutral probability distributions

	Consider using cubic splines anchored at endpoints when interpolating
	prices, maybe this can be another method (make this a class?)
	See Allan M. Malz (2014) for details

	Inputs:
		chain	-	a dataframe containing an option chain, already cleaned
					using yahoo_option_chain_multi_exp.py or the version that
					reads from file

	Outputs:
		gc		-	the implied probability distribution from calls
		gp		- 	the implied probability distribution from puts; should be
					the same as gc but it might be useful to actually check.

"""

def risk_neutral_european(chain):
	## Need the Black-Scholes analytical solver; maybe just make sure it's 
	## in the same path as this function?
	# insert at 1, 0 is the script path (or '' in REPL)
	sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')
	from bs_analytical_solver import bs_analytical_solver

	## calculate the total time between now and expiration date, and convert to
	## annualized percentage; you need to find an appropriate risk free bond
	## at the option expiration date; time to maturity equal to dexp-dnow
	y_annual=0.003

	## only include data points where there is volume, and a bid and an ask
	
	xtemp=np.array(df_calls.strike[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&		(df_calls.ask!=0))])
	ytemp=np.array((df_calls.ask[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))]+df_calls.bid[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))])/2.0)
	iv_temp=np.array(df_calls.impliedVolatility[~np.isnan(df_calls.volume)&((df_calls.bid!=0)&(df_calls.ask!=0))])

	## duplicate with puts

	xptemp=np.array(df_puts.strike[~np.isnan(df_puts.volume)&((df_puts.bid!=0)&(df_puts.ask!=0))])
	yptemp=np.array((df_puts.ask[~np.isnan(df_puts.volume)&((df_puts.bid!=0)&(df_puts.ask!=0))]+df_puts.bid[~np.isnan(df_puts.volume)&((df_puts.bid!=0)&(df_puts.ask!=0))])/2.0)
	ivp_temp=np.array(df_puts.impliedVolatility[~np.isnan(df_puts.volume)&((df_puts.bid!=0)&(df_puts.ask!=0))])

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

	return gc,gp
