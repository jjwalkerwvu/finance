'''

bs_analytical_test.py

28 April 2019
Jeffrey J. Walker

A simple test of the bs_analytical_solver.py function

'''

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import sys

## insert the path corresponding to bs_analytical solver; we will need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')
from bs_analytical_solver import bs_analytical_solver

strike=294.0
St=293.41
rfr=(2.36)/100
texp=4/365.0
## you need to divide volatility percentage by 100!
sig=(6.3361/100)
otype='p'

#strike=290.0
#St=290.09
#rfr=(1.9)/100
#texp=1/365.0
#sig=(21.3044/100)
#otype='c'
#actual_price=1.0

strike=2380
St=2300
rfr=(0.1)/100
texp=1/365.0
sig=(60.17/100)
otype='c'
actual_price=71.0


solution,second_deriv,delta,gamma,vega,theta,rho = bs_analytical_solver(
	S=St,K=strike,r=rfr,T=texp,sigma=sig,o_type=otype)

print('Price:'+str(solution))
print('2nd Derivative:'+str(second_deriv))
print('Delta:'+str(delta))
print('Gamma:'+str(gamma))
print('Vega:'+str(vega))
print('Theta:'+str(theta))
print('Rho:'+str(rho))
## This does line does not look right...
#print('Implied Volatilty, %: ' + str((sig/solution)*100))

