"""
Created on Tuesday March 10

@author: Jeffrey J. Walker

    This script computes (or tries to!) the /zb futures price corresponding
	to a given yield.
	Working with 30 year bond for now, but could consider branching out to 
	other maturies later.

	Some notes on deliveries:
	symbol:	$ contract size (face value):	deliverable grade:
	/ub: 	1e5		t>=25 years to maturity
	/zb: 	1e5		15<=t<=25 years to maturity
	/tn: 	1e5		9 years, 6 months <=t<=10 years to maturity
	/zn: 	1e5		6 years, 6 months <=t<=10 years to maturity
	/zf: 	1e5		original term: T<=5 years, 3 months to maturity,
					remaining term: t<=4 years, 2 months to maturity
	/z3n: 	2e5		original term: T<=5 years, 3 months to maturity,
					remaining term: 2 years, 9 months <=t<=3 years to maturity
	/zt: 	2e5		original term: T<=5 years, 3 months to maturity,
					remaining term: 1 year, 9 months <=t<=2 years to maturity

	Cheapest to deliver:
	ctd = current bond price - (settlement price)*(conversion factor)
	*Keep in mind, the reference bond is a 6% coupon bond.
	Conversion factor:
	1.) calculate bond's time to maturity as of first delivery date
	2.) round time to maturity to the nearest whole quarter (futures contracts
		are quarterly?)
	3.) Price a given %-coupon bond with the appropriate duration at 6% yield
		to maturity
	EXAMPLE CONVERSION FACTOR:
	bond_price(p0=100,r=
"""
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import sys

## insert the path corresponding to bond_price; we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/bonds')

## make sure you are in the correct directory!
from bond_price import bond_price

## Is there some way to query a live yield curve to get the risk free rate 
## between now and contract delivery date?

## assume cheapest to deliver?
## How can we calculate cheapest to deliver; what is the conversion factor?

## The foward price:
## F=S0*np.exp(rfr-q)*T+sum_{i=1}^{N} D_i*np.exp(rfr-q)*(T-t_i) 
## S0 is the spot price
## rfr is the risk free rate
## q is the convenience yield
## T is the time to maturity
## D_i is the dividend guaranteed to be paid at time t_i, where 0<t_i<T

