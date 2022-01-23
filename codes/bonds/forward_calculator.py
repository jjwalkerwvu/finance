#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 21:50:33 2021
    
    forward_calculator.py
        This script performs some calculations to determine the market 
        expected return from a coupon paying bond

@author: jeff
"""

import pandas as pd
import numpy as np
from scipy.optimize import newton

## Zero coupon yield curve from FRED:
## read in data; have to use (7)th line as the header, I don't know why
#datafile="/home/jjwalker/Desktop/finance/data/bonds/feds200628.csv"
#zc=pd.read_csv(datafile,header=7)
#zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
#zc.set_index('Date',inplace=True)

url='https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv';
zc=pd.read_csv(url,sep=',',header=7)
zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
zc.set_index('Date',inplace=True)

## the SVENY variable names contain the zero-coupon yield, continuously 
## compounded
## the market price of the 30 year zc bond:
par_val=1000
## Date where you want to calculate the return
#calc_date='1997-06-16'
#calc_date='2021-09-10'
## Most recent date:
calc_date=zc.index[-1]

## year of the note/bond we want to check
## This is a password for something
#KeepHavocsfoodsafe
current_mat=30
## maturity in years of the bond after n years??
next_mat=29
## the coupon rate, which, as of now, you will need to look up
c=2.00
#c=1.125
#c=11

## The comparison?

## calculate forward rates 1 year into the future for all coupon payments
# 1/m*((n+m)*y(n+m)-n*y(n))
## marr is an array of all the semi-annual coupon payments, assuming the 
## security has exactly next_mat years to maturity
marr=0.5*np.arange(1,next_mat*2+1)
yfwd=(1.0/(marr))*((marr+1)*(zc.BETA0.loc[calc_date]+
		zc.BETA1.loc[calc_date]*(1-np.exp(-(marr+1)/zc.TAU1.loc[calc_date])
		)/((marr+1)/zc.TAU1.loc[calc_date])+
		zc.BETA2.loc[calc_date]*((1-np.exp(-(marr+1)/zc.TAU1.loc[calc_date])
		)/((marr+1)/zc.TAU1.loc[calc_date])-np.exp(-(marr+1)/zc.TAU1.loc[calc_date]))+
		zc.BETA3.loc[calc_date]*((1-np.exp(-(marr+1)/zc.TAU2.loc[calc_date])
		)/((marr+1)/zc.TAU2.loc[calc_date])-np.exp(-(marr+1)/zc.TAU2.loc[calc_date])))-
		zc.SVENY01.loc[calc_date])

## price of the bond, using continuous compounding:
p_nextc=c/200*par_val*np.sum(
    np.exp(-yfwd*marr))+par_val*np.exp(-yfwd[-1]*marr[-1])
## convert zero coupon yields to coupon-equivalent:
yfwd=2*(np.exp(yfwd/200)-1)
## price the 29 year bond based on forward rates (semi-annual payment)
p_next=(c/200*par_val*np.sum(1/(1+yfwd/2)**(2*marr))+
     par_val/(1+yfwd[-1]/2)**(2*marr[-1]))
## Get the yield associated with this price:
## calculate Macaulay duration for fun; need to find the yield first
## How can this be turned into a wrapper??
def f(y):
    c=2.0
    par_val=1000
    marr=0.5*np.arange(1,29*2+1)
    return c/200*par_val*np.sum(np.exp(-marr*y))+par_val*np.exp(-marr[-1]*y)-927
 
## The solution is the ytm yield (continuously compounded), using highest zero
## yield as a starting guess   
ytm=newton(f,x0=yfwd[-1])
## Now calculate the Macaulay duration; same as modified duration since I have
## used continuously compounding yields
dfwd=(c/200*par_val*np.sum((marr*np.exp(-marr*ytm))/p_nextc)+
      marr[-1]*par_val*np.exp(-marr[-1]*ytm)/p_nextc)
                                      

## calculate the price for a bill/note/bond with maturity given by current_mat
## farr is the array of all the semi-annual coupon payments, assuming the
## security has exactly current_mat years to maturity
farr=0.5*np.arange(1,current_mat*2+1)
ynow=(zc.BETA0.loc[calc_date]+
		zc.BETA1.loc[calc_date]*(1-np.exp(-farr/zc.TAU1.loc[calc_date])
		)/(farr/zc.TAU1.loc[calc_date])+
		zc.BETA2.loc[calc_date]*((1-np.exp(-farr/zc.TAU1.loc[calc_date])
		)/(farr/zc.TAU1.loc[calc_date])-np.exp(-farr/zc.TAU1.loc[calc_date]))+
		zc.BETA3.loc[calc_date]*((1-np.exp(-farr/zc.TAU2.loc[calc_date])
		)/(farr/zc.TAU2.loc[calc_date])-np.exp(-farr/zc.TAU2.loc[calc_date])))
		
## convert zero coupon yields to coupon-equivalent:
ynow=2*(np.exp(ynow/200)-1)
p_now=(c/200*par_val*np.sum(1/(1+ynow/2)**(2*farr))+
     par_val/(1+ynow[-1]/2)**(2*farr[-1]))


## total return is the capital appreciation plus the 2 coupon payments we will
## have received in 1 year
ret=(p_next+2*c/200*par_val-p_now)/p_now*100
print("Total return: "+str(ret)+"%")
print("Current yield on 1 year zero coupon: "+str(ynow[1]*100)+"%")
