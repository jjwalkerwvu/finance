#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 21:07:27 2019

    bond_backtest.py
        This tests bond investing, where the investor invests in a 10-year bond
        and "re-balances" every year

@author: jeffreywalker
"""

import pandas as pd
import numpy as np
from bond_price import bond_price
import matplotlib.pyplot as plt


## read in bond data
bond_yield=pd.read_csv('10_year_treasury_bond_rate_yield_chart.csv',
                       skiprows=[8],header=8)

bond_yield=bond_yield.rename(columns={' value':'y'})
bond_yield['date'] = pd.to_datetime(bond_yield.date,infer_datetime_format=True)
bond_yield=bond_yield.set_index('date')

## Maybe use data straight from the fed, should be very reliable. 
## Also, 10 year and 7 year 

## variables
r=0.01625
r=0.0
## principal; but actually the par value here.
p0=100.0
## the actual principal, the initial investment in dollars
invest=1e2
## time to maturity of the bond
texp=10

## daily rebalance?

price=np.zeros((len(bond_yield)))

for i in range(len(bond_yield)):
    price[i]=bond_price(r=r,y=bond_yield.y[i]/100,n=texp,p0=p0)
 
## add the price to the dataframe
price_df=pd.DataFrame(price,index=bond_yield.index)
bond_yield.insert(1, "price", price_df)     
    
## use this loop to calculate the return?    
prev_year='1981'
date_array=pd.date_range('1/2/1981','1/2/2019',freq='BAS-oct')
purchase_date=date_array[0]
return_rate=np.zeros((len(date_array)))
## the number of bonds corresponding to the investment.
nbonds=np.zeros((len(date_array)))
sell_price=np.zeros((len(date_array)))
purchase_price=np.zeros((len(date_array)))
tot_return=np.zeros((len(date_array)))
tot_return[0]=0
return_factor=np.zeros((len(date_array)))

index=0
for time in date_array[1:]:
    ## use the bond price from when it was purchased; the previous date in the
    ## date array
    purchase_price[index]=bond_price(r=r,
                  y=bond_yield.y[purchase_date]/100,
                  n=texp,
                  p0=p0)
    
    ## find the factor by which the initial investment increased
    return_factor[index]=purchase_price[index]/purchase_price[index-1]
    rebalance_date=time
    ## compute the return;    
    index=index+1
    sell_price[index]=bond_price(
            r=r,
            y=bond_yield.y[rebalance_date]/100,
            n=texp-1,
            p0=p0)
    
    #return_rate[index]=(sell_price[index]-purchase_price[index])/purchase_price[index]
    #tot_return[index]=return_rate[index]*tot_return[index-1]
    tot_return[index]=sell_price[index]-purchase_price[index-1]
    
    purchase_date=time
 
## return factor has inf for first element; discard this 
return_factor[0]=1
    
plt.figure()
plt.title('US 10 Year Note Yield')
plt.plot(bond_yield.y)

## the price plot:
plt.figure()
plt.title('Bond Price')
plt.plot(bond_yield.index,price,'-k',label=str(texp)+'yr '+'Bond Price')
plt.xlabel('Date')
plt.ylabel('Bond Price')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
plt.savefig('bond_backtest.png')

