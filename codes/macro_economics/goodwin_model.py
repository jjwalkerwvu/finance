'''
goodwin_model.py

9 January 2020
Author: Jeffrey J. Walker


This function computes a time series for the worker and capitalist share of
capital.
See: Matheus R. Grasselli and Aditya Maheshwari 2017

Inputs:
	l			- employment of labor, time dependent
	k			- homogenous capital; can use single wage rate w.
	rho			- output/capital ratio; this is a constant with time?
	x			- labor productivity, which increases exponentially with time
				  as a result of technology, with rate g_x. This seems 
				  uncontroversial
	g_x			- growth rate of labor productivity due to technology
	g_l 		- growth rate of labor. Labor expected to grow exponentially?
				  (with the population)
	
	
Outputs:
	q			- aggregate output, q = min(g_x*l,k/rho)
	
'''

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## importations and declarations
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from scipy import integrate

##
## productivity growth rate
alpha=0.018
## labor force growth rate
beta=0.02
delta=0.06
## defined different? as a negative number?
gamma=0.3
rho=0.4
nu=3.0
k=1.0

## values from Robertvienneau's blog:
## url="http://robertvienneau.blogspot.com/2008/"
## k=s and nu=sigma for his parameter set
alpha=0.05
beta=0.1
delta=-0.1
gamma=0.95
rho=1.0
nu=0.20
k=0.25


## long-run value of the capital output ratio is 0.4
#rho=0.4
## capital to output ratio
#nu=3.0
## fraction reinvisted into the accumulation of capital, <=1
#k=1.0
## what is beta??
#beta=0.06
## productivity growth rate; maybe the long run average is 1%?
#g_x=0.018
## growth rate of labor pool; approximately the same as the population growth?
#g_l=0.02

## I don't know what phi or l_p are, but require 0<phi+g_x<l_p
#phi=0.3
#l_p=0.4

## time, what units? make an array.
## Should be normalized maybe, what timescale to use?
period=2*np.pi/np.sqrt((alpha+gamma)*(k/nu-(alpha+beta+delta)))
ts=np.linspace(0,4*period,1e4)

def de_dt(e, t):
    return [e[0]*(-gamma-alpha+rho*e[1]), 
			e[1]*((1.0-e[0])*k/nu-(alpha+beta+delta))]

## The employment rate, e=l/N, where N is the labor pool

## Set the initial values for employment rate and worker share in an array:
## First value is worker share, second value is employment rate
#e0=[.68,.84]
e0=[0.9,.7]
e=integrate.odeint(de_dt,e0,ts)

## plot the phase portrait, employment rate as function of wage share
plt.plot(e[:,0],e[:,1],'.k');plt.show()

## Here is how you calculate aggregate output:
## output=a(t)*L(t)=a(t)*[N(t)*employment_rate(t)]
a0=1.0	# productivity level at t=0
N0=1.0	# Total labor force, as number of people
## total output (GDP!)
q=a0*N0*np.exp((alpha+beta)*ts)*e[:,1]
## total wages; is this correct?
w=q*e[:,0]

## make a simple diagnostic plot
## plot employment rate?
plt.plot(ts,e[:,0],'.k');plt.show()

## The "fun" plot: plot potential gross profit, 
## then gross output (GDP!) and total wages:
plt.plot(ts,a0*N0*np.exp((alpha+beta)*ts),'-k');plt.plot(ts,q,'-b');plt.plot(ts,w,'-r');plt.show()






