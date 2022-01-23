#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 21:30:07 2021
    bond_etf_calibration.py
        This script gets a bond etf price history, and compares to an interest
        rate (or collection of rates) history to it.
        
        Get MAPE, other metrics to compare.
@author: jeff
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
## import the csv reader for FRED data, yahoo, etc.
sys.path.insert(1, '/Users/jeff/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader
from yahoo_stock_query import yahoo_stock_query
from FedsYieldCurve import FedsYieldCurve

# I want to use this; figure out how to make it work!
def get_hurst_exponent(time_series, max_lag=20):
    """Returns the Hurst Exponent of the time series"""
    
    lags = range(2, max_lag)

    # variances of the lagged differences
    tau = [np.std(np.subtract(time_series[lag:], time_series[:-lag])) for lag in lags]

    # calculate the slope of the log plot -> the Hurst Exponent
    reg = np.polyfit(np.log(lags), np.log(tau), 1)

    return reg[0]

# Get NSS yield curve data
# url='https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv';
# zc=pd.read_csv(url,sep=',',header=7)
# zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
# zc.set_index('Date',inplace=True)
par_val=1000
# Use FedsYieldCurve class to get the yield curve based on off the run issues
yield_curve=FedsYieldCurve.get_data()





# Here is an example etf to calibrate
ticker='VUSTX'
instrument=yahoo_stock_query(ticker,filename='',query=True,dividends=True)

# convert to monthly total return
instrument_monthly=instrument.adjclose.resample('M').last()/(
    instrument.adjclose.resample('M').last()[0])


# The comparison instrument:
#comparison=gs20_ret[start_date:].cumprod()/gs20_ret[start_date]

# Various Barclays Indices:
# 20 year bond index
barclays_20=pd.read_csv('/Users/jeff/Desktop/finance/data/bonds/BSWRTU20.csv',
                        header=2,error_bad_lines=False).dropna()
barclays_20['Date'] = pd.to_datetime(barclays_20.Date,infer_datetime_format=True)
barclays_20=barclays_20.set_index('Date')
barclays_20=barclays_20[barclays_20.columns].apply(pd.to_numeric,errors='coerce')
# convert to regular series and resample to daily frequency.
barclays_20=barclays_20['Index Level'].resample('D').asfreq().fillna(method='ffill')
barclays_20_start=barclays_20.index[0]

# SVENPY20 will serve as the comparison.
# svenpy20_temp=zc.SVENPY20.resample('M').last()
# svenpy20_arr=0.5*np.arange(1,20*2+1)
# svenpy20_exp=2*np.log(1+zc.SVENPY20/200)
# svenpy20_dur=(svenpy20_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(svenpy20_exp.values).T*
#     np.asmatrix(svenpy20_arr))*np.asmatrix(svenpy20_arr).T)))+
#       svenpy20_arr[-1]*np.exp(-svenpy20_arr[-1]*svenpy20_exp))  
# svenpy19_11=zc.SVENPY19.resample('M').last()+11/12.0*(
#     zc.SVENPY20.resample('M').last()-zc.SVENPY19.resample('M').last())
# int_period=(svenpy20_temp[1:].index-svenpy20_temp[:-1].index).days
# svenpy20_lint=(svenpy20_temp[:-1].values/100*(int_period/365.24)+
#           svenpy20_temp[:-1].values/svenpy19_11[1:]*(
#               1-(1+svenpy19_11[1:]/200)**(2*int_period/365.24-2*20))+
#           (1+svenpy19_11[1:]/200)**(2*int_period/365.24-2*20)) 
# My new way of doing things:
# y20dr is the daily return, and y20cr is the cumulative daily return
y20dr,y20cr=yield_curve.cumulative_return(years_tm=20)
# resample the returns however you like
# Make sure this works!
y20_dur=yield_curve.duration_from_par_yield(years_tm=20)

# gs20 data goes back further, but it is monthly:
gs20=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/GS20')

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

# Try spglobal, see how it compares
# sp20plus=pd.read_csv('/Users/jeff/Desktop/finance/data/bonds/spglobal_20_plus.csv',
#                      header=3,decimal=",")
sp20plus=pd.read_excel('/Users/jeff/Desktop/finance/data/bonds/spglobal_20_plus.xls',
                    header=6,skipfooter=1,thousands=',')
sp20plus.dropna(inplace=True)
sp20plus['Effective date ']=pd.to_datetime(sp20plus['Effective date '],
                                       infer_datetime_format=True)
sp20plus.set_index('Effective date ',inplace=True)
sp20plus_start=sp20plus.index[0]


# Also compare futures, probably closest in maturity to 20y (or is zb closer?)
sp20ub=pd.read_excel('/Users/jeff/Desktop/finance/data/bonds/spglobal_ub_futures.xls',
                    header=6,skipfooter=1,thousands=',')
sp20ub.dropna(inplace=True)
sp20ub['Effective date ']=pd.to_datetime(sp20ub['Effective date '],
                                       infer_datetime_format=True)
sp20ub.set_index('Effective date ',inplace=True)
sp20ub_start=sp20ub.index[0]

# 25 year bond index
barclays_25=pd.read_csv('/Users/jeff/Desktop/finance/data/bonds/BSWRTU25.csv',
                        header=2,error_bad_lines=False).dropna()
barclays_25['Date'] = pd.to_datetime(barclays_25.Date,infer_datetime_format=True)
barclays_25=barclays_25.set_index('Date')
barclays_25=barclays_25[barclays_25.columns].apply(pd.to_numeric,errors='coerce')


# VGLT as an index func comparison
vglt=yahoo_stock_query(ticker='VGLT',dividends=True)
vglt_start=vglt.index[0]


# 5 year bond index
barclays_5=pd.read_csv('/Users/jeff/Desktop/finance/data/bonds/BSWRTU05.csv',
                        header=2,error_bad_lines=False).dropna()
barclays_5['Date'] = pd.to_datetime(barclays_5.Date,infer_datetime_format=True)
barclays_5=barclays_5.set_index('Date')
barclays_5=barclays_5[barclays_5.columns].apply(pd.to_numeric,errors='coerce')
# convert to regular series and resample to daily frequency.
barclays_5=barclays_5['Index Level'].resample('D').asfreq().fillna(method='ffill')
barclays_5_start=barclays_5.index[0]

# SVENPY05 will serve as the comparison;
# Look at various implementations (linear interpolated rolldown, NSS rolldown,
# flat term structure, etc.)
# svenpy5_temp=zc.SVENPY05.resample('M').last()
# svenpy5_arr=0.5*np.arange(1,5*2+1)
# svenpy5_exp=2*np.log(1+zc.SVENPY05/200)
# svenpy5_dur=(svenpy5_exp/2*np.squeeze(np.asarray((np.exp(-np.asmatrix(svenpy5_exp.values).T*
#     np.asmatrix(svenpy5_arr))*np.asmatrix(svenpy5_arr).T)))+
#       svenpy5_arr[-1]*np.exp(-svenpy5_arr[-1]*svenpy5_exp))  
# svenpy4_11=zc.SVENPY04.resample('M').last()+11/12.0*(
#     zc.SVENPY05.resample('M').last()-zc.SVENPY04.resample('M').last())
# int_period=(svenpy5_temp[1:].index-svenpy5_temp[:-1].index).days
# svenpy5_lint=(svenpy5_temp[:-1].values/100*(int_period/365.24)+
#           svenpy5_temp[:-1].values/svenpy4_11[1:]*(
#               1-(1+svenpy4_11[1:]/200)**(2*int_period/365.24-2*5))+
#           (1+svenpy4_11[1:]/200)**(2*int_period/365.24-2*5)) 

y5dr,y5cr=yield_curve.cumulative_return(years_tm=5)
# resample the returns however you like
# Make sure this works!
y5_dur=yield_curve.duration_from_par_yield(years_tm=5)

# What is a good term to maturity for the ctd of a 5 year note futures 
# contract? Obviously it changed over time, but I think 4.5 is close now
y4_5dr,y4_5cr=yield_curve.cumulative_return(years_tm=4.5)
y4_5_dur=yield_curve.duration_from_par_yield(years_tm=4.5)

# Try to load spglobal data; difficult format for me to parse.
# Hopefully this pattern works for other spglobal files.
spg_5=pd.read_excel('/Users/jeff/Desktop/finance/data/bonds/spglobal_5yr.xls',
                    header=6,skipfooter=1,thousands=',')
spg_5.dropna(inplace=True)
spg_5['Effective date ']=pd.to_datetime(spg_5['Effective date '],
                                       infer_datetime_format=True)
spg_5.set_index('Effective date ',inplace=True)
# convert to regular series and resample to daily frequency.
spg_5=spg_5[spg_5.columns[0]].resample('D').asfreq().fillna(method='ffill')
spg_5_start=spg_5.index[0]

# The five year futures index:
spg_future_5=pd.read_excel('/Users/jeff/Desktop/finance/data/bonds/spglobal_5y_futures.xls',
                    header=6,skipfooter=1,thousands=',')
spg_future_5.dropna(inplace=True)
spg_future_5['Effective date ']=pd.to_datetime(spg_future_5['Effective date '],
                                       infer_datetime_format=True)
spg_future_5.set_index('Effective date ',inplace=True)
# convert to regular series and resample to daily frequency.
spg_future_5=spg_future_5[spg_future_5.columns[0]].resample('D').asfreq().fillna(method='ffill')
spg_future_5_start=spg_future_5.index[0]


# VGIT as another comparison
vgit=yahoo_stock_query(ticker='VGIT',dividends=True)
vgit_start=vgit.index[0]

vfiux=yahoo_stock_query(ticker='VFIUX',dividends=True)
vfiux_start=vfiux.index[0]

# VSIGX is probably the best comparison for 5 year notes.
vsigx=yahoo_stock_query(ticker='VSIGX',dividends=True)
vsigx_start=vsigx.index[0]

# Five year futures index, appears to be useless to me right now
barclays_fv=pd.read_csv('/Users/jeff/Desktop/finance/data/bonds/BXIITEFV.csv',
                        header=2,error_bad_lines=False).dropna()
barclays_fv['Date'] = pd.to_datetime(barclays_fv.Date,infer_datetime_format=True)
barclays_fv=barclays_fv.set_index('Date')
barclays_fv=barclays_fv[barclays_fv.columns].apply(pd.to_numeric,errors='coerce')


# Barclays Cash index
barclays_cash=pd.read_csv('/Users/jeff/Desktop/finance/data/bonds/BCC23MTB.csv',
                        header=2,error_bad_lines=False).dropna()
barclays_cash['Date'] = pd.to_datetime(barclays_cash.Date,infer_datetime_format=True)
barclays_cash=barclays_cash.set_index('Date')
barclays_cash=barclays_cash[barclays_cash.columns].apply(pd.to_numeric,errors='coerce')
barclays_cash_start=barclays_cash.index[0]

# What about starting with 25 and 1/24 year zero and selling after month 
# (24 and 23/24 year zero)
# buy_dur=24+30.41/365.24/2
# ybuy=(zc.BETA0+
# 			zc.BETA1*(1-np.exp(-buy_dur/zc.TAU1)
# 			)/(buy_dur/zc.TAU1)+
# 			zc.BETA2*((1-np.exp(-buy_dur/zc.TAU1)
# 			)/(buy_dur/zc.TAU1)-np.exp(-buy_dur/zc.TAU1))+
# 			zc.BETA3*((1-np.exp(-buy_dur/zc.TAU2)
# 			)/(buy_dur/zc.TAU2)-np.exp(-buy_dur/zc.TAU2)))
# pzc_buy=par_val/(np.exp(ybuy*buy_dur/100.0))


# rem_dur=24-30.41/365.24/2
# yeff=(zc.BETA0+
# 			zc.BETA1*(1-np.exp(-rem_dur/zc.TAU1)
# 			)/(rem_dur/zc.TAU1)+
# 			zc.BETA2*((1-np.exp(-rem_dur/zc.TAU1)
# 			)/(rem_dur/zc.TAU1)-np.exp(-rem_dur/zc.TAU1))+
# 			zc.BETA3*((1-np.exp(-rem_dur/zc.TAU2)
# 			)/(rem_dur/zc.TAU2)-np.exp(-rem_dur/zc.TAU2)))
## yeff must be converted from continuous compounding convention to 
## semi-annual coupon equivalent compounding convention!	
#pzc_sell=par_val/(np.exp(yeff*rem_dur/100.0))

# Monthly return for a 25 year zero coupon bond (STRIPS)
# a bid ask spread of 0.5% means that each return should be multiplied by 
# 0.995?
# (1-0.0025)/(1+0.0025)
# Some snooping shows 0.9996215092173162 gives the correct cagr; 3.785 bps 
# "cost" per month
# zc25_ret=pzc_sell.resample('M').last()[1:]/(
#     pzc_buy.resample('M').last()[:-1].values)



start_date=instrument_monthly.index[0]
end_date=pd.to_datetime('2021-09-30')

elapsed_time=(end_date-start_date).days/365.24

# Can we try applying an expense ratio?
# er=0.06

# zc_abbrev=zc25_ret[start_date:end_date].cumprod()/(
#     zc25_ret[start_date:end_date].cumprod()[0])

# New method, much simplier/cleaner.
strips25dr,strips25cr=yield_curve.cumulative_strips_return(maturity_years=24.5)

zc_abbrev=strips25cr[start_date:end_date]

ticker='VEDTX'
vedtx=yahoo_stock_query(ticker,filename='',query=True,dividends=True)
vedtx_daily=vedtx.adjclose.resample('D').asfreq().fillna(method='ffill')
vedtx_start=vedtx_daily.index[0]


# The comparison instrument:
comparison=gs20_ret[start_date:].cumprod()/gs20_ret[start_date]


# Calculate important metrics
#zc_cagr=100*((zc_abbrev[end_date]/zc_abbrev[start_date])**(1/elapsed_time)-1)
comparison_cagr=100*((comparison[end_date]/comparison[start_date])**(1/elapsed_time)-1)


instrument_cagr=100*((instrument_monthly[end_date]/instrument_monthly[start_date])**(1/elapsed_time)-1)

mape=100/len(zc_abbrev)*np.sum(abs((comparison-instrument_monthly)/instrument_monthly))

mse=1/len(zc_abbrev)*np.sum((comparison-instrument_monthly)**2)

# Path for saving plots.
path='/Users/jeff/Desktop/finance/data/bonds/'

# Now make a plot to show the comparison.
plt.figure();
#plt.title(str(ticker)+' and 25y ZC comparison, MAPE = %.2f' %mape)
plt.title(str(ticker)+' and GS20 comparison, MAPE = %.2f' %mape)
plt.plot(instrument_monthly,'o',
         label=str(ticker)+', CAGR: %.2f' %instrument_cagr)
#plt.plot(zc_abbrev,'+',label='25y ZC, CAGR: %.2f' %zc_cagr)
plt.plot(comparison,'+',label='GS20 Comparison CAGR: %.2f' %comparison_cagr)
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
#plt.yscale('log')
plt.legend(loc='best')
plt.grid(which='both',axis='both')
plt.tight_layout()


# Compare SVENPY20 and Barclays 20 year index
y20_start=barclays_20_start
#y20_start=sp20plus_start
plt.figure();
plt.title('20Y Treasury Total Return Indices')
plt.plot(100*barclays_20['Index Level'][y20_start:]/
         barclays_20['Index Level'][y20_start],'--',label='Barclays 20Y')
plt.plot(100*y20dr[y20_start:].cumprod()/0.966378,
         'x',label='NSS Roll')
#plt.plot(100*svenpy20_lint[barclays_20_start:].cumprod(),'+',label='SVENPY20 L. Int.')
plt.plot(100*dgs20_ret[y20_start:].cumprod()/dgs20_ret[y20_start],
         '.',label='Flat Term Structure Roll')
plt.plot(100*vglt.adjclose[y20_start:]/vglt.adjclose[y20_start],':',
         label='VGLT')
plt.plot(100*sp20plus[sp20plus.columns[0]][y20_start:]/(
    sp20plus[sp20plus.columns[0]][y20_start]),label='SPGlobal 20+y TR Index')
plt.plot(100*sp20ub[sp20ub.columns[0]][y20_start:]/(
    sp20ub[sp20ub.columns[0]][y20_start]),label='SPGlobal UB TR Index')
plt.xlabel('Date')
plt.ylabel('Total Return Index (Start at 100)')
plt.legend(loc='best')
plt.tight_layout()

plt.savefig(path+'y20_ret_calibration.png')

plt.figure()
plt.plot((100*(y20dr[barclays_20_start:].resample('M').last()).cumprod())/
         (barclays_20[barclays_20_start:]/
         barclays_20[barclays_20_start]).resample('M').last()-100)

# Compare SVENPY05 and Barclays 5 year index;
# Might also consider VGIT and VFITX
# 30 November 2021: Now I have spglobal 5 year note total return index!
#y5_start='2001-04-30'
y5_start=spg_5_start
plt.figure();
plt.subplot(2,1,1)
plt.title('5Y Treasury Total Return Indices')
plt.plot(100*barclays_5[y5_start:]/barclays_5[y5_start],'--',
         label='Barclays 5Y')
#plt.plot(100*vfiux.adjclose[y5_start:]/vfiux.adjclose[y5_start], label='VFIUX')
#plt.plot(100*vfitx.adjclose[y5_start:]/vfitx.adjclose[y5_start], label='VFITX')
plt.plot(100*vsigx.adjclose[y5_start:]/vsigx.adjclose[y5_start], label='VSIGX')
# Flat term structure works poorly, as should be expected; maybe remove
#plt.plot(100*dgs5_lint[y5_start:].cumprod(),'+',label='DGS5 L. Int. Roll')
#plt.plot(100*y5_ret[y5_start:].cumprod(),'x',label='NSS Roll')
#plt.plot(100*y5_splice[y5_start:].cumprod(),'x',label='NSS Roll')
plt.plot(100*y5dr[y5_start:].cumprod(),'x',label='NSS Roll')
plt.plot(100*spg_5[y5_start:]/(spg_5[y5_start]),':',
         label='SPGlobal 5y TR Index')
plt.plot(100*spg_future_5[y5_start:]/(spg_future_5[y5_start]),'.',
                                        label='SPGlobal 5y Futures TR Index')
#plt.plot(100*dgs5_ret[y5_start:].cumprod(),'*',label='DGS5 Flat Term Structure Roll')
plt.xlabel('Date')
plt.ylabel('Total Return Index (Start at 100)')
# Make subplot below this with a "tell-tale" chart
plt.legend(loc='best')
plt.subplot(2,1,2)
plt.title('TellTale Chart')
# What is best to plot here??
plt.xlabel('Date')
plt.ylabel('Cumulative Return Ratios')
# should I divide y5_splice by the first return factor?
# plt.plot(100*y5_splice[y5_start:].cumprod()/y5_splice[y5_start]/(
#     barclays_5[y5_start:]/barclays_5[y5_start]),
#     label='(NSS Roll Model)/(Barclays 5Y)')
# plt.plot(100*y5_splice[y5_start:].cumprod()/y5_splice[y5_start]/(
#     vsigx.adjclose[y5_start:]/vsigx.adjclose[y5_start]),
#     label='(NSS Roll Model)/VSIGX')
plt.plot(100*y5dr[y5_start:].cumprod()/y5dr[y5_start]/(
    barclays_5[y5_start:]/barclays_5[y5_start]),
    label='(NSS Roll Model)/(Barclays 5Y)')
plt.plot(100*y5dr[y5_start:].cumprod()/y5dr[y5_start]/(
    vsigx.adjclose[y5_start:]/vsigx.adjclose[y5_start]),
    label='(NSS Roll Model)/VSIGX')
plt.plot(100*spg_5[y5_start:]/spg_5[y5_start]/(
    barclays_5[y5_start:]/barclays_5[y5_start]),
    label='(SPGlobal 5y)/(Barclays 5)')
plt.legend(loc='best')
plt.tight_layout()
plt.savefig(path+'y5_ret_calibration.png')

# Cash index comparisons



