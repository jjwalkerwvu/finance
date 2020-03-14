"""
Created on Saturday March 14

@author: Jeffrey J. Walker

    yahoo_option_chain_scraper.py
        This script obtains the options chain for a particular stock symbol.
        Turn this into a function later?
"""

import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date
import requests
import lxml.html as lh
import re
import pandas as pd
import numpy as np
## import the analytical solver to calculate the greeks for each option chain!
#from bs_analytical_solver import bs_analytical_solver

## keep in mind, structure of the table may differ for different securities!
## note also, that etfs like spy pay dividends

## the full put call inequality for american options:
# s - k <= c_a - p_a <= S - k*exp(-rT)
# s - the spot price
# k - strike price
# c_a - american call
# p_a - american put
# r - risk free rate
# T - time to expiration

## the yield of the risk-free rate; scrape this from somewhere too or use as a
## constant for now?
y=0.02

# the ticker to use?
ticker='SPY'
# the url:
url_string='https://finance.yahoo.com/quote/'+ticker+'/options/'
# another url example:
#https://www.marketwatch.com/investing/stock/uber/options?countrycode=US&showAll=True
# so stock or fund matters!
#url='https://www.nasdaq.com/market-activity/stocks/tsla/option-chain'
## or:
#url='https://old.nasdaq.com/symbol/tsla/option-chain'

#soup = BeautifulSoup(url_string, 'html.parser')
r = requests.get(url_string)
c=r.content

doc = lh.fromstring(r.content)
tr_elements = doc.xpath('//tr')

## From Yahoo finance, the columns of the table for calls comes from 
## tr_elements[0].text_content()

## find out the next table element number that corresponds to puts;
## this number is the cutoff for reading calls data.
header=tr_elements[0].text_content()
for line in range(len(tr_elements)):
	if tr_elements[line].text_content()==header:
		puts_begin=line
		
## now reuse the header variable, fill with the column names
header=tr_elements[0].text_content().split()

call_cols=[]
## Here is a method to further split column names on capital letters
for string in header:
	label=re.findall('[A-Z][^A-Z]*', string)
	call_cols.extend(label)

## or simpler, just input them here since I know what the columns are.
## Would be good if I could automate this, though.
call_cols=['Contract Name','Last Trade Date','Strike','Last Price','Bid','Ask',
	'Change','% Change','Volume','Open Interest','Implied Volatility']
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## prepare the columns for calls?
## prepare a dictionary based on the column names we just generated;
## this dictionary will be used later to produce a data frame

## old method, which I have replaced.
## The old method automatically populates the columns
#chain_dict={i:[] for i in call_cols}

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Now that we have the columns, input the data for calls
## counter not needed in new method?
#counter=0
#option_list=[]
#new_table=[]
cname=[]
tdate=[]
sprice=[]
ltprice=[]
bid=[]
ask=[]
change=[]
pchange=[]
volume=[]
ointerest=[]
iv=[]
for line in range(1,puts_begin):
	## the first split is used to get the contract name and last trade date.
	first_split=tr_elements[line].text_content().split('EDT')
	## subtract off four to include the year; works as long as the current 
	## year is less than 10000 :-)
	date_begin=len(first_split[0].split('-')[0])-4
	## update some columns?
	cname.append(first_split[0][:date_begin-4])
	tdate.append(first_split[0][date_begin-4:])
	## separating the strike from the last price is tricky.
	## Right now, it appears that there are only two decimal places for 
	## strike prices, so look for position of the first decimal.
	strike_end=len(first_split[1].split('.')[0])+2
	## add one needed for python indexing
	sprice.append(first_split[1][:strike_end+1])
	## getting last trade price, bid, ask, change, % change, volume, open
	## interest and implied volatility is also tricky.
	## Assuming again there are only two decimal places for strike prices,
	## which is a reasonable assumption.
	## Let us just get all the positions in the string for the decimals.
	dec_pos=[pos for pos, char in enumerate(first_split[1]) if char == '.']
	## add two to each position for the number of digits after the decimal,
	## plus one for the decimal itself.
	ltprice.append(first_split[1][dec_pos[0]+3:dec_pos[1]+3])
	bid.append(first_split[1][dec_pos[1]+3:dec_pos[2]+3])
	ask.append(first_split[1][dec_pos[2]+3:dec_pos[3]+3])
	## That may be all we can get with splits on decimal points; in fact,
	## bid and ask may have '-' characters...
	## the following procedure will work if we assume that the bid and ask do
	## not ever have '-' characters.
	## First step: look for '-' characters in the rest of the string.
	## Remember, there are 5 columns left to populate.
	## It appears that IV is always given as a decimal, and never as '-'
	if '-' in first_split[1][dec_pos[3]+3:]:
		## first, get the position of all '-' characters, then count how many
		## there are.
		dash_pos=[pos for pos, char in enumerate(first_split[1]) if char == '-']
		ndashes=len(dash_pos)
		## first case: the max number of dashes, which is 4
		if ndashes==4:
			## if there are 4 dashes, Change,% Change, Volume, and Open 
			## Interest do not have values.
			change.append(np.nan)
			pchange.append(np.nan)
			volume.append(np.nan)
			ointerest.append(np.nan)
			## but get rid of the '%' at the end, that's why :-1
			iv=first_split[1][dash_pos[-1]+1:-1]
		elif ndashes==3:
			## if there are 3 dashes, we need to see where they are.
			## if the first dash is the first character, then we know change
			## has no value
			## I think this statement works
			if dash_pos[0]==dec_pos[3]+2:
				change.append(np.nan)
			## if dash_pos[0]~=0, then change cannot be nan
			else:
				change.append(first_split[1][dec_pos[3]+3:dash_pos[0]])
		elif ndashes==2:

		elif ndashes==1:
			
	## If not, we may proceed as normal!
	else:
		change.append(first_split[1][dec_pos[3]+3:dec_pos[4]+3])
		## may have to remove + later? will to_numeric get rid of possible plus
		## signs?
		pchange.append(first_split[1][dec_pos[4]+3:dec_pos[5]+3])
		## will need to add 1 to get rid of '%' character?
		volume.append(first_split[1][dec_pos[5]+3:dec_pos[6]+3])
	
## all of the columns have been populated into lists; put into dictionary.
## I had another way of doing this, but does not seem readily adaptible to 
## yahoo's formatting.	
rows=[cname,tdate,sprice,ltprice,bid,ask,change,pchange,volume,ointerest,iv]

## for testing only	
#cname=0;tdate=0;sprice=0;ltprice=0;bid=0;ask=0;change=0;pchange=0;volume=0;ointerest=0;iv=0; 

chain_dict={call_cols[i]:[rows[i]] for i in range(len(call_cols))}
## make the dataframe for calls:
call_chain=pd.DataFrame.from_dict(chain_dict)
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Now get the puts side of the chain.
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## provisional stuff (vestigal) after here

## prepare the columns for calls
df_col=['Symbolc']
for element in col[1:7]:
    df_col.append(element[0].replace('.','')+"c")
df_col.append('Strike')
df_col.append('Symbolp')
## prepare the columns for puts
for element in col[9:]:
    df_col.append(element[0].replace('.','')+"p")
## get rid of any spaces!
i=0
for name in df_col:
    df_col[i]=name.replace(' ', '_')
    i=i+1
## prepare a dictionary based on the column names we just generated.
chain_dict={i:[] for i in df_col}

counter=0
option_list=[]
strike_equal_spot=[]
new_table=[]
exp_date=[]
for element in tr_elements:
    table_row=element.text_content().split()
    ## have to get rid of commas for each element in table_row, somehow
    option_list.append(table_row)
    if 'Expires' in table_row:
        new_table.append(counter)
        
        exp_date.append(element.text_content().replace("\r\n","").strip())
    if 'Current' in table_row:
        strike_equal_spot.append(counter)
        ## I think this command works to remove the rows where the current
        ## strike price is listed
        option_list.remove(table_row)
    counter=counter+1
    
table2=option_list[new_table[1]+2:new_table[2]-1]
