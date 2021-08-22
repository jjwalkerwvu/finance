#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 18 21:48:56 2021

@author: jeff
"""

import requests
import ssl
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from bs4 import Comment
import pandas as pd
import numpy as np
import re

## A quick function to get the checksum digit for an ISIN
def isin_checksum(cc,cusip):
    ## check that cc and cusip are strings?
    ## Too lazy for error checking right now
    isin=cc+cusip
    running_string=''
    for i in range(len(isin)):
        if isin[i].isdigit()==False:
            number=str(ord(isin[i])-55)
        else:
            number=isin[i]
        ## concatenate every number together, as string
        running_string=running_string+number
        #print(running_string)
        
    ## Now, operate on running_string
    num_str=''
    for i in range(len(running_string)):
        ## For every OTHER digit, starting from rightmost digit, multiply by 2
        ## This statement should be equivalent
        if (i+1)%2!=0:
            num_str=num_str+str(int(running_string[i])*2)
        else:
            num_str=num_str+running_string[i]
    ## Now, add up all digits to get the sum
    isin_sum=0
    for a in num_str:
        isin_sum=int(a)+isin_sum
    ## Now find value, which is the smallest number greater than or equal to
    ## bill_sum that ends in a zero
    isin_value=np.ceil(isin_sum/10.0)*10
    checksum=str(int(isin_value-isin_sum))    
    return checksum

# Ignore SSL Certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

tnow=pd.to_datetime('today').now()

## Get the year
year=str(tnow.year)
## Get the last month
last_month=str(tnow.month-1)
if len(last_month)<2:
    last_month='0'+last_month
## Get all Cusip IDs for Tbills!
df=pd.read_excel(
    'https://www.treasurydirect.gov/govt/reports/pd/mspd/'+year+'/opdm'+
    last_month+year+'.xls',sheet_name='Marketable')
## ex. Url for strips: https://www.treasurydirect.gov/govt/reports/pd/mspd/2021/opdr072021.xls

## There are a lot of repeat cusips with different yields in the spreadsheet;
## how do I handle this when scraping Marketwatch?
cusips=df[df.columns[2]]
ir=df[df.columns[3]]
yields=df[df.columns[4]]
issue_dates=df[df.columns[6]]
## maturity dates need to be filled down
maturity_dates=df[df.columns[7]]
## payable dates
payable_dates=df[df.columns[8]]

## clean the cusips into bills, notes, bonds, and tips
## Bills
## Assuming the spreadsheets are always organized in the same way,
## This is another way to do it
bill_start=df[df.columns[1]][df[df.columns[1]]=='Treasury Bills (Maturity Value):'].index[0]+2
bill_end=df[df.columns[1]][df[df.columns[1]]==
        'Total Unmatured Treasury Bills...............................................................................…'].index[0]-1
## Have to add one to bill_end due to how range works
bill_index=range(bill_start,bill_end+1)
#bill_index=cusips.str.match('91279').fillna(False)
bill_cusips=cusips[bill_index]
bill_yields=yields[bill_index]
bill_issue_dates=pd.to_datetime(issue_dates[bill_index])
bill_maturities=pd.to_datetime(maturity_dates[bill_index]).ffill()
bill_payable_dates=pd.to_datetime(payable_dates[bill_index]).ffill()

## Notes
note_start=df[df.columns[1]][df[df.columns[1]]=='Treasury Notes:'].index[0]+2
note_end=df[df.columns[1]][df[df.columns[1]]==
        'Total Unmatured Treasury Notes...............................................................................…'].index[0]-1
## old method, does not work as I intended
#note_index=cusips.str.match('91282').fillna(False)
note_index=range(note_start,note_end+1)
note_cusips=cusips[note_index]
note_rates=ir[note_index]
note_yields=yields[note_index]
note_issue_dates=pd.to_datetime(issue_dates[note_index])
note_maturities=pd.to_datetime(maturity_dates[note_index]).ffill()
#note_payable_dates=pd.to_datetime(payable_dates[note_index])
#payable_dates[note_index].str.split(' ',3,expand=True).replace(to_replace=[None], value=np.nan))

## Bonds
bond_start=df[df.columns[1]][df[df.columns[1]]=='Treasury Bonds:'].index[0]+2
bond_end=df[df.columns[1]][df[df.columns[1]]==
        'Total Unmatured Treasury Bonds...............................................................................…'].index[0]-1
bond_index=range(bond_start,bond_end+1)
#bond_index=cusips.str.match('912810').fillna(False)
bond_cusips=cusips[bond_index]
bond_rates=ir[bond_index]
bond_yields=yields[bond_index]
bond_issue_dates=pd.to_datetime(issue_dates[bond_index])
bond_maturities=pd.to_datetime(maturity_dates[bond_index]).ffill()
#bond_payable_dates=p

## TIPS
tips_start=df[df.columns[1]][df[df.columns[1]]==
        'Treasury Inflation-Protected Securities:'].index[0]+2
tips_end=df[df.columns[1]][df[df.columns[1]]==
        'Total Treasury TIPS 23 ......................................……'].index[0]-1
tips_index=range(tips_start,tips_end+1)
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Helpful for scraping, I think
headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'}

## Country code for ISIN; can easily use this for other countries with their
## codes
country_code='US'

## get the (maximum?) overnight rate from marketwatch
url='https://www.marketwatch.com/investing/InterestRate/USDR-TU1?countryCode=MR'
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
soup=BeautifulSoup(webpage, 'html5lib')
## the maximum overnight rate (guaranteed rate)
dr=float(soup.find('td',{"class": "table__cell u-semi"}).get_text().replace(
    '%',''))

## This does not seem to work, because Marketwatch tacks on a 10th number to 
## the cusip
## UPDATE! THE 10TH NUMBER IS A CHECKSUM, ASSUMING ISIN!
## Use: 'US'+cusip+str(checksum); so need to calculate the checksum
base_url='https://www.marketwatch.com/investing/bond/'
## preallocate array for bill yields, scraped from marketwatch
y_bill=np.zeros(len(bill_cusips.values))
## Array for time to maturity
bill_tmat=np.array((pd.to_datetime(bill_maturities.values)-
                    pd.to_datetime('today').now())/np.timedelta64(1,'D'))
## get bill data
for j in range(len(bill_cusips.values)):
    bill=bill_cusips.values[j]
    isin=country_code+bill
    running_string=''
    for i in range(len(isin)):
        if isin[i].isdigit()==False:
            number=str(ord(isin[i])-55)
        else:
            number=isin[i]
        ## concatenate every number together, as string
        running_string=running_string+number
        #print(running_string)
        
    ## Now, operate on running_string
    num_str=''
    for i in range(len(running_string)):
        ## For every OTHER digit, starting from rightmost digit, multiply by 2
        ## This statement should be equivalent
        if (i+1)%2!=0:
            num_str=num_str+str(int(running_string[i])*2)
        else:
            num_str=num_str+running_string[i]
    ## Now, add up all digits to get the sum
    bill_sum=0
    for a in num_str:
        bill_sum=int(a)+bill_sum
    ## Now find value, which is the smallest number greater than or equal to
    ## bill_sum that ends in a zero
    bill_value=np.ceil(bill_sum/10.0)*10
    checksum=str(int(bill_value-bill_sum))
    
    ## Finally, construct the url string.    
    url=base_url+bill+checksum
    #print(url)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup=BeautifulSoup(webpage, 'html5lib')
    ## Use try/except block to skip past possible invalid cusips
    try:
        ## get the yield, in %
        y_bill[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                      ).get_text().replace('%',''))
    except:
        pass

## get note data

    
## get bond data
## preallocate array for bond yields, scraped from marketwatch
y_bond=np.zeros(len(bond_cusips.values))
## Array for time to maturity
bond_tmat=np.array((pd.to_datetime(bond_maturities.values)-
                    pd.to_datetime('today').now())/np.timedelta64(1,'D'))
## Array for age of bond, in days?
## Maybe there should be a way to eliminate duplicates?
for j in range(len(bond_cusips)):
    checksum=isin_checksum(country_code,bond_cusips.values[j])
    url=base_url+bond_cusips.values[j]+checksum
    #print(url)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup=BeautifulSoup(webpage, 'html5lib')
    ## Use try/except block to skip past possible invalid cusips
    try:
        ## get the yield, in %
        y_bond[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                      ).get_text().replace('%',''))
    except:
        pass

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Now do Bootstrapping of the yield curve!

## discard bonds that have expired, require bond_tmat>=0


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## original attempt was going to use regex, but not necessary now that I have 
#matches=re.finditer(r'Coupon Rate',soup.body.text)
#matches_list=[i for i in matches]
#e_ind=[]
#for i in matches_list:
#    e_ind.append(i.end())

#coupon=soup.body.text[e_ind[0]:e_ind[0]+200]

#matches=re.finditer(r'Maturity',soup.body.text)

## grab the price, because we can why not
#matches=re.finditer(r'Price',soup.body.text)





