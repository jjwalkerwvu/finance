"""
October 18,2019

earnings_predictor.py

	This program (function?) opens the relevant earnings files and tries to
	predict the price change of specified stock after the most recent earnings
	release (need at least one other company for the most recent earnings 
	season besides the specified stock.)

@author Jeffrey J. Walker
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

## path where the various data files are located.
path='/home/jjwalker/Desktop/finance/earnings_predictor/'
## load railroad data; generalize to other stocks later.
## the ticker
ticker='cni'

## earnings data/relevant stock data
earnings=pd.read_csv(path+ticker+'_test.csv',header=0)
earnings['date'] = pd.to_datetime(earnings.date,infer_datetime_format=True)
## convert quarter_end to datetime as well
earnings['quarter_end']=pd.to_datetime(earnings.quarter_end,infer_datetime_format=True)
## for now, let's only keep the data that I think is most important; expand
## later if necessary.
## I still need revenue data!
earnings_dummy=earnings[['date','announcement_time','eps_surprise_percent',
					'volume_before','volume_after','price_change',
					'spy_volume_before','spy_volume_after',
					'spy_price_change']]
earnings_dummy=earnings_dummy.rename(columns=lambda x: ticker+'_'+x)
earnings_dummy['quarter_end']=earnings.quarter_end
cni_earnings=earnings_dummy
#cni_earnings=earnings.set_index('date')
#delete earnings

ticker='cp'
## earnings data/relevant stock data
earnings=pd.read_csv(path+ticker+'_test.csv',header=0)
earnings['date'] = pd.to_datetime(earnings.date,infer_datetime_format=True)
## convert quarter_end to datetime as well
earnings['quarter_end']=pd.to_datetime(earnings.quarter_end,infer_datetime_format=True)
## for now, let's only keep the data that I think is most important; expand
## later if necessary.
## I still need revenue data!
earnings_dummy=earnings[['date','announcement_time','eps_surprise_percent',
					'volume_before','volume_after','price_change',
					'spy_volume_before','spy_volume_after',
					'spy_price_change']]
earnings_dummy=earnings_dummy.rename(columns=lambda x: ticker+'_'+x)
earnings_dummy['quarter_end']=earnings.quarter_end
cp_earnings=earnings_dummy
#cp_earnings=earnings.set_index('date')
#delete earnings

ticker='csx'
## earnings data/relevant stock data
earnings=pd.read_csv(path+ticker+'_test.csv',header=0)
earnings['date'] = pd.to_datetime(earnings.date,infer_datetime_format=True)
## convert quarter_end to datetime as well
earnings['quarter_end']=pd.to_datetime(earnings.quarter_end,infer_datetime_format=True)
## for now, let's only keep the data that I think is most important; expand
## later if necessary.
## I still need revenue data!
earnings_dummy=earnings[['date','announcement_time','eps_surprise_percent',
					'volume_before','volume_after','price_change',
					'spy_volume_before','spy_volume_after',
					'spy_price_change']]
earnings_dummy=earnings_dummy.rename(columns=lambda x: ticker+'_'+x)
earnings_dummy['quarter_end']=earnings.quarter_end
csx_earnings=earnings_dummy
#csx_earnings=earnings.set_index('date')
#delete earnings

ticker='ksu'
## earnings data/relevant stock data
earnings=pd.read_csv(path+ticker+'_test.csv',header=0)
earnings['date'] = pd.to_datetime(earnings.date,infer_datetime_format=True)
## convert quarter_end to datetime as well
earnings['quarter_end']=pd.to_datetime(earnings.quarter_end,infer_datetime_format=True)
## for now, let's only keep the data that I think is most important; expand
## later if necessary.
## I still need revenue data!
earnings_dummy=earnings[['date','announcement_time','eps_surprise_percent',
					'volume_before','volume_after','price_change',
					'spy_volume_before','spy_volume_after',
					'spy_price_change']]
earnings_dummy=earnings_dummy.rename(columns=lambda x: ticker+'_'+x)
earnings_dummy['quarter_end']=earnings.quarter_end
ksu_earnings=earnings_dummy
#ksu_earnings=earnings.set_index('date')
#delete earnings

ticker='nsc'
## earnings data/relevant stock data
earnings=pd.read_csv(path+ticker+'_test.csv',header=0)
earnings['date'] = pd.to_datetime(earnings.date,infer_datetime_format=True)
## convert quarter_end to datetime as well
earnings['quarter_end']=pd.to_datetime(earnings.quarter_end,infer_datetime_format=True)
## for now, let's only keep the data that I think is most important; expand
## later if necessary.
## I still need revenue data!
earnings_dummy=earnings[['date','announcement_time','eps_surprise_percent',
					'volume_before','volume_after','price_change',
					'spy_volume_before','spy_volume_after',
					'spy_price_change']]
earnings_dummy=earnings_dummy.rename(columns=lambda x: ticker+'_'+x)
earnings_dummy['quarter_end']=earnings.quarter_end
nsc_earnings=earnings_dummy
#nsc_earnings=earnings.set_index('date')
#delete earnings

ticker='unp'
## earnings data/relevant stock data
earnings=pd.read_csv(path+ticker+'_test.csv',header=0)
earnings['date'] = pd.to_datetime(earnings.date,infer_datetime_format=True)
## convert quarter_end to datetime as well
earnings['quarter_end']=pd.to_datetime(earnings.quarter_end,infer_datetime_format=True)
## for now, let's only keep the data that I think is most important; expand
## later if necessary.
## I still need revenue data!
earnings_dummy=earnings[['date','announcement_time','eps_surprise_percent',
					'volume_before','volume_after','price_change',
					'spy_volume_before','spy_volume_after',
					'spy_price_change']]
earnings_dummy=earnings_dummy.rename(columns=lambda x: ticker+'_'+x)
earnings_dummy['quarter_end']=earnings.quarter_end
unp_earnings=earnings_dummy
#unp_earnings=earnings.set_index('date')
#delete earnings

## merge all of the dataframes based on the quarter_end column?
df=[cni_earnings,cp_earnings,csx_earnings,ksu_earnings,nsc_earnings,unp_earnings]
#df=pd.merge(cp_earnings,csx_earnings, nsc_earnings, on="quarter_end")
#df=df.set_index('date_x')

## Sample plot:
## See how well csx eps beat percentage predicts nsc eps beat percentage 
## when csx earnings happen BEFORE nsc
## current hack because csx and nsc do not have same number of elements; 
## automate later!
match1=1	# csx_earnings[1] matches with nsc_earnings[0]
match2=29	# csx_earnings[28] matches with nsc_earnings[27]
csx_eps_beat=csx_earnings.csx_eps_surprise_percent[match1:match2]
csx_date=csx_earnings.csx_date[match1:match2]
csx_announce=csx_earnings.csx_announcement_time[match1:match2]
csx_price=csx_earnings.csx_price_change[match1:match2]
nsc_eps_beat=nsc_earnings.nsc_eps_surprise_percent
nsc_date=nsc_earnings.nsc_date
nsc_announce=nsc_earnings.nsc_announcement_time
nsc_price=nsc_earnings.nsc_price_change
## scroll through these arrays, discard any indices where nsc earnings happen
## before csx
csx_eps_surprise=(csx_date.values<nsc_date.values)*csx_eps_beat.values
nsc_eps_surprise=(csx_date.values<nsc_date.values)*nsc_eps_beat.values

#(csx_date<nsc_date)

#for i in range(0,len(csx_eps_beat)):
#	if csx_date.iloc[0]<nsc_date.iloc
#	print(i)

## First, determine whether there is a relationship between eps beat % and 
## stock price change percentage
[m,b,rval,pval,stderr]=(linregress(
		x=nsc_eps_beat[~np.isnan(nsc_price)&~np.isnan(nsc_eps_beat)],
		y=nsc_price[~np.isnan(nsc_price)&~np.isnan(nsc_eps_beat)]))

## Plot the best fit line with the data
plt.figure()
plt.plot(nsc_eps_beat,nsc_price,'rd',label='NSC Price')
plt.plot(nsc_eps_beat,
		m*nsc_eps_beat+b,'.b',
		label='Linear Regression')
## plot a line over the symbols
plt.plot(nsc_eps_beat,
		m*nsc_eps_beat+b,'-b')
plt.title()
plt.xlabel('EPS Beat %')
#plt.ylabel('Portfolio Value')
plt.ylabel('NSC Price Change %')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
plt.show()
plt.savefig('nsc_regression.png')






## can even consider loading some of the stock data to find their correlations?
#corr_coef=close_price.corr(method='pearson')
