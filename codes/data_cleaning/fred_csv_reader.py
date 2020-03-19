"""
Created on Friday March 13

@author: Jeffrey J. Walker

	fred_csv_reader.py
		This function reads csv files downloaded from FRED website and 
		automatically puts them into a useful format based on the type of 
		data (bond yield, initial claims, unemployment, etc.)

	Inputs:
		filename	-	filename, must be a string! Make sure to error check.
						Filename should include the path as well.
	

"""

import pandas as pd
import numpy as np
import datetime
import sys

def fred_csv_reader(filename):

	## Do we need to make if else statements for different types of data 
	## downloaded from FRED?
	df=pd.read_csv(filename+'.csv',header=0)
	df['DATE'] = pd.to_datetime(df.DATE,infer_datetime_format=True)
	## This rename is not really needed.
	#df=df.rename(columns={'DATE':'date'})
	df=df.set_index('DATE')
	df=df[df.columns].apply(pd.to_numeric,errors='coerce')

	## return the data as a data frame with the chosen format
	return df
