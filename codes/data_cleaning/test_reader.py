"""
Created on Thursday March 19

@author: Jeffrey J. Walker

	test_reader.py
		Simple script to test the yahoo_csv_reader.py function.
	

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

## insert the path corresponding to the Yahoo csv reader.
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from yahoo_csv_reader import yahoo_csv_reader

## path to the security you want to plot:
path='/home/jjwalker/Desktop/finance/data/commodities/'
ticker='HG=F'

filename=path+ticker

df=yahoo_csv_reader(filename,ticker)


## What is a good default plot, to include the chart, and maybe the volume?
plt.plot(df.Close,'.k');plt.show()
