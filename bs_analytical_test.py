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

strike=294.0
St=293.41
rfr=(2.36)/100
texp=4/365.0
sig=(6.3361/100)
otype='p'

solution,delta,gamma,vega,theta,rho = bs_analytical_solver(
	S=St,K=strike,r=rfr,T=texp,sigma=sig,o_type=otype)

print('Price:'+str(solution))
print('Delta:'+str(delta))
print('Gamma:'+str(gamma))
print('Vega:'+str(vega))
print('Theta:'+str(theta))
print('Rho:'+str(rho))

