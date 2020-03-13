"""
October 14 2019

dice_tester.py
	
	This script rolls 4 dice, and sees how many of the dice have values 
	greater than 4.
	Many trials are performed, to find the probability of rolling 2 dice with
	values greater than 4.

	Consider turning this into function with 
	Inputs:
	n_sides
	n_dice
	roll_success
	n_successes
	n_trials

@author Jeffrey J. Walker
"""

import numpy as np

## The size of the die; 6 for d6, etc.; can only be a whole number!
n_sides=6
## The number of dice; can only be a whole number!
n_dice=4
## number needed to roll for success; n_success=5 means you have to roll 5 or
## greater.
## can only be a whole number!
roll_success=5
## number of successful rolls needed for the entire roll to be a success;
## can only be a whole number!
n_successes=2


n_trials=10000
success_counter=0


## perform the trials
for i in range(n_trials):
	## np.random.permutation(m) returns an array, where m-1 is the max value
	#d1=np.random.permutation(6)

	## easier to use np.random.randint(1,7) to generate dice rolls (simpler).
	## Have to use 7 instead of 6, because 6 will not be returned if 6 is the
	## maximum range
	#d1=np.random.randint(1,n_sides+1)
	#d2=np.random.randint(1,n_sides+1)
	#d3=np.random.randint(1,n_sides+1)
	#d4=np.random.randint(1,n_sides+1)
	#trial_successes=(1.0*(d1>(roll_success-1))+
	#	1.0*(d2>(roll_success-1))+
	#	1.0*(d3>(roll_success-1))+
	#	1.0*(d4>(roll_success-1)))
	
	## Surely there is a better, vectorized method to do this?
	d=np.zeros((n_dice))
	for i in range(n_dice):
		d[i]=1.0*(np.random.randint(1,n_sides+1)>(roll_success-1))
	
	trial_successes=sum(d)
	success_counter=success_counter+1.0*(trial_successes>(n_successes-1))
	
## Include printout of number of dice, how many sides, and number of 
## successes needed, and probability of success.
## Maybe make this printout a little cleaner; split into multiple lines?
print('Require: '+str(n_successes)+' successes from: '+str(n_dice)+ ' Dice thrown on: '+str(n_sides)+'-sided dice, where success is a die roll>' + str(roll_success-1))
print('Probability of Success: '+str(success_counter/n_trials)+', After '+str(n_trials)+' Trials')
