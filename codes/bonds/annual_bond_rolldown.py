"""
October 14, 2019

annual_bond_rolldown.py

	This is a script that finds the return from selling a bond purchased in a
	previous year, and then reinvesting that into another bond, etc.
	Conceived as a backtest for the long bond, maybe take some of the features
	and use them as a function.

	I am mostly interested in examining the period from october 1981 to the   
	near present, the so-called "long bond"	

	NECESSARY FILES:
	(in folder IRTCM_csv_2)
	DGS3MO.csv	- 	3 month bond yield daily data, 1982-2019 --> do not use?
	DGS6MO.csv	-	6 month bond yield daily data, 1982-2019 --> do not use?
	DGS1.csv	-	1 year bond yield daily data, 1962-2019
	DGS2.csv	-	2 year bond yield daily data, 1976-2019
	DGS3.csv	- 	3 year bond yield daily data, 1962-2019
	DGS5.csv	- 	5 year bond yield daily data, 1962-2019
	DGS7.csv	- 	7 year bond yield daily data, 1969-2019
	DGS10.csv	- 	10 year bond yield daily data, 1962-2019
	DGS20.csv	- 	20 year bond yield daily data, only goes from 1993
	DGS30.csv	- 	30 year bond yield daily data, 1977-2002, 2006-2019
	*Readme file says these are all "Constant Maturity Rates"

	So, based on the data availability, I will make daily yield curves with  
	DGS1 through DGS10.


@author Jeffrey J. Walker
"""


import pandas as pd
import numpy as np
## import my bond price calculator
from bond_price import bond_price
import matplotlib.pyplot as plt

## path where the various data files are located.
path='/home/jjwalker/Desktop/finance/data/bonds/IRTCM_csv_2/data/'

## bond details:
r=0.0	# zero-coupon
p0=100.0		# par value of the bond
invest=100.0	# initial investment in dollars

## 1 year bond data
bond_1=pd.read_csv(path+'DGS1.csv',header=0)
bond_1['DATE'] = pd.to_datetime(bond_1.DATE,infer_datetime_format=True)
bond_1=bond_1.set_index('DATE')
bond_1=bond_1.rename(columns={'VALUE':'y1'})
## there are annoying ellipses in this csv, get rid of them
bond_1=bond_1.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_1.y1=pd.to_numeric(bond_1.y1)

## 2 year bond data
bond_2=pd.read_csv(path+'DGS2.csv',header=0)
bond_2['DATE'] = pd.to_datetime(bond_2.DATE,infer_datetime_format=True)
bond_2=bond_2.set_index('DATE')
bond_2=bond_2.rename(columns={'VALUE':'y2'})
## there are annoying ellipses in this csv, get rid of them
bond_2=bond_2.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_2.y2=pd.to_numeric(bond_2.y2)

## 3 year bond data
bond_3=pd.read_csv(path+'DGS3.csv',header=0)
bond_3['DATE'] = pd.to_datetime(bond_3.DATE,infer_datetime_format=True)
bond_3=bond_3.set_index('DATE')
bond_3=bond_3.rename(columns={'VALUE':'y3'})
## there are annoying ellipses in this csv, get rid of them
bond_3=bond_3.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_3.y3=pd.to_numeric(bond_3.y3)

## 5 year bond data
bond_5=pd.read_csv(path+'DGS5.csv',header=0)
bond_5['DATE'] = pd.to_datetime(bond_5.DATE,infer_datetime_format=True)
bond_5=bond_5.set_index('DATE')
bond_5=bond_5.rename(columns={'VALUE':'y5'})
## there are annoying ellipses in this csv, get rid of them
bond_5=bond_5.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_5.y5=pd.to_numeric(bond_5.y5)

## 7 year bond data
bond_7=pd.read_csv(path+'DGS7.csv',header=0)
bond_7['DATE'] = pd.to_datetime(bond_7.DATE,infer_datetime_format=True)
bond_7=bond_7.set_index('DATE')
bond_7=bond_7.rename(columns={'VALUE':'y7'})
## there are annoying ellipses in this csv, get rid of them
bond_7=bond_7.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_7.y7=pd.to_numeric(bond_7.y7)

## 10 year bond data
bond_10=pd.read_csv(path+'DGS10.csv',header=0)
bond_10['DATE'] = pd.to_datetime(bond_10.DATE,infer_datetime_format=True)
bond_10=bond_10.set_index('DATE')
bond_10=bond_10.rename(columns={'VALUE':'y10'})
## there are annoying ellipses in this csv, get rid of them
bond_10=bond_10.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_10.y10=pd.to_numeric(bond_10.y10)

## 30 year bond data
bond_30=pd.read_csv(path+'DGS30.csv',header=0)
bond_30['DATE'] = pd.to_datetime(bond_30.DATE,infer_datetime_format=True)
bond_30=bond_30.set_index('DATE')
bond_30=bond_30.rename(columns={'VALUE':'y30'})
## there are annoying ellipses in this csv, get rid of them
bond_30=bond_30.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_30.y30=pd.to_numeric(bond_30.y30)

## we may as well concatenate the dataframes; drop any nans
bond_yield=pd.concat([bond_1.y1,bond_2.y2,bond_3.y3,bond_5.y5,bond_7.y7,bond_10.y10],axis=1).dropna()
## perform an interpolation to get 4 year, 6 year, 8 year, and 9 year yields
## x is date to maturity for each bond
x=np.array([1.0,2.0,3.0,5.0,7.0,10.0])
## loop through dataframe to do the interpolation
## set up arrays for the interpolated yields
y4=[]
y6=[]
y8=[]
y9=[]

for i in range(len(bond_yield)):
	c=np.polynomial.hermite.hermfit(x,bond_yield.iloc[i],deg=3)
	## 9 years is the most important, but also calculate for 4, 6, 8 and 9 years
	#fit=np.polynomial.hermite.hermval([4.0,6.0,8.0,9.0],c))
	y4=np.append(y4,np.polynomial.hermite.hermval([4.0],c))
	y6=np.append(y6,np.polynomial.hermite.hermval([6.0],c))
	y8=np.append(y8,np.polynomial.hermite.hermval([8.0],c))
	y9=np.append(y9,np.polynomial.hermite.hermval([9.0],c))

	## the coefficients for the hermite polynomial fit; use 3rd degree?
	#c=np.polynomial.hermite.hermfit(x,bond_yield.iloc[i],deg=3)
	 
## insert these new yield values into the dataframe:
y4_df=pd.DataFrame(y4,index=bond_yield.index)
y6_df=pd.DataFrame(y6,index=bond_yield.index)
y8_df=pd.DataFrame(y8,index=bond_yield.index)
y9_df=pd.DataFrame(y9,index=bond_yield.index)
##[y1,y2,y3,y5,y7,y10]
##[0,1,2,3,4,5]
bond_yield.insert(3, "y4", y4_df) 
##[y1,y2,y3,y4,y5,y7,y10]
##[0,1,2,3,4,5,6] 
bond_yield.insert(5, "y6", y6_df) 
##[y1,y2,y3,y4,y5,y6,y7,y10]
##[0,1,2,3,4,5,6,7] 
bond_yield.insert(7, "y8", y8_df)
##[y1,y2,y3,y4,y5,y6,y7,y8,y10]
##[0,1,2,3,4,5,6,7,8]
bond_yield.insert(8, "y9", y9_df)

## take snapshots every year to get the yield curve plot?
## Make an animation?

## use this loop to calculate the return?    
prev_year='1981'
date_array=pd.date_range('1/2/1981','1/2/2019',freq='BAS-oct')
## the number of bonds corresponding to the investment.
nbonds=np.zeros((len(date_array)))
d={'value':np.zeros((len(date_array)))}
portfolio=pd.DataFrame(data=d,index=date_array)

purchase_date=date_array[0]
return_rate=np.zeros((len(date_array)))
## the number of bonds corresponding to the investment.
nbonds=np.zeros((len(date_array)))
## the number of bonds at the begining
nbonds[0]=invest/bond_price(r=r,y=bond_yield.y10[date_array[0]]/100,n=10,p0=p0)
nb=nbonds[0]
sell_price=np.zeros((len(date_array)))
purchase_price=np.zeros((len(date_array)))
tot_return=np.zeros((len(date_array)))
tot_return[0]=0
return_factor=np.zeros((len(date_array)))

index=0
for date in date_array[1:]:
	## sell the bond from last year
	p=nb*(bond_price(r=r,y=bond_yield.y9.values[bond_yield.index==date][0]/100,
		n=9,p0=p0))
	portfolio.value[portfolio.index==date]=p
	## buy the bond for the current year
	nb=p/bond_price(r=r,y=bond_yield.y10.values[bond_yield.index==date][0]/100,
		n=10,p0=p0)

    ## use the bond price from when it was purchased; the previous date in the
    ## date array
    #purchase_price[index]=bond_price(r=r,
    #              y=bond_yield.y10[purchase_date]/100,
    #              n=10,
    #              p0=p0)
    
    ## find the factor by which the initial investment increased
    #return_factor[index]=purchase_price[index]/purchase_price[index-1]
    #rebalance_date=time
    ## compute the return;    
    #index=index+1
    #sell_price[index]=bond_price(
    #        r=r,
    #        y=bond_yield.y9[rebalance_date]/100,
    #        n=9,
    #        p0=p0)
    
    #return_rate[index]=(sell_price[index]-purchase_price[index])/purchase_price[index]
    #tot_return[index]=return_rate[index]*tot_return[index-1]
    #tot_return[index]=sell_price[index]-purchase_price[index-1]
    
    #purchase_date=time

#print(len(y9))
#print(bond_yield.iloc[0])
print(str(portfolio))

