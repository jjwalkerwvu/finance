% hedging_optimizer.m
%
% Created 4 April 2020
%
% This script uses glpk to solve an integer programming problem

% read in the data:

puts=csvread('hedge_test.csv');

% This was the standard for how the csv is structured; may change
% Maybe strip the columns?
delta=puts(:,2)
gamma=puts(:,3)
price=puts(:,7)
strike=puts(:,9)


% number of shares
Ns=100;

c=100*price
%A=diag(sparse(delta))
%Aeq=full(A)
Aeq=delta'
beq=(-Ns/100)
lb=zeros(size(c));
%ub=[];
%ctype=repmat("S",1)
ctype="S"
vartype=repmat("I",size(c))

% the 1 is for minimization
[x, fval, errnum] = glpk(c, Aeq, beq, lb, ub, ctype, vartype, 1);

% The array elements corresponding to non-zero elements of solution array x
non_triv=find(x)
% Strikes to purchase and how many of each:
for i=1:length(non_triv)
	fprintf(...
	'Buy %d contract(s) at the $%d strike price at cost $%d per contract\n',...
	x(non_triv(i)),strike(non_triv(i)),price(non_triv(i))*100);
endfor
fprintf('At total cost $%d\n',fval);
