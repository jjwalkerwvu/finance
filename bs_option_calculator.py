'''
Simple script that calls heat_solver.py to solve the Black-Scholes equation.
In the future, I envision turning this into a function that returns: 
*The time-dependent value of the put/call option in terms of value of the 
underlying.
*Plot the Option value in (time,value of the underlying) space
*The analytical solution
*Can calculate the greeks for a given option?
*Can calculate the implied volitity given real bid/ask data?
*Can calculate risk-neutral portfolios, including:
	- Delta neutral (insensitive to changes in value of an underlying asset)
	- Gamma neutral (If portfolio is initially delta neutral, being gamma
					 neutral ensures that the portfolio will remain delta 
					 neutral to further price changes in the underlying asset
	- Vega neutral (???) (insensitive to changes in implied volatility?)
	- Theta neutral(???) (insensitive to time value)
	- rho (???) (insenstive to change in interest rates? maybe this is not
				 so important, but wanted to list this)
*Calculate Option value using binomial pricing model!
*Can calculate the "volatility" smile from the option chain!
*We might be required to use a fully implicit method for non-smooth final 
conditions: the method is unconditionally stable for 1/2<=theta<=1
Theta-method overview:
	- Heat equation becomes: 
		(u_[i]^[n+1]-u_[i]^[n])/dt =
       		theta*(u_[i+1]^[n+1]-2u_[i]^[n-1]+u_[i-1]^[n+1])/(dx)^2 +
			(1-theta)*(u_[i+1]^[n]-2u_[i]^[n]+u_[i-1]^[n])/(dx)^2 
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	- theta=0 explicit:             *
						            |
					             *--*--*
	- 
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	- theta=1/2, CN:             *--*--*
                                    |
                                 *--*--*

	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	- theta=0, fully implicit:   *--*--*
	                                |
                                    *
	  Finite difference:	  
		(u_[i]^[n+1]-u_[i]^[n])/dt =
       		theta*(u_[i+1]^[n+1]-2u_[i]^[n-1]+u_[i-1]^[n+1])/(dx)^2
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
16 December 2018
J.J. Walker
'''
## import libraries
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erf
from heat_solver_dirichlet import heat_solver_dirichlet

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## This is just a Crank-Nicolson Method for solving heat equation
## just a simple test right now for checking heat_solver.py:
## (Appears to work as of 1/19/2019)
#L=np.pi
#xn=np.pi
#x0=0
#un=0
#u0=0
#p=20
#N=50
#T=0.01*50
#x=np.zeros(p-1)
#u=np.zeros(p-1)
#dx=L/p
#x=x0+dx*np.arange(1,p,1)
#for i in range(0,p-1):
#	u[i]=np.sin(x[i])

#x,U=heat_solver(u,T,N,p,x0,xn,u0,un)


#x=np.append(x,xn);	
#x=np.insert(x,1,x0);
#exact=np.exp(-0.5)*np.sin(x);
#error=abs(exact-U);

#print(str(U))
#plt.figure()
#plt.plot(x,U,'.b')
#plt.show()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## let's try using heat_solver.py in order to compute the value of a european 
## option

## strike price
K=1

## Smax is the largest stock price we will consider; which corresponds to the  
## right boundary condition. 
## I will first try considering a maximum value that is ten times the strike
## price
Smax=10*K
## Smin cannot be zero, because we will transform to log(S/K) later
Smin=1e-4
## Include the spot price; value of underlying at t=0:
St=K
## 100 points per S increment, which gives 1000 total points
p=1000
## the resulting S, stock price array:
S=np.linspace(Smin,Smax,p)
## total time till expiry, in months?
T=1
## number of time steps; dt = T/N
N=50
## We then have a time array that should go from t=0 to t=T (expiration)
t=np.linspace(0,T,N)
## risk free rate (use 4 week treasury bill)
r=(2.4)/100
## volatility (this is given as a percentage?)
sigma=(10.0)/100
## the factor k; risk free rate as a multiple of the volatility
k=2*r/(sigma**2)
## alpha and beta, which will be needed when we transform back later
a=-(k-1)/2
b=-(k-1)**2/4

## 
## perform the transformations:
x=np.log(S/K)
## Tau: Tau=(sigma**2)/2*(T-t)
## when we convert back later, it will be: t=T-2*Tau/(sigma**2)
Tau=(sigma**2)/2*(T-t)
## The initial values for the value of the call option
## calculate according to max[exp((k+1)*x/2)-exp((k-1)*x/2),0]
u=(np.exp((k+1)/2*x)-np.exp((k-1)/2*x))*(
	(np.exp((k+1)/2*x)-np.exp((k-1)/2*x))>0)

## call the CN solver; use dummy for x because we already have x-variable
xdummy,U=heat_solver_dirichlet(u,Tau[0],N,p-2,x[0],x[-1])

## Now we have to transform back! 
## S array has already been made, transformations involve u
## V is the value, or payoff of the option as a function of stock price
## recall that Tau~T-t, so Tau[0] corresponds to t=0, and Tau[-1] corresponds
## to t=T
VN=K*np.exp(a*x+b*Tau[0])*U[0,:]
V0=K*np.exp(a*x+b*Tau[-1])*U[-1,:]


## plug in exact solution of Black-Scholes Equation to see how good the method
## is!
exact=np.zeros([N,p])
V=np.zeros([N,p])
for index in range(0,N):
	d1=1/sigma/np.sqrt(T-t[index])*(np.log(S/K)+(r+sigma**2/2)*(T-t[index]))
	d2=d1-sigma*np.sqrt(T-t[index])
	exact[index,:]=1.0/2*(1+sp.special.erf(d1/np.sqrt(2)))*S-1.0/2*(1+sp.special.erf(d2/np.sqrt(2)))*K*np.exp(-r*(T-t[index]))
	V[N-index-1,:]=K*np.exp(a*x+b*Tau[index])*U[index,:]
#exact=np.exp(-0.5)*np.sin(x);
error=abs(exact-V);

print(str(VN[100]))
#plt.figure()
#plt.plot(x,U[0,:],'.b')
#plt.plot(x,U[N-1,:],'.k')
#plt.plot(S,VN,'.r')
#plt.plot(S,V0,'.g')
#plt.xlim(0,2*K)
#plt.ylim(0,2*K)
plt.xlim(0.5,1.5)
plt.ylim(0,1)
## because the solver "works backward", there will be the most error at t=0,
## not at expiration
l=0
plt.plot(S,exact[l,:],'.k')
plt.plot(S,V[l,:],'.b')
plt.plot(S,error[l,:],'.r')
plt.show()
#plt.savefig('test_final.png')






