#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  2 08:54:42 2021

@author: jeff
"""
import pandas as pd
import numpy as np

url='https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv';
zc=pd.read_csv(url,sep=',',header=7)
zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
zc.set_index('Date',inplace=True)

## most recent set of zc data 
yield_curve=zc.iloc[-1]
last_date=zc.index[-1]


## for monthly frequency, use 1/12.0
freq=1/12.0
## number of years where payments are needed
nyears=30
npayments=nyears*(1/freq)

## as an example, consider a mortgage:
principal=400e3
## the mortgage payment, from the annuity equation
## interest rate of mortgage
r_mort=0.025
mort=principal*(r_mort*freq*(1+r_mort*freq)**(npayments)/
                ((1+r_mort*freq)**npayments-1))

## required payment and frequency (/year)
p=1.0*mort/freq


## array of time until each payment
tarr=(1+np.arange(npayments))*freq


## plug into equation 22 from Gurkayanka
yrem=(zc.BETA0.loc[last_date]+
		zc.BETA1.loc[last_date]*(1-np.exp(-tarr/zc.TAU1.loc[last_date])
		)/(tarr/zc.TAU1.loc[last_date])+
		zc.BETA2.loc[last_date]*((1-np.exp(-tarr/zc.TAU1.loc[last_date])
		)/(tarr/zc.TAU1.loc[last_date])-np.exp(-tarr/zc.TAU1.loc[last_date]))+
		zc.BETA3.loc[last_date]*((1-np.exp(-tarr/zc.TAU2.loc[last_date])
		)/(tarr/zc.TAU2.loc[last_date])-np.exp(-tarr/zc.TAU2.loc[last_date])))
		
dfact=1/(1+yrem/200.0)**(2*tarr)

tot_cost=np.sum(p*freq*dfact)
print('Initial capital needed in zero coupon bonds to support fixed cost of $'+
      str(p)+'/year: $'+str(tot_cost))
print('Total cash flow of the fixed cost: $'+str(p*freq*npayments))
    