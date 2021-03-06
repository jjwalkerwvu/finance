#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 16:31:42 2019

bond_rolldown.py

    This script loads 10 year and 7 year note yield data (data source: the Fed.)
    An intial investment is split evenly into 3 years starting in october 1, 
    1981. The 10 year coupon bonds are sold every year as they become 7 year
    notes. The proceeds from each sale is used to buy more 10 year notes.
    
    Update the files 'DGS7.csv' and 'DGS10.csv' as necessary

@author: jeffreywalker
"""

import pandas as pd
import numpy as np
from bond_price import bond_price
import matplotlib.pyplot as plt

bond_7=pd.read_csv('DGS7.csv',header=0)
bond_7['DATE'] = pd.to_datetime(bond_7.DATE,infer_datetime_format=True)
bond_7=bond_7.set_index('DATE')
bond_7=bond_7.rename(columns={'DGS7':'y7'})
## there are annoying ellipses in this csv, get rid of them
bond_7=bond_7.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_7.y7=pd.to_numeric(bond_7.y7)
bond_10=pd.read_csv('DGS10.csv',header=0)
bond_10['DATE'] = pd.to_datetime(bond_10.DATE,infer_datetime_format=True)
bond_10=bond_10.set_index('DATE')
bond_10=bond_10.rename(columns={'DGS10':'y10'})
## there are annoying ellipses in this csv, get rid of them
bond_10=bond_10.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_10.y10=pd.to_numeric(bond_10.y10)

## we may as well concatenate the dataframes; drop any nans
bond_yield=pd.concat([bond_7.y7,bond_10.y10],axis=1).dropna()

## r=0 for zero-coupon bonds
r=0.0
## The par value here for a note/bond
p0=100.0
## the actual principal, the initial investment in dollars
invest=1e2
## time to maturity of each note/bond you want to calculate
t10=10
t7=7
texp=10

## daily rebalance?

## initialize arrays for all desired note/bond prices
price10=np.zeros((len(bond_yield)))
price7=np.zeros((len(bond_yield)))

for i in range(len(bond_yield)):
    price7[i]=bond_price(r=r,y=bond_yield.y7[i]/100,n=t7,p0=p0)
    price10[i]=bond_price(r=r,y=bond_yield.y10[i]/100,n=t10,p0=p0)
    
## add the price to the dataframe
price7_df=pd.DataFrame(price7,index=bond_yield.index)
price10_df=pd.DataFrame(price10,index=bond_yield.index)
bond_yield.insert(2, "price7", price7_df) 
bond_yield.insert(3, "price10", price10_df)

## okay, now ready to do backtesting with the following strategy:

## we start rolling from the date:
#prev_year='1981'
date_array=pd.date_range('1/2/1981','1/2/2019',freq='BAS-oct')

## divide our initial investment into 3 ten year notes, starting with 1981,
## then 1982, then 1983.
## calculate the "number" of notes you can purchase with the allocated capital.
n1=invest/3/bond_yield.price10.values[bond_yield.index==date_array[0]][0]
n2=invest/3/bond_yield.price10.values[bond_yield.index==date_array[1]][0]
n3=invest/3/bond_yield.price10.values[bond_yield.index==date_array[2]][0]
## make arrays to include the value of the bond portfolio for each year
## By the way, here is how to make a dataframe from an array and make a title
d={'value':np.zeros((len(date_array)))}
portfolio=pd.DataFrame(data=d,index=date_array)
## fill in the first three rows
portfolio.value[0]=invest/3
portfolio.value[1]=invest/3
portfolio.value[2]=invest/3

## construct a new dataframe with the date_array as the index and fill in each
## entry with the year's portfolio value

## find the profit and calculate new investment for 1984, 1987, etc.
for date in date_array[3::3]:
	print(date)
	p1=n1*bond_yield.price7.values[bond_yield.index==date][0]
	n1=p1/bond_yield.price10.values[bond_yield.index==date][0]
	portfolio.value[portfolio.index==date]=p1
			
    
for date in date_array[4::3]:
	print(date)
	p2=n2*bond_yield.price7.values[bond_yield.index==date][0]
	n2=p2/bond_yield.price10.values[bond_yield.index==date][0]
	#value=n1*bond_yield.price7.values[bond_yield.index==date][0]
	portfolio.value[portfolio.index==date]=p2
  
for date in date_array[5::3]:
	print(date)
	p3=n3*bond_yield.price7.values[bond_yield.index==date][0]
	n3=p3/bond_yield.price10.values[bond_yield.index==date][0]
	portfolio.value[portfolio.index==date]=p3

## organize the portfolio values, so we get the annual value, which includes
## the "off-year" bonds
#for i in range(3,len(date_array),3):
#	print(date_array[i])
#	portfolio.value[i]=(portfolio.value[i]+portfolio.value[i-1]+
#		portfolio.value[i-2])
#for i in range(4,len(date_array),3):
#	print(date_array[i])
#	portfolio.value[i]=(portfolio.value[i]+portfolio.value[i-1]+
#		portfolio.value[i-2])
#for i in range(5,len(date_array),3):
#	print(date_array[i])
#	portfolio.value[i]=(portfolio.value[i]+portfolio.value[i-1]+
#		portfolio.value[i-2])

print(portfolio.value)

## make a figure; include the bond price and the value of the portfolio?
## the price plot:
plt.figure()
plt.title(str(texp)+'yr Bond Yearly Rolldown')
plt.plot(portfolio,'-k',label=str(texp)+'yr '+'Bond Price')
plt.xlabel('Date')
plt.ylabel('Portfolio Value')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
plt.savefig('bond_rolldown.png')
