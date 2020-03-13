"""
February 17 2020

yield_curve_inversion.py

	This simple script loads 3 month, 2 year, and 10 year bond data, an
	array for recessions, and performs logistic regression to see how well
	a yield curve inversion predicts a recession for a given forecasting 
	period.

	NECESSARY FILES:
	(in folder /home/jjwalker/Desktop/finance/data/bonds/IRTCM_csv_2/data/)
	DGS3MO.csv	- 	3 month bond yield daily data, 1982-2019
	DGS2.csv	-	2 year bond yield daily data, 1976-2019
	DGS10.csv	- 	10 year bond yield daily data, 1962-2019
	*Readme file says these are all "Constant Maturity Rates"
	Can find the data here:
	url='https://fred.stlouisfed.org/categories/115'

	(in folder /home/jjwalker/Desktop/finance/data/us_economic_data)
	fred_recession_dates.csv
 
	
"""

import pandas as pd
import numpy as np
import datetime
## import my bond price calculator; make sure you are in the right directory
#from bond_price import bond_price
import matplotlib.pyplot as plt


## path where the various data files are located.
path='/home/jjwalker/Desktop/finance/data/bonds/IRTCM_csv_2/data/'
## path for the recession dates?
path_economics='/home/jjwalker/Desktop/finance/data/us_economic_data/'

## 3 month bond data
bond_3mo=pd.read_csv(path+'DGS3MO.csv',header=0)
bond_3mo['DATE'] = pd.to_datetime(bond_3mo.DATE,infer_datetime_format=True)
bond_3mo=bond_3mo.set_index('DATE')
bond_3mo=bond_3mo.rename(columns={'VALUE':'mo3'})
## there are annoying ellipses in this csv, get rid of them
bond_3mo=bond_3mo.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_3mo.mo3=pd.to_numeric(bond_3mo.mo3)

## 2 year bond data
bond_2=pd.read_csv(path+'DGS2.csv',header=0)
bond_2['DATE'] = pd.to_datetime(bond_2.DATE,infer_datetime_format=True)
bond_2=bond_2.set_index('DATE')
bond_2=bond_2.rename(columns={'VALUE':'y2'})
## there are annoying ellipses in this csv, get rid of them
bond_2=bond_2.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_2.y2=pd.to_numeric(bond_2.y2)

## 10 year bond data
bond_10=pd.read_csv(path+'DGS10.csv',header=0)
bond_10['DATE'] = pd.to_datetime(bond_10.DATE,infer_datetime_format=True)
bond_10=bond_10.set_index('DATE')
bond_10=bond_10.rename(columns={'VALUE':'y10'})
## there are annoying ellipses in this csv, get rid of them
bond_10=bond_10.replace('.',np.nan)
## and also, the column is read in as a string, so turn into numerical value
bond_10.y10=pd.to_numeric(bond_10.y10)

## now compute the inversion time series, 10y-2y, 10y-3mo
inversion_10_2=bond_10.y10-bond_2.y2
inversion_10_2=inversion_10_2.dropna()
inversion_10_3mo=bond_10.y10-bond_3mo.mo3
inversion_10_3mo=inversion_10_3mo.dropna()

## The dataframe that contains the dates for recessions
recessions=pd.read_csv(path_economics+'fred_recession_dates.csv',header=0)
recessions['DATE'] = pd.to_datetime(recessions.DATE,infer_datetime_format=True)
## rename the first column
recessions=recessions.set_index('DATE')
recessions=recessions.rename(columns={recessions.columns[0]:"recession"})
## with the one year offset:
frame={'offset_date':recessions.index-pd.DateOffset(years=1),'recession':recessions.recession.values}
## can retain the original date if needed, but I am just using the offset date
## for the index as of now.
recession_offset = pd.DataFrame(frame) 
recession_offset=recession_offset.set_index('offset_date')
## resample on daily basis and backfill? Or ffill?
#recession_offset=recession_offset.resample('D').bfill()
recession_offset=recession_offset.resample('D').ffill()

## Do I need to merge data frames? 
## probably not a good idea!

## scroll through inversion data, look ahead 12 months and see if there is a
## recession?
## 0=false, 1=true?
array=pd.concat([(inversion_10_3mo<0),recession_offset.recession],axis=1).dropna()
## the accuracy array:
accuracy=array[array.columns[0]]==array[array.columns[1]]
## the true positive array, yield curve inverts and there is a recession
## after 12 months
tp_array=(array[array.columns[0]]==True)&(array[array.columns[1]]==True)
## the true negative array:
tn_array=(array[array.columns[0]]==False)&(array[array.columns[1]]==False)
## the false positive array:
fp_array=(array[array.columns[0]]==True)&(array[array.columns[1]]==False)
## the false negative array:
fn_array=(array[array.columns[0]]==False)&(array[array.columns[1]]==True)

## the accuracy?
acc=1.0*sum(accuracy)/len(accuracy)
## various rates:
tpr=1.0*sum(tp_array)/(sum(tp_array)+sum(fn_array))
fnr=1.0*sum(fn_array)/(sum(fn_array)+sum(tp_array))
## f1 score:
f1=2.0*sum(tp_array)/(2.0*sum(tp_array)+1.0*sum(fp_array)+1.0*sum(fn_array))

	
