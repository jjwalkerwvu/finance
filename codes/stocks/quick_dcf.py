#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May  8 21:00:26 2021

@author: jeff
"""
import numpy as np

## free cash flow in dollars; the "variable coupon payment"
f0=2.154

## assumed growth rate of free cash flow:
g=0.5

## expected gdp growth for country where the firm is located; 4% is quite
## generous
gg=0.04

## sp500 equity risk premium (right now, decimal)
erp=0.04

## ten year bond yield; or use zero coupon array for risk free rate
rf=1.6/100

## Stock's Market Beta:
beta=1.35

## stock's book value:
bval=0

## discount factor for 10 years:
d=(erp+rf)*beta

## the market cap:
cash_flows=f0*(1+g)**(1+np.arange(10))
dcash_flows=cash_flows/((1+d)**(1+np.arange(10)))

## terminal value:
tval=dcash_flows[-1]*(1+gg)/(d-gg)

## the evaluation:
val=np.sum(dcash_flows)+tval+bval

## number of shares
nshares=775e6


