#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 19:00:22 2019

@author: jeffreywalker

    option_chain_scraper.py
        This script obtains the options chain for a particular stock symbol.
        Turn this into a function later
        
"""

#from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import requests
import lxml.html as lh
import pandas as pd
import numpy as np

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

## the yield of the risk-free rate
y=0.02

# the ticker to use?
ticker='spy'
# the url:
url_string='https://www.marketwatch.com/investing/fund/SPY/options?countrycode=US&showAll=True'
# another url example:
#https://www.marketwatch.com/investing/stock/uber/options?countrycode=US&showAll=True
# so stock or fund matters!

#soup = BeautifulSoup(url_string, 'html.parser')
r = requests.get(url_string)
c=r.content

doc = lh.fromstring(r.content)
tr_elements = doc.xpath('//tr')
#Check the length of the first 12 rows; see how the number of columns varies
[len(T) for T in tr_elements[:12]]

#option_list=[]
#for element in tr_elements:
#    option_list.append(element.text_content().split())

#soup = BeautifulSoup(c,"lxml")
#samples = soup.find_all("tr",text="month")

## look for the options tables!
#table=soup.find_all("table")
#table = soup.table
#table = soup.find('table', attrs={'class':'subs noBorders evenRows'})

## right now, I see that the third element is the expiration date
exp_date=tr_elements[3].text_content().replace('\r\n','').strip()

## go to the 5th row? to get the headers.
tr_elements[4].text_content()

col=[];
#i=0

for t in tr_elements[4]:
    name=t.text_content()
    col.append((name,[]))   
## remove the symbol column? or not?

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


## There is a problem though, because this is only one half of the option
## chain.    
for j in range(5,len(tr_elements)):
    #T is our j'th row
    T=tr_elements[j]
    #print(str(i))
    #If row is not of size 15, the //tr data is not from our desired table 
    if len(T)!=15:
        break
    #i is the index of our column
    i=0
    
    #Iterate through each element of the row
    for t in T.iterchildren():
        data=t.text_content() 
        data=data.replace(',','')
        data=data.replace("\r\n","")
        ## how do I get rid of annoying \r and \n characters in bid and ask?
        #data=data.strip()
        #data=data.replace('\\n','')
        #data=data.replace("\\r\\n","")
        
        #Check if row is empty
        if i>0:
            #Convert any numerical value to float
            try:
                #data=float(data.replace(',','')) 
                data=float(data)
            except:
                pass
        #Append the data to the empty list of the i'th column
        col[i][1].append(data)
        #Increment i for the next column
        i+=1

## make the dictionary
chain_dict={df_col[i]:col[i][1] for i in range(len(df_col))}
## make the dataframe
option_chain=pd.DataFrame.from_dict(chain_dict)
## drop the symbol columns.
option_chain=option_chain.drop(['Symbolc', 'Symbolp'], axis=1)
## make everything numeric??
#option_chain.astype('float')

## Now we are ready to plot!

## plot the last price
plt.figure()
plt.plot(option_chain.Strike,option_chain.Lastc,'dc')
plt.plot(option_chain.Strike,option_chain.Lastp,'sm')

## plot the call bid/ask and put bid/ask for each strike
plt.figure()
plt.plot(option_chain.Strike,option_chain.Askc,'vc',label='Call Ask')
plt.plot(option_chain.Strike,option_chain.Bidc,'^c',label='Call Bid')
plt.title('Date: Option Chain Call Prices')
plt.xlabel('Strike Price')
plt.ylabel('Price, $')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
plt.savefig('call_prices.png')
#
plt.figure()
plt.plot(option_chain.Strike,option_chain.Askp,'vm',label='Put Ask')
plt.plot(option_chain.Strike,option_chain.Bidp,'^m',label='Put Ask')
plt.title('Date: Option Chain Put Prices')
plt.xlabel('Strike Price')
plt.ylabel('Price, $')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
plt.savefig('put_prices.png')

## try to find the probability distribution??
g=np.zeros((len(option_chain)))
delta=option_chain.Strike[2]-option_chain.Strike[1]
for i in range(2,len(option_chain)-2):
    #g[i]=np.exp(0.02*1/365)*(
    #        option_chain.Lastc[i+1]
    #        -2*option_chain.Lastc[i]
    #        +option_chain.Lastc[i-1])/delta**2
    g[i]=np.exp(y*1/365)*(
            option_chain.Askc[i+1]
            -2*option_chain.Askc[i]
            +option_chain.Askc[i-1])/delta**2

## plot the implied distribution!
plt.plot(option_chain.Strike,g,'.k')
## make a figure; include the bond price and the value of the portfolio?
## the price plot:
plt.figure()
plt.title('Date: Implied Distribution')
plt.plot(option_chain.Strike,g,'.k',label="Date: Implied Distribution")
plt.xlabel('Strike Price')
plt.ylabel('Implied Distribution')
## Make a legend
plt.legend(loc='best')
## tight_layout makes everything fit nicely in the plot
plt.tight_layout()
plt.savefig('implied_distribution.png')





    
