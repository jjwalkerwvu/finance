"""
Created on Thursday, October 29, 2020

@author: Jeffrey J. Walker

    multi_chain_test.py
        This is a test script for the yahoo_option_chain_multi_exp.py function

"""

import pandas as pd
import numpy as np
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil.tz import *
import time
import os
import sys
import json
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/data_cleaning')
from yahoo_option_chain_multi_exp import yahoo_option_chain_multi_exp
## insert the path corresponding to bs_analytical solver; we may need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')

## Want to execute in python shell? then use:
#execfile('/home/jjwalker/Desktop/finance/codes/options/multi_chain_test.py')


#tnow,expiry_dates,spot_price,df_calls,df_puts=yahoo_option_chain_multi_exp()
