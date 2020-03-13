'''
Tri-diagonal matrix solver for python
15 December 2018
J.J. Walker
'''

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## importations and declarations
import numpy as np

## the function:
def trisolver(a,b,c,d):
	## inputs: 	a - the off-diagonal, lower triangular part of the matrix;
	##				has in principle len(b)-1 elements; but in my function,
	##				input len(a)=len(b), where a0 value is unused
	##			b - the diagonal vector of the matrix, determines 
	##				dimensionality of the system
	##			c - the off-diagonal, upper triangular part of the matrix;
	##				has in principle len(b)-1 elements; but in my function,
	##				input len(a)=len(b), where cn value is unused
	##			d - the right-hand side of the equation; has len(b) elements
	## output:  x - the solution array, has len(b) elements
	## Here is a schematic to illustrate:
	##			|b0 c0             0   ||x0|   |d0|
	##			|a1 b1 c1          .   ||x1|   |d1|
	##			|   a2 b2 c2       .   ||x2|   |d2|
	##			|.     .  .  .     .   ||. | = |. |
	##			|.        .  .  .  .   ||. |   |. |
	##			|.           .  .  cn-1||. |   |. |
	##			|0              an bn  ||xn|   |dn|
	##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	## perform some basic error checking on the input variables!
	## make sure a,b,c,d are np arrays, or non-nested lists with numerical 
	## values only!
	
	## annoyingly, we have to copy the arrays before doing operations?
	ac, bc, cc, dc = map(np.array, (a, b, c, d))
	
	## total number of equations
	n=len(b)
	## initialize x array now:
	x=np.zeros(n)
	## first row:
	cc[0]=c[0]/b[0];
	dc[0]=d[0]/b[0];
	
	for i in range(1,n-1):
		## 
		temp=bc[i]-ac[i]*cc[i-1];
		cc[i]=c[i]/temp;
		dc[i]=(d[i]-ac[i]*dc[i-1])/temp;
				
	
	dc[n-1]=(d[n-1]-ac[n-1]*dc[n-2])/(bc[n-1]-ac[n-1]*cc[n-2]);

	x[n-1]=dc[n-1];
	## go "backwards" to fill in all the values for x
	for i in reversed(range(0,n-1)):
		x[i]=dc[i]-cc[i]*x[i+1];

	return x,dc,ac,bc,cc

def alt_trisolver(a,b,c,d):
	## Note: I found this online at: 
	## https://gist.github.com/cbellei/8ab3ab8551b8dfc8b081c518ccd9ada9
	## Unlike my trisolver, len(a)=len(c)=len(b)-1
	'''
    TDMA solver, a b c d can be NumPy array type or Python list type.
    refer to http://en.wikipedia.org/wiki/Tridiagonal_matrix_algorithm
    and to http://www.cfd-online.com/Wiki/Tridiagonal_matrix_algorithm_-_TDMA_(Thomas_algorithm)
    '''
	nf = len(d) # number of equations
	ac, bc, cc, dc = map(np.array, (a, b, c, d)) # copy arrays
	for it in xrange(1, nf):
		mc = ac[it-1]/bc[it-1]
		bc[it] = bc[it] - mc*cc[it-1] 
		dc[it] = dc[it] - mc*dc[it-1]
        	    
	xc = bc
	xc[-1] = dc[-1]/bc[-1]

	for il in xrange(nf-2, -1, -1):
		xc[il] = (dc[il]-cc[il]*xc[il+1])/bc[il]

	return xc
