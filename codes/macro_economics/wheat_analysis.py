"""
Created March 5, 2021

@author: Jeffrey J. Walker

wheat_analysis.py
	load wheat prices (from FRED) and Oceanic Nino Index

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
## insert the path corresponding to bond_price; we will need this function!
# insert at 1, 0 is the script path (or '' in REPL)
## import the csv reader for FRED data
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from fred_csv_reader import fred_csv_reader


## import wheat prices
filename='/home/jjwalker/Desktop/finance/data/commodities/WPU0121'
wt=fred_csv_reader(filename)

oni=pd.read_csv('/home/jjwalker/Desktop/finance/data/commodities/monthly_oni.csv',header=0)
oni['PeriodNum'] = pd.to_datetime(oni.PeriodNum,infer_datetime_format=True)
## This rename is not really needed.
#df=df.rename(columns={'DATE':'date'})
oni=oni.set_index('PeriodNum')
oni=oni[oni.columns].apply(pd.to_numeric,errors='coerce')
