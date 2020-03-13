'''

bs_analytical_test.py

28 April 2019
Jeffrey J. Walker

A simple test of the bs_analytical_solver.py function

'''

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from bs_analytical_solver import bs_analytical_solver

strike=25
St=31.67
rfr=(1.77)/100
#texp=7.5/24/365.0
texp=(85)/365.0
sig=(42.552/100)
otype='p'

solution,delta,gamma,vega,theta,rho = bs_analytical_solver(
	S=St,K=strike,r=rfr,T=texp,sigma=sig,o_type=otype)

print('Underlying Price:'+str(St))
print('Strike Price:'+str(strike)+otype)
print('Price:'+str(solution))
print('Delta:'+str(delta))
print('Gamma:'+str(gamma))
print('Vega:'+str(vega))
print('Theta:'+str(theta))
print('Rho:'+str(rho))

