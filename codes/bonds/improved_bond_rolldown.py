"""
Created on Friday, May 1, 2020

@author: Jeffrey J. Walker

improved_bond_rolldown.py

    This script loads the entire yield curve history from FRED website.
    The purpose of this script is find the return of a bond invested at some
	starting date, rolling down the yield curve once per year.


"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
#from scipy import interpolate
from scipy.interpolate import interp1d
## insert the path corresponding to bond_price; we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/bonds')
from bond_price import bond_price
## import the csv reader for FRED data
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader


filename='/home/jjwalker/Desktop/finance/data/bonds/fredgraph_01_may_2020'


yc=fred_csv_reader(filename)
## get recession dates?
recession_dates=fred_csv_reader('/home/jjwalker/Desktop/finance/data/us_economic_data/fred_recession_dates')
## get fed funds rate?
fedfunds=fred_csv_reader('/home/jjwalker/Desktop/finance/data/us_economic_data/FEDFUNDS')
## change some column names:
yc.rename(columns={'DGS1MO':'0.083','DGS3MO':'0.25','DGS6MO':'0.5','DGS1':'1',
	'DGS2':'2','DGS3':'3','DGS5':'5','DGS7':'7','DGS10':'10','DGS20':'20',
	'DGS30':'30',},inplace=True)
## drop the 'DFII30' column if it exists
#yc.drop('DFII30',axis=1,inplace=True)
## restructure the dataframe, sort the columns numerically
## However, this sorts alphabetically instead of numerically
#yc.sort_index(axis=1,ascending=True,inplace=True)
## FINALLY found the way to do this:
yc=yc[np.argsort(yc.columns.astype(float))]

## All of this goes into a loop?
## standard us treasury maturities
xtemp = np.array(yc.columns.astype(float))

## fill in values for ytemp, for each of the maturity dates listed above
#ytemp = np.array((yc.iloc[0].dropna()).astype(float))

## I seem to use this command a lot; pasted here so I do not forget it
#price=bond_price(r=0.0,y=yc['30'].loc['1981-10-01'],n=30,p0=1000)

## number of years to include for the interpolation
#nyears=float(yc.columns[-1])
#nyears=10
f=interp1d(xtemp[~np.isnan(ytemp)],ytemp[~np.isnan(ytemp)],kind='cubic')
xnew=np.linspace(xtemp[~np.isnan(ytemp)][0],xtemp[~np.isnan(ytemp)][-1],
	(xtemp[~np.isnan(ytemp)][-1]-xtemp[~np.isnan(ytemp)][0])+1,
	endpoint=True)





