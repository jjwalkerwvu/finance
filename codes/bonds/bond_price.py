#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 10:37:17 2019

    bond_price.py
        This function computes the price of a bond given the yield, 
		interest rate, and number of years until maturity.

	Inputs:
	p0	-	the par value of the bond; $100 or $1000 are common values to use
	r	- 	the interest rate of the (bi-annual) coupon
	n	- 	number of years to maturity; in the future allow for this to be a 
			floating point value which rounds off to half-year increments.
			Rounding the number of years to maturity should be done before 
			it is used as an input for this function.
	y	-	the yield of the bond; needs to be floating point and cannot be
			imaginary of course. This function will still work with negative
			yield bonds.

@author: jeffreywalker
"""

import numpy as np

## calculate semi-annual coupon bond price based on yield.
def bond_price(r,y,n,p0):

	## multiply by 1.0 to ensure that the coupon is a floating point value
    c=1.0*r*p0
    
    T=0.0
    for i in range(1,n+1):
        #print(str(i))
        T=T+c/(1.0+y)**i
        #print(str(T))
    T=T+p0/(1.0+y)**(n)
    #print(str(T))
    
    return T
    

