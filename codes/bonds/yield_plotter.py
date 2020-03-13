#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 25 22:22:04 2019

yield_plotter.py

    This script plots bond price as a function of yield

@author: jeffreywalker
"""

import numpy as np
from bond_price import bond_price

y=np.linspace(-0.1,0.1,1e3)
p=np.zeros((len(y)))
## rate=0 for zero coupon bonds
rate=0
texp=30
par=100

for i in range(0,len(y)):
    p[i]=bond_price(rate,y[i],texp,par)
    
plt.figure()
plt.title('Bond Price as Function of Yield')
plt.plot(y,p,'-k',label='Bond Price')
plt.legend()
plt.xlabel('Yield')
plt.ylabel('Bond Price')
