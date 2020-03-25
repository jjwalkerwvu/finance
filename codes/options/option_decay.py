'''

bs_analytical_test.py

28 April 2019
Jeffrey J. Walker

A simple test of the bs_analytical_solver.py function

'''

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

## insert the path corresponding to bs_analytical solver; we will need this 
## function!
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jjwalker/Desktop/finance/codes/options')
from bs_analytical_solver import bs_analytical_solver

otm_strike=300.09
atm_strike=290.09
itm_strike=280.09
St=290.09
rfr=(1.9)/100
texp=1/365.0
sig=(21.3044/100)
otype='c'
actual_price=1.0
t=np.linspace(1,365,365)
texp=t[::-1]
otm_solution=np.zeros((len(t)))
atm_solution=np.zeros((len(t)))
itm_solution=np.zeros((len(t)))
## do we need any arrays for the second derivative?

for i in range(len(t)):
    otm_solution[i],second_deriv,delta,gamma,vega,theta,rho = bs_analytical_solver(
	S=St,K=otm_strike,r=rfr,T=texp[i]/365.0,sigma=sig,o_type=otype)
    atm_solution[i],second_deriv,delta,gamma,vega,theta,rho = bs_analytical_solver(
	S=St,K=atm_strike,r=rfr,T=texp[i]/365.0,sigma=sig,o_type=otype)
    itm_solution[i],second_deriv,delta,gamma,vega,theta,rho = bs_analytical_solver(
	S=St,K=itm_strike,r=rfr,T=texp[i]/365.0,sigma=sig,o_type=otype)

#print('Price:'+str(solution))
#print('Delta:'+str(delta))
#print('Gamma:'+str(gamma))
#print('Vega:'+str(vega))
#print('Theta:'+str(theta))
#print('Rho:'+str(rho))
## This does line does not look right...
#print('Implied Volatilty, %: ' + str((sig/solution)*100))

## plot the value of extrinsic value (just the time value, intrinsic value
## remains constant
plt.figure()
plt.subplot(211)
plt.title('Normalized Time Value of Option')
plt.plot(texp,atm_solution/atm_solution[0],'-k',label='ATM')
#plt.plot(texp,(itm_solution-(St-itm_strike))/(itm_solution[0]-(St-itm_strike)),'-b',label='ITM')
plt.plot(texp,(itm_solution-(St-itm_strike))/(itm_solution[0]-(St-itm_strike)),'-b',label="{0:.2}".format(100*(St-itm_strike)/St)+'% '+'ITM')
plt.plot(texp,otm_solution/otm_solution[0],'-r',label="{0:.2}".format(100*(otm_strike-St)/St)+'% '+'OTM')
#plt.ylim(bottom=0,top=np.max(solution))
plt.xlim(left=texp[0],right=texp[-1])
plt.xlabel('Time (days to expiration)')
plt.ylabel('[Extrinsic Value]/[Extrinsic Value at t=0]')
plt.legend(loc='best')
plt.tight_layout()
## Also plot the Normalized Value of Option. 
plt.subplot(212)
plt.title('Normalized Value of Option')
plt.plot(texp,atm_solution/atm_solution[0],'-k',label='ATM')
plt.plot(texp,itm_solution/(itm_solution[0]),'-b',label="{0:.2}".format(100*(St-itm_strike)/St)+'% '+'ITM')
plt.plot(texp,otm_solution/otm_solution[0],'-r',label="{0:.2}".format(100*(otm_strike-St)/St)+'% '+'OTM')
#plt.ylim(bottom=0,top=np.max(solution))
plt.xlim(left=texp[0],right=texp[-1])
plt.xlabel('Time (days to expiration)')
plt.ylabel('[Value]/[Value at t=0]')
plt.legend(loc='best')
plt.tight_layout()
##
plt.savefig('option_decay.png')
