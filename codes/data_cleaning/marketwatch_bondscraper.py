#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 18 21:48:56 2021

@author: jeff
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import ssl
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from bs4 import Comment
import re
import os

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Coupon/cashflow matrix making function here?

# Ignore SSL Certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

## it is a good idea to keep track of the start time, since the process can 
## take a while
tstart=pd.to_datetime('today').now()
tnow=pd.to_datetime('today').now()

## Get the year
year=str(tnow.year)
## Get the last month; it is possible that it may take a while for the website
## to update the spreadsheet
last_month=str(tnow.month-1)
if len(last_month)<2:
    last_month='0'+last_month
## Get all Cusip IDs for Tbills, Tnotes, and Tbonds!
## Try to get rid of duplicate cusips to save computational resources
## td_url_base is the base url for getting spreadsheet information from 
## treasurydirect.gov
tr_url_base='https://www.treasurydirect.gov/govt/reports/pd/mspd/'
try:
    df=pd.read_excel(tr_url_base+year+'/opdm'+last_month+year+'.xls',
                     sheet_name=None)
except:
    ## Using this exception in case it takes up to a month for treasury.gov
    ## to update the spreadsheet; if this does not give enough of a buffer 
    ## then I will have to come up with something else if it breaks
    last_month=str(tnow.month-2)
    if len(last_month)<2:
        last_month='0'+last_month
    df=pd.read_excel(tr_url_base+year+'/opdm'+last_month+year+'.xls',
                     sheet_name=None)

## sheets is a list of all the spreadsheet names
sheets=list(df.keys())
## ex. Url for strips: https://www.treasurydirect.gov/govt/reports/pd/mspd/2021/opdr072021.xls
#df_strips=pd.read_excel(tr_url_base+year+'/opdr'+last_month+year+'.xls')

## We could also get the STRIPS info from  TableV in the full spreadsheet:
## I sitll need to get the rest of the information into arrays
#strips_index=df[sheets[4]][df[sheets[4]].columns[0]]

## Example for reading Netherlands data?
#link=https://english.dsta.nl/documents/publication/2021/09/02/august-2021#:~:text=Download%20%22August%202021,02-09-2021
#pd.read_excel(link, engine="odf",sheet_name=None)

## Assume a face value of $100, since that is the basis by which marketwatch
## lists price
face_val=100.0

## There are a lot of repeat cusips with different yields in the spreadsheet;
## how do I handle this when scraping Marketwatch?
#cusips=df[df.columns[2]]
cusips=df[sheets[1]][df[sheets[1]].columns[2]]
#ir=df[df.columns[3]]
ir=df[sheets[1]][df[sheets[1]].columns[3]]
#yields=df[df.columns[4]]
yields=df[sheets[1]][df[sheets[1]].columns[4]]
#issue_dates=df[df.columns[6]]
issue_dates=df[sheets[1]][df[sheets[1]].columns[6]]
## maturity dates need to be filled down
#maturity_dates=df[df.columns[7]]
maturity_dates=df[sheets[1]][df[sheets[1]].columns[7]]
## payable dates
#payable_dates=df[df.columns[8]]
payable_dates=df[sheets[1]][df[sheets[1]].columns[8]]

## clean the cusips into bills, notes, bonds, and tips
## Bills
## Assuming the spreadsheets are always organized in the same way,
## This is another way to do it
#bill_start=df[df.columns[1]][df[df.columns[1]]=='Treasury Bills (Maturity Value):'].index[0]+2
bill_start=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]==
    'Treasury Bills (Maturity Value):'].index[0]+2
bill_end=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]==
        'Total Unmatured Treasury Bills...............................................................................…'].index[0]-1
## Have to add one to bill_end due to how range works
bill_index=np.arange(bill_start,bill_end+1)
#bill_index=cusips.str.match('91279').fillna(False)
bill_cusips=cusips[bill_index]
bill_yields=yields[bill_index]
bill_issue_dates=pd.to_datetime(issue_dates[bill_index])
bill_maturities=pd.to_datetime(maturity_dates[bill_index]).ffill()
bill_payable_dates=pd.to_datetime(payable_dates[bill_index]).ffill()

## Notes
note_start=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]=='Treasury Notes:'].index[0]+2
note_end=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]==
        'Total Unmatured Treasury Notes...............................................................................…'].index[0]-1
## old method, does not work as I intended
#note_index=cusips.str.match('91282').fillna(False)
note_index=np.arange(note_start,note_end+1)
note_cusips=cusips[note_index]
note_rates=ir[note_index]
note_yields=yields[note_index]
note_issue_dates=pd.to_datetime(issue_dates[note_index])
note_maturities=pd.to_datetime(maturity_dates[note_index]).ffill()
## payable dates are tricky; no year is given!
note_payable_dates=payable_dates[note_index].str.split(' ',3,expand=True
            ).replace(to_replace=[None], value=np.nan)+'/'+str(tnow.year)[2:]
## I think filling forward works and is correct
note_first_payment=pd.to_datetime(note_payable_dates[0], 
                                  dayfirst=True,errors='coerce').ffill()
note_second_payment=pd.to_datetime(note_payable_dates[1], 
                                  dayfirst=True,errors='coerce').ffill()
## This is my best guess as to how to interpret the spreadsheet;
## Since no year is given, I assume that if the first listed payment occurs
## at a greater month than the second payment, then the second payment 
## corresponds to the following calendar year.
## If the first listed payment happens at a lower month, than the second
## payment date, I presume the first payment has already occurred.
note_second_payment[
    note_first_payment>note_second_payment]=note_second_payment[
    note_first_payment>note_second_payment]+pd.DateOffset(years=1)

## Bonds
bond_start=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]=='Treasury Bonds:'].index[0]+2
bond_end=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]==
        'Total Unmatured Treasury Bonds...............................................................................…'].index[0]-1
bond_index=np.arange(bond_start,bond_end+1)
#bond_index=cusips.str.match('912810').fillna(False)
bond_cusips=cusips[bond_index]
bond_rates=ir[bond_index]
bond_yields=yields[bond_index]
bond_issue_dates=pd.to_datetime(issue_dates[bond_index])
bond_maturities=pd.to_datetime(maturity_dates[bond_index]).ffill()
## payable dates are tricky; no year is given!
bond_payable_dates=payable_dates[bond_index].str.split(' ',3,expand=True
            ).replace(to_replace=[None], value=np.nan)+'/'+str(tnow.year)[2:]
## I think filling forward works and is correct
bond_first_payment=pd.to_datetime(bond_payable_dates[0], 
                                  dayfirst=True,errors='coerce').ffill()
bond_second_payment=pd.to_datetime(bond_payable_dates[1], 
                                  dayfirst=True,errors='coerce').ffill()
## This is my best guess as to how to interpret the spreadsheet;
## Since no year is given, I assume that if the first listed payment occurs
## at a greater month than the second payment, then the second payment 
## corresponds to the following calendar year.
## If the first listed payment happens at a lower month, than the second
## payment date, I presume the first payment has already occurred.
bond_second_payment[
    bond_first_payment>bond_second_payment]=bond_second_payment[
    bond_first_payment>bond_second_payment]+pd.DateOffset(years=1)

## TIPS
tips_start=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]==
        'Treasury Inflation-Protected Securities:'].index[0]+2
## Hopefully this will continue to work!
tips_end=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]==
        'Treasury Floating Rate Notes:'].index[0]-3
tips_index=np.arange(tips_start,tips_end+1)
tips_cusips=cusips[tips_index]
tips_rates=ir[tips_index]
tips_yields=yields[tips_index]
tips_issue_dates=pd.to_datetime(issue_dates[tips_index])
tips_maturities=pd.to_datetime(maturity_dates[tips_index]).ffill()
## payable dates are tricky; no year is given!
tips_payable_dates=payable_dates[tips_index].str.split(' ',3,expand=True
            ).replace(to_replace=[None], value=np.nan)+'/'+str(tnow.year)[2:]
## I think filling forward works and is correct
tips_first_payment=pd.to_datetime(tips_payable_dates[0], 
                                  dayfirst=True,errors='coerce').ffill()
tips_second_payment=pd.to_datetime(tips_payable_dates[1], 
                                  dayfirst=True,errors='coerce').ffill()
## This is my best guess as to how to interpret the spreadsheet;
## Since no year is given, I assume that if the first listed payment occurs
## at a greater month than the second payment, then the second payment 
## corresponds to the following calendar year.
## If the first listed payment happens at a lower month, than the second
## payment date, I presume the first payment has already occurred.
tips_second_payment[
    tips_first_payment>tips_second_payment]=tips_second_payment[
    tips_first_payment>tips_second_payment]+pd.DateOffset(years=1)

## FLOATING RATE NOTES
frn_start=df[sheets[1]][df[sheets[1]].columns[1]][
    df[sheets[1]][df[sheets[1]].columns[1]]==
        'Treasury Floating Rate Notes:'].index[0]+2
## I think this should work; the last three lines are bold and I think they are
## always there
frn_end=len(cusips)-4
frn_index=np.arange(frn_start,frn_end+1)
frn_cusips=cusips[frn_index]
## No interest rate for frns it seems, just yields
frn_yields=yields[frn_index]
# 2021-11-11: Getting an error here; Must fix!
#frn_issue_dates=pd.to_datetime(issue_dates[frn_index])
#frn_maturities=pd.to_datetime(maturity_dates[frn_index]).ffill()
## How do I extract the four coupon payments per year??
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

## CONSIDER PARALLELIZING THIS CODE!
## This does not seem to work, because Marketwatch tacks on a 10th number to 
## the cusip
## UPDATE! THE 10TH NUMBER IS A CHECKSUM, ASSUMING ISIN!
## Use: 'US'+cusip+str(checksum); so need to calculate the checksum
base_url='https://www.marketwatch.com/investing/bond/'
## preallocate array for bill yields, scraped from marketwatch
y_bill=np.zeros(len(bill_cusips.values))
## price of bill
p_bill=np.zeros(len(bill_cusips.values))
## Array for time to maturity
bill_tmat=np.array((pd.to_datetime(bill_maturities.values)-
                    pd.to_datetime('today').now())/np.timedelta64(1,'D'))
## Maybe there should be a way to eliminate duplicates?
bill_cusip_check=bill_cusips.drop_duplicates().index.values
## get bill data
for j in range(len(bill_cusips.values)):
    checksum=isin_checksum(country_code,bill_cusips.values[j])
    url=base_url+bill_cusips.values[j]+checksum
    #print(url)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup=BeautifulSoup(webpage, 'html5lib')
    ## Use if statement to make sure cusip j is not a duplicate
    if bill_cusips.index[j] in bill_cusip_check:
        ## Use try/except block to skip past possible invalid cusips
        try:
            ## get the yield, in %
            y_bill[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                      ).get_text().replace('%',''))
            ## try to get price; this command should get everything out of the 
            ## table
            #soup.select('.kv__item .primary')
            p_bill_str=soup.select('.kv__item .primary')[3].string.rsplit()
            p_bill[j]=(float(p_bill_str[0])+float(p_bill_str[1].rsplit('/')[0])/
                float(p_bill_str[1].rsplit('/')[1]))
            print("Successfully scraped Bill cusip: "+ 
                  bill_cusips.values[j]+
                  " with Maturity: "+
                  pd.to_datetime(
                      bill_maturities.values[j]).strftime("%Y-%m-%d"))
        except:
            print("Successfully scraped Bills cusip: "+
              bill_cusips.values[j]+
              " with Maturity: "+
              pd.to_datetime(bill_maturities.values[j]).strftime("%Y-%m-%d"))
    else:
        print("Bill cusip: "+bill_cusips.values[j]+ " is a duplicate CUSIP")
## make data series out of this:
y_bill=pd.Series(data=y_bill,index=pd.to_datetime(bill_maturities),name='yield')  
y_bill.index.rename('Maturity',inplace=True) 
## Probably not necessary to record the price, but doing so anyway for 
## completeness
p_bill=pd.Series(data=p_bill,index=bill_index,name='price')
p_bill.index.rename('Bill Index',inplace=True) 
p_bill_date=pd.Series(data=p_bill.values,index=pd.to_datetime(bill_maturities),
                 name='price')
p_bill_date.index.rename('Maturity',inplace=True) 
# A dataframe is probably better.
bill_df=pd.DataFrame(data={'bill_cusip':bill_cusips.values,
                           'y_bill':y_bill.values,
                           'bill_price':p_bill_date.values,
                           'spreadsheet_row':p_bill.index},index=y_bill.index)
print('Bill scraping complete')

## get note data
## preallocate array for note yields, scraped from marketwatch
y_note=np.zeros(len(note_cusips.values))
## price of notes
p_note=np.zeros(len(note_cusips.values))
## Array for time to maturity
note_tmat=np.array((pd.to_datetime(note_maturities.values)-
                    pd.to_datetime('today').now())/np.timedelta64(1,'D'))
## Array for age of note/bond, in days?
## Maybe there should be a way to eliminate duplicates?
note_cusip_check=note_cusips.drop_duplicates().index.values
for j in range(len(note_cusips)):
    checksum=isin_checksum(country_code,note_cusips.values[j])
    url=base_url+note_cusips.values[j]+checksum
    #print(url)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup=BeautifulSoup(webpage, 'html5lib')
    ## Use if statement to make sure cusip j is not a duplicate
    if note_cusips.index[j] in note_cusip_check:
        ## Use try/except block to skip past possible invalid cusips
        try:
            ## get the yield, in %
            y_note[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                      ).get_text().replace('%',''))
            p_note_str=soup.select('.kv__item .primary')[3].string.rsplit()
            p_note[j]=(float(p_note_str[0])+
                       float(p_note_str[1].rsplit('/')[0])/
                       float(p_note_str[1].rsplit('/')[1]))
            print("Successfully scraped Note cusip: "+ 
                  note_cusips.values[j]+
                  " with Maturity: "+
                  pd.to_datetime(note_maturities.values[j]).strftime("%Y-%m-%d"))
        except:
            print("Successfully scraped Note cusip: "+
              note_cusips.values[j]+
              " with Maturity: "+
              pd.to_datetime(note_maturities.values[j]).strftime("%Y-%m-%d"))
    else:
        print("Note cusip: "+note_cusips.values[j]+ " is a duplicate CUSIP")
## make data series out of this:
y_note=pd.Series(data=y_note,index=pd.to_datetime(note_maturities),
                 name='yield')    
y_note.index.rename('Maturity',inplace=True) 
## Useful to make a series out of p_note; datetime index will be useful later
## I think I may need spreadsheet index numbers... use as index?
p_note=pd.Series(data=p_note,index=note_index,name='price')
p_note.index.rename('Note Index',inplace=True)
p_note_date=pd.Series(data=p_note.values,index=pd.to_datetime(note_maturities),
                 name='price')
p_note_date.index.rename('Maturity',inplace=True) 
# A dataframe is probably better.
note_df=pd.DataFrame(data={'note_cusip':note_cusips.values,
                           'y_note':y_note.values,
                           'note_price':p_note_date.values,
                           'spreadsheet_row':p_note.index},index=y_note.index)
print('Note scraping complete')
 
   
## get bond data
## preallocate array for bond yields, scraped from marketwatch
y_bond=np.zeros(len(bond_cusips.values))
## price of notes
p_bond=np.zeros(len(bond_cusips.values))
## Array for time to maturity
bond_tmat=np.array((pd.to_datetime(bond_maturities.values)-
                    pd.to_datetime('today').now())/np.timedelta64(1,'D'))
## Array for age of bond, in days?
## Maybe there should be a way to eliminate duplicates?
bond_cusip_check=bond_cusips.drop_duplicates().index.values
for j in range(len(bond_cusips)):
    checksum=isin_checksum(country_code,bond_cusips.values[j])
    url=base_url+bond_cusips.values[j]+checksum
    #print(url)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup=BeautifulSoup(webpage, 'html5lib')
    ## Use try/except block to skip past possible invalid cusips
    ## Use if statement to make sure cusip j is not a duplicate
    if bond_cusips.index[j] in bond_cusip_check:
        try:
            ## get the yield, in %
            y_bond[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                      ).get_text().replace('%',''))
            p_bond_str=soup.select('.kv__item .primary')[3].string.rsplit()
            p_bond[j]=(float(p_bond_str[0])+float(p_bond_str[1].rsplit('/')[0])/
                float(p_bond_str[1].rsplit('/')[1]))
            print("Successfully scraped Bond cusip: "+
              bond_cusips.values[j]+
              " with Maturity: "+
              pd.to_datetime(bond_maturities.values[j]).strftime("%Y-%m-%d"))
        except:
            print("Successfully scraped Bond cusip: "+
              bond_cusips.values[j]+
              " with Maturity: "+
              pd.to_datetime(bond_maturities.values[j]).strftime("%Y-%m-%d"))
    else:
        print("Bond cusip: "+bond_cusips.values[j]+ " is a duplicate CUSIP")
## Log the end time now.
#tend=pd.to_datetime('today').now()

## make data series out of this:
y_bond=pd.Series(data=y_bond,index=pd.to_datetime(bond_maturities),
                 name='yield')  
y_bond.index.rename('Maturity',inplace=True) 
p_bond=pd.Series(data=p_bond,index=bond_index,name='price')
p_bond.index.rename('Bond Index',inplace=True)
## Useful to make a series out of p_note; datetime index will be useful later
p_bond_date=pd.Series(data=p_bond.values,index=pd.to_datetime(bond_maturities),
                 name='price')
p_bond_date.index.rename('Maturity',inplace=True) 
# A dataframe is probably better.
bond_df=pd.DataFrame(data={'bond_cusip':bond_cusips.values,
                           'y_bond':y_bond.values,
                           'bond_price':p_bond_date.values,
                           'spreadsheet_row':p_bond.index},
                     index=y_bond.index)
print('Bond scraping complete')


## Should also scrape TIPS!
## get bond data
## preallocate array for bond yields, scraped from marketwatch
y_tips=np.zeros(len(tips_cusips.values))
## price of notes
p_tips=np.zeros(len(tips_cusips.values))
## Array for time to maturity
tips_tmat=np.array((pd.to_datetime(tips_maturities.values)-
                    pd.to_datetime('today').now())/np.timedelta64(1,'D'))
## Array for age of bond, in days?
## Maybe there should be a way to eliminate duplicates?
tips_cusip_check=tips_cusips.drop_duplicates().index.values
for j in range(len(tips_cusips)):
    checksum=isin_checksum(country_code,tips_cusips.values[j])
    url=base_url+tips_cusips.values[j]+checksum
    #print(url)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup=BeautifulSoup(webpage, 'html5lib')
    ## Use try/except block to skip past possible invalid cusips
    ## Use if statement to make sure cusip j is not a duplicate
    if tips_cusips.index[j] in tips_cusip_check:
        try:
            ## get the yield, in %
            y_tips[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                      ).get_text().replace('%',''))
            p_tips_str=soup.select('.kv__item .primary')[3].string.rsplit()
            p_tips[j]=(float(p_tips_str[0])+float(p_tips_str[1].rsplit('/')[0])/
                float(p_tips_str[1].rsplit('/')[1]))
            print("Successfully scraped TIPS cusip: "+
              tips_cusips.values[j]+
              " with Maturity: "+
              pd.to_datetime(tips_maturities.values[j]).strftime("%Y-%m-%d"))
        except:
            print("Failed to scrape TIPS cusip: "+
              tips_cusips.values[j]+
              " for Maturity: "+
              pd.to_datetime(tips_maturities.values[j]).strftime("%Y-%m-%d"))
    else:
        print("TIPS cusip: "+tips_cusips.values[j]+ " is a duplicate CUSIP")
        
## Log the end time now.
tend=pd.to_datetime('today').now()
## time spent scraping:
tscrape=(tend-tstart).total_seconds()
    
## make data series out of this:
y_tips=pd.Series(data=y_tips,index=pd.to_datetime(tips_maturities),
                 name='yield')  
y_tips.index.rename('Maturity',inplace=True) 
p_tips=pd.Series(data=p_tips,index=tips_index,name='price')
p_tips.index.rename('Bond Index',inplace=True)
## Useful to make a series out of p_note; datetime index will be useful later
p_tips_date=pd.Series(data=p_tips.values,index=pd.to_datetime(tips_maturities),
                 name='price')
p_tips_date.index.rename('Maturity',inplace=True) 
# A dataframe is probably better.
tips_df=pd.DataFrame(data={'tips_cusip':tips_cusips.values,
                           'y_tips':y_tips.values,
                           'tips_price':p_tips_date.values,
                           'spreadsheet_row':p_tips.index},
                     index=y_tips.index)
print('TIPS scraping complete')

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Now do Bootstrapping of the yield curve!

## Consider a bid curve (highest yield bond/coupon available) and
## an ask curve (lowest yield bond/coupon available)
## This should solve the problem of whether you plan to buy a certain 
## zero coupon bond (ask yield) or sell it (bid yield) for option pricing or
## other uses.

## discard bonds that have expired, require bond_tmat>=0
## Start with soonest to maturity bill/note/bond.
## Also need y_bill!=0
bills_available_index=np.where((y_bill!=0)&(bill_tmat>=0)==True)
## index of nearest bill; pick first element?
nearest_bill=np.where((y_bill!=0)&(bill_tmat>=0)&
            (bill_tmat==np.min(bill_tmat[bills_available_index]))==True)[0][0]

## Find all notes and bonds with ONLY one payment remaining; these are also
## effectively zero coupon
# Okay, what if there are none? I encountered this problem on 2021-12-07
#note_zero=pd.DatetimeIndex(note_first_payment).year
#(note_first_payment<tnow)&(note_second_payment>tnow)
## Maybe use something like note_second_payment==note_maturities?
note_zero=note_maturities[(note_second_payment==note_maturities)&
                      (tnow>note_first_payment)]
note_zero_index=np.arange(note_zero.index[0],note_zero.index[-1]+1)
bond_zero=bond_maturities[(bond_second_payment==bond_maturities)&
                      (tnow>bond_first_payment)]
bond_zero_index=np.arange(bond_zero.index[0],bond_zero.index[-1]+1)
## remaining notes/bonds indices?
## Includes the cusips that have not matured up until a specified datetime
remaining_note_index=np.setxor1d(note_zero_index,note_index)
##
remaining_bond_index=np.setxor1d(bond_zero_index,bond_index)

## Go through maturities of these zero coupon instruments, and select 
## lowest yield for a given maturity date ("ask yield"),
## highest yield for a given maturity date ("bid yield")
## starting ask yield and bid yield
date_collect=np.concatenate((
    pd.to_datetime(bill_maturities.values[y_bill!=0]),
    pd.to_datetime(note_maturities[(p_note[note_zero_index]!=0).index[
        (p_note[note_zero_index]!=0).values]]),
    pd.to_datetime(bond_maturities[(p_bond[bond_zero_index]!=0).index[
        (p_bond[bond_zero_index]!=0).values]])), 
    axis=0)
## convert to datetime index, and sort chronologically
date_collect, date_collect_index=pd.DatetimeIndex(date_collect).sort_values(
    return_indexer=True)

yield_collect=np.concatenate((y_bill[y_bill!=0],
                y_note[:len(note_zero_index)].values[
                    y_note[:len(note_zero_index)].values!=0],
                y_bond[:len(bond_zero_index)].values[
                    y_bond[:len(bond_zero_index)].values!=0]), axis=0)
## put yield_collect into same order as sorted date_collect
yield_collect=yield_collect[date_collect_index]

## 
ask_yield=np.array([])
bid_yield=np.array([])
zero_dates=pd.to_datetime(np.unique(date_collect))
for date in np.unique(date_collect):
    ask_yield=np.append(ask_yield,np.min(yield_collect[date_collect==date]))
    bid_yield=np.append(bid_yield,np.max(yield_collect[date_collect==date]))

## How do I generate the coupons efficiently for my purpose?
## Generate all coupon dates for a given bond, and then loop through these
## dates to get the zero coupon value for each?

## Also, there is the problem that date range will not catch the next coupon
## payment of a note/bond

## dataframe for notes:
note_coupon_df=[]
note_maturity_df=[]
for index in remaining_note_index:
    ## NO LONGER USED
    ## need to add an extra period for the endpoints.
    ## There are 3 samples (6 months sampling) in exactly 1 year, for example.
    #nperiods=int(np.floor((note_maturities[index]-tnow).days/182.5))+1
    ## 
    # note_coupon_dates=(pd.date_range(end=note_maturities[index],
    #                             periods=nperiods,
    #                             freq='6MS')+
    #                             pd.DateOffset(note_maturities[index].day-1))
    
    if note_first_payment[index].is_month_end:
        note_coupon_dates=(pd.date_range(start=note_first_payment[index],
                                end=note_maturities[index],
                                freq='6M'))
    ## I think that if coupon payments are not at a month end, then they are
    ## Always on the 15th of a month. 
    ## IF THIS TURNS OUT TO NOT BE TRUE, THIS MUST BE CHANGED!
    else:
        note_coupon_dates=(pd.date_range(start=note_first_payment[index]-
                                pd.DateOffset(15),
                                end=note_maturities[index]+pd.DateOffset(15),
                                freq='6M')+pd.DateOffset(15))
    
    
    
    ## In case the first payment has already occurred:
    ## Use greater than or equal, or just greater than?
    note_coupon_dates=note_coupon_dates[note_coupon_dates>=tnow]
    
    ## Fill in second payment, if it is not correctly represented in
    ## note_coupon_dates
    # if (not (note_first_payment[index] in note_coupon_dates)) and (
    #         note_first_payment[index]>tnow):
    # ## Need to drop the incorrect coupon payment!
    #     note_coupon_dates=note_coupon_dates.drop(
    #         note_coupon_dates[
    #             abs((note_coupon_dates-note_first_payment[index]).days)==
    #             np.min(
    #             abs((note_coupon_dates-note_first_payment[index]).days))])
    #     note_coupon_dates=note_coupon_dates.append(pd.DatetimeIndex(
    #         [note_first_payment[index]])).sort_values()
    
    ## placeholder vector array
    note_coupons=np.ones((np.size(note_coupon_dates)))*note_rates[index]/2
    ## This a placeholder vector array for the maturities of each cash flow
    note_mat_values=((note_coupon_dates-tnow)/np.timedelta64(1,'D')
                     ).values/365.2425
    ## if you want to add the principal here
    #note_coupons[-1]=note_coupons[-1]+face_val
    note_coupon_series=pd.Series(note_coupons,index=note_coupon_dates)
    #
    note_mat_series=pd.Series(note_mat_values,note_coupon_dates)
    note_coupon_df.append(note_coupon_series)
    #
    note_maturity_df.append(note_mat_series)
## And this is the resulting dataframe for all coupon payments, with the 
## (slightly modified) spreadsheet number as column number
note_coupon_df=pd.concat(note_coupon_df, axis=1, 
                keys=[item for item in remaining_note_index.astype(str)])
note_maturity_df=pd.concat(note_maturity_df, axis=1, 
                keys=[item for item in remaining_note_index.astype(str)])

## for bonds:
bond_coupon_df=[]
bond_maturity_df=[]
for index in remaining_bond_index:
    
    
    ## NO LONGER USED (POSSIBLY)
    ## need to add an extra period for the endpoints.
    ## There are 3 samples (6 months sampling) in exactly 1 year, for example.
    # nperiods=int(np.floor((bond_maturities[index]-tnow).days/182.5))+1
    # ## 
    # bond_coupon_dates=(pd.date_range(end=bond_maturities[index],
    #                             periods=nperiods,
    #                             freq='6MS')+
    #                             pd.DateOffset(bond_maturities[index].day-1))
    
    # ## Fill in second payment, if it is not correctly represented in
    # ## bond_coupon_dates
    # if (not (bond_first_payment[index] in bond_coupon_dates)) and (
    #         bond_first_payment[index]>tnow):
    #     ## Need to drop the incorrect coupon payment!
    #     bond_coupon_dates=bond_coupon_dates.drop(
    #         bond_coupon_dates[
    #             abs((bond_coupon_dates-bond_first_payment[index]).days)==
    #             np.min(
    #             abs((bond_coupon_dates-bond_first_payment[index]).days))])
    #     bond_coupon_dates=bond_coupon_dates.append(pd.DatetimeIndex(
    #         [bond_first_payment[index]])).sort_values()
     
    ## New, possibly improved method:
    if bond_first_payment[index].is_month_end:
        bond_coupon_dates=(pd.date_range(start=bond_first_payment[index],
                                end=bond_maturities[index],
                                freq='6M'))
    ## I think that if coupon payments are not at a month end, then they are
    ## Always on the 15th of a month. 
    ## IF THIS TURNS OUT TO NOT BE TRUE, THIS MUST BE CHANGED!
    else:
        bond_coupon_dates=(pd.date_range(start=bond_first_payment[index]-
                                pd.DateOffset(15),
                                end=bond_maturities[index]+pd.DateOffset(15),
                                freq='6M')+pd.DateOffset(15))
    
    
    
    ## In case the first payment has already occurred:
    ## Use greater than or equal, or just greater than?
    bond_coupon_dates=bond_coupon_dates[bond_coupon_dates>=tnow]
    ## placeholder vector array
    bond_coupons=np.ones((np.size(bond_coupon_dates)))*bond_rates[index]/2
    ## This a placeholder vector array for the maturities of each cash flow
    bond_mat_values=((bond_coupon_dates-tnow)/np.timedelta64(1,'D')
                     ).values/365.2425
    ## if you want to add the principal here
    #bond_coupons[-1]=bond_coupons[-1]+face_val
    bond_coupon_series=pd.Series(bond_coupons,index=bond_coupon_dates)
    #
    bond_mat_series=pd.Series(bond_mat_values,bond_coupon_dates)
    bond_coupon_df.append(bond_coupon_series)
    #
    bond_maturity_df.append(bond_mat_series)
## And this is the resulting dataframe for all coupon payments, with the 
## (slightly modified) spreadsheet number as column number
bond_coupon_df=pd.concat(bond_coupon_df, axis=1, 
                keys=[item for item in remaining_bond_index.astype(str)])
bond_maturity_df=pd.concat(bond_maturity_df, axis=1, 
                keys=[item for item in remaining_bond_index.astype(str)])

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ytm_curve=np.append(y_note[p_note_date!=0].values,y_bond[p_bond_date!=0])
ytm_dates=y_note[p_note_date!=0].index.append(y_bond[p_bond_date!=0].index)

term, ytm_index=ytm_dates.sort_values(return_indexer=True)

term_years=(term-tnow).days/365.2425

## make cash flow and maturity matrices?
## Should probably include all cash flows, including Bills and "zero coupon"
## notes, bonds
## Only way I could figure out how to do this uses a for loop; try to 
## vectoriize!
note_matrix=1.0*note_coupon_df
for column in note_matrix.columns:
    note_matrix.loc[note_matrix[column].last_valid_index(),column]=(
        note_matrix.loc[note_matrix[column].last_valid_index(),column]+
        face_val)


bond_matrix=1.0*bond_coupon_df
for column in bond_matrix.columns:
    bond_matrix.loc[bond_matrix[column].last_valid_index(),column]=(
        bond_matrix.loc[bond_matrix[column].last_valid_index(),column]+
        face_val)

## cash_flow_df is a data frame with all cash flows.
cash_flow_df=note_matrix.append(bond_matrix)
## cash_flow is the 2d cashflow matrix, and we need the transpose
cash_flow=cash_flow_df.values.T
## Now, calculate the maturity matrix
maturity_df=note_maturity_df.append(bond_maturity_df)
maturity_matrix=maturity_df.values.T
## Construct the price vector.
price_series=p_note[remaining_note_index].append(p_bond[remaining_bond_index])
#
price_vector=price_series.values
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
## Try doing Nelson Siegel Svensson fitting routine here?

## Use most recent yield curve from this data set to help with calibration?
url='https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv';
# zc=pd.read_csv(url,sep=',',header=7)
# zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
# zc.set_index('Date',inplace=True)

## COUPON BONDS ONLY!


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Analytically Bootstrap the yield curve from here
## APPEARS TO BE MOSTLY WORKING AS OF 2021-09-22
## Datetime where we start bootstrapping
t_bootstart=pd.to_datetime(date_collect[-1])
note_boot_index=note_boot_index=note_maturities[
    note_coupon_df[note_coupon_df.index>t_bootstart]
    [remaining_note_index.astype(str)].iloc[0].index.astype(int)]
bond_boot_index=bond_maturities[
    bond_coupon_df[bond_coupon_df.index>t_bootstart]
    [remaining_bond_index.astype(str)].iloc[0].index.astype(int)]

boot_dates=pd.DatetimeIndex(np.union1d(note_boot_index.unique(),
                            bond_boot_index.unique()))

note_maturity_index=pd.Series(data=note_boot_index.index,
                              index=note_boot_index.values)

bond_maturity_index=pd.Series(data=bond_boot_index.index,
                              index=bond_boot_index.values)

## keep track of notes and bonds used to bootstrap the curve
notes_used=np.array([])
bonds_used=np.array([])
## tolearnce for how far a coupon payment can be from the closest matching 
## date between a coupon payment for a given maturity date and the current
## set of zero coupon yield dates, in days
date_tol=16

for date in boot_dates:
    ## dates from which we can pick yields from; the zero_dates at the 
    ## beginning of this loop iteration
    sample_dates=zero_dates
    
    ask_temp=1.0*ask_yield
    bid_temp=1.0*bid_yield
    
    ask_collect=np.array([])
    bid_collect=np.array([])
    
    
    ## Only notes maturing, no bonds
    if ((pd.DatetimeIndex([date]).isin(note_maturities.values)[0])&
         ~((pd.DatetimeIndex([date])).isin(bond_maturities.values)[0])):
        maturing_notes=note_maturity_index[date].astype(str) 
        if np.isscalar(maturing_notes):
            maturing_notes=[maturing_notes]
    
        #p_index=p_note[maturing_notes.values.astype(int)][p_note[maturing_notes.values.astype(int)].values!=0].index.astype(str)
        
        for instrument in maturing_notes:
            coupon_stream=note_coupon_df[instrument].dropna()
            ## find closest date in the coupon dataframe to a date in 
            ## date_collect to within some tolerance (15-16 days?)
            ask_boot_yield=np.array([])
            bid_boot_yield=np.array([])
            AI=0
            # calculate accrued interest??
            AI=(tnow-(coupon_stream.index[0]-pd.DateOffset(months=6))).days/(
                coupon_stream.index[0]-(coupon_stream.index[0]-
                                        pd.DateOffset(months=6))
                                        ).days*coupon_stream.values[0]
            
            price=p_note[int(instrument)]+AI
            
            for cdate in coupon_stream.index[:-1]:
                ## What if there is no match within a specfied tolerance?
                ask_yield_match=ask_yield[(abs((cdate-sample_dates).days)
                                    ==np.min(abs(cdate-sample_dates).days))&
                                    (abs((cdate-sample_dates).days)<=date_tol)]
                bid_yield_match=bid_yield[(abs((cdate-sample_dates).days)
                                    ==np.min(abs(cdate-sample_dates).days))&
                                    (abs((cdate-sample_dates).days)<=date_tol)]
                if (len(ask_yield_match)>0)&(len(bid_yield_match)>0):
                    ask_boot_yield=np.append(
                        ask_boot_yield,np.min(ask_yield_match))
                    bid_boot_yield=np.append(
                        bid_boot_yield,np.min(bid_yield_match))
                    has_match=True
                else:
                    has_match=False
            
            if (price!=0)&(has_match):
                ## make an array for the exponent for discount factors
                tarr=((coupon_stream.index-tnow).days/365.0).values
                ## Don't I have to multiply by 100 to get correct value?
                ask_value=200*((face_val*(1+coupon_stream[0]/100)/(
                        price-face_val*coupon_stream[0]/100*np.sum(
                        1/(1+ask_boot_yield[:]/200)**(2*tarr[:-1]))))**(
                        1/(2*tarr[-1]))-1)
                                          
                bid_value=200*((face_val*(1+coupon_stream[0]/100)/(
                        price-face_val*coupon_stream[0]/100*np.sum(
                        1/(1+bid_boot_yield[:]/200)**(2*tarr[:-1]))))**(
                        1/(2*tarr[-1]))-1)
                
                ## collect calculated yields
                ask_collect=np.append(ask_collect,ask_value)
                bid_collect=np.append(bid_collect,bid_value)
                ## append the cusip of this note/bond used
                notes_used=np.append(notes_used,instrument)
                print('Note:'+note_cusips[int(instrument)]+
                          ' Matures on date: '+ date.strftime("%Y-%m-%d"))
                    ## okay to append this date to the zero_dates index, if
                    ## it is not already in the index
                if ~pd.DatetimeIndex([date]).isin(zero_dates)[0]:
                        zero_dates=zero_dates.append(pd.DatetimeIndex([date]))
                                                    
            else:
                print('Could not retrieve price for Note: '+
                          note_cusips[int(instrument)])
    ## Only bonds are maturing, no notes            
    elif (~(pd.DatetimeIndex([date]).isin(note_maturities.values)[0])&
         ((pd.DatetimeIndex([date])).isin(bond_maturities.values)[0])):
        maturing_bonds=bond_maturity_index[date].astype(str)
        if np.isscalar(maturing_bonds):
            maturing_bonds=[maturing_bonds]
        for instrument in maturing_bonds:
            coupon_stream=bond_coupon_df[instrument].dropna()
            ## find closest date in the coupon dataframe to a date in 
            ## date_collect to within some tolerance (15-16 days?)
            ask_boot_yield=np.array([])
            bid_boot_yield=np.array([])
            # calculate accrued interest??
            AI=0
            AI=(tnow-(coupon_stream.index[0]-pd.DateOffset(months=6))).days/(
                coupon_stream.index[0]-(coupon_stream.index[0]-
                                        pd.DateOffset(months=6))
                                        ).days*coupon_stream.values[0]
            price=p_bond[int(instrument)]+AI
            
            for cdate in coupon_stream.index[:-1]:
                ## What if there is no match within a specfied tolerance?
                ask_yield_match=ask_yield[(abs((cdate-sample_dates).days)
                                    ==np.min(abs(cdate-sample_dates).days))&
                                    (abs((cdate-sample_dates).days)<=date_tol)]
                bid_yield_match=bid_yield[(abs((cdate-sample_dates).days)
                                    ==np.min(abs(cdate-sample_dates).days))&
                                    (abs((cdate-sample_dates).days)<=date_tol)]
                if (len(ask_yield_match)>0)&(len(bid_yield_match)>0):
                    ask_boot_yield=np.append(
                        ask_boot_yield,np.min(ask_yield_match))
                    bid_boot_yield=np.append(
                        bid_boot_yield,np.min(bid_yield_match))
                    no_match=False
                else:
                    no_match=True
            
            if (price!=0)&(has_match):
                ## make an array for the exponent for discount factors
                tarr=((coupon_stream.index-tnow).days/365.0).values
                ## make an array for the exponent for discount factors
                tarr=((coupon_stream.index-tnow).days/365.0).values
                ## Don't I have to multiply by 100 to get correct value?
                ask_value=200*((face_val*(1+coupon_stream[0]/100)/(
                        price-face_val*coupon_stream[0]/100*np.sum(
                            1/(1+ask_boot_yield[:]/200)**(2*tarr[:-1]))))**(
                                1/(2*tarr[-1]))-1)
                                          
                bid_value=200*((face_val*(1+coupon_stream[0]/100)/(
                        price-face_val*coupon_stream[0]/100*np.sum(
                            1/(1+bid_boot_yield[:]/200)**(2*tarr[:-1]))))**(
                        1/(2*tarr[-1]))-1)
                
                                ## collect calculated yields
                ask_collect=np.append(ask_collect,ask_value)
                bid_collect=np.append(bid_collect,bid_value)
                ## append the cusip of this note/bond used
                bonds_used=np.append(bonds_used,instrument)
                print('Bond:'+bond_cusips[int(instrument)]+
                          ' Matures on date: '+ date.strftime("%Y-%m-%d"))
                    ## okay to append this date to the zero_dates index, if
                    ## it is not already in the index
                if ~pd.DatetimeIndex([date]).isin(zero_dates)[0]:
                    zero_dates=zero_dates.append(pd.DatetimeIndex([date]))
            else:
                print('Could not retrieve price for Bond: '+
                          bond_cusips[int(instrument)])
                
    ## both notes and bonds are maturing            
    elif ((pd.DatetimeIndex([date]).isin(note_maturities.values)[0])&
         ((pd.DatetimeIndex([date])).isin(bond_maturities.values)[0])):
        maturing_bonds=bond_maturity_index[date].astype(str)
        if np.isscalar(maturing_bonds):
            maturing_bonds=[maturing_bonds]
        for instrument in maturing_bonds:
            coupon_stream=bond_coupon_df[instrument].dropna()
            ## find closest date in the coupon dataframe to a date in 
            ## date_collect to within some tolerance (15-16 days?)
            ask_boot_yield=np.array([])
            bid_boot_yield=np.array([])
            # calculate accrued interest??
            AI=0
            AI=(tnow-(coupon_stream.index[0]-pd.DateOffset(months=6))).days/(
                coupon_stream.index[0]-(coupon_stream.index[0]-
                                        pd.DateOffset(months=6))
                                        ).days*coupon_stream.values[0]
            price=p_bond[int(instrument)]+AI
            
            for cdate in coupon_stream.index[:-1]:
                ## What if there is no match within a specfied tolerance?
                ask_yield_match=ask_yield[(abs((cdate-sample_dates).days)
                                    ==np.min(abs(cdate-sample_dates).days))&
                                    (abs((cdate-sample_dates).days)<=date_tol)]
                bid_yield_match=bid_yield[(abs((cdate-sample_dates).days)
                                    ==np.min(abs(cdate-sample_dates).days))&
                                    (abs((cdate-sample_dates).days)<=date_tol)]
                if (len(ask_yield_match)>0)&(len(bid_yield_match)>0):
                    ask_boot_yield=np.append(
                        ask_boot_yield,np.min(ask_yield_match))
                    bid_boot_yield=np.append(
                        bid_boot_yield,np.min(bid_yield_match))
                    no_match=False
                else:
                    no_match=True
            
            if (price!=0)&(has_match):
                ## make an array for the exponent for discount factors
                tarr=((coupon_stream.index-tnow).days/365.0).values
                ## Don't I have to multiply by 100 to get correct value?
                ask_value=200*((face_val*(1+coupon_stream[0]/100)/(
                        price-face_val*coupon_stream[0]/100*np.sum(
                            1/(1+ask_boot_yield[:]/200)**(2*tarr[:-1]))))**(
                                1/(2*tarr[-1]))-1)
                                          
                bid_value=200*((face_val*(1+coupon_stream[0]/100)/(
                        price-face_val*coupon_stream[0]/100*np.sum(
                            1/(1+bid_boot_yield[:]/200)**(2*tarr[:-1]))))**(
                        1/(2*tarr[-1]))-1)
                
                                ## collect calculated yields
                ask_collect=np.append(ask_collect,ask_value)
                bid_collect=np.append(bid_collect,bid_value)
                ## append the cusip of this note/bond used
                bonds_used=np.append(bonds_used,instrument)
                print('Bond:'+bond_cusips[int(instrument)]+
                          ' Matures on date: '+ date.strftime("%Y-%m-%d"))
                    ## okay to append this date to the zero_dates index, if
                    ## it is not already in the index
                if ~pd.DatetimeIndex([date]).isin(zero_dates)[0]:
                    zero_dates=zero_dates.append(pd.DatetimeIndex([date]))
            else:
                print('Could not retrieve price for Bond: '+
                          bond_cusips[int(instrument)]) 
                
        maturing_notes=note_maturity_index[date].astype(str) 
        if np.isscalar(maturing_notes):
            maturing_notes=[maturing_notes]
        
        for instrument in maturing_notes:
            coupon_stream=note_coupon_df[instrument].dropna()
            ## find closest date in the coupon dataframe to a date in 
            ## date_collect to within some tolerance (15-16 days?)
            ask_boot_yield=np.array([])
            bid_boot_yield=np.array([])
            # calculate accrued interest??
            AI=0
            AI=(tnow-(coupon_stream.index[0]-pd.DateOffset(months=6))).days/(
                coupon_stream.index[0]-(coupon_stream.index[0]-
                                        pd.DateOffset(months=6))
                                        ).days*coupon_stream.values[0]
            price=p_note[int(instrument)]+AI
            
            for cdate in coupon_stream.index[:-1]:
                ## What if there is no match within a specfied tolerance?
                ask_yield_match=ask_yield[(abs((cdate-sample_dates).days)
                                    ==np.min(abs(cdate-sample_dates).days))&
                                    (abs((cdate-sample_dates).days)<=date_tol)]
                bid_yield_match=bid_yield[(abs((cdate-sample_dates).days)
                                    ==np.min(abs(cdate-sample_dates).days))&
                                    (abs((cdate-sample_dates).days)<=date_tol)]
                if (len(ask_yield_match)>0)&(len(bid_yield_match)>0):
                    ask_boot_yield=np.append(
                        ask_boot_yield,np.min(ask_yield_match))
                    bid_boot_yield=np.append(
                        bid_boot_yield,np.min(bid_yield_match))
                    no_match=False
                else:
                    no_match=True
            
            if (price!=0)&(has_match):
                ## make an array for the exponent for discount factors
                tarr=((coupon_stream.index-tnow).days/365.0).values
                ## Don't I have to multiply by 100 to get correct value?
                ask_value=200*((face_val*(1+coupon_stream[0]/100)/(
                        price-face_val*coupon_stream[0]/100*np.sum(
                        1/(1+ask_boot_yield[:]/200)**(2*tarr[:-1]))))**(
                        1/(2*tarr[-1]))-1)
                                          
                bid_value=200*((face_val*(1+coupon_stream[0]/100)/(
                        price-face_val*coupon_stream[0]/100*np.sum(
                        1/(1+bid_boot_yield[:]/200)**(2*tarr[:-1]))))**(
                        1/(2*tarr[-1]))-1)
                
                                ## collect calculated yields
                ask_collect=np.append(ask_collect,ask_value)
                bid_collect=np.append(bid_collect,bid_value)
                ## append the cusip of this note/bond used
                notes_used=np.append(notes_used,instrument)
                print('Note:'+note_cusips[int(instrument)]+
                          ' Matures on date: '+ date.strftime("%Y-%m-%d"))
                    ## okay to append this date to the zero_dates index, if
                    ## it is not already in the index
                if ~pd.DatetimeIndex([date]).isin(zero_dates)[0]:
                        zero_dates=zero_dates.append(pd.DatetimeIndex([date]))
            else:
                print('Could not retrieve price for Note: '+
                          note_cusips[int(instrument)])
    if ask_collect.size>0:    
        ask_yield=np.append(ask_yield,np.min(ask_collect))
        bid_yield=np.append(bid_yield,np.max(bid_collect))




##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## sample zero curve
plt.plot(pd.to_datetime(bill_maturities.values[y_bill!=0]),y_bill[y_bill!=0],
         '.',label='Bills')
plt.plot(pd.to_datetime(note_maturities[note_zero_index].values[
    y_note[:len(note_zero_index)].values!=0]),
    y_note[:len(note_zero_index)].values[
        y_note[:len(note_zero_index)].values!=0],
        '.',label='Notes')
plt.plot(pd.to_datetime(bond_maturities[bond_zero_index].values[
    y_bond[:len(bond_zero_index)].values!=0]),
    y_bond[:len(bond_zero_index)].values[
        y_bond[:len(bond_zero_index)].values!=0],
        '.',label='Bonds')




plt.figure()
plt.plot(y_tips[p_tips_date!=0],'*',label='TIPS')
## plot the bootstrapped curve, if you can:
#plt.plot(zero_dates,ask_yield,'^',markerfacecolor="None",label='Bootstrapped Ask')
#plt.plot(zero_dates,bid_yield,'v',markerfacecolor="None",label='Bootstrapped Bid')
plt.title('Real Yield Curve, all TIPS securities')
plt.xlabel('Maturity Date')
plt.ylabel('Real Yield (%)')
plt.legend(loc='best')

## save data to csv
path='/Users/jeff/Desktop/finance/data/bonds'+''+tnow.strftime("/%Y/%m/%d")
## the line below is apparently for python 3!
os.makedirs(path, exist_ok=True)
## Workaround for python 2
#if not os.path.exists(path):
#   os.makedirs(path)
## convert tnow, the time at which the data was retrieved, into a 
## string for a filename.
tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
	
bill_file=path+'/'+'bills_'+tnow_str+'.txt'
#y_bill.to_csv(bill_file,sep=',')
bill_df.to_csv(bill_file,sep=',')

note_file=path+'/'+'notes_'+tnow_str+'.txt'
#y_note.to_csv(note_file,sep=',')
note_df.to_csv(note_file,sep=',')

bond_file=path+'/'+'bond_'+tnow_str+'.txt'
#y_bond.to_csv(bond_file,sep=',')
bond_df.to_csv(bond_file,sep=',')

tips_file=path+'/'+'tips_'+tnow_str+'.txt'
y_tips.to_csv(tips_file,sep=',')

## Quick plot of bills, notes, and bonds;
## Drop any zero yields for now?
plt.figure()
plt.plot(y_bill[y_bill!=0],'x',label='Bills')
plt.plot(y_note[p_note_date!=0],'+',label='Notes')
plt.plot(y_bond[p_bond_date!=0],'.',label='Bonds')
## plot the bootstrapped curve, if you can:
plt.plot(zero_dates,ask_yield,'^',markerfacecolor="None",label='Bootstrapped Ask')
plt.plot(zero_dates,bid_yield,'v',markerfacecolor="None",label='Bootstrapped Bid')
plt.title(tnow.strftime("%Y-%m-%d")+ ' Yield to Maturity Curve, all securities')
plt.xlabel('Maturity Date')
plt.ylabel('Yield (%)')
plt.legend(loc='best')
plt.savefig(path+'ytm_curve'+tnow_str+'.png')


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





