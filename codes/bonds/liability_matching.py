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

## required payment and frequency (/year)
p=1600
freq=1/12.0
## number of years where payments are needed
nyears=15
npayments=nyears/(1/freq)

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

tot_cost=np.sum(p*dfact)
    