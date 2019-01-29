%%	Jeffrey Walker
%%	Math 522, assignment 1 (b): Crank-Nicolson method solution for the heat 
%%  equation. The following program ASSUMES DIRICHLET BOUNDARY CONDITIONS ONLY.
%%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
%% clear everything as a precaution
clear all;
%% Size of the spatial domain:
L=pi;
%% location of "left-most' boundary in the spatial domain:
x0=0;

%% Number of grid points in spatial domain:
p=20;	%% For this explicit method, we will have (p-1) elements in the 
        %% simulation volume.

%% set up the spatial grid:
dx=L/p;
%% set up the 1-dimensional x-vector (array) so that it has (p-1)-number of 
%% elements. 
x=zeros(1,p-1); 
%% set up array for the initial conditions, and later the solution array.
u=zeros(1,p-1);
%% set up arrays for a,b,c,d,piv, and V vectors:
a=zeros(1,p-2);
b=zeros(1,p-1);
c=zeros(1,p-2);
d=zeros(1,p-1);
piv=zeros(1,p-2);
V=zeros(1,p-1);
%% Declare boundary conditions:
u0=0;u_L=0;

%% Time information:

%% Time step size:
dt=0.01;

%% Number of time steps:
N=50;

r=dt/dx/dx;

%% Statement below assures that we have p-number of grid points uniformly spaced 
%% between 0 and L. The points 0 and L are not included because they are specified 
%% on the boundary.
for i=1:p-1
	x(i)=x0+i*dx;
	%% While we're in this loop, set up the initial condition array
	u(i)=sin(x(i));
	%% Also, calculate b-vector:
	b(i)=(1+r);
	
end;
%% concatenate boundary values to the initial condition array, makes next steps 
%% easier.
u=[u0,u,u_L];	%% u now has p+1 elements instead of p-1.

%% After the initial conditions have been specified, the d-vector can be constructed,
%% starting with the first and p-1 elements:
d(1)=r*u(1)+u(2)-r*u(2)+0.5*r*u(3);

%% I have simplified and changed the form in the notes to exploit my matrix 
%% concatenation above; Need to add one to each index for matlab.
d(p-1)=r*u(p+1)+u(p)-r*u(p)+0.5*r*u(p-1);

for i=3:p-1
	%% This line below should be correct:
	d(i-1)=0.5*r*u(i+1)+u(i)-r*u(i)+0.5*r*u(i-1);
end
%% set the array V=d
V=d;

%% compute the a-vector:
for i=1:p-2
	a(i)=-0.5*r;
end
%% compute the c-vector:
for i=1:p-2
	c(i)=-0.5*r;
end

%% calculate pivots and rescale the diagonal elements and V array; This is 
%% the forward sweep which ensures that we will have an upper triangular matrix 
%% for u.
for i=1:p-2
	piv(i)=-a(i)/b(i);	%% I put a minus sign in front, as used in Gordon 
                        %% Everstine's text
	b(i+1)=b(i+1)+piv(i)*c(i);
	V(i+1)=V(i+1)+piv(i)*V(i);
	
end
%% get the solution for the last row of the matrix. Tricky, because u(1) and 
%% u(p+1) were set to the bc's earlier.
u(p)=V(p-1)/b(p-1);	%% u(p) is in the simulation volume, not a boundary value!!

%% back subsitution, i.e., solve the upper triangular matrix. 
%% Solving this the first time means that we have made one time iteration!!
for i=p-1:-1:2
	u(i)=(V(i-1)-c(i-1)*u(i+1))/b(i-1);
end


%% The time loop:
%% first timestep was already done (as discussed above,) so only go to the N-1 
%% timestep
for j=1:N-1
	%% update V appropriately; i.e., we need to calculate d again.
	%% After the initial conditions have been specified, the d-vector can be 
    %% constructed, starting with the first and p-1 elements:
	d(1)=r*u(1)+u(2)-r*u(2)+0.5*r*u(3);
	d(p-1)=r*u(p+1)+u(p)-r*u(p)+0.5*r*u(p-1);

	for i=3:p-1
		%% This line below should be correct:
		d(i-1)=0.5*r*u(i+1)+u(i)-r*u(i)+0.5*r*u(i-1);
	end
	%% set the array V=d
	V=d;
	%% already have the pivots, so this next step can be done quickly. 
	for i=1:p-2
		V(i+1)=V(i+1)+piv(i)*V(i);
	end
	%% get the solution for the last row of the matrix. Tricky, because u(1) 
    %% and u(p+1) were set to the bc's earlier.
	u(p)=V(p-1)/b(p-1);	%% u(p) is in the simulation volume, not a boundary 
                        %% value!! b(p-1) is a known value, calculated earlier.
			
	%% already have c and b arrays, so this next step is just solving the upper 
    %% triangular matrix.
	for i=p-1:-1:2
		u(i)=(V(i-1)-c(i-1)*u(i+1))/b(i-1);
	
	end
	%% I've commented out the line below, but this allows the user to watch 
    %% the solution evolve in time.
	%drawnow;plot([x0,x,L],u);axis([x0 L 0 1])
end	

%% commands I need to make a table for p-index, u, exact, and error:
p_index=[0:1:20];
%% concatenate the 1D array for the x-axis with its boundary values.
%% exp(-1/2)*sin(x) is the exact solution for this pde.
exact=exp(-0.5)*sin([x0,x,L]);
error=abs(exact-u);