"""
Created on Monday March 16

@author: Jeffrey J. Walker

    option_test_script.py
        This script uses the yahoo_option_chain_scraper to plot the volatility
		surface and produce a 

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date
from dateutil.tz import *
import time
## import what we need to automatically write output to a folder
import os
import sys

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Some plots for now; put into a separate script/function later?
plt.plot(df_calls.Strike,df_calls.Last_Price,'.k');plt.show()

g=np.zeros((len(df_calls)))
delta=df_calls.Strike[1]-df_calls.Strike[0]
for i in range(1,len(df_calls)-1):
    #g[i]=np.exp(0.02*1/365)*(
    #        option_chain.Lastc[i+1]
    #        -2*option_chain.Lastc[i]
    #        +option_chain.Lastc[i-1])/delta**2
    g[i]=np.exp(y*1/365)*(
            (df_calls.Ask[i+1]+df_calls.Bid[i+1])/2
            -(df_calls.Ask[i]+df_calls.Bid[i])
            +(df_calls.Ask[i-1]+df_calls.Ask[i-1])/2)/delta**2

plt.plot(df_calls.Strike,g,'.k');plt.show()
plt.title('Date: Implied Distribution')
plt.xlabel('Strike Price')
plt.ylabel('Implied Distribution')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
#plt.savefig('implied_distribution.png')
