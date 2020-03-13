#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 23 17:58:03 2019

@author: jeffreywalker
"""

import pandas as pd
import numpy as np

## read in all the data frames you would like to check
btc=pd.read_csv('btc_to_usd_2013_to_2019.csv',header=1)
spy=pd.read_csv('spy_2013_to_2019.csv')
## read in bond data
bond=pd.read_csv('10_year_treasury_bond_rate_yield_chart.csv',
                       skiprows=[8],header=8)
## fix some pecularities in the structure of the bond data file
bond=bond.rename(columns={' value':'y'})
bond['date'] = pd.to_datetime(bond.date,infer_datetime_format=True)
bond=bond.set_index('date')

## set indices?
btc['Date'] = pd.to_datetime(btc.Date,infer_datetime_format=True)
btc=btc.set_index('Date')
btc=btc.rename(columns={'Close':'btc_close'})

spy['date'] = pd.to_datetime(spy.date,infer_datetime_format=True)
spy=spy.set_index('date')
spy=spy.rename(columns={'close':'spy_close'})

close_price=pd.concat([btc.btc_close,spy.spy_close],axis=1)
## calculate pearson correlation coefficient, easy peasy:
corr_coef=close_price.corr(method='pearson')


## convert to simple numpy arrays?

## close_price including bonds?
close_price=pd.concat([btc.btc_close,spy.spy_close,bond.y],axis=1)
spy_btc=close_price.spy_close.corr(close_price.btc_close)
spy_bond=close_price.spy_close.corr(close_price.y)
btc_bond=close_price.btc_close.corr(close_price.y)