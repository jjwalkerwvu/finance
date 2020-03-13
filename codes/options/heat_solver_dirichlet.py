'''
One-dimensional heat equation pde solver
Based on my old notes, adapted from my numerical methods class in grad school.
As of now the following function ASSUMES DIRICHLET BOUNDARY CONDITIONS ONLY.

15 December 2018
J.J. Walker

Confirmed working: 19 January 2019
'''

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## importations and declarations
import numpy as np
import matplotlib as plt
## do I need to import trisolver? make sure it is in the same directory!
## (or merge that function in with this)
from trisolver import trisolver

## make sure to do error checking on all of these variables! Make sure they
## are numpy arrays, etc.
def heat_solver_dirichlet(u,T,N,p,x0,xn):
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## inputs:
	##			u  - the initial condition array
	##			N  - number of time steps
	##			u0 - boundary condition of u at x0
	##			un - boundary condition of u at xn	 
	##			p  - number of grid points in the spatial domain
	##			T  - final time of the simulation
	##			x0 - location of "left-most' boundary in the spatial domain
	##			xn - location of "right-most' boundary in the spatial domain,
	##				 xn>x0
	## outputs:
	##			U  - the spatial and temporal solution for 1d heat equation,
	##				 which means u is output as a 2d array
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## compute the size of the spatial domain, L
	## better idea to get p is just find size of initial u:
	p=len(u)-2
	L=xn-x0
	## set up the spatial grid:
	dx=L/p;
	## set up the 1-dimensional x-vector (array) so that it has (p-1)-number  
	## of elements. 
	#x=np.zeros(p-1); 
	

	## how to choose time step size?? want to make sure we satisfy courant 
	## condition
	dt = T/N
	r=dt/dx/dx
	## set up arrays for a,b,c,d,piv, and V vectors:
	a=np.ones(p-2)*(-0.5*r);
	b=np.ones(p-1)*(1+r);
	c=np.ones(p-2)*(-0.5*r);
	d=np.zeros(p-1);
	piv=np.zeros(p-2);
	V=np.zeros(p-1);
	## preallocate for the temporal and spatial solution array
	U=np.zeros([N,p+2])
	## t=0 values for the U solution array are equal to u0(x)
	U[0,:]=u
	
	## Statement below assures that we have p-number of grid points uniformly  
	## spaced between x0 and xn. The points 0 and n are not included because  
	## they are specified on the boundary.
	x=x0+dx*np.arange(1,p,1)
	

	## concatenate boundary values to the initial condition array, makes next  
	## steps easier.
	#u=np.append(u,un);	
	#u=np.insert(u,0,u0); 
	
	## u now has p+1 elements instead of p-1.

	## After the initial conditions have been specified, the d-vector can be 
	## constructed, starting with the first and p-1 elements:
	d[0]=r*u[0]+u[1]-r*u[1]+0.5*r*u[2];

	## I have simplified and changed the form in the notes to exploit my  
	## matrix concatenation above; Need to add one to each index for matlab.
	d[p-2]=r*u[p]+u[p-1]-r*u[p-1]+0.5*r*u[p-2];

	## can I vectorize this?
	#for i=3:p-1
	for i in range(2,p-1):
	## This line below should be correct:
		d[i-1]=0.5*r*u[i+1]+u[i]-r*u[i]+0.5*r*u[i-1];

	## set the array V=d:
	## have to multiply by some constant; have to be careful with equating
	## variables in python
	V=(1.0)*d;
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## calculate pivots and rescale the diagonal elements and V array; This is 
	## the forward sweep which ensures that we will have an upper triangular  
	## matrix for u.
	for i in range(0,p-2):
		piv[i]=-a[i]/b[i];	## I put a minus sign in front, as used in Gordon 
                        	## Everstine's text
		b[i+1]=b[i+1]+piv[i]*c[i];
		V[i+1]=V[i+1]+piv[i]*V[i];
	

	## get the solution for the last row of the matrix. Tricky, because u(1) and 
	## u(p+1) were set to the bc's earlier.
	## u(p) is in the simulation volume, not a boundary value!
	u[p-1]=V[p-2]/b[p-2];	

	## back subsitution, i.e., solve the upper triangular matrix. 
	## Solving this the first time means that we have made one time iteration!!
	for i in reversed(range(1,p-1)):#i=p-1:-1:2
		u[i]=(V[i-1]-c[i-1]*u[i+1])/b[i-1];
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## The time loop:
	## first timestep was already done (as discussed above,) so only go to the  
	## N-1 timestep. There are a total of N-1 steps
	
	for j in range(1,N):
		## update V appropriately; i.e., we need to calculate d again.
		## After the initial conditions have been specified, the d-vector can be 
    	## constructed, starting with the first and p-1 elements:
		#print(str(j))		
		d[0]=r*u[0]+u[1]-r*u[1]+0.5*r*u[2];
		d[p-2]=r*u[p]+u[p-1]-r*u[p-1]+0.5*r*u[p-2];

		## isn't there some way to vectorize this?
		for i in range(2,p-1):
		## This line below should be correct:
			d[i-1]=0.5*r*u[i+1]+u[i]-r*u[i]+0.5*r*u[i-1];
	
		## set the array V=d
		V=(1.0)*d;
		## already have the pivots, so this next step can be done quickly. 
		for i in range(0,p-2):
			V[i+1]=V[i+1]+piv[i]*V[i];
	
		## get the solution for the last row of the matrix. Tricky, because  
    	## u(1) and u(p+1) were set to the bc's earlier.
		## u(p) is in the simulation volume, not a boundary 
		## value!! b(p-1) is a known value, calculated earlier.
		u[p-1]=V[p-2]/b[p-2];	
                        	
			
		## already have c and b arrays, so this next step is just solving the  
    	## upper triangular matrix.
		#for i=p-1:-1:2
		for i in reversed(range(1,p-1)):
			u[i]=(V[i-1]-c[i-1]*u[i+1])/b[i-1];
		
		## update the U array, so we can keep track of it in time
		U[j,:]=u
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## return the solution array; in the future may want to return some 
	## diagnostic information, like whether we've violated a courant 
	## condition, etc.
	## return a time array?
		
	return x,U
	





	
