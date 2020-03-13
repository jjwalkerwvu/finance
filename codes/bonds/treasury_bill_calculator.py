#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 21:27:41 2019

@author: jeffreywalker

    This is a function that takes a principal and determines the payoff.
    p - the principal
    r - the (time-dependent!) interest rate; should be annualized!
    n - compounding periods
    
    The idea is that you take a principal amount, and divide into increments of
    $100, since that is the smallest t-bill one can buy
"""

## libraries
import numpy as np

def treasury_bill_calculator(p,r,n):
    ## generally, $100 is the smallest increment
    inc=100
    ## find the number of tbills that can be purchased
    nbills=np.floor(p/(inc-r*inc))
    
    
    ## the total payoff, which includes the principal amount
    payoff=nbills*inc
    ## the profit only, which subtracts the discounted principal 
    profit=nbills*inc*r
    ## the "leftover" amount; the amount of principal leftover that cannot be
    ## used to purchase a treasury bond
    waste=np.mod(p,(inc-r*inc))
    
    for i in range(0,n-1):
        #nprev=nbills
        nbills=np.floor((payoff+waste)/(inc-r*inc))
        payoff=nbills*inc
        #profit=nbills*inc*r
        waste=waste+np.mod(payoff,(inc-r*inc))
        #profit=profit+nbills*inc-payoff
    
    profit=payoff-p+waste
    return payoff,profit,waste