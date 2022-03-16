#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 23 20:42:41 2021
    duration_history.py
        This script calculates the duration for a par equivalent security, 
         over time, given a specific maturity 
@author: jeff
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
## import the csv reader for FRED data, yahoo, etc.
sys.path.insert(1, '/Users/jeff/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
from shiller_excel_reader import shiller_excel_reader 
from yahoo_stock_query import yahoo_stock_query
from yahoo_csv_reader import yahoo_csv_reader
from FedsYieldCurve import FedsYieldCurve


# Quick note:
# net_liq = fed balance sheet - treasury general account 
# tga up, tightening 
# tga down, easing, adding liquidity 


def calculations_from_cmt_yields(fred_cmt_series):
    
    cutoff='2021-09'
    dgs5_temp=dgs5.DGS5.resample('M').last()[:cutoff]
    dgs3_temp=dgs3.DGS3.resample('M').last()[:cutoff]
    dgs4_11=dgs3_temp+23/24.0*(dgs5_temp.values-
                                    dgs3_temp.values)
    int_period=(dgs5_temp[1:].index-dgs5_temp[:-1].index).days
    dgs5_lint=(dgs5_temp[:-1].values/100*(int_period/365.24)+
          dgs5_temp[:-1].values/dgs4_11[1:]*(
              1-(1+dgs4_11[1:]/200)**(2*int_period/365.24-2*5))+
          (1+dgs4_11[1:]/200)**(2*int_period/365.24-2*5))
    
    duration=0
    flat_return=0
    lint_return=0
    return duration,flat_return,lint_return

# Use FedsYieldCurve class to get the yield curve based on off the run issues
yield_curve=FedsYieldCurve.get_data()


# Function needed to get duration, various returns from fred data
   

# get some index fund data from yahoo finance.
sp500tr=yahoo_stock_query('^SP500TR')
vustx=yahoo_stock_query('VUSTX',dividends=True)
vfitx=yahoo_stock_query('VFITX',dividends=True)

# Load ^GSPC data; I saved a copy from when yahoo still had it easily available
gspc=yahoo_csv_reader(
    filename='/Users/jeff/Desktop/finance/data/stocks/^GSPC', 
    ticker='^GSPC')


## get shiller data, either from file or from Shiller's website.
## If you don't put an actual filename, it will pull from Shiller's website.
shiller=shiller_excel_reader('/Users/Jeff/Desktop/finance/data/stocks/ie_data.xls')
## prepare a total return for sp500 based on Shiller dividend data.
## simple loop for now:
nshares_tr=np.zeros(len(shiller))
value_tr=np.zeros(len(shiller))
## Start with one share
nshares_tr[0]=1
value_tr[0]=shiller.P[0]
for i in range(1,len(shiller)):
	last_price=shiller.P[i-1]
	nshares_tr[i]=nshares_tr[i-1]+(nshares_tr[i-1]*shiller.D[i-1]/12)/last_price
	value_tr[i]=nshares_tr[i]*shiller.P[i]	
## make a data series from this array:
shiller_tr=pd.Series(data=value_tr,index=shiller.index,
                     name="Shiller Total Return")  
shiller_tr.index.rename('Date',inplace=True)   
# faster method: (something like this)
#ret=(shiller.P[1:].values+shiller.D[1:].values/12)/shiller.P[:-1]

# Use ^GSPC data with Shiller dividend data to make a total return series up
# until the start of sp500tr.
# Begin by resampling sp500 so that all days are included.
gspc_daily=gspc.Close.resample('D').ffill()
shiller_div=(shiller.D/12).resample('D').asfreq().fillna(0)
shiller_div=shiller_div[gspc_daily.index[0]:gspc_daily.index[-1]]
gspc_ret=(gspc_daily[1:].values+shiller_div[1:].values)/gspc_daily[:-1]
gspc_tot_ret=gspc_ret.cumprod()
# Now, stitch this together with 1988 total return series.
gspc_splice=pd.concat([gspc_tot_ret[:gspc_tot_ret[:sp500tr.index[0]].index[-2]
                    ]*sp500tr.Close[0]/(
                    gspc_tot_ret[gspc_tot_ret[:sp500tr.index[0]].index[-2]]),
                    sp500tr.Close])

# Get dgs7 data just to check with seven year data, or try a different maturity
dgs7=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/DGS7')

# Get dgs5 data, look at this as well
dgs5=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/DGS5')

# gs5 goes back further, but is monthly
gs5=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS5')

dgs3=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/DGS3')

gs3=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS3')

gs1=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS1')

gs10=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS10')


# Get dgs20 data for kicks:
dgs20=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/DGS20')

# gs20 data goes back further, but it is monthly:
gs20=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS20')

# DGS30 data:
gs30=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS30')


par_val=1000
ttm=20



# THIS CODE IS THE PROTOTYPE FOR GIVING BOND RETURNS!
# Are Daily returns possible??
#
# y20_exp=2*np.log(1+zc.SVENPY20/200)
# y20_arr=0.5*np.arange(1,20*2+1)
# y20_dur=(y20_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(y20_exp.values).T*
#     np.asmatrix(y20_arr))*np.asmatrix(y20_arr).T)))+
#       y20_arr[-1]*np.exp(-y20_arr[-1]*y20_exp))  
# y19_11_arr=y20_arr-1/12.0

#y19_11_cont=zero_yields(zc,y19_11_arr)
# I am calling this the annuity return; you could get the value of the annuity
# by multiplying by par_val
# y20_annuity_ret=(np.sum(
#     np.exp(-np.array(y19_11_cont)*np.array(
#         np.asmatrix(np.ones(len(y20_exp))).T*np.asmatrix(y19_11_arr))),
#     axis=1)*y20_exp**0).resample('MS').first()
# Likewise, the principal payment is given as a return here, but you can 
# multiply by par_val to get its value.
# y20_principal_ret=(y20_exp**0*(np.squeeze(np.array(
#     np.exp(-y19_11_cont[:,-1]*y19_11_arr[-1]))))).resample('MS').first()
# y20_ret=(zc.SVENPY20.resample('MS').first()[:-1].values/200*y20_annuity_ret[1:]+
#          y20_principal_ret[1:])

# My new way of doing things:
# y20dr is the daily return, and y20cr is the cumulative daily return
y20dr,y20cr=yield_curve.cumulative_return(years_tm=20)
# resample the returns however you like
# Make sure this works!
y20_dur=yield_curve.duration_from_par_yield(years_tm=20)

# Try continuous compounding par equivalent yield?
# ypar_cont=y20_exp**0*np.squeeze(np.array(1-np.exp(-y19_11_arr[-1]*y19_11_cont[:,-1])))/(
#     np.trapz(np.exp(-np.array(y19_11_cont)*
#     (np.array(np.asmatrix(np.ones(len(y20_exp))).T*np.asmatrix(y19_11_arr)))),
#         x=y19_11_arr))


# Make another series, with beta3=False (regular NS)
# y20_ns=zero_yields(zc,y20_arr,beta3=False)
# y20_par_ns=2*(1-(y20_exp**0*(
#     np.squeeze(np.array(np.exp(-y20_ns[:,-1]*y20_arr[-1]))))))/(np.sum(
#     np.exp(-np.array(y20_ns)*np.array(
#         np.asmatrix(np.ones(len(y20_exp))).T*np.asmatrix(y20_arr))),
#     axis=1)*y20_exp**0)
# y20_ns_exp=2*np.log(1+y20_par_ns/2)
# You might also want the duration for this, could be different than dgs20
# y20_ns_dur=(y20_ns_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(y20_ns_exp.values).T*
#     np.asmatrix(y20_arr))*np.asmatrix(y20_arr).T)))+
#       y20_arr[-1]*np.exp(-y20_arr[-1]*y20_ns_exp))  
# y19_11_ns=zero_yields(zc,y19_11_arr,beta3=False)
# I am calling this the annuity return; you could get the value of the annuity
# by multiplying by par_val
# y20_annuity_ns=(np.sum(
#     np.exp(-np.array(y19_11_ns)*np.array(
#         np.asmatrix(np.ones(len(y20_exp))).T*np.asmatrix(y19_11_arr))),
#     axis=1)*y20_exp**0).resample('MS').first()
# Likewise, the principal payment is given as a return here, but you can 
# multiply by par_val to get its value.
# y20_principal_ns=(y20_exp**0*(np.squeeze(np.array(
#     np.exp(-y19_11_ns[:,-1]*y19_11_arr[-1]))))).resample('MS').first()
# y20_ret_ns=(y20_par_ns.resample('MS').first()[:-1].values/2*y20_annuity_ns[1:]+
#          y20_principal_ns[1:])


#sven23_temp=zc.SVENPY23.resample('MS').first()/100
# so many problems; let's just try simple linear interpolation to get 22 yr,
# 11 month yield:
# THIS IS SO MUCH BETTER NOW! 
# I suspect an error in all the complicated code above to get yield via NSS
# sven22_11_temp=(zc.SVENPY22.resample('MS').first()+11/12.0*(
#     zc.SVENPY23.resample('MS').first()-zc.SVENPY22.resample('MS').first()))/100
# int_period=(sven22_11_temp[1:].index-sven22_11_temp[:-1].index).days
# sven23_alt=(sven23_temp[:-1].values*(int_period/365.24)+
#           sven23_temp[:-1].values/sven22_11_temp[1:]*(
#               1-(1+sven22_11_temp[1:]/2)**(2*int_period/365.24-2*23))+
#           (1+sven22_11_temp[1:]/2)**(2*int_period/365.24-2*23))




# Monthly return, using "Shiller Method"
# monthly return for 25 year bond:
# svenpy23_resample=12*((1+zc.SVENPY23.resample('M').last()/100)**(1/12.0)-1)
# svenpy23_ret=(svenpy23_resample[:-1].values/svenpy23_resample[1:]+svenpy23_resample[:-1].values/12+
#            (1-svenpy23_resample[:-1].values/svenpy23_resample[1:])*(
#                1+svenpy23_resample[1:]/12)**(-(23*12-1))) 
## flat term structure:
# svenpy23_resample=zc.SVENPY23.resample('M').last()/100
# int_period=(svenpy23_resample[1:].index-svenpy23_resample[:-1].index).days
# sven23_alt=(svenpy23_resample[:-1].values*(int_period/365.24)+
#           svenpy23_resample[:-1].values/svenpy23_resample[1:]*(
#               1-(1+svenpy23_resample[1:]/2)**(2*int_period/365.24-2*23))+
#           (1+svenpy23_resample[1:]/2)**(2*int_period/365.24-2*23))    
    
# get duration
# svenpy23_arr=0.5*np.arange(1,23*2+1)
# svenpy23_exp=2*np.log(1+zc.SVENPY23/200)
# svenpy23_dur=(svenpy23_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(svenpy23_exp.values).T*
#     np.asmatrix(svenpy23_arr))*np.asmatrix(svenpy23_arr).T)))+
#       svenpy23_arr[-1]*np.exp(-svenpy23_arr[-1]*svenpy23_exp)) 

# it might be interesting to see a 25 year zero, rolled monthly (really more 
# like quarterly)
#pzc=par_val/((1+(np.exp(zc[zc.columns[67:97]]/200)-1))**2)**(range(1,31))
#pzc25=par_val/((np.exp(zc.SVENY25/200))**2)**(25)

# What about starting with 25 and 1/24 year zero and selling after month 
# (24 and 23/24 year zero)
# buy_dur=25+30.41/365.24/2
# ybuy=(zc.BETA0+
# 			zc.BETA1*(1-np.exp(-buy_dur/zc.TAU1)
# 			)/(buy_dur/zc.TAU1)+
# 			zc.BETA2*((1-np.exp(-buy_dur/zc.TAU1)
# 			)/(buy_dur/zc.TAU1)-np.exp(-buy_dur/zc.TAU1))+
# 			zc.BETA3*((1-np.exp(-buy_dur/zc.TAU2)
# 			)/(buy_dur/zc.TAU2)-np.exp(-buy_dur/zc.TAU2)))
# pzc_buy=par_val/(np.exp(ybuy/200.0))**(2*buy_dur)


# rem_dur=25-30.41/365.24/2
# yeff=(zc.BETA0+
# 			zc.BETA1*(1-np.exp(-rem_dur/zc.TAU1)
# 			)/(rem_dur/zc.TAU1)+
# 			zc.BETA2*((1-np.exp(-rem_dur/zc.TAU1)
# 			)/(rem_dur/zc.TAU1)-np.exp(-rem_dur/zc.TAU1))+
# 			zc.BETA3*((1-np.exp(-rem_dur/zc.TAU2)
# 			)/(rem_dur/zc.TAU2)-np.exp(-rem_dur/zc.TAU2)))
## yeff must be converted from continuous compounding convention to 
## semi-annual coupon equivalent compounding convention!	
#pzc_sell=par_val/(np.exp(yeff/200.0))**(2*rem_dur)

# Monthly return for a 25 year zero coupon bond (STRIPS)
#zc25_ret=pzc_sell.resample('M').last().values[1:]/pzc_buy.resample('M').last()[:-1]

# New method, much simplier/cleaner.
# I think maturity=24.5 years is closer to EDV's target
zc25_ret,zc25cr=yield_curve.cumulative_strips_return(maturity_years=24.5)

#                        
#
#

# comparison
# time to maturity; must be an integer!
ttm_comp=7
ytm_comp=2*np.log(1+yield_curve.data[yield_curve.data.columns[
    36+ttm_comp]]/200)
marr_comp=0.5*np.arange(1,ttm_comp*2+1)
mod_dur_comp=(ytm_comp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(ytm_comp.values).T*
    np.asmatrix(marr_comp))*np.asmatrix(marr_comp).T)))+
      marr_comp[-1]*np.exp(-marr_comp[-1]*ytm_comp))

# Get the ratio of durations:
mod_dur=1.0*y20_dur
comp_ratio=mod_dur/mod_dur_comp

# calculate the modified duration for dgs7, to see comparison with SVENPY07
dgs7_exp=2*np.log(1+dgs7.DGS7/200)
dgs7_dur=(dgs7_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(dgs7_exp.values).T*
    np.asmatrix(marr_comp))*np.asmatrix(marr_comp).T)))+
      marr_comp[-1]*np.exp(-marr_comp[-1]*dgs7_exp))
# Try a monthly return, assuming annuity and principal:
dgs7_resample=12*((1+dgs7.DGS7.resample('M').last()/100)**(1/12.0)-1)
dgs7_ret=(dgs7_resample[:-1].values/dgs7_resample[1:]+dgs7_resample[:-1].values/12+
           (1-dgs7_resample[:-1].values/dgs7_resample[1:])*(
               1+dgs7_resample[1:]/12)**(-(7*12-1)))     


# For 5 year notes, using the NSS bootstrap of the yield curve (my preferred
# method)
# y5_arr=0.5*np.arange(1,5*2+1)
# y4_11_arr=0.5*np.arange(1,5*2+1)-1/12.0 
# int_period=(zc.SVENPY05[1:].index-zc.SVENPY05[:-1].index).days 
# y4_11_cont=zero_yields(zc,y4_11_arr)  
# y5_exp=2*np.log(1+zc.SVENPY05/200)
# y5_dur=(y5_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(y5_exp.values).T*
#     np.asmatrix(y5_arr))*np.asmatrix(y5_arr).T)))+
#       y5_arr[-1]*np.exp(-y5_arr[-1]*y5_exp))  
# y5_ret=(zc.SVENPY05.resample('M').last()[:-1].values/200*(
#     np.sum(np.exp(-np.array(y4_11_cont)*np.array(
#         np.asmatrix(np.ones(len(y4_11_cont))).T*np.asmatrix(y4_11_arr))),
#     axis=1)*zc.SVENPY05**0).resample('M').last()[1:]+
#     (zc.SVENPY05**0*(np.squeeze(np.array(np.exp(-y4_11_cont[:,-1]*y4_11_arr[-1]))))
#         ).resample('M').last()[1:])

# Using the faster method now:
y5_ret,y5_cr=yield_curve.cumulative_return(years_tm=5)
# resample the returns however you like
# Make sure this works!
y5_dur=yield_curve.duration_from_par_yield(years_tm=5)

    

# Same thing, but for dgs5:
dgs5_arr=0.5*np.arange(1,5*2+1)
dgs5_exp=2*np.log(1+dgs5.DGS5/200)
dgs5_dur=(dgs5_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(dgs5_exp.values).T*
    np.asmatrix(dgs5_arr))*np.asmatrix(dgs5_arr).T)))+
      dgs5_arr[-1]*np.exp(-dgs5_arr[-1]*dgs5_exp))
# Try a monthly return 
dgs5_resample=12*((1+dgs5.DGS5.resample('M').last()/200)**(1/6.0)-1)
# So far, this has come out the closest.
int_period=(dgs5_resample[1:].index-dgs5_resample[:-1].index).days
dgs5_ret=(dgs5_resample[:-1].values/dgs5_resample[1:]+
          dgs5_resample[:-1].values/12+
           (1-dgs5_resample[:-1].values/dgs5_resample[1:])*(
               1+dgs5_resample[1:]/12)**(-(5*12-1))) 
# Alternative formulation (trying to match Portfolio Visualizer)
# Monthly compounded data?
dgs5_mstart=12*((1+dgs5.DGS5.resample('MS').first()/200)**(1/6.0)-1)
dgs5_mend=12*((1+dgs5.DGS5.resample('M').last()/200)**(1/6.0)-1)

# This is even closer...
# From 1972 to 1990, total return is 5.03262, compared to PV 5.02337
dgs5_temp=dgs5.DGS5.resample('M').last()
int_period=(dgs5_temp[1:].index-dgs5_temp[:-1].index).days
dgs5_alt=(dgs5_temp[:-1].values/100*(int_period/365.24)+
          dgs5_temp[:-1].values/dgs5_temp[1:]*(
              1-(1+dgs5_temp[1:]/200)**(2*int_period/365.24-2*5))+
          (1+dgs5_temp[1:]/200)**(2*int_period/365.24-2*5))

# Another, similar attempt
#dgs5_temp=dgs5.DGS5.resample('M').last()
# dgs5_temp=zc.SVENPY05.resample('M').last()
# svenpy5_arr=0.5*np.arange(1,5*2+1)
# svenpy5_exp=2*np.log(1+zc.SVENPY05/200)
# svenpy5_dur=(svenpy5_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(svenpy5_exp.values).T*
#     np.asmatrix(svenpy5_arr))*np.asmatrix(svenpy5_arr).T)))+
#       svenpy5_arr[-1]*np.exp(-svenpy5_arr[-1]*svenpy5_exp))  
# dgs4_11=zc.SVENPY04.resample('M').last()+11/12.0*(
#     zc.SVENPY05.resample('M').last()-zc.SVENPY04.resample('M').last())
# int_period=(dgs5_temp[1:].index-dgs5_temp[:-1].index).days
# dgs5_lint=(dgs5_temp[:-1].values/100*(int_period/365.24)+
#           dgs5_temp[:-1].values/dgs4_11[1:]*(
#               1-(1+dgs4_11[1:]/200)**(2*int_period/365.24-2*5))+
#           (1+dgs4_11[1:]/200)**(2*int_period/365.24-2*5))


# Account for leap years or dont bother? dgs5.DGS5[1:].index.is_leap_year
int_period=(dgs5.DGS5[1:].index-dgs5.DGS5[:-1].index).days
dgs5_alt=(dgs5.DGS5[:-1].values/100*(int_period/365.24)+
          dgs5.DGS5[:-1].values/dgs5.DGS5[1:]*(
              1-(1+dgs5.DGS5[1:]/200)**(2*int_period/365.24-2*5))+
          (1+dgs5.DGS5[1:]/200)**(2*int_period/365.24-2*5))

# This works surprisingly poorly
# dgs5_ret=(dgs5_mstart.values/dgs5_mend+dgs5_mstart.values/12+
#            (1-dgs5_mstart.values/dgs5_mend)*(
#                1+dgs5_mend/12)**(-(5*12-1))) 

# Return of 5 year bond yields, using linear interpolation for roll down
cutoff='2021-09'
dgs5_temp=dgs5.DGS5.resample('M').last()[:cutoff]
dgs3_temp=dgs3.DGS3.resample('M').last()[:cutoff]
dgs4_11=dgs3_temp+23/24.0*(dgs5_temp.values-
                                    dgs3_temp.values)
int_period=(dgs5_temp[1:].index-dgs5_temp[:-1].index).days
dgs5_lint=(dgs5_temp[:-1].values/100*(int_period/365.24)+
          dgs5_temp[:-1].values/dgs4_11[1:]*(
              1-(1+dgs4_11[1:]/200)**(2*int_period/365.24-2*5))+
          (1+dgs4_11[1:]/200)**(2*int_period/365.24-2*5))

cutoff='2021-09'
# gs5_temp=gs5.GS5.resample('M').last()[:cutoff]
# gs3_temp=gs3.GS3.resample('M').last()[:cutoff]
gs5_temp=gs5.GS5
gs3_temp=gs3.GS3
gs4_11=gs3_temp+23/24.0*(gs5_temp.values-
                                    gs3_temp.values)
int_period=(gs5_temp[1:].index-gs5_temp[:-1].index).days
gs5_lint=(gs5_temp[:-1].values/100*(int_period/365.24)+
          gs5_temp[:-1].values/gs4_11[1:]*(
              1-(1+gs4_11[1:]/200)**(2*int_period/365.24-2*5))+
          (1+gs4_11[1:]/200)**(2*int_period/365.24-2*5))


# Same thing, but for gs5:
gs5_arr=0.5*np.arange(1,5*2+1)
gs5_exp=2*np.log(1+gs5.GS5/200)
gs5_dur=(gs5_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(gs5_exp.values).T*
    np.asmatrix(gs5_arr))*np.asmatrix(gs5_arr).T)))+
      gs5_arr[-1]*np.exp(-gs5_arr[-1]*gs5_exp))

# Try a monthly return 
gs5_resample=12*((1+gs5.GS5/200)**(1/6.0)-1)
gs5_ret=(gs5_resample[:-1].values/gs5_resample[1:]+
         gs5_resample[:-1].values/12+
           (1-gs5_resample[:-1].values/gs5_resample[1:])*(
               1+gs5_resample[1:]/12)**(-(5*12-1))).resample('M').last() 
# get duration

# splice all of the methods used to get the 5 year return.
y5_splice=pd.concat([gs5_lint[:gs5_lint[:y5_ret.index[0]].index[-2]],
    y5_ret])
y5_dur_splice=pd.concat([gs5_dur[:gs5_dur[:y5_dur.index[0]].index[-2]],
    y5_dur])

# Get Linear interpolation rolldown to get returns for 3 year using:
# gs1, gs3
# dgs1, dgs3
# Then, NSS to get returns for 3 year


# Same thing, but for dgs20:
dgs20_arr=0.5*np.arange(1,20*2+1)
dgs20_exp=2*np.log(1+dgs20.DGS20/200)
dgs20_dur=(dgs20_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(dgs20_exp.values).T*
    np.asmatrix(dgs20_arr))*np.asmatrix(dgs20_arr).T)))+
      dgs20_arr[-1]*np.exp(-dgs20_arr[-1]*dgs20_exp))
# This is even closer...
dgs20_temp=dgs20.DGS20.resample('M').last()
int_period=(dgs20_temp[1:].index-dgs20_temp[:-1].index).days
dgs20_alt=(dgs20_temp[:-1].values/100*(int_period/365.24)+
          dgs20_temp[:-1].values/dgs20_temp[1:]*(
              1-(1+dgs20_temp[1:]/200)**(int_period/365.24-2*20))+
          (1+dgs20_temp[1:]/200)**(int_period/365.24-2*20))
# Daily returns:
int_period=(dgs20.DGS20[1:].index-dgs20.DGS20[:-1].index).days
dgs20_alt=(dgs20.DGS20[:-1].values/100*(int_period/365.24)+
          dgs20.DGS20[:-1].values/dgs20.DGS20[1:]*(
              1-(1+dgs20.DGS20[1:]/200)**(2*int_period/365.24-2*20))+
          (1+dgs20.DGS20[1:]/200)**(2*int_period/365.24-2*20))
# Try a monthly return 
dgs20_resample=12*((1+dgs20.DGS20.resample('M').last()/200)**(1/6.0)-1)
dgs20_ret=(dgs20_resample[:-1].values/dgs20_resample[1:]+
           dgs20_resample[:-1].values/12+
           (1-dgs20_resample[:-1].values/dgs20_resample[1:])*(
               1+dgs20_resample[1:]/12)**(-(20*12-1))) 

# linear interpolation to get 19 year, 11 month bond
#dgs20_temp=zc.SVENPY20.resample('M').last()
# dgs20_temp=dgs20.resample('M').last()
# svenpy20_arr=0.5*np.arange(1,20*2+1)
# svenpy20_exp=2*np.log(1+zc.SVENPY20/200)
# svenpy20_dur=(svenpy20_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(svenpy20_exp.values).T*
#     np.asmatrix(svenpy20_arr))*np.asmatrix(svenpy20_arr).T)))+
#       svenpy20_arr[-1]*np.exp(-svenpy20_arr[-1]*svenpy20_exp))  
# dgs19_11=zc.SVENPY19.resample('M').last()+11/12.0*(
#     zc.SVENPY20.resample('M').last()-zc.SVENPY19.resample('M').last())
# int_period=(dgs20_temp[1:].index-dgs20_temp[:-1].index).days
# dgs20_lint=(dgs20_temp[:-1].values/100*(int_period/365.24)+
#           dgs20_temp[:-1].values/dgs19_11[1:]*(
#               1-(1+dgs19_11[1:]/200)**(2*int_period/365.24-2*20))+
#           (1+dgs19_11[1:]/200)**(2*int_period/365.24-2*20)) 

# gs20 goes back further
gs20_arr=0.5*np.arange(1,20*2+1)
gs20_exp=2*np.log(1+gs20.GS20/200)
gs20_dur=(gs20_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(gs20_exp.values).T*
    np.asmatrix(gs20_arr))*np.asmatrix(gs20_arr).T)))+
      gs20_arr[-1]*np.exp(-gs20_arr[-1]*gs20_exp))
# Try a monthly return, flat term structure
#gs20_resample=12*((1+gs20.GS20.resample('M').last()/200)**(1/6.0)-1)
gs20_resample=12*((1+gs20.GS20/200)**(1/6.0)-1)
gs20_ret=(gs20_resample[:-1].values/gs20_resample[1:]+gs20_resample[:-1]/12+
           (1-gs20_resample[:-1].values/gs20_resample[1:])*(
               1+gs20_resample[1:]/12)**(-(20*12-1))) 
# Better version, as used above:
int_period=(gs20.GS20[1:].index-gs20.GS20[:-1].index).days
gs20_alt=(gs20.GS20[:-1].values/100*(int_period/365.24)+
          gs20.GS20[:-1].values/gs20.GS20[1:]*(
              1-(1+gs20.GS20[1:]/200)**(2*int_period/365.24-2*20))+
          (1+gs20.GS20[1:]/200)**(2*int_period/365.24-2*20))

# Splice both 20y return series.
#y20_splice=pd.concat([dgs20_ret[:'1981-08-01'],y20_ret.dropna()])
# y20_splice=pd.concat([gs20_ret[:gs20_ret[:dgs20_ret.index[0]].index[-1]],
#     dgs20_ret[:y20_ret.dropna().index[0]],y20_ret.dropna()])

y20_splice=pd.concat([gs20_ret[:gs20_ret[:y20dr.dropna().index[0]].index[-1]],
    y20dr.dropna()])

# y20_dur_splice=pd.concat([gs20_dur[:gs20_dur[:dgs20_alt.index[0]].index[-1]],
#     dgs20_dur[:y20_dur.dropna().index[0]],y20_dur.dropna()])

# y20_dur_splice=pd.concat([gs20_dur[:gs20_dur[:dgs20_alt.index[0]].index[-1]],
#     dgs20_dur[:y20_dur.dropna().index[0]],y20_dur.dropna()])

y20_dur_splice=pd.concat([gs20_dur[:gs20_dur[:y20dr.dropna().index[0]].index[-1]],
    y20_dur[y20dr.dropna().index]])

# monthly return for 25 year bond:
# svenpy25_resample=12*((1+zc.SVENPY25.resample('M').last()/100)**(1/12.0)-1)
# svenpy25_ret=(svenpy25_resample[:-1].values/svenpy25_resample[1:]+svenpy25_resample[:-1].values/12+
#            (1-svenpy25_resample[:-1].values/svenpy25_resample[1:])*(
#                1+svenpy25_resample[1:]/12)**(-(25*12-1))) 
# # get duration
# svenpy25_arr=0.5*np.arange(1,25*2+1)
# svenpy25_exp=2*np.log(1+zc.SVENPY25/200)
# svenpy25_dur=(svenpy25_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(svenpy25_exp.values).T*
#     np.asmatrix(svenpy25_arr))*np.asmatrix(svenpy25_arr).T)))+
#       svenpy25_arr[-1]*np.exp(-svenpy25_arr[-1]*svenpy25_exp))   

# linear interpolation to get 24 year, 11 month bond
# dgs25_temp=zc.SVENPY25.resample('M').last()
# dgs24_11=zc.SVENPY24.resample('M').last()+11/12.0*(
#     zc.SVENPY25.resample('M').last()-zc.SVENPY24.resample('M').last())
# int_period=(dgs25_temp[1:].index-dgs25_temp[:-1].index).days
# dgs25_lint=(dgs25_temp[:-1].values/100*(int_period/365.24)+
#           dgs25_temp[:-1].values/dgs24_11[1:]*(
#               1-(1+dgs24_11[1:]/200)**(2*int_period/365.24-2*25))+
#           (1+dgs24_11[1:]/200)**(2*int_period/365.24-2*25)) 

## make a dataframe and concatenate 7y par equivalent and dgs7, turn ytm_comp
## back to percent
parequiv_cm_comp=pd.concat([100*ytm_comp,dgs7.DGS7],axis=1)
parequiv_cm_comp.dropna(inplace=True)
parequiv_cm_comp_diff=100*(parequiv_cm_comp[parequiv_cm_comp.columns[1]]-
                            parequiv_cm_comp[parequiv_cm_comp.columns[0]])



plt.figure()
plt.plot(mod_dur,label=str(ttm)+'y Maturity')
plt.plot(mod_dur_comp,label=str(ttm_comp)+'y Maturity')
plt.xlabel('Date')
plt.ylabel('Duration (years)')
plt.legend(loc='best')
plt.tight_layout()
#plt.savefig('duration_history.png')

plt.figure()
plt.plot(comp_ratio,label="("+str(ttm)+"y Par Equivalent)/("+
         str(ttm_comp)+"y Par Equivalent)"+
         " Duration Ratio" )
plt.xlabel('Date')
plt.legend(loc='best')
plt.tight_layout()
#plt.savefig('par_equiv_23y_to_7y_ratio.png')


plt.figure()
plt.title('Par-Equivalent Yield and DGS7 Comparison')
plt.plot(dgs7,'+r',label='DGS7')
#plt.plot(zc[zc.columns[36+ttm_comp]],label='Par Equivalent Yield From NSS Bootstrap')
#plt.plot(ytm_comp*100-dgs7,label='Par Equivalent Yield From NSS Bootstrap-DGS7')
plt.xlabel('Date')
plt.legend(loc='best')
plt.tight_layout()

plt.figure()
plt.title(str(ttm_comp)+'y Par Equivalent - '+str(ttm_comp)+'y CMT Histogram')
plt.hist(parequiv_cm_comp_diff,bins=100)
plt.ylabel('Counts')
plt.xlabel(str(ttm_comp)+'y Par Equivalent - '+str(ttm_comp)+'y CMT')


# A small snippet here to do backtesting for vfitx, vustx, and vfinx if you 
# have them:
 
# Need cash if you want to do a levered strategy
dtb3=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/DTB3')


# Might consider fed funds for borrowing rate?
fedfunds=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/FEDFUNDs')

# pick what to use as the borrow rate.
cash=dtb3

cash=fedfunds

cash=cash[cash.columns[0]]


# do 60/40 vfinx/vfitx split, cross check with portfolio visualizer!
# (I have to use first of the month here because of TB3MS)
#start_date='1971-12'
#start_date='1963'
#start_date='1976-12'
#start_date='1986-01'
#start_date='1986-05'
#start_date='1980-03'
#start_date='1981-09'
#start_date='2008-01-31'
#start_date='2009-01'
#start_date='1991-11'
#start_date='1990-12'
#start_date='1962-01'
#start_date='1994-01'
#start_date='1955-03-31'
start_date='1955'
#start_date='1954-07'
#start_date='1994'
#end_date='2021-09-30'
#end_date='2021-02'
#end_date='2019-03'
#end_date='1981-09-30'
#end_date='1981'
#end_date='1990-12'
#end_date='1995-01'
#end_date='2009-03'
end_date='2021-10'
#end_date='2022-01'


# In case you want to use shiller sp500 returns data:
vfinx_abbrev=gspc_splice[start_date:end_date].resample('M').last()
#vfinx_abbrev=((shiller.P[1:].values+shiller.D[1:].values/12)/shiller.P[:-1]).shift(1)[start_date:end_date].cumprod().shift(-1).resample('M').last()
#vfinx_abbrev=shiller_tr[start_date:end_date].shift(periods=-1).resample('M').last()
#vfinx_abbrev=shiller_tr[start_date:end_date].resample('M').last()
#vfinx_abbrev=vfinx[start_date:end_date].adjclose.resample('M').last()
#vfitx_abbrev=vfitx[start_date:end_date].adjclose.resample('M').last()
#vfitx_abbrev=dgs5_ret[start_date:end_date].cumprod()
#vfitx_abbrev=dgs5_lint[start_date:end_date].cumprod()
#vfitx_abbrev=y5_ret[start_date:end_date].cumprod()
vfitx_abbrev=(y5_splice[start_date:end_date].cumprod()).resample('M').last()
#vfitx_abbrev=gs5_ret[start_date:end_date].cumprod()
#vustx_abbrev=vustx[start_date:end_date].adjclose.resample('M').last()
#vustx_abbrev=svenpy25_ret[start_date:end_date].cumprod()/(svenpy25_ret[start_date:end_date][0])
#vustx_abbrev=dgs20_ret[start_date:end_date].cumprod()
#vustx_abbrev=y20_ret[start_date:end_date].cumprod()
vustx_abbrev=(y20_splice[start_date:end_date].cumprod()).resample('M').last()
#vustx_abbrev=dgs20_lint[start_date:end_date].cumprod()
#vustx_abbrev=gs20_ret[start_date:end_date].cumprod()
#vustx_abbrev=((zc25_ret[zc25_ret.columns[0]][start_date:end_date]).cumprod()).resample('M').last()
cash_abbrev=cash[start_date:end_date].resample('M').last()
# Simulate a small additional cost of leverage, 40 bps (unrealistic! should 
# change based on cyclical rate changes)
borrow_rate=cash_abbrev+0.4

dtb3_abbrev=dtb3.DTB3[start_date:end_date].resample('M').last()
fedfunds_abbrev=fedfunds.FEDFUNDS[start_date:end_date].resample('M').last()
# A special data series for the duration multiplier between "VUSTX" and "VFITX:
#dur_multiplier=comp_ratio[start_date:end_date].resample('M').last()
#dur_multiplier=(svenpy25_dur/dgs5_dur)[start_date:end_date].resample('M').last()
#dur_multiplier=(dgs20_dur/dgs5_dur)[start_date:end_date].resample('M').last()
#dur_multiplier=(dgs5_dur/dgs20_dur)[start_date:end_date].resample('M').last()
#dur_multiplier=(gs20_dur/gs5_dur)[start_date:end_date].resample('M').last()
#dur_multiplier=(gs5_dur/gs20_dur)[start_date:end_date].resample('M').last()
#dur_multiplier=(svenpy5_dur/svenpy20_dur)[start_date:end_date].resample('M').last()
#dur_multiplier=(gs5_dur/25.0)[start_date:end_date].resample('M').last()
#dur_multiplier=y5_dur_splice[start_date:end_date].resample('M').last()/y20_dur_splice[start_date:end_date].resample('M').last()
# Other way around:
dur_multiplier=y20_dur_splice[start_date:end_date].resample('M').last()/y5_dur_splice[start_date:end_date].resample('M').last()
#dur_multiplier=(y5_dur_splice/24.5)[start_date:end_date].resample('M').last()
#dur_multiplier=(24.5/y5_dur_splice)[start_date:end_date].resample('M').last()

#dur_multiplier=1.35/4.00*vfinx_abbrev**0
#dur_multiplier=1.35/2.5*vfinx_abbrev**0
#dur_multiplier=0.5*vfinx_abbrev**0
# The ridiculous, overfit 214% leverage ratio
#dur_multiplier=1.35/2.98*vfinx_abbrev**0

frac_vustx=1.0
frac_vfinx=0
#frac_vfitx=2.98
#frac_vfitx=2.50
#frac_vustx=dur_multiplier[0]*frac_vfitx
frac_vfitx=dur_multiplier[0]*frac_vustx
# a debt ratio?
#frac_itt_debt=1-(frac_vfinx+frac_vfitx)
start_cash=10e3

# A running tally of how much leverage is being taken, in percent above 100
ltt_leverage=np.zeros(len(vfinx_abbrev))
ltt_leverage[0]=frac_vfinx+frac_vustx-1
itt_leverage=np.zeros(len(vfinx_abbrev))
itt_leverage[0]=frac_vfinx+frac_vfitx-1

nvustx=np.zeros(len(vfinx_abbrev))
nvfinx=np.zeros(len(vfinx_abbrev))


nvustx[0]=start_cash*frac_vustx/vustx_abbrev[0]
nvfinx[0]=start_cash*frac_vfinx/vfinx_abbrev[0]

# Leveraged portfolio with ITT
nsp500_itt=np.zeros(len(vfinx_abbrev))
nvfitx=np.zeros(len(vfitx_abbrev))
debt=np.zeros(len(vfitx_abbrev))
debt[0]=-(1-frac_vfinx-frac_vfitx)*start_cash
nvfitx[0]=start_cash*frac_vfitx/vfitx_abbrev[0]
nsp500_itt[0]=start_cash*frac_vfinx/vfinx_abbrev[0]
sp500_itt=np.zeros(len(vfinx_abbrev))
sp500_itt[0]=start_cash

# leveraged portfolio with LTT
nsp500_ltt=np.zeros(len(vfinx_abbrev))
nvustx=np.zeros(len(vfinx_abbrev))
debt_ltt=np.zeros(len(vfinx_abbrev))
debt_ltt[0]=-(1-frac_vfinx-frac_vustx)*start_cash
nvustx[0]=start_cash*frac_vustx/vustx_abbrev[0]
nsp500_ltt[0]=start_cash*frac_vfinx/vfinx_abbrev[0]
sp500_ltt=np.zeros(len(vfinx_abbrev))
sp500_ltt[0]=start_cash

# A "vanilla" portfolio
port_val=np.zeros(len(vfinx_abbrev))
port_val[0]=start_cash

# Years between updates to cash index
cash_years=(cash_abbrev.index[1:]-cash_abbrev.index[:-1]).days/360
#
fedfunds_years=(fedfunds_abbrev.index[1:]-fedfunds_abbrev.index[:-1]).days/360



# I had added a 1 to len(vfinx_abbrev) before, but I don't remember why
for i in range(1,len(vfinx_abbrev.index[1:])+1):
    # Calculate the current value of a basic portfolio
    #port_val[i]=nvustx[i-1]*vustx_abbrev[i]+nvfinx[i-1]*vfinx_abbrev[i]
    # Now adjust the shares to be in-line with the asset allocation
    #nvustx[i]=port_val[i]*frac_vustx/vustx_abbrev[i]
    #nvfinx[i]=port_val[i]*frac_vfinx/vfinx_abbrev[i]
    
    # The original HFEA leveraged portfolio
    # sp500_ltt[i]=(nvustx[i-1]*vustx_abbrev[i]+
    #               nsp500_ltt[i-1]*vfinx_abbrev[i]-
    #               debt_ltt[i-1]*cash_abbrev[i-1]/12/100
    #               -debt_ltt[i-1])
    sp500_ltt[i]=(nvustx[i-1]*vustx_abbrev[i]+
                  nsp500_ltt[i-1]*vfinx_abbrev[i]-
                  debt_ltt[i-1]*borrow_rate[i-1]/12/100
                  -debt_ltt[i-1])
    # recalculate the duration multiplier (to keep same risk as vfitx)
    #frac_vustx=dur_multiplier[i]*frac_vfitx
    # Now adjust the shares to be in-line with the asset allocation; reset
    # the leverage as well
    debt_ltt[i]=-(1-frac_vfinx-frac_vustx)*sp500_ltt[i]
    nvustx[i]=(sp500_ltt[i])*frac_vustx/vustx_abbrev[i]
    nsp500_ltt[i]=(sp500_ltt[i])*frac_vfinx/vfinx_abbrev[i] 
    # Keep track of the leverage; subtract by 1 to see how much leverage
    # you are taking
    ltt_leverage[i]=frac_vfinx+frac_vustx-1
    
    # A leveraged portfolio needs to pay the interest, 
    # sp500_itt[i]=(nvfitx[i-1]*vfitx_abbrev[i]+
    #               nsp500_itt[i-1]*vfinx_abbrev[i]-
    #               debt[i-1]*cash_abbrev[i-1]/12/100
    #               -debt[i-1])
    sp500_itt[i]=(nvfitx[i-1]*vfitx_abbrev[i]+
                  nsp500_itt[i-1]*vfinx_abbrev[i]-
                  debt[i-1]*borrow_rate[i-1]/12/100
                  -debt[i-1])
    # recalculate the duration multiplier (to keep same risk as vustx)
    frac_vfitx=dur_multiplier[i]*frac_vustx
    # Now adjust the shares to be in-line with the asset allocation; reset
    # the leverage as well
    debt[i]=-(1-frac_vfinx-frac_vfitx)*sp500_itt[i]
    nvfitx[i]=(sp500_itt[i])*frac_vfitx/vfitx_abbrev[i]
    nsp500_itt[i]=(sp500_itt[i])*frac_vfinx/vfinx_abbrev[i] 
    # Keep track of the leverage; subtract by 1 to see how much leverage
    # you are taking
    itt_leverage[i]=frac_vfinx+frac_vfitx-1
    
    
# make data series.
#port_series=pd.Series(data=port_val,index=vfinx_abbrev.index)

sp500_itt_series=pd.Series(data=sp500_itt,index=vfinx_abbrev.index)

sp500_ltt_series=pd.Series(data=sp500_ltt,index=vfinx_abbrev.index)

# Leverage time series
itt_leverage_series=pd.Series(data=itt_leverage,index=vfinx_abbrev.index)
ltt_leverage_series=pd.Series(data=ltt_leverage,index=vfinx_abbrev.index)


# Returns:
# calculate the monthly return on 3 month treasury bill:
# recall that tbills use actual/360 day count convention!
# leap_year_fix=(cash_abbrev.index.is_leap_year[1:])*366+(
#     ~cash_abbrev.index.is_leap_year[1:])*365
cash_tot_return=(1+dtb3_abbrev[:-1]*cash_years/100).cumprod()

cash_cagr=(cash_tot_return[-1]-1)**(1/(
    (cash_tot_return.index[-1]-cash_tot_return.index[0]).days/365.24))

# Get total return for fed funds rate:
fedfunds_tot_return=(1+fedfunds_abbrev[:-1]*fedfunds_years/100).cumprod()

# I use the little trick cash_abbrev[:-1].values*cash_abbrev[1:]**0 to make
# sure the returns correspond to the date when the bill would pay out, not
# when it is purchased.
#cash_log_ret=np.log(1+cash_abbrev[:-1].values*cash_abbrev[1:]**0*(
#    cash_abbrev.index[1:]-cash_abbrev.index[:-1]).days/365.0/100)

cash_ret=(dtb3_abbrev[:-1].values*dtb3_abbrev[1:]**0*(
    dtb3_abbrev.index[1:]-dtb3_abbrev.index[:-1]).days/360/100)
    
# Portfolio Visualizer uses regular returns for Sharpe ratio!
#sp500_ltt_ret=np.log(sp500_ltt_series[1:]/sp500_ltt_series[:-1].values)
sp500_ltt_ret=(sp500_ltt_series[1:]/sp500_ltt_series[:-1].values-1)
sp500_ltt_std=100*sp500_ltt_ret.std()*np.sqrt(12)

# Portfolio Visualizer uses regular returns for Sharpe ratio!
#sp500_itt_ret=np.log(sp500_itt_series[1:]/sp500_itt_series[:-1].values)
sp500_itt_ret=(sp500_itt_series[1:]/sp500_itt_series[:-1].values-1)
sp500_itt_std=100*sp500_itt_ret.std()*np.sqrt(12)


# Portfolio Visualizer uses regular returns for Sharpe ratio!
#sp500_ret=np.log(vfinx_abbrev[1:]/vfinx_abbrev[:-1].values)
sp500_ret=(vfinx_abbrev[1:]/vfinx_abbrev[:-1].values-1).astype(float)
sp500_std=100*sp500_ret.std()*np.sqrt(12)

# Get the standard deviations from the monthly data, for each year:
#sp500_ltt_std=sp500_ltt_ret.groupby(sp500_ltt_ret.index.year).std()
#sp500_ltt_std=(sp500_ltt_ret-cash_log_ret).groupby(sp500_ltt_ret.index.year).std()
#sp500_ltt_sharpe=(sp500_ltt_ret-cash_log_ret).groupby(sp500_ltt_ret.index.year).mean()/(sp500_ltt_std)

# Sharpe ratio, monthly, and then annualized with np.sqrt(12)
ltt_sharpe=(sp500_ltt_ret-cash_ret).mean()*np.sqrt(12)/(
    sp500_ltt_ret-cash_ret).std()

itt_sharpe=(sp500_itt_ret-cash_ret).mean()*np.sqrt(12)/(
    sp500_itt_ret-cash_ret).std()

sp500_sharpe=(sp500_ret-cash_ret).mean()*np.sqrt(12)/(
    sp500_ret-cash_ret).std()



# We can calculate Modigliani Measure; double check to make sure this is correct!
ltt_modigliani=100*((sp500_ltt_ret-cash_ret).mean()*(
    sp500_ret-cash_ret).std()/(sp500_ltt_ret-cash_ret).std()+
    (cash_cagr-1))
itt_modigliani=100*((sp500_itt_ret-cash_ret).mean()*(
    sp500_ret-cash_ret).std()/(sp500_itt_ret-cash_ret).std()+
    (cash_cagr-1))


plt.figure();
plt.title('Leverage funded at rate: ' + cash.name)
plt.plot(sp500_itt_series,'+',
         label=str('%.0f' %(frac_vfinx*100))+' SP500, 200 5y, St. Dev: '+
         str('%.2f' %sp500_itt_std)+
         ', Sharpe: '+str('%.2f' %itt_sharpe))
plt.plot(sp500_ltt_series,'.',
         label=str('%.0f' %(frac_vfinx*100))+' SP500, 200*dur(5y)/dur(20y)*20y, St. Dev: '+
         str('%.2f' %sp500_ltt_std)+
         ', Sharpe: '+str('%.2f' %ltt_sharpe))
plt.plot(10e3*vfinx_abbrev/vfinx_abbrev[0],label='SP500, St. Dev: ' +
         str('%.2f' %sp500_std)+
         ', Sharpe: '+str('%.2f' %sp500_sharpe))
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
plt.yscale('log')
plt.legend(loc='best')
plt.grid(which='both',axis='both')
plt.tight_layout()
#plt.savefig('165_135_vustx_vs_itt_leverage_match.png')

    
# Interesting, "telltale chart" 
plt.figure();
plt.title('('+str('%.0f' %(frac_vfinx*100))+' SP500 + '
          +str('%.0f' %(frac_vfitx*100))+' ITT)/('
          +str('%.0f' %(frac_vfinx*100))+' SP500 + LTT) Telltale Chart')
plt.plot(sp500_itt_series/sp500_ltt_series);plt.yscale('log')
plt.ylabel('(ITT Portfolio Value)/(LTT Portfolio Value)')
plt.xlabel('Date')
plt.tight_layout()
#plt.savefig('hfea_mhfea_telltale_chart.png')

# plot the leverage above 100%
plt.figure();
#plt.title('')
plt.plot(itt_leverage_series, label='LTT Portfolio Leverage');
plt.plot(ltt_leverage_series, label='ITT Portfolio Leverage')
plt.ylabel('Leverage above 100')
plt.xlabel('Date')

    

