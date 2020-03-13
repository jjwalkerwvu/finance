
"""
February 9 2020

yield_curve.py

    This script loads bond data for various maturities and makes a dataframe
    
    Update the files listed below as necessary

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
	Can find the data here:
	url='https://fred.stlouisfed.org/categories/115'

	Consider also loading 

	So, based on the data availability, I will make daily yield curves with  
	DGS1 through DGS10.


@author Jeffrey J. Walker
"""


import pandas as pd
import numpy as np
import datetime
## import my bond price calculator; make sure you are in the right directory
from bond_price import bond_price
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

## path where the various data files are located.
path='/home/jjwalker/Desktop/finance/data/bonds/IRTCM_csv_2/data/'
## path for the recession dates?
path_alt='/home/jjwalker/Desktop/finance/data/us_economic_data/fred_recession_dates.csv'

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
#bond_yield=pd.concat([bond_1.y1,bond_2.y2,bond_3.y3,bond_5.y5,bond_7.y7,bond_10.y10,bond_30.y30],axis=1).dropna()
bond_yield=pd.concat([bond_1.y1,bond_2.y2,bond_3.y3,bond_5.y5,bond_7.y7,bond_10.y10],axis=1).dropna()

## Would it be nice to make a gif from this data?

fig, ax = plt.subplots()
## Any way to set up xlim and ylim before starting?
ax.set_xlim([0,10])
## y1 actually has the highest yield; may want to check all columns to find
## the max value
ax.set_ylim([0.0,bond_yield.values.max()])
## Make the titles
ax.set_ylabel('Yield (%)')
ax.set_xlabel('Years to Maturity')
date_string=bond_yield.index[0].strftime('%Y %b %d')
ax.set_title(date_string)
## Make sure to use the tight layout
#plt.tight_layout()
## do we need a legend?
#plt.legend(loc='best')

x = np.array([1.0,2.0,3.0,5.0,7.0,10.0])
## using line, as a variable name? what is this here?
line, = ax.plot(x, bond_yield.iloc[0])



def update(i):
	line.set_ydata(bond_yield.iloc[i]);  # update the data
	date_string=ax.set_title(str(bond_yield.index[i]));
	return line, date_string

# Init only required for blitting to give a clean slate.
def init():
	line.set_ydata(np.ma.array(x, mask=True))
	date_string=ax.set_title(str(bond_yield.index[0]))
	return line, date_string

## blit=True does not seem to work, but blit=False does
#ani = FuncAnimation(fig, animate, np.arange(0,len(bond_yield)), init_func=init, interval=25, blit=True)

ani = FuncAnimation(fig, update, np.arange(0,len(bond_yield)), init_func=init, interval=25, blit=False)


#ani.save('yield_curve.gif', writer='imagemagick', fps=30)
#ani.save('yield_curve.mp4', fps=30, extra_args=['-vcodec', 'libx264'])


