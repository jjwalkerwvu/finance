#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 26 21:30:47 2021

@author: jeff
    YieldCurve
        Class for yield curves generated from scraping, and subsequent 
        bootstrapping, usually instantaneous
        
    Recent git token: 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
"""

import pandas as pd
import json
from datetime import timedelta
from pandas.tseries.offsets import MonthEnd
from pandas.tseries.offsets import MonthBegin
from pandas.tseries.offsets import QuarterBegin
from pandas.tseries.offsets import QuarterEnd
from pandas.tseries.offsets import BMonthEnd
from pandas.tseries.offsets import BMonthBegin
from pandas.tseries.offsets import WeekOfMonth
from pandas.tseries.holiday import USFederalHolidayCalendar
import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt
import calendar
#import requests
import ssl
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
#from bs4 import Comment
#import re
import os
import sys
import time
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/Users/31643/Desktop/finance_2023/codes/data_cleaning')
from fred_api import fred_api

# 2023-08-16:
# I realized that I should just add the write_to_file=False into this function,
# so that the control logic is only written once!
# This way, I can get rid of many lines of unnecessary lines of code.
def write_dataframe_to_file(df,
                  write_to_file=False,
                  filename='sample_csv',
                  write_path='/Users/31643/Desktop/finance_2023/data/bonds'):
    
    tnow=pd.to_datetime('today').now()
    if write_to_file==True:
        try:
            path=write_path+tnow.strftime("/%Y/%m/%d")
            os.makedirs(path, exist_ok=True)
            tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
            fullname=path+'/'+filename+'_'+tnow_str+'.csv'
            df.to_csv(fullname,sep=',')
            print(filename+'.csv successfully printed to file in path: '
                  +path+'/')
        except:
            print('Your file did not save.')
    else:
        print("Warning: You have chosen not to save the file. "+
              "write_to_file=False")
    
    return

def write_plot_to_file(figure,filename):
    
    
    pass

def year_delta(dstart,dend):
    dstart=pd.Series(dstart)
    dend=pd.Series(dend)
    # difference in years:
    # dy=dend.year-dstart.year
    # number of leap years
    ys=np.array([e.year for e in dstart])
    ye=np.array([e.year for e in dend])
    nlpyrs=pd.Series(calendar.leapdays(ys,ye),index=dstart.index)
    # dm=dend.month-dstart.month
    # dday=dend.day-dstart.day
    
    # years=dy+dm/12.
    
    years=((dend-dstart)/np.timedelta64(1,'D')-nlpyrs)/365.
    
    return years

# A quick function to get the checksum digit for an ISIN
def isin_checksum(cc,cusip):
    # check that cc and cusip are strings?
    # Too lazy for error checking right now.
    # 26-Feb-2022: I finally realized that this does not work properly
    
    # isin=cc+cusip
    # running_string=''
    # for i in range(len(isin)):
    #     if isin[i].isdigit()==False:
    #         number=str(ord(isin[i])-55)
    #     else:
    #         number=isin[i]
    #     ## concatenate every number together, as string
    #     running_string=running_string+number
    #     #print(running_string)
        
    # ## Now, operate on running_string
    # num_str=''
    # for i in range(len(running_string)):
    #     ## For every OTHER digit, starting from rightmost digit, multiply by 2
    #     ## This statement should be equivalent
    #     if (i+1)%2!=0:
    #         num_str=num_str+str(int(running_string[i])*2)
    #     else:
    #         num_str=num_str+running_string[i]
    # ## Now, add up all digits to get the sum
    # isin_sum=0
    # for a in num_str:
    #     isin_sum=int(a)+isin_sum
    # ## Now find value, which is the smallest number greater than or equal to
    # ## bill_sum that ends in a zero
    # isin_value=np.ceil(isin_sum/10.0)*10
    # checksum=str(int(isin_value-isin_sum))  
    
    # I found this on the internet, maybe try this instead.
    # See arthurdejong's github page.
    number=cc+cusip
    _alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # convert to numeric first, then double some, then sum individual digits
    number = ''.join(str(_alphabet.index(n)) for n in number)
    number = ''.join(
        str((2, 1)[i % 2] * int(n)) for i, n in enumerate(reversed(number)))
    checksum = str((10 - sum(int(n) for n in number)) % 10)

    return checksum

def calc_check_digit(number):
    """Calculate the check digits for the number."""
    _alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # convert to numeric first, then double some, then sum individual digits
    number = ''.join(str(_alphabet.index(n)) for n in number)
    number = ''.join(
        str((2, 1)[i % 2] * int(n)) for i, n in enumerate(reversed(number)))
    return str((10 - sum(int(n) for n in number)) % 10)

# There are a few different types of scraping I do with Marketwatch; break 
# into functions. Separate functions are needed because the "scraping" 
# commands will be different 
def marketwatch_futures_scraper(futures_symbol,
                            calculation_date=pd.to_datetime('today').now(),
                            price_history=False,
                            price_history_months=1,
                            save_history=False):
    base_url='https://www.marketwatch.com/investing/future/'
        
     # Ignore SSL Certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
        
    #price=np.zeros(len(futures_symbol))
    #query_string=base_url+futures_symbol
    
    url=base_url+futures_symbol
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup=BeautifulSoup(webpage, 'html5lib')
    try:
        settlement_price=float(soup.find('td',{"class": "table__cell u-semi"}
                                              ).get_text().replace('$',''))
        print("Succesfully scraped settlement price data for futures contract: "
                      +futures_symbol)
    except:
        print("Unable to obtain settlement price data for futures contract: " 
              + futures_symbol+", filled as nan.")
        settlement_price=np.nan
        
    try:
        # This might be better for intra-day price; the one above is 
        # settlement price
        intraday_price=float(soup.select('.intraday__price .value')[0].string)
        print("Succesfully scraped intraday price data for futures contract: "
                      +futures_symbol)
    except:
        print("Unable to obtain intraday price data for futures contract: " 
              + futures_symbol+", filled as nan.")
        intraday_price=np.nan
        
    try:
        # Also might want the open interest, other info?
        oi=float((soup.select('.kv__item .primary')[3].string).replace(",",""))
        print("Succesfully scraped open interest data for futures contract: "
                      +futures_symbol)
    except:
        print("Unable to obtain open interest data for futures contract: " 
              + futures_symbol)
        oi=np.nan
        
    if price_history==True:
        # Right now, I am only using one month as a default setting
        try:
            # Use the volatility of the middle contract as a proxy? Adjust as 
            # necessary
            price_df=pd.read_csv(
                        'https://www.marketwatch.com/investing/future/'
                        +futures_symbol
                        +'/downloaddatapartial?startdate='
                        +(calculation_date-
                          pd.DateOffset(months=price_history_months)
                          ).strftime('%m/%d/%Y')
                        +'&enddate='+calculation_date.strftime('%m/%d/%Y')
                        +'&daterange=d30&frequency=p1d&csvdownload=true'
                        +'&downloadpartial=false&newdates=false')
            print("Successfully scraped price history for futures symbol "
                  +futures_symbol)
            
            if save_history==True:
                try:
                    write_dataframe_to_file(price_df,
                              filename=futures_symbol+'_'
                              +str(price_history_months)+'mo_history',
                              write_path='/Users/31643/Desktop/finance_2023/data/bonds')
                except:
                    print("Unable to save contract: "
                          +futures_symbol+" "+str(price_history_months)
                          +"-month price history data to file")
            
        except:
            print('Unable to get price history for futures symbol: '
                  +futures_symbol)
            price_df=[]
    else:
        price_df=[]
        
    return settlement_price,intraday_price,oi,price_df

# This is meant as an improvement on marketwatch_treasury_scraper
# I am calling this bond scraper for now, but this may change to treasury
# scraper later if it can truly be a drop-in replacement for 
# marketwatch_treasury_scraper.
# bond_info holds bond cusip, or other specific details.
# like for an otr bond, would include: 'tmubmusd?countrycode=bx'+term_mat
def marketwatch_bond_scraper(bond_info):
    
    # error checking for bond_info; it must be a string!
        
    base_url='https://www.marketwatch.com/investing/bond/'
    url=base_url+bond_info
   
    # Ignore SSL Certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
  
    # Use try/except block to skip past possible errors
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        soup=BeautifulSoup(webpage, 'html5lib')
        # get the yield, in %
        # But this is wrong, this is the previous close!
        # y=float(soup.find('td',{"class": "table__cell u-semi"}
        #                                       ).get_text().replace('%',''))
        
        y=float(soup.select('.intraday__price .value')[0].string)
        
        coupon=(soup.select('.kv__item .primary'
                                        )[6].string.replace('%',''))
        # Added this for the case of tbills, where there is no coupon
        if coupon=='N/A':
            coupon=np.nan
        else:
            coupon=float(coupon)
        
        maturity=(pd.to_datetime(soup.select('.kv__item .primary')[7].string))
        # try to get price; this command should get everything out of the 
        # table
        #soup.select('.kv__item .primary')
        p_str=soup.select('.kv__item .primary')[3].string.rsplit()
        # I do not know if this is necessarily the best way to do this
        try:
            price=float(p_str[0].rsplit('/')[0])/float(
                                        p_str[0].rsplit('/')[1])
        except:
            price=(float(p_str[0])+float(p_str[1].rsplit('/')[0])/
                              float(p_str[1].rsplit('/')[1]))
             
            print("Successfully scraped on the run security: " +  bond_info)
            # I just want to make it wait a short amount of time to 
            # minimize the chance that Marketwatch rejects my scraping.
            time.sleep(1)
            
    except:
        print("Failed to scrape on the run security: " + bond_info)
        y=np.nan
        price=np.nan
        coupon=np.nan
        maturity=pd.NaT
    
    return y,price,coupon,maturity
    

# Should this be a static method or a standalone function in this module?
def marketwatch_treasury_scraper(country_code,security_cusips,
                                 security_maturities):
    # Ignore SSL Certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
        
    # CONSIDER PARALLELIZING THIS CODE!
    # This does not seem to work, because Marketwatch tacks on a 10th  
    # number to the cusip
    # UPDATE! THE 10TH NUMBER IS A CHECKSUM, ASSUMING ISIN!
    # Use: 'US'+cusip+str(checksum); so need to calculate the checksum
    base_url='https://www.marketwatch.com/investing/bond/'
    # Preallocate array for yields that will be scraped from 
    # marketwatch
    y=np.zeros(len(security_cusips.values))
    # What if we fill in the yield and price with nans?
    y[:]=np.nan
    # price of bill/note/bond
    price=np.zeros(len(security_cusips.values))
    price[:]=np.nan
    # Array for time to maturity
    # tmat=np.array((pd.to_datetime(security_maturities.values)-
    #                 pd.to_datetime('today').now())/np.timedelta64(1,'D')
    #               )/365.2425

    # Maybe there should be a way to eliminate duplicates?
    cusip_check=security_cusips.drop_duplicates().index.values
    # get bill/note/bond data
    for j in range(len(security_cusips.values)):
        checksum=isin_checksum(country_code,security_cusips.values[j])
        url=base_url+security_cusips.values[j]+checksum
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        soup=BeautifulSoup(webpage, 'html5lib')
        # Use if statement to make sure cusip j is not a duplicate
        if security_cusips.index[j] in cusip_check:
            # Use try/except block to skip past possible invalid cusips
            try:
                # get the yield, in %, but this is the previous close!
                # y[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                #                               ).get_text().replace('%',''))
                
                y[j]=float(soup.select('.intraday__price .value')[0].string)
                
                # try to get price; this command should get everything out of the 
                # table
                #soup.select('.kv__item .primary')
                p_str=soup.select('.kv__item .primary')[3].string.rsplit()
                price[j]=(float(p_str[0])+
                              float(p_str[1].rsplit('/')[0])/
                              float(p_str[1].rsplit('/')[1]))
                print("Successfully scraped CUSIP: "+ 
                          security_cusips.values[j]+
                          " with Maturity: "+
                          pd.to_datetime(
                              security_maturities.values[j]
                              ).strftime("%Y-%m-%d"))
                
                # I just want to make it wait a short amount of time to 
                # minimize the chance that Marketwatch rejects my scraping.
                time.sleep(1)
            except:
                print("Failed to scrape CUSIP: "+
                          security_cusips.values[j]+
                          " with Maturity: "+
                              pd.to_datetime(security_maturities.values[j])
                              .strftime("%Y-%m-%d"))
        else:
            print("CUSIP: "+security_cusips.values[j]+ 
                  " is a duplicate CUSIP; cannot do more than 1 unique "+
                  "CUSIP with Marketwatch")
    # make data series out of this:
    y=pd.Series(data=y,index=pd.to_datetime(
            security_maturities),name='yield')  
    y.index.rename('Maturity',inplace=True) 
    # Probably not necessary to record the price, but doing so anyway for 
    # completeness
    price=pd.Series(data=price,index=security_cusips.index,name='price')
    price.index.rename('CUSIP Index',inplace=True) 
    price_date=pd.Series(data=price.values,index=pd.to_datetime(security_maturities),
                 name='price')
    price_date.index.rename('Maturity',inplace=True) 
    # Making a dataframe for price might be better, so that we have an 
    # index for the spreadsheet and for the date in one place
    # price_df=pd.DataFrame({'Maturity':price_date.index, 
    #                        'years_to_maturity':tmat,
    #                        'price':price.values,
    #                        'yield_to_maturity':y},index=price.index)
    # price_df=pd.DataFrame(data={'cusip':security_cusips.values,
    #                        'yield':y.values,
    #                        'price':price.values,
    #                        'spreadsheet_row':price.index},
    #                  index=y.index)
    
    price_df=pd.DataFrame(data={'market_yield':y.values,
                                'market_price':price.values},
                          index=security_cusips.index)
    
    print('Yield and price scraping complete.')
  
    return price_df

def zero_coupon_from_forward_hull(frate,texp):
    
    y=np.zeros(len(frate))
    y[0]=frate[0]
    
    for index in range(len(y)-1):
        # Original code:
        # y[index+1]=(sofr_zero_rate[index+1]*(t_exp[index+1]-t_exp[index])
        #             +y[index]*t_exp[index])/(t_exp[index+1])
        tau=(texp[index+1]-texp[index])
        y[index+1]=(texp[index]*y[index]
                    +tau*frate[index+1])/(texp[index+1])
    return y

def zero_coupon_from_forward_mercurio(frate,texp):
    
    y=np.zeros(len(frate))
    y[0]=frate[0]
    
    for index in range(len(y)-1):
        tau=(texp[index+1]-texp[index])
        # Shouldn't the rate be divided by something?
        y[index+1]=(texp[index]*y[index]
                    +np.log(1+tau*frate[index+1]))/texp[index+1]
    return y

def reorder_interest_payments(first_payment,
                              second_payment,
                              calculation_date=pd.to_datetime('today').now()):
    
    # Set aside the payments I have to change
    wrong_payment_order=first_payment>second_payment
        
    # Need to hold onto these values for the second payment
    first_payment_hold=first_payment[wrong_payment_order]
        
    first_payment[wrong_payment_order]=second_payment[wrong_payment_order]
        
    second_payment[wrong_payment_order]=(first_payment_hold)
        
    # If the first payment has already happened, we set 
    # first payment equal to the second payment, add a year to the first
    # payment and set second payment to the original first payment
        
    first_payment_paid=(calculation_date>first_payment)&(
                                        calculation_date<second_payment)
        
    first_payment_hold=first_payment[first_payment_paid]
        
    first_payment[first_payment_paid]=second_payment[first_payment_paid]
    second_payment[first_payment_paid]=(first_payment_hold
                                                 + pd.DateOffset(years=1))
        
    # The first and second payments may have already happened; add a year
    # to both if that is the case.
        
    both_payments_paid=(calculation_date>first_payment)&(
                                            calculation_date>second_payment)
        
    first_payment[both_payments_paid]=first_payment[
                                    both_payments_paid]+pd.DateOffset(years=1)
    second_payment[both_payments_paid]=second_payment[
                                    both_payments_paid]+pd.DateOffset(years=1)
                    
    
    return first_payment,second_payment

def rename_treasury_columns(df,treasury_type='note'):
    
    # These will be the keys in the renaming dictonary
    original_columns=df.columns.to_list()
    # the values in the renaming dictionary
    renamed_columns=[treasury_type+'_'+column for column in original_columns]
    
    rename_dict=dict(zip(original_columns,renamed_columns))
    df.rename(columns=rename_dict,inplace=True)
    
    return df

# Make a function that returns data frames for all marketable securities
def marketable_securities_from_most_recent_mspd(write_to_file=False):
    
    tnow=pd.to_datetime('today').now()
    year=str(tnow.year)
    # try the last month, and if that does not work, try 2 months ago.
    one_month_ago=tnow-pd.DateOffset(months=1)
    two_months_ago=tnow-pd.DateOffset(months=2)
    
    # most recent reporting date
    report_date=(tnow-pd.DateOffset(months=1)+MonthEnd(0)
                 ).date().strftime('%Y-%m-%d')
    
    mspd_base=('https://api.fiscaldata.treasury.gov/services/api/'
               +'fiscal_service/v1/debt/mspd/')

    marketable_treasuries='mspd_table_3_market'
    # have a method in place for STRIPS, also.
    # All other, important tables:
    # summary is the overview of outstanding debt
    summary='mspd_table_1'
    stat_debt_limit='mspd_table_2'
    treasuries_outstanding='mspd_table_3'
    nonmarketable_treasuries='mspd_table_3_nonmarket'
    # what is historical data?
    historical_data='mspd_table_4'  
    strips='mspd_table_5'
    
    # I think you have to use end of month most recent past month for the record 
    # date.
    record_date='?filter=record_date:eq:'+report_date
    
    # construct the url for the request
    url=mspd_base+marketable_treasuries+record_date
    # make urls for all the other tables
    url_strips=mspd_base+strips+record_date
    url_debt_limit=mspd_base+stat_debt_limit+record_date
    url_treas_outstanding=mspd_base+treasuries_outstanding+record_date
    url_historical_data=mspd_base+historical_data+record_date
    url_nonmarketable=mspd_base+nonmarketable_treasuries+record_date
    
    # Sometimes, there is no data yet for the most recent month end. In that
    # case, just go back one month to get the most recent data.
    try:
        print('Retrieving Statement of US Public Debt for date: ' + 
                  one_month_ago.strftime('%Y-%m'))
        response = urlopen(url)
        
        fd_json=json.loads(response.read())
        total_count=fd_json['meta']['total-count']
        # total_pages=fd_json['meta']['total-pages']   
        # Now that we have the metadata for the most recent record date, get 
        # all marketable treasuries.
        page_no_size=',page[number]=1&page[size]='+str(total_count)
        response = urlopen(url+page_no_size)
        fd_json=json.loads(response.read())
        # Now get data for strips:
        response=urlopen(url_strips)
        strips_json=json.loads(response.read())
        total_count=strips_json['meta']['total-count']
        page_no_size=',page[number]=1&page[size]='+str(total_count)
        response=urlopen(url_strips+page_no_size)
        strips_json=json.loads(response.read())
        
        
    except:
        print('Unable to Retrieve Data for record date: '
              +one_month_ago.strftime('%Y-%m'))
        report_date=((tnow-pd.DateOffset(months=1)
                     -pd.DateOffset(months=1))
                     +MonthEnd(0)).date().strftime('%Y-%m-%d')
        record_date='?filter=record_date:eq:'+report_date
        url=mspd_base+marketable_treasuries+record_date
        url_strips=mspd_base+strips+record_date
        print('Retrieving Statement of US Public Debt for date: ' +
                  two_months_ago.strftime('%Y-%m'))
        response = urlopen(url)
        
        fd_json=json.loads(response.read())
        total_count=fd_json['meta']['total-count']    
        # Now that we have the metadata for the most recent record date, get 
        # all marketable treasuries.
        page_no_size=',page[number]=1&page[size]='+str(total_count)
        response = urlopen(url+page_no_size)
        fd_json=json.loads(response.read())
        # Now get data for strips:
        response=urlopen(url_strips)
        strips_json=json.loads(response.read())
        total_count=strips_json['meta']['total-count']
        page_no_size=',page[number]=1&page[size]='+str(total_count)
        response=urlopen(url_strips+page_no_size)
        strips_json=json.loads(response.read())
        
    print('Data Retrieved, now parsing.')
    
    # get the strips_df now?
    strips_df=pd.DataFrame.from_dict(strips_json['data'])
    # drop some of the columns that are not needed; bring back if needed
    strips_df.drop(columns=['record_fiscal_year',
                                'record_fiscal_quarter',
                                'record_calendar_year',
                                'record_calendar_quarter',
                                'record_calendar_month',
                                'record_calendar_day'],inplace=True)
    # get rid of null values, possibly get rid of strips that are already
    # matured?
    strips_df=strips_df.loc[strips_df.maturity_date!='null']
    strips_df.maturity_date=pd.to_datetime(strips_df.maturity_date)
    strips_df=strips_df.loc[(strips_df.maturity_date>tnow)]
    strips_df.portion_stripped_amt=strips_df.portion_stripped_amt.astype(float)
    strips_df.portion_unstripped_amt=strips_df.portion_unstripped_amt.astype(float)
    
    # collect the columns, possibly needed later for compatibility
    # columns=fd_json['data'][0].keys()
    
    treasury_df=pd.DataFrame.from_dict(fd_json['data'])
    # I think src_line_nbr should be the index, and it should tie in with 
    # previous code/solution.
    treasury_df.set_index('src_line_nbr',inplace=True)
    # drop some of the columns that are not needed; bring back if needed
    treasury_df.drop(columns=['security_type_desc',
                              'series_cd',
                                'record_fiscal_year',
                                'record_fiscal_quarter',
                                'record_calendar_year',
                                'record_calendar_quarter',
                                'record_calendar_month',
                                'record_calendar_day'],inplace=True)
    # Some column renaming right now, to maintain compatibility
    rename_dict={'security_class2_desc':'cusip',
                 'interest_rate_pct':'coupon',
                 'yield_pct':'yield',
                 'interest_pay_date_1':'first_payment',
                 'interest_pay_date_2':'second_payment',
                 'interest_pay_date_3':'third_payment',
                 'interest_pay_date_4':'fourth_payment'}
    
    # We have to convert datetime columns to datetimes; this includes several
    # columns
    
    # make sure to only look at non-null rows?
    # treasury_df.maturity_date.loc[treasury_df.maturity_date!='null'
    #                         ]=pd.to_datetime(treasury_df.maturity_date.loc[
    #                             treasury_df.maturity_date!='null'])
    
    # Just as before, we need to get rid of securities on the list that have
    # matured.
    treasury_df=treasury_df.loc[treasury_df.maturity_date!='null']
    treasury_df.maturity_date=pd.to_datetime(treasury_df.maturity_date)
    treasury_df=treasury_df.loc[(treasury_df.maturity_date>tnow)]
    treasury_df.issue_date=pd.to_datetime(treasury_df.issue_date)
    
    # convert any string values that should be float
    treasury_df.interest_rate_pct.loc[treasury_df.interest_rate_pct!='null'
                        ]=treasury_df.interest_rate_pct.loc[
                        treasury_df.interest_rate_pct!='null'].astype(float)

    treasury_df.rename(columns=rename_dict,inplace=True)
    # We need to drop the following rows that contain aggregation values;
    # these contain the word 'Total' as the cusip value. Check this later if
    # errors occur!
    treasury_df.drop(treasury_df.loc[
        treasury_df.cusip.str.contains('Total')].index,inplace=True)
    
    # procedure to reorder interest payments
    first_payment=treasury_df.first_payment.loc[
                    (treasury_df.security_class1_desc=='Notes')
                    |(treasury_df.security_class1_desc=='Bonds')
                    |(treasury_df.security_class1_desc
                      =='Inflation-Protected Securities')]
    
    second_payment=treasury_df.second_payment.loc[
                    (treasury_df.security_class1_desc=='Notes')
                    |(treasury_df.security_class1_desc=='Bonds')
                    |(treasury_df.security_class1_desc
                      =='Inflation-Protected Securities')]
    
    # I think this is sufficient
    if ~calendar.isleap(int(year)):
        first_payment.loc[first_payment.str.contains('02/29')]='02/28'
        second_payment.loc[second_payment.str.contains('02/29')]='02/28'
    
    first_payment=pd.to_datetime(first_payment+'/'+year[2:],
                                 dayfirst=True,errors='coerce')
    second_payment=pd.to_datetime(second_payment+'/'+year[2:],
                                 dayfirst=True,errors='coerce')
        
    # Use the reorder_interest_payments function here
    first_paydate,second_paydate=reorder_interest_payments(
        first_payment,second_payment)
    
    treasury_df.first_payment.loc[
                    (treasury_df.security_class1_desc=='Notes')
                    |(treasury_df.security_class1_desc=='Bonds')
                    |(treasury_df.security_class1_desc
                      =='Inflation-Protected Securities')]=first_paydate
    treasury_df.second_payment.loc[
                    (treasury_df.security_class1_desc=='Notes')
                    |(treasury_df.security_class1_desc=='Bonds')
                    |(treasury_df.security_class1_desc
                      =='Inflation-Protected Securities')]=second_paydate
    
    bill_df=treasury_df.loc[treasury_df.security_class1_desc
                            =='Bills Maturity Value']
    bill_df.drop(columns=['security_class1_desc',
                          'second_payment',
                          'third_payment',
                          'fourth_payment'],inplace=True)
    bill_df=rename_treasury_columns(bill_df,treasury_type='bill')
    
    note_df=treasury_df.loc[treasury_df.security_class1_desc
                            =='Notes']
    note_df.drop(columns=['security_class1_desc',
                          'third_payment',
                          'fourth_payment'],inplace=True)
    note_df=rename_treasury_columns(note_df,treasury_type='note')
    
    bond_df=treasury_df.loc[treasury_df.security_class1_desc
                            =='Bonds']
    bond_df.drop(columns=['security_class1_desc',
                          'third_payment',
                          'fourth_payment'],inplace=True)
    bond_df=rename_treasury_columns(bond_df,treasury_type='bond')
    
    frn_df=treasury_df.loc[treasury_df.security_class1_desc
                            =='Floating Rate Notes']
    frn_df.drop(columns=['security_class1_desc'],inplace=True)
    frn_df=rename_treasury_columns(frn_df,treasury_type='frn')
    
    tips_df=treasury_df.loc[treasury_df.security_class1_desc
                            =='Inflation-Protected Securities']
    tips_df.drop(columns=['security_class1_desc',
                          'third_payment',
                          'fourth_payment'],inplace=True)
    tips_df=rename_treasury_columns(tips_df,treasury_type='tips')
    
    return bill_df,note_df,bond_df,strips_df,frn_df,tips_df

# Still getting some things wrong from bloomberg example:
# 4.) 11/30/24, 2.125, 98.4297: 3.1076
# 5.) 10/31/24, 2.25, 99.2578: 3.3301
# However, I see that these are not ten year notes; these should correspond
# to seven year notes, and they would not have been issued yet
# Should this partially replace the class method in USTreasuryFutures?
def calculate_irr(first_payment,second_payment,coupon,bond_price,
                  futures_price,cf=1.0,
                  calculation_date=pd.to_datetime('today').now(),
                  delivery_date=pd.to_datetime('today').now()+pd.DateOffset(months=1)):
    # I think the convention that I use here is first payment is the next
    # payment, and the second payment comes six months after that, so that
    # all payments occur in the future
    
    # calculate accrued interest  on settlement of cash bond
    # Stackexchange answer/Bloomberg terminal suggests that days=0 gives
    # closer answer, instead of days=1 that I was using, but I'm not fully
    # convinced.
    # Do I need to perform the reordering of interest Payments?
    # first_payment,second_payment=reorder_interest_payments(
    #         pd.Series(first_payment),
    #         pd.Series(second_payment),
    #         calculation_date=calculation_date)
    
    ai=calculate_accrued_interest(
                            pd.Series(first_payment),
                            pd.Series(second_payment),
                            calculation_date=calculation_date
                            +pd.DateOffset(days=0),
                            interest_rate=coupon)
    # just take the first element of the pandas series.
    ai=ai[0]
        
    # Accrued interest on delivery date:
    # First step:
    # reorder payment dates to coincide with the delivery date
    delivery_first_payment,delivery_second_payment=reorder_interest_payments(
            pd.Series(first_payment),
            pd.Series(second_payment),
            calculation_date=delivery_date)
     
    print(delivery_first_payment)
    ad=calculate_accrued_interest(delivery_first_payment,
                                  delivery_second_payment,
                        pd.Series(coupon),
                        calculation_date=delivery_date)
    # just take the first element of the pandas series.
    ad=ad[0]
        
    # Interim coupons between settlement and delivery.
    # There are only up to 4 quarterly contract dates at any given time for
    # US Treasury futures,so I think that means there can be at most 2 
    # iterim coupons.
    ic_first=coupon/2*(first_payment<delivery_date)
    ic_second=coupon/2*(second_payment<delivery_date)
    
    first_payment_days=(delivery_date-first_payment)/np.timedelta64(1,'D')
    second_payment_days=(delivery_date-second_payment)/np.timedelta64(1,'D')
    delivery_days=(delivery_date-calculation_date)/np.timedelta64(1,'D')
    
    # yf=delivery_days/360.
        
    # I think I do not need the "sum over ic" that I see in:
    # https://www.factset.com/hubfs/Resources%20Section/White%20Papers/Bond%20Future%20White%20Paper.pdf
    # because of how I calculate the first and second payments
    irr=100*(futures_price*cf+ad+ic_first+ic_second-(bond_price+ai))*360./(
            (bond_price+ai)*delivery_days-ic_first*first_payment_days
            -ic_second*second_payment_days)

    return irr

def cashflows_from_securities(securities_index,
                              coupon_payment,
                              first_payment,
                              second_payment,
                              maturity_date,
                              calculation_date=pd.to_datetime('today').now()):
    # can bypass dataframe, if we have the index, first and second payments,
    # and maturity date
    
    # switch all instances of tnow to calculation date later.
    tnow=calculation_date
    
    face_val=100
    # Try with note coupon dataframe first.
    coupon_df=[]
    maturity_df=[]
    for index in securities_index:
        
        #print(first_payment[index])
        #print(second_payment[index])
    
        if first_payment[index].is_month_end:
            coupon_dates=(
                pd.date_range(start=first_payment[index],
                                end=maturity_date[index],
                                freq='6M'))
            # I think that if coupon payments are not at a month end, then they are
            # Always on the 15th of a month. 
            # IF THIS TURNS OUT TO NOT BE TRUE, THIS MUST BE CHANGED!
        else:
            coupon_dates=(pd.date_range(
                    start=first_payment[index]-
                    pd.DateOffset(15),
                    end=maturity_date[index]+pd.DateOffset(15),
                    freq='6M')+pd.DateOffset(15))
    
    
    
        # In case the first payment has already occurred:
        # Use greater than or equal, or just greater than?
        # I am taking this line out; just use 
        # coupon_df=coupon_df[coupon_df.index>tnow] if you need to, later.
        #coupon_dates=coupon_dates[coupon_dates>=tnow]
        # placeholder vector array
        coupons=np.ones((np.size(coupon_dates))
                                 )*coupon_payment[index]/2
        # This a placeholder vector array for the maturities of each cash 
        # flow; Remember that we do need to use actual/actual convention
        mat_values=((coupon_dates-tnow)/np.timedelta64(1,'D')
                     ).values/365.2425
        # if you want to add the principal here
        coupons[-1]=coupons[-1]+face_val
        coupon_series=pd.Series(coupons,index=coupon_dates)
        #
        mat_series=pd.Series(mat_values,coupon_dates)
        coupon_df.append(coupon_series)
        #
        maturity_df.append(mat_series)
        # And this is the resulting dataframe for all coupon payments, with the 
        # (slightly modified) spreadsheet number as column number
    coupon_df=pd.concat(coupon_df, axis=1, 
                keys=[item for item in securities_index.astype(str)])
    maturity_df=pd.concat(maturity_df, axis=1, 
                keys=[item for item in securities_index.astype(str)])
    return coupon_df,maturity_df

def calculate_accrued_interest(first_payment,
                               second_payment,
                               interest_rate,
                               calculation_date=pd.to_datetime('today').now()):
    
    # 1 August 2022:
    # May be problem with end of month payments
    # Calculate accrued interest here.
    # Have to add the offset because otherwise the first payment will get 
    # changed
    most_recent_payment=(first_payment + pd.DateOffset(days=0))
    most_recent_payment[(calculation_date-second_payment
                             )/np.timedelta64(1,'D')>0
                            ]=second_payment[
                            (calculation_date-second_payment
                             )/np.timedelta64(1,'D')>0]
    # What if calculation date is less than BOTH first and second payment??
    # We need to handle this case also.
    most_recent_payment[(calculation_date<first_payment)&(
            calculation_date<second_payment)]=most_recent_payment[
                (calculation_date<first_payment)&(
                calculation_date<second_payment)]-pd.DateOffset(months=6)
    
    # 6 August 2022:
    # Need same solution for most recent payment:
    for no,date in enumerate(most_recent_payment):
        if date.day!=15:
            (most_recent_payment)[no]=date+MonthEnd(0)

    # 3 August 2022:
    # problem here - need to add MonthEnd(0) if the day of the month is not 15
    next_payment=most_recent_payment+pd.DateOffset(months=6)
    # The solution:
    for no,date in enumerate(next_payment):
        if date.day!=15:
            next_payment[no]=date+MonthEnd(0)

    coupon_period=(next_payment-most_recent_payment)/np.timedelta64(1,'D')
    # print(coupon_period)
        
    # Divide by 2, because it is a semiannual coupon
    accrued_interest=(calculation_date-most_recent_payment
            )/np.timedelta64(1,'D')/coupon_period*interest_rate/2.0
        
    
    return accrued_interest

def order_delivery_months(calculation_date=pd.to_datetime('today').now()):
    # Dates really need to be localized to US CT zone
    
    # Need a calendar to handle US business holidays!
    cal = USFederalHolidayCalendar()
    # Business month begin and end dates will be useful
    start_offset=pd.tseries.offsets.CustomBusinessMonthBegin(calendar=cal)
    end_offset=pd.tseries.offsets.CustomBusinessMonthEnd(calendar=cal)
    
    
    # Create an offset of 7 Business days using the US federal holiday 
    # calendar, to use for long duration contracts
    last_trade_offset=pd.tseries.offsets.CustomBusinessDay(calendar=cal,n=7)
    # This seems consistent with the CME website and makes sense; a new 
    # contract is not traded until the front month stops trading.
    first_trade_offset=pd.tseries.offsets.CustomBusinessDay(calendar=cal,n=6)
    
    # offset for first trading day of short duration contracts
    short_dur_first_trade_offset=pd.tseries.offsets.CustomBusinessDay(
                                                            calendar=cal,n=1)
    # offset for final delivery day of short duration contracts
    short_dur_final_delivery_offset=pd.tseries.offsets.CustomBusinessDay(
                                                            calendar=cal,n=2)
  
    month_start=start_offset.rollback(calculation_date)
    
    tend=month_start+pd.DateOffset(years=1)
     
    # The basis for future calculations; the last day of the delivery month is
    # also important for filtering two year notes
    query_dates=pd.date_range(start=calculation_date,end=tend,freq='Q')
     
    # the conversion factor is calculated for the first day of the delivery
    # month
    cf_calc_dates=query_dates-MonthBegin()
    
    # First Delivery Day is the first business day of the contract delivery 
    # month, which is the same as the cf_calc_dates.
   
    # Last trading date for longer durations:
    # UB, TWE, ZB, TN, ZN
    # Trading in the expiring contract terminates on the seventh business day 
    # before the last business day of the delivery month
    long_dur_last_trade_date=pd.DatetimeIndex(
                            [end_offset.rollback(query_date)-last_trade_offset
                                        for query_date in query_dates])
    # The last delivery day for long duration contracts; this is important
    # for calculating implied repo rate!
    long_dur_last_delivery_date=pd.DatetimeIndex(
                            [end_offset.rollback(query_date)
                                        for query_date in query_dates])
    
    short_dur_last_trade_date=pd.DatetimeIndex(
                            [end_offset.rollback(query_date)
                                        for query_date in query_dates])
    
    # The last delivery day for short duration contracts
    # 3rd business day of next calendar month
    # I think this is correct, but I am not confident that the rollforward
    # works properly in all cases! It matches the last delivery dates on the
    # cme website when I first tested this (8 May 2022)
    short_dur_last_delivery_date=pd.DatetimeIndex(
                            [start_offset.rollforward(query_date)+short_dur_final_delivery_offset
                                        for query_date in 
                            pd.date_range(start=calculation_date,
                                          end=tend,freq='QS')])
    
    # See 
    # https://www.cmegroup.com/markets/interest-rates/us-treasury/30-year-us-treasury-bond.calendar.html
    # for ideas on how to calculate.
    # These are the first trades of the contracts in query_dates
    long_dur_first_trade_date=pd.DatetimeIndex(
                    [end_offset.rollback(query_date)-first_trade_offset
                     for query_date in 
                     (query_dates-pd.DateOffset(months=9)+MonthEnd(0))])
    
    # Short duration first trade date; this seems to work so far!
    short_dur_first_trade_date=pd.DatetimeIndex(
                    [end_offset.rollback(query_date)
                     +short_dur_first_trade_offset
                     for query_date in 
                     (query_dates-pd.DateOffset(months=9)+MonthEnd(0))])
    
    # I also need:
    # First intention day/First position day
    # First notice day
    # First delivery day
    # Last intention day
    # Last notice day
    # but I will put these in later.

    long_dur_keep=(calculation_date<long_dur_last_trade_date)&(
                                calculation_date>long_dur_first_trade_date)
    
    # which contracts to keep for the short contracts:
    short_dur_keep=(calculation_date<short_dur_last_trade_date)&(
                                calculation_date>short_dur_first_trade_date)    

    
    futures_codes=['h','m','u','z']
    
    # 3 quarterly contracts are listed. When do we replace the front month?
    # I placed zn here for now, but need to do all contracts, how to arrange?
    # Remove untradeable contracts?
    long_dur_tradeable_contracts=[
                            (str(futures_codes[int(np.floor(date.month/3))-1])
                            +str(date.year)[2:]) for date in 
                            query_dates[long_dur_keep]]
    
    short_dur_tradeable_contracts=[
                            (str(futures_codes[int(np.floor(date.month/3))-1])
                            +str(date.year)[2:]) for date in 
                            query_dates[short_dur_keep]]
    
    # 
    short_dur_sybmols=['tu','3yr','fv']
    short_dur_cme_symbols=['tu','z3n','fv']
    # TN and TWE are not available with marketwatch :`(
    long_dur_symbols=['ty','us','ul']
    long_dur_cme_symbols=['ty','us','ub']
    
    # Interesting ticker for 2 year deliverable interest rate swap
    #T1UCM22
    
    # Make a column for the active contract? (tnow<first_delivery_date?)
    # Make a column for delivery_month_end_date
    short_dur_contracts=[]
    first_trade_date=[]
    last_trade_date=[]
    last_delivery_date=[]
    cf_calc_date=[]
    delivery_month_end_date=[]
    short_dur_cme_symbol=[]
    for symbol_number,symbol in enumerate(short_dur_sybmols):
        for number, contract in enumerate(short_dur_tradeable_contracts):
            short_dur_contracts.append(symbol+contract)
            short_dur_cme_symbol.append(short_dur_cme_symbols[symbol_number])
            first_trade_date.append(
                short_dur_first_trade_date[short_dur_keep][number])
            last_trade_date.append(
                short_dur_last_trade_date[short_dur_keep][number])
            last_delivery_date.append(
                short_dur_last_delivery_date[short_dur_keep][number])
            cf_calc_date.append(
                cf_calc_dates[short_dur_keep][number])
            delivery_month_end_date.append(query_dates[short_dur_keep][number])
            
    short_dur_df=pd.DataFrame(
                data={'cme_code':short_dur_cme_symbol,
                        'first_trade_date':first_trade_date,
                        'last_trade_date':last_trade_date,
                        'last_delivery_date':last_delivery_date,
                        'first_delivery_date':cf_calc_date,
                        'cf_calc_date':cf_calc_date,
                        'delivery_month_end_date':delivery_month_end_date},
                            index=short_dur_contracts)
        
    
    # Same thing, but for the longer duration contracts
    long_dur_contracts=[]
    first_trade_date=[]
    last_trade_date=[]
    last_delivery_date=[]
    cf_calc_date=[]
    delivery_month_end_date=[]
    long_dur_cme_symbol=[]
    for symbol_number,symbol in enumerate(long_dur_symbols):
        for number, contract in enumerate(long_dur_tradeable_contracts):
            long_dur_contracts.append(symbol+contract)
            long_dur_cme_symbol.append(long_dur_cme_symbols[symbol_number])
            first_trade_date.append(
                long_dur_first_trade_date[long_dur_keep][number])
            last_trade_date.append(
                long_dur_last_trade_date[long_dur_keep][number])
            last_delivery_date.append(
                long_dur_last_delivery_date[long_dur_keep][number])
            cf_calc_date.append(
                cf_calc_dates[long_dur_keep][number])
            delivery_month_end_date.append(query_dates[long_dur_keep][number])
            
    long_dur_df=pd.DataFrame(
                data={'cme_code':long_dur_cme_symbol,
                        'first_trade_date':first_trade_date,
                        'last_trade_date':last_trade_date,
                        'last_delivery_date':last_delivery_date,
                        'cf_calc_date':cf_calc_date,
                        'delivery_month_end_date':delivery_month_end_date},
                            index=long_dur_contracts)
    
    # Make a dataframe with all of this information?
    tf_df=short_dur_df.append(long_dur_df)
     
    return tf_df


class YieldCurve(object):
    """ Class docstring goes here?
    """
    # Do I need the init statement or not?
    def __init__(self, issuer, cashflow_df, maturity_df, market_df):
        self.issuer=issuer
        #self.security_cusips=security_cusips
        self.cashflow_df=cashflow_df
        self.maturity_df=maturity_df
        self.market_df=market_df
                 
    def calculate_price_from_yield(self):
        
        # can we assume that accrued interest has been calculated in the 
        # market_df?
        
        return
    
    def analytical_bootstrap(self,cutoff_days=0,tol_days=15,use_yield=True):
        # This method should be inherited by all subclasses!
        # Consider a simple interpolation for gaps between maturities?
        # Seems to be working reasonably, 2021 December 26
        tnow=pd.to_datetime('today').now()
        
        # 2023-08-13
        # Sometimes, treasury securities behave strangely close to maturity.
        # use a cutoff date to eliminate securities that mature within a 
        # specified timeframe 
        cutoff_date=tnow+pd.DateOffset(days=cutoff_days)
        
        market_subframe=self.market_df[self.market_df.index>cutoff_date]
        # market_subframe=self.market_df
        
        # 2023-08-13:
        # Use of a specific column is an annoying source of fragility and 
        # future problems, but I am using this for now.
        use_columns=market_subframe['CUSIP Index'].values
        # Original, older code that may work in the future, but does not work
        # now
        # cash_subframe=self.cashflow_df[self.cashflow_df.index>cutoff_date]    
        # mat_subframe=self.maturity_df[self.maturity_df.index>cutoff_date]
        cash_subframe=self.cashflow_df[use_columns]    
        mat_subframe=self.maturity_df[use_columns]
        
        
        # Let us try to calculate market prices from the quoted yield, and
        # compare to the market price; perhaps the price is note listed
        # properly?
        
        # tolerance between coupons; in years
        # Maybe I could even make this 0
        tol=tol_days/365.24
        # "preallocate" for the spot yield?
        # s=np.ones(len(market_subframe))*0.053
        s=np.zeros(len(market_subframe))*np.nan
        #s_ask=np.zeros(len(self.note_df))
        # or, use length of the cash_subframe?
        #salt=np.zeros(len(cash_subframe))
        # this actually works, unlike my implementation for s so far.
        # salt=np.zeros(len(self.market_df))
        # maturity array?
        mat=np.zeros(len(market_subframe))
        
        bond_price=[]
        bd=[]
        
        ncols=len(cash_subframe.columns)
        for col in range(ncols):
            # Find number of coupon payments remaining
            npayments=len(cash_subframe[cash_subframe.columns[col]].dropna())
            
            # 2023-08-13:
            # calculate the coupon maturities for this particular note/bond
            # in the loop; I think this should work even if npayments==1.
            # However, this probably does not work for tbills, but maybe this is
            # ok, Tbills are in a segmented market relative to notes and bonds
            coupon_maturities=mat_subframe[
                                mat_subframe.columns[col]].dropna().values
            
            # correction needed for the nearest coupon payment due to accrued 
            # interest
            ai_correction=np.zeros(
                len(cash_subframe[cash_subframe.columns[col]].dropna().values))
            
            ai_correction[0]=market_subframe.accrued_interest.iloc[col]
            
            # Calculate the clean price from yield
            price_from_yield=(np.sum((
                cash_subframe[cash_subframe.columns[col]].dropna().values
                -ai_correction)/(
                    1+market_subframe.market_yield.iloc[col]/200)**(
                        2*coupon_maturities)))
            
            bond_price.append(price_from_yield)            
                        
            if use_yield==True:
                clean_price=1.0*price_from_yield
            else:
                clean_price=market_subframe.market_price.iloc[col]
            
            dirty_price=(clean_price
                    +market_subframe.accrued_interest.iloc[col])
            
            # dirty_price=clean_price*1.0
            
            bd.append(dirty_price)
            
            # This statement allows us to compute spot rates at start of the 
            # bootstrap
            if (npayments==1) and (market_subframe.market_price.iloc[col]!=0):
                mat[col]=mat_subframe[mat_subframe.columns[col]].dropna()
                
                s[col]=2*(np.exp(np.log(cash_subframe[
                    cash_subframe.columns[col]].dropna().values[0]/dirty_price
                    )/(2*mat[col]))-1)
                
                # if use_yield==True:
                #     # Very simple solution; just convert the market yields of 
                #     # "zero-coupon" notes/bonds to exponential
                #     # s[col]=2*np.log(1+self.market_df.market_yield.iloc[col]/200)
                #     s[col]=self.market_df.market_yield.iloc[col]/100
                    
                    
                # else:
                #     s[col]=np.log((cash_subframe[cash_subframe.columns[col]
                #                             ].dropna().values)/(
                #             self.market_df.market_price.iloc[col]+
                #             self.market_df.accrued_interest.iloc[col]))/(
                #                 mat[col])
                                
                    
                                
            # What to do when we get past the "zero coupon" notes?
            elif (npayments>1) and (market_subframe.market_price.iloc[col]!=0):
                mat[col]=mat_subframe[mat_subframe.columns[col]].dropna()[-1]
                # There must be a better way to do this, with a np method
                closest_indices=[]
                for elapsed_time in coupon_maturities[:-1]:
                    # Maybe pick highest yield from securities available, if
                    # there is more than one match?
                    # 2023-08-13:
                    # I think this command, while well-intentioned, is 
                    # oversimplifed if I want to take the highest spot yield 
                    # available
                    # match=abs(mat-elapsed_time).argmin()
                    
                    # 2023-08-13:
                    # Here is the new solution:
                    # find the highest yield available for the payment date 
                    # that is closest to the maturity date in the maturity 
                    # array, mat
                    closest_mat=np.where((abs(mat-elapsed_time)
                                          ==np.min(abs(mat-elapsed_time))))

                    # 2023-08-13:
                    # Sometimes you can get the error: All-NaN slice 
                    # encountered. 
                    try:
                        spot_index=np.nanargmax(s[(abs(mat-elapsed_time)
                                          ==np.min(abs(mat-elapsed_time)))])
                    
                        match=closest_mat[0][spot_index]
                    except:
                        # possibly print an error message
                        print("No non-Nan spot values; s,mat array number: "
                              +str(col)+" cannot be used for the bootstrap.")
                        # Use "the old command", just to keep the program 
                        # running. No non-nan spot value will be calculated.
                        match=abs(mat-elapsed_time).argmin()
                    
                    closest_indices.append(match)
                
                if np.all(abs(coupon_maturities[:-1]-mat[closest_indices])<
                          tol):
                    
                    # if use_yield==True:
                    #     # price_from_yield=(np.sum(cash_subframe[
                    #     #     cash_subframe.columns[col]].dropna().values/(
                    #     #         1+self.market_df.market_yield.iloc[col]/200)**(
                    #     #             2*coupon_maturities))-
                    #     #             self.market_df.accrued_interest.iloc[col])
                        
                    #     clean_price=(np.sum(cash_subframe[
                    #         cash_subframe.columns[col]].dropna().values/(
                    #             1+self.market_df.market_yield.iloc[col]/200)**(
                    #                 2*coupon_maturities)))
                        
                    #     # 2023-08-13:
                    #     # I read that the dirty price must be used!
                    #     dirty_price=(clean_price
                    #             +self.market_df.accrued_interest.iloc[col])
              
                    #     # Now that closest time indices are known, we can solve  
                    #     # for the spot rate at the maturity date at mat[col]           
                    #     # s[col]=np.log((cash_subframe[cash_subframe.columns[col]
                    #     #                         ].dropna().values[-1])/(
                    #     #         dirty_price-
                    #     #             np.sum(cash_subframe[
                    #     #                 cash_subframe.columns[col]
                    #     #                 ].dropna().values[:-1]*np.exp(-
                    #     #                         s[closest_indices]*mat[
                    #     #                         closest_indices]))))/(mat[col]) 

                    # else:
                    #     # Now that closest time indices are known, we can solve  
                    #     # for the spot rate
                    #     # s[col]=np.log((cash_subframe[cash_subframe.columns[col]
                    #     #                     ].dropna().values[-1])/(
                    #     #     self.market_df.market_price.iloc[col]+
                    #     #        self.market_df.accrued_interest.iloc[col]-
                    #     #        np.sum(cash_subframe[cash_subframe.columns[col]
                    #     #                     ].dropna().values[:-1]*np.exp(-
                    #     #                         s[closest_indices]*mat[
                    #     #                         closest_indices]))))/(mat[col])
                        
                    #     dirty_price=(self.market_df.market_price.iloc[col]+
                    #                  self.market_df.accrued_interest.iloc[col])
                        
                    # Now that closest time indices are known, we can solve  
                    # for the spot rate
                    s[col]=2*(np.exp(np.log(
                            (cash_subframe[cash_subframe.columns[col]
                                ].dropna().values[-1])/(dirty_price-
                                np.sum(cash_subframe[
                                cash_subframe.columns[col]
                                ].dropna().values[:-1]*(
                                    1/(1+s[closest_indices]/2)**(
                                        2*mat[closest_indices])) 
                                        )))/(2*mat[col]))-1) 
                        
                else:
                    mat[col]=0
        
        # 2023-08-13: Double check that this is the best way to produce a 
        # datetime array
        mat_date=[tnow+timedelta(x) for x in np.round(mat*365.25)]
        
        # output the spot rate, continuously compounded:
        s_cc=100*(2*np.log(1+s/2))
        
        return mat_date,mat,s,s_cc,bond_price,bd,cash_subframe,mat_subframe
    
    # simple linear interpolation instance method here to get zero coupon bonds
    # between maturity dates; call the method above to get the values
    #def analytical_bootstrap_linear_interpolate():
  
# Maybe USYieldCurve is really a SovereignYieldCurve, a subclass of YieldCurve
# And SovereignYieldCurve has the methods for bootstrapping, etc.
class USYieldCurve(YieldCurve):
    def __init__(self, 
                 issuer,
                 cashflow_df,
                 maturity_df,
                 market_df,
                 public_debt,
                 bill_df,
                 note_df,
                 bond_df,
                 strips_df,
                 frn_df,
                 tips_df):
        
        self.issuer='US'
        self.cashflow_df=cashflow_df
        self.maturity_df=maturity_df
        self.market_df=market_df
        self.public_debt=public_debt
        self.bill_df=bill_df
        self.note_df=note_df
        self.bond_df=bond_df
        self.strips_df=strips_df
        self.frn_df=frn_df
        self.tips_df=tips_df
        #self.security_cusips=security_cusips
        #self.cashflow_df=cashflow_df
        # Use super to fill in the more general attributes of YieldCurve class?
        #super().__init__(issuer, cashflow_df)
        
    @classmethod
    def get_mspd_with_api(cls, write_to_file=False):
        
        # Stick with $100 face value for now.
        face_val=100
        
        tnow=pd.to_datetime('today').now()
        
        bill_df,note_df,bond_df,strips_df,frn_df,tips_df=(
            marketable_securities_from_most_recent_mspd(write_to_file=False))
        
        # Figure out what to do with this later
        public_debt=0
        
        # bill cashflows.
        #bill_cashflow=pd.Series(data=face_val,index=bill_df.maturity_date)
        bill_cashflow=[]
        bill_maturity=[]
        for index in bill_df.index:
            
            bill_series=pd.Series(np.array([face_val]),
                                  index=[bill_df.bill_maturity_date[index]])
            bill_cashflow.append(bill_series)
            
            bill_mat_values=((bill_df.bill_maturity_date[index]-tnow
                              )/np.timedelta64(1,'D'))/365.2425
            bill_mat_series=pd.Series(bill_mat_values,
                                      [bill_df.bill_maturity_date[index]])
            bill_maturity.append(bill_mat_series)
        # This appears to work for bills. (16 December 2021)
        bill_cashflow=pd.concat(bill_cashflow, axis=1, 
                keys=[item for item in bill_df.index.astype(str)])
        bill_maturity=pd.concat(bill_maturity, axis=1, 
                keys=[item for item in bill_df.index.astype(str)])
        
        # get cashflow, maturity dataframes
        note_coupon_df,note_maturity_df=cashflows_from_securities(
                note_df.index,
                note_df.note_coupon,
                note_df.note_first_payment,
                note_df.note_second_payment,
                note_df.note_maturity_date)
        
        bond_coupon_df,bond_maturity_df=cashflows_from_securities(
                bond_df.index,
                bond_df.bond_coupon,
                bond_df.bond_first_payment,
                bond_df.bond_second_payment,
                bond_df.bond_maturity_date)
        
        # Do I need accrued interest in the bill, note, bond dataframes?
        # Maybe it is good to calculate now.
           
        # How do I construct this cashflow dataframe??   
        # Maybe just concat all cash flows together.
        cashflow_df=pd.concat([bill_cashflow,note_coupon_df,bond_coupon_df],
                              axis=1)
        maturity_df=pd.concat([bill_maturity,
                               note_maturity_df,
                               bond_maturity_df],axis=1)
        # Maybe there should be a TIPS cashflow??
        # Yes, need something separate for that.
        # SAVE THE CASHFLOW AND MATURITY DATAFRAMES!
        
        market_df=0
        
        print('US Treasury data is now parsed, ready to get market data.')
        
        return cls('US',
                   cashflow_df,
                   maturity_df,
                   market_df,
                   public_debt,
                   bill_df,
                   note_df,
                   bond_df,
                   strips_df,
                   frn_df,
                   tips_df)
    
    # This is a class method to reconstruct a USYieldCurve from file
    @classmethod
    def reconstruct_from_file(cls, write_to_file=False):
        
        cashflow_df=0
        maturity_df=0
        market_df=0
        public_debt=0
        bill_df=0
        note_df=0
        bond_df=0
        strips_df=0
        frn_df=0
        tips_df=0
        
        return cls('US',
                   cashflow_df,
                   maturity_df,
                   market_df,
                   public_debt,
                   bill_df,
                   note_df,
                   bond_df,
                   strips_df,
                   frn_df,
                   tips_df)
    
    @classmethod
    def get_us_public_debt(cls, write_to_file=False):
        # Use this method as class method to fill in USYieldCurve instance
        # attributes.
        # You should only really need/want to run this once in a session.
        # After a USYieldCurve object has been instantiated, use the other 
        # methods in this class to make adjustments to yield curve attributes?
        
        # Stick with $100 face value for now.
        face_val=100
        
        tnow=pd.to_datetime('today').now()

        # Get the year
        #year=str(tnow.year)
        #months_arr=[1,2,3,4,5,6,7,8,9,10,11,12]
        #months_str=['01','02','03','04','05','06','07','08','09','10','11','12']
        #closest_month=min(months_arr,key=lambda x:(tnow.month-x)>0)
        #exp_months=(months_str[months_arr.index(closest_month):]+
        #      months_str[:months_arr.index(closest_month)])
        
        # try the last month, and if that does not work, try 2 months ago.
        one_month_ago=tnow-pd.DateOffset(months=1)
        two_months_ago=tnow-pd.DateOffset(months=2)
        
        
        tr_url_base='https://www.treasurydirect.gov/govt/reports/pd/mspd/'
        try:
            year=str(one_month_ago.year)
            last_month=str(one_month_ago.month)
            if len(last_month)<2:
                last_month='0'+last_month        
            df=pd.read_excel(tr_url_base+year+'/opdm'+last_month+year+'.xls',
                     sheet_name=None)
            print('Retrieving Statement of US Public Debt for date: ' + 
                  one_month_ago.strftime('%Y-%m'))
            
        except:
            year=str(two_months_ago.year)
            last_month=str(two_months_ago.month)
            if len(last_month)<2:
                last_month='0'+last_month
            print('Retrieving Statement of US Public Debt for date: ' +
                  two_months_ago.strftime('%Y-%m'))
            df=pd.read_excel(tr_url_base+year+'/opdm'+last_month+year+'.xls',
                     sheet_name=None)
            
        print('Data Retrieved, now parsing.')
        # I think I have to reset the year given from tnow in order for the
        # first payment/second payment logic to work
        # THIS MUST BE HERE! CONFIRMED WORKING AS OF 2022-03-11
        year=str(tnow.year)
        
        # Get the last month; it is possible that it may take a while for the 
        # website to update the spreadsheet
        # last_month=str(tnow.month-1)
        # if len(last_month)<2:
        #     last_month='0'+last_month
        #     # Get all Cusip IDs for Tbills, Tnotes, and Tbonds!
        #     # Try to get rid of duplicate cusips to save computational resources
        #     # td_url_base is the base url for getting spreadsheet information from 
        #     # treasurydirect.gov
        # tr_url_base='https://www.treasurydirect.gov/govt/reports/pd/mspd/'
        # try:
        #     print('Retrieving Statement of US Public Debt')
        #     df=pd.read_excel(tr_url_base+year+'/opdm'+last_month+year+'.xls',
        #              sheet_name=None)
        # except:
        # # Using this exception in case it takes up to a month for treasury.gov
        # # to update the spreadsheet; if this does not give enough of a buffer 
        # # then I will have to come up with something else if it breaks
        #     last_month=str(tnow.month-2)
        #     if len(last_month)<2:
        #         last_month='0'+last_month
        #         print('Retrieving Statement of US Public Debt')
        #         df=pd.read_excel(tr_url_base+year+'/opdm'+last_month+year+
        #              '.xls',sheet_name=None)
        #print('Data Retrieved, now parsing.')
        
        
        # Am I having problems here?
        assert ('df' in locals())
        # sheets is a list of all the spreadsheet names
        sheets=list(df.keys())
        
        public_debt=df
        
        # Now, I assemble dataframes for each type of marketable US public 
        # debt security.
        
        # Bills.
        bill_start=df[sheets[1]][df[sheets[1]].columns[1]][
                df[sheets[1]][df[sheets[1]].columns[1]]==
                'Treasury Bills (Maturity Value):'].index[0]+2
        bill_end=df[sheets[1]][df[sheets[1]].columns[1]][
            df[sheets[1]][df[sheets[1]].columns[1]]==
            'Total Unmatured Treasury Bills..................................'+
            '.............................................…'].index[0]-1
        
        bill_df=df[sheets[1]][bill_start:bill_end]
        # Deal with the fact that the spreadsheet may contain notes that have
        # matured.
        bill_df=bill_df[bill_df[bill_df.columns[7]]>tnow]
        # Get rid of unnecessary columns with no data; 
        # This can be done by inspecting the spreadsheet.
        drop_cols=[0,1,3,5,10,12,14]
        bill_df=bill_df.drop(bill_df.columns[drop_cols],axis=1).fillna(
            method='ffill')
        bill_df.columns=['bill_cusip','bill_yield','bill_issue_date',
                         'bill_maturity_date',
                         'bill_payable_date','bill_issued',
                         'bill_inflation_adj','bill_redeemed',
                         'bill_outstanding']
        
        # Notes.
        note_start=df[sheets[1]][df[sheets[1]].columns[1]][
            df[sheets[1]][df[sheets[1]].columns[1]]=='Treasury Notes:'].index[0]+2
        note_end=df[sheets[1]][df[sheets[1]].columns[1]][
            df[sheets[1]][df[sheets[1]].columns[1]]==
            'Total Unmatured Treasury Notes..................................'+
            '.............................................…'].index[0]-1
        note_df=df[sheets[1]][note_start:note_end]
        # Deal with the fact that the spreadsheet may contain notes that have
        # matured.
        note_df=note_df[note_df[note_df.columns[7]]>tnow]
        # Deal with payable dates.
        # note_payable_dates=note_df[note_df.columns[8]].str.split(' ',3,expand=True
        #             ).replace(to_replace=[None],value=np.nan)+'/'+str(
        #                 tnow.year)[2:]
                        
        # Reuse the year from the spreadsheet that we got earlier.
        note_payable_dates=note_df[note_df.columns[8]].str.split(
            ' ',3,expand=True).replace(to_replace=[None],value=np.nan
                                       )+'/'+year[2:]                
        note_payable_dates.columns=['first_payment','second_payment']
        note_first_payment=pd.to_datetime(note_payable_dates['first_payment'], 
                                  dayfirst=True,errors='coerce').ffill()
        note_payable_dates[
            (note_payable_dates['second_payment'].str[:5]=='02/29')
            & [~calendar.isleap(int(year))]*len(note_payable_dates)]=('02/28/'
                                                                + year[2:])
         
        #print(note_payable_dates['second_payment'])
        note_second_payment=pd.to_datetime(
                                note_payable_dates['second_payment'], 
                                  dayfirst=True,errors='coerce').ffill()
        # This is my best guess as to how to interpret the spreadsheet;
        # Since no year is given, I assume that if the first listed payment occurs
        # at a greater month than the second payment, then the second payment 
        # corresponds to the following calendar year.
        # If the first listed payment happens at a lower month, than the second
        # payment date, I presume the first payment has already occurred.
        # note_second_payment[
        #     note_first_payment>note_second_payment]=note_second_payment[
        #         note_first_payment>note_second_payment]+pd.DateOffset(years=1)
        
        # Set aside the payments I have to change
        wrong_payment_order=note_first_payment>note_second_payment
        
        # Need to hold onto these values for the second payment
        note_first_payment_hold=note_first_payment[wrong_payment_order]
        
        note_first_payment[wrong_payment_order]=note_second_payment[
                                                    wrong_payment_order]
        
        note_second_payment[wrong_payment_order]=(note_first_payment_hold)
        
        # If the first payment has already happened, we set 
        # first payment equal to the second payment, add a year to the first
        # payment and set second payment to the original first payment
        
        first_payment_paid=(tnow>note_first_payment)&(tnow<note_second_payment)
        
        first_payment_hold=note_first_payment[first_payment_paid]
        
        note_first_payment[first_payment_paid]=note_second_payment[
                                                    first_payment_paid]
        note_second_payment[first_payment_paid]=(first_payment_hold
                                                 + pd.DateOffset(years=1))
        
        # The first and second payments may have already happened; add a year
        # to both if that is the case.
        
        both_payments_paid=(tnow>note_first_payment)&(tnow>note_second_payment)
        
        note_first_payment[both_payments_paid]=note_first_payment[
                                    both_payments_paid]+pd.DateOffset(years=1)
        note_second_payment[both_payments_paid]=note_second_payment[
                                    both_payments_paid]+pd.DateOffset(years=1)
                
        # 6 May 2022
        # This problem keeps happening, so I wrote a function to handle it.
        # Uncomment this and start using it once I am truly confident that it
        # works!
        
        # note_first_payment,note_second_payment=reorder_interest_payments(
        #                                                 note_first_payment,
        #                                                 note_second_payment,
        #                                                 tnow)
        
        
        drop_cols=[0,1,5,8,10,12,14]
        note_df=note_df.drop(note_df.columns[drop_cols],axis=1).fillna(
            method='ffill')
        note_df.columns=['note_cusip','note_coupon','note_yield',
                         'note_issue_date',
                         'note_maturity_date',
                         'note_issued','note_inflation_adj','note_redeemed',
                         'note_outstanding']
        note_df['note_first_payment']=note_first_payment
        note_df['note_second_payment']=note_second_payment
        
        # Bonds. Now includes newly issued 20 year bonds and 30 year bonds.
        bond_start=df[sheets[1]][df[sheets[1]].columns[1]][
            df[sheets[1]][df[sheets[1]].columns[1]]==
            'Treasury Bonds:'].index[0]+2
        bond_end=df[sheets[1]][df[sheets[1]].columns[1]][
            df[sheets[1]][df[sheets[1]].columns[1]]==
            'Total Unmatured Treasury Bonds..................................'+
            '.............................................…'].index[0]-1
        bond_df=df[sheets[1]][bond_start:bond_end]
        # Deal with the fact that the spreadsheet may contain bonds that have
        # matured.
        bond_df=bond_df[bond_df[bond_df.columns[7]]>tnow]
        # Deal with payable dates.
        # bond_payable_dates=bond_df[bond_df.columns[8]].str.split(' ',3,
        #                     expand=True).replace(
        #                     to_replace=[None],value=np.nan)+'/'+str(
        #                         tnow.year)[2:]
        
        # Reuse the year from the spreadsheet that we got earlier.
        bond_payable_dates=bond_df[bond_df.columns[8]].str.split(' ',3,
                            expand=True).replace(
                            to_replace=[None],value=np.nan)+'/'+year[2:]
        bond_payable_dates.columns=['first_payment','second_payment']
        bond_first_payment=pd.to_datetime(bond_payable_dates['first_payment'], 
                                  dayfirst=True,errors='coerce').ffill()
        bond_second_payment=pd.to_datetime(
                                bond_payable_dates['second_payment'], 
                                  dayfirst=True,errors='coerce').ffill()
        # bond_second_payment[
        #     bond_first_payment>bond_second_payment]=bond_second_payment[
        #         bond_first_payment>bond_second_payment]+pd.DateOffset(years=1)
        
        # Set aside the payments I have to change
        wrong_payment_order=bond_first_payment>bond_second_payment
        
        # Need to hold onto these values for the second payment
        bond_first_payment_hold=bond_first_payment[wrong_payment_order]
        
        bond_first_payment[wrong_payment_order]=bond_second_payment[
                                                    wrong_payment_order]
        
        bond_second_payment[wrong_payment_order]=(bond_first_payment_hold) 
        
        # If the first payment has already happened, we set 
        # first payment equal to the second payment, add a year to the first
        # payment and set second payment to the original first payment
        
        first_payment_paid=(tnow>bond_first_payment)&(tnow<bond_second_payment)
        
        first_payment_hold=bond_first_payment[first_payment_paid]
        
        bond_first_payment[first_payment_paid]=bond_second_payment[
                                                    first_payment_paid]
        bond_second_payment[first_payment_paid]=(first_payment_hold
                                                 + pd.DateOffset(years=1))
        
        # The first and second payments may have already happened; add a year
        # to both if that is the case.
        
        both_payments_paid=(tnow>bond_first_payment)&(tnow>bond_second_payment)
        
        bond_first_payment[both_payments_paid]=bond_first_payment[
                                    both_payments_paid]+pd.DateOffset(years=1)
        bond_second_payment[both_payments_paid]=bond_second_payment[
                                    both_payments_paid]+pd.DateOffset(years=1)
        
                
        drop_cols=[0,1,5,8,10,12,14]
        bond_df=bond_df.drop(bond_df.columns[drop_cols],axis=1).fillna(
            method='ffill')
        bond_df.columns=['bond_cusip','bond_coupon','bond_yield',
                         'bond_issue_date','bond_maturity_date',
                         'bond_issued','bond_inflation_adj','bond_redeemed',
                         'bond_outstanding']
        bond_df['bond_first_payment']=bond_first_payment
        bond_df['bond_second_payment']=bond_second_payment
        
        # What to do with floating rate notes?
        frn_df=0
        
        
        # Tips
        tips_start=df[sheets[1]][df[sheets[1]].columns[1]][
            df[sheets[1]][df[sheets[1]].columns[1]]==
            'Treasury Inflation-Protected Securities:'].index[0]+2
        # Hopefully this will continue to work!
        tips_end=df[sheets[1]][df[sheets[1]].columns[1]][
            df[sheets[1]][df[sheets[1]].columns[1]]==
            'Treasury Floating Rate Notes:'].index[0]-3
        
        tips_df=df[sheets[1]][tips_start:tips_end]
        # Deal with the fact that the spreadsheet may contain tips that have
        # matured.
        tips_df=tips_df[tips_df[tips_df.columns[7]]>tnow]
        
        # tips_payable_dates=tips_df[tips_df.columns[8]].str.split(' ',3,
        #                     expand=True).replace(
        #                     to_replace=[None],value=np.nan)+'/'+str(
        #                         tnow.year)[2:]
        # Reuse the year from the spreadsheet that we got earlier.   
        tips_payable_dates=tips_df[tips_df.columns[8]].str.split(' ',3,
                            expand=True).replace(
                            to_replace=[None],value=np.nan)+'/'+year[2:]                     
        tips_payable_dates.columns=['first_payment','second_payment']
        tips_first_payment=pd.to_datetime(tips_payable_dates['first_payment'], 
                                  dayfirst=True,errors='coerce').ffill()
        tips_second_payment=pd.to_datetime(
                                tips_payable_dates['second_payment'], 
                                  dayfirst=True,errors='coerce').ffill()
        # tips_second_payment[
        #     tips_first_payment>tips_second_payment]=tips_second_payment[
        #         tips_first_payment>tips_second_payment]+pd.DateOffset(years=1)
        
        # Set aside the payments I have to change
        wrong_payment_order=tips_first_payment>tips_second_payment
        
        # Need to hold onto these values for the second payment
        tips_first_payment_hold=tips_first_payment[wrong_payment_order]
        
        tips_first_payment[wrong_payment_order]=tips_second_payment[
                                                    wrong_payment_order]
        
        tips_second_payment[wrong_payment_order]=(tips_first_payment_hold)
        
        # If the first payment has already happened, we set 
        # first payment equal to the second payment, add a year to the first
        # payment and set second payment to the original first payment
        
        first_payment_paid=(tnow>tips_first_payment)&(tnow<tips_second_payment)
        
        first_payment_hold=tips_first_payment[first_payment_paid]
        
        tips_first_payment[first_payment_paid]=tips_second_payment[
                                                    first_payment_paid]
        tips_second_payment[first_payment_paid]=(first_payment_hold
                                                 + pd.DateOffset(years=1))
        
        # The first and second payments may have already happened; add a year
        # to both if that is the case.
        
        both_payments_paid=(tnow>tips_first_payment)&(tnow>tips_second_payment)
        
        tips_first_payment[both_payments_paid]=tips_first_payment[
                                    both_payments_paid]+pd.DateOffset(years=1)
        tips_second_payment[both_payments_paid]=tips_second_payment[
                                    both_payments_paid]+pd.DateOffset(years=1)
        
        drop_cols=[0,1,5,8,10,12,14]
        tips_df=tips_df.drop(tips_df.columns[drop_cols],axis=1).fillna(
            method='ffill')
        tips_df.columns=['tips_cusip','tips_coupon','tips_yield',
                         'tips_issue_date','tips_maturity_date',
                         'tips_issued','tips_inflation_adj','tips_redeemed',
                         'tips_outstanding']
        tips_df['tips_first_payment']=tips_first_payment
        tips_df['tips_second_payment']=tips_second_payment
        
        # STRIPS, start with notes
        # 2022 Jan 5: I have not excluded any matured strips here, but should
        # be easy enough to handle by excluding data<tnow
        note_strips_start=df[sheets[4]][df[sheets[4]].columns[0]][
            df[sheets[4]][df[sheets[4]].columns[0]]==
            'Treasury Notes:'].index[0]+2
        note_strips_end=df[sheets[4]][df[sheets[4]].columns[0]][
            df[sheets[4]][df[sheets[4]].columns[0]]==
            'Total Treasury Notes............................................'+
            '................................................................'+
            '............................................................'
            ].index[0]
        
        note_strips_df=df[sheets[4]][note_strips_start:note_strips_end]   
        # Do I need to link any of this information to the principal 
        # securities?
        drop_cols=[2,9,10,11,12]
        note_strips_df=note_strips_df.drop(note_strips_df.columns[drop_cols],
                            axis=1).fillna(method='ffill')
        note_strips_df.columns=['note_cusip','note_coupon',
                                'note_corpus_STRIP_CUSIP',
                           'note_maturity_date','note_total_outstanding',
                           'note_portion_held_unstripped',
                           'note_portion_held_stripped',
                           'note_reconstituted_this_month']
        # Now, bond STRIPS
        bond_strips_start=note_strips_end+3
        bond_strips_end=df[sheets[4]][df[sheets[4]].columns[0]][
            df[sheets[4]][df[sheets[4]].columns[0]]==
            'Total Treasury Bonds............................................'+
            '................................................................'+
            '......................................................'].index[0]
        bond_strips_df=df[sheets[4]][bond_strips_start:bond_strips_end]
        # I think the drop columns are the same as for notes
        drop_cols=[2,9,10,11,12]
        bond_strips_df=bond_strips_df.drop(bond_strips_df.columns[drop_cols],
                            axis=1).fillna(method='ffill')
        bond_strips_df.columns=['bond_cusip','bond_coupon',
                                'bond_corpus_STRIP_CUSIP',
                           'bond_maturity_date','bond_total_outstanding',
                           'bond_portion_held_unstripped',
                           'bond_portion_held_stripped',
                           'bond_reconstituted_this_month']
        
        # Combine the two data frames; what do I want to do about the index?
        # maybe use maturity date?? I currently use the original index number
        # of the spreadsheet
        #strips_df=pd.concat([note_strips_df,bond_strips_df],axis=1)
        
        #separate dataframe for TIPS STRIPS???
        tips_strips_start=bond_strips_end+3
        tips_strips_end=df[sheets[4]][df[sheets[4]].columns[0]][
            df[sheets[4]][df[sheets[4]].columns[0]]==
            'Total Treasury Inflation-Protected Securities...................'+
            '..............................'].index[0]
        tips_strips_df=df[sheets[4]][tips_strips_start:tips_strips_end]
        drop_cols=[2,9,10,11,12]
        tips_strips_df=tips_strips_df.drop(tips_strips_df.columns[drop_cols],
                            axis=1).fillna(method='ffill')
        tips_strips_df.columns=['tips_cusip','tips_coupon',
                                'tips_corpus_STRIP_CUSIP',
                           'tips_maturity_date','tips_total_outstanding',
                           'tips_portion_held_unstripped',
                           'tips_portion_held_stripped',
                           'tips_reconstituted_this_month']
        
        # Maybe just put them all together; should I change index to mat. date?
        strips_df=pd.concat([note_strips_df,bond_strips_df,tips_strips_df],
                            axis=1)
        
        # bill cashflows.
        #bill_cashflow=pd.Series(data=face_val,index=bill_df.maturity_date)
        bill_cashflow=[]
        bill_maturity=[]
        for index in bill_df.index:
            
            bill_series=pd.Series(np.array([face_val]),
                                  index=[bill_df.bill_maturity_date[index]])
            bill_cashflow.append(bill_series)
            
            bill_mat_values=((bill_df.bill_maturity_date[index]-tnow
                              )/np.timedelta64(1,'D'))/365.2425
            bill_mat_series=pd.Series(bill_mat_values,
                                      [bill_df.bill_maturity_date[index]])
            bill_maturity.append(bill_mat_series)
        # This appears to work for bills. (16 December 2021)
        bill_cashflow=pd.concat(bill_cashflow, axis=1, 
                keys=[item for item in bill_df.index.astype(str)])
        bill_maturity=pd.concat(bill_maturity, axis=1, 
                keys=[item for item in bill_df.index.astype(str)])
        
        # get cashflow, maturity dataframes
        note_coupon_df,note_maturity_df=cashflows_from_securities(
                note_df.index,
                note_df.note_coupon,
                note_df.note_first_payment,
                note_df.note_second_payment,
                note_df.note_maturity_date)
        
        # It may be a good idea to put accrued interest into the note_df!
        
        # Now for bonds. Is there a better way to do this??
        # bond_coupon_df=[]
        # bond_maturity_df=[]
        # for index in bond_df.index:
    
        #     if bond_df.bond_first_payment[index].is_month_end:
        #         bond_coupon_dates=(
        #             pd.date_range(start=bond_df.bond_first_payment[index],
        #                         end=bond_df.bond_maturity_date[index],
        #                         freq='6M'))
        #     # I think that if coupon payments are not at a month end, then they are
        #     # Always on the 15th of a month. 
        #     # IF THIS TURNS OUT TO NOT BE TRUE, THIS MUST BE CHANGED!
        #     else:
        #         bond_coupon_dates=(pd.date_range(
        #             start=bond_df.bond_first_payment[index]-
        #             pd.DateOffset(15),
        #             end=bond_df.bond_maturity_date[index]+pd.DateOffset(15),
        #             freq='6M')+pd.DateOffset(15))
    
    
    
        #     # In case the first payment has already occurred:
        #     # Use greater than or equal, or just greater than?
        #     bond_coupon_dates=bond_coupon_dates[bond_coupon_dates>=tnow]
        #     # placeholder vector array
        #     bond_coupons=np.ones((np.size(bond_coupon_dates))
        #                          )*bond_df.bond_coupon[index]/2
        #     # This a placeholder vector array for the maturities of each cash 
        #     # flow; Remember that we do need to use actual/actual convention
        #     bond_mat_values=((bond_coupon_dates-tnow)/np.timedelta64(1,'D')
        #              ).values/365.2425
        #     # if you want to add the principal here
        #     bond_coupons[-1]=bond_coupons[-1]+face_val
        #     bond_coupon_series=pd.Series(bond_coupons,index=bond_coupon_dates)
        #     #
        #     bond_mat_series=pd.Series(bond_mat_values,bond_coupon_dates)
        #     bond_coupon_df.append(bond_coupon_series)
        #     #
        #     bond_maturity_df.append(bond_mat_series)
        # # And this is the resulting dataframe for all coupon payments, with the 
        # # (slightly modified) spreadsheet number as column number
        # bond_coupon_df=pd.concat(bond_coupon_df, axis=1, 
        #         keys=[item for item in bond_df.index.astype(str)])
        # bond_maturity_df=pd.concat(bond_maturity_df, axis=1, 
        #         keys=[item for item in bond_df.index.astype(str)])
        
        bond_coupon_df,bond_maturity_df=cashflows_from_securities(
                bond_df.index,
                bond_df.bond_coupon,
                bond_df.bond_first_payment,
                bond_df.bond_second_payment,
                bond_df.bond_maturity_date)
        
        # Do I need accrued interest in the bill, note, bond dataframes?
        
        
        # How do I construct this cashflow dataframe??   
        # Maybe just concat all cash flows together.
        cashflow_df=pd.concat([bill_cashflow,note_coupon_df,bond_coupon_df],axis=1)
        maturity_df=pd.concat([bill_maturity,note_maturity_df,bond_maturity_df],axis=1)
        # Maybe there should be a TIPS cashflow??
        # Yes, need something separate for that.
        # SAVE THE CASHFLOW AND MATURITY DATAFRAMES!
        
        market_df=0
        
        print('US Treasury data is now parsed, ready to get market data.')
        
        return cls('US',
                   cashflow_df,
                   maturity_df,
                   market_df,
                   public_debt,
                   bill_df,
                   note_df,
                   bond_df,
                   strips_df,
                   frn_df,
                   tips_df) 
    
    def save_cashflow_matrix(self,
                        write_path='/Users/jeff/Desktop/finance/data/bonds'):
        
        tnow=pd.to_datetime('today').now()
        try:
            path=write_path+tnow.strftime("/%Y/%m/%d")
            os.makedirs(path, exist_ok=True)
            tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
            cashflow_filename=path+'/'+'cashflows_'+tnow_str+'.csv'
            maturity_filename=path+'/'+'cashflow_maturities_'+tnow_str+'.csv'
            self.cashflow_df.to_csv(cashflow_filename)
            self.maturity_df.to_csv(maturity_filename)
            
            
            print('Data successfully printed to file.')
        except:
                print('Something bad happened, I dunno. Your file didnt save.')
        
        
        return
    
    def get_bills(self,write_path='/Users/jeff/Desktop/finance/data/bonds',
                  write_to_file=False):
        """

        Parameters
        ----------
        write_path : TYPE, optional
            DESCRIPTION. The default is '/Users/jeff/Desktop/finance/data/bonds'.
        write_to_file : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        market_data=marketwatch_treasury_scraper('US',self.bill_df.bill_cusip,
                                 self.bill_df.bill_maturity_date)
        # Update note dataframe with yields and prices from Marketwatch data
        
        tnow=pd.to_datetime('today').now()
        
        # Raise error is smarter here instead of just plowing ahead
        self.bill_df=pd.concat([self.bill_df,market_data],axis=1)
        
        
        try:
                # path=write_path+tnow.strftime("/%Y/%m/%d")
                # os.makedirs(path, exist_ok=True)
                # tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # bill_file=path+'/'+'bills'+tnow_str+'.txt'
                # # We do not need the whole file.
                # self.bill_df[["bill_cusip","bill_maturity_date",
                #               "market_price","market_yield"]
                #              ].to_csv(bill_file,sep=',')
                
            write_dataframe_to_file(write_to_file=write_to_file,
                                        df=self.bill_df[
                    ["bill_cusip","bill_issue_date","bill_maturity_date",
                              "market_price","market_yield"]],
                    filename='bills')
                
            print('Data successfully printed to file.')
        except:
            print('Your file did not save.')
        
        return market_data,self.bill_df
    
    def get_notes(self,write_path='/Users/jeff/Desktop/finance/data/bonds',
                  write_to_file=False):
        """

        Parameters
        ----------
        write_path : TYPE, optional
            DESCRIPTION. The default is '/Users/jeff/Desktop/finance/data/bonds'.
        write_to_file : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        
        note_data=marketwatch_treasury_scraper('US',self.note_df.note_cusip,
                                 self.note_df.note_maturity_date)
        
        tnow=pd.to_datetime('today').now()
        
        
        
        # Calculate accrued interest here. Should this go into class method?
        # Does not seem like a great idea to put here
        # Have to add the offset because otherwise the first payment will get 
        # changed
        most_recent_payment=(self.note_df.note_first_payment
                             + pd.DateOffset(days=0))
        most_recent_payment[(tnow-self.note_df.note_second_payment
                             )/np.timedelta64(1,'D')>0
                            ]=self.note_df.note_second_payment[
                            (tnow-self.note_df.note_second_payment
                             )/np.timedelta64(1,'D')>0]
        # What if tnow is less than BOTH first and second payment??
        # We need to handle this case also.
        most_recent_payment[(tnow<self.note_df.note_first_payment)&(
            tnow<self.note_df.note_second_payment)]=most_recent_payment[
                (tnow<self.note_df.note_first_payment)&(
                tnow<self.note_df.note_second_payment)]-pd.DateOffset(months=6)
        
        next_payment=most_recent_payment+pd.DateOffset(months=6)
        
        
        coupon_period=(next_payment-most_recent_payment)/np.timedelta64(1,'D')
        
        # Divide by 2, because it is a semiannual coupon
        ai=(tnow-most_recent_payment
            )/np.timedelta64(1,'D')/coupon_period*self.note_df.note_coupon/2
        ai.rename("note_accrued_interest",axis=1,inplace=True)
        
        
        
        # Update note dataframe with yields and prices from Marketwatch data
        # Raise error is smarter here instead of just plowing ahead
        self.note_df=pd.concat([self.note_df,ai,note_data],axis=1)
        
        # We should calculate Macaulay duration here.
        # Need to re-calculate prices; I don't trust market_price
        #self.maturity_df[self.note_df.index.astype(str)].values*self.cashflow_df[self.note_df.index.astype(str)].values
        #d=1/(1+self.note_df.market_yield/2)**(2*self.maturity_df[self.note_df.index.astype(str)].values)
        mac_dur=np.zeros(len(self.note_df))
        for counter,cusip_row in enumerate(self.note_df.index):
            fact=self.maturity_df[str(cusip_row)
                                ].dropna().values*self.cashflow_df[
                str(cusip_row)].dropna().values
            d=1/(1+self.note_df.market_yield[cusip_row]/200)**(
                    2*self.maturity_df[str(cusip_row)].dropna().values)
            # Use the price calculated from yield!
            price=np.sum(self.cashflow_df[str(cusip_row)].dropna().values*d)
            # print(price)
            # price from scraping; I do not trust it 
            # price=self.note_df.market_price[cusip_row]
            mac_dur[counter]=np.sum(fact*d)/(price+
                self.note_df.note_accrued_interest[cusip_row])    
        
        mac_dur=pd.Series(data=mac_dur,index=self.note_df.index,
                          name='note_mac_dur')
        # Update with Macaulay duration 
        self.note_df=pd.concat([self.note_df,mac_dur],axis=1)
        
        # Include also Modified duration!
        mod_dur=pd.Series(data=mac_dur/(1+self.note_df.market_yield/200.),
                          index=self.note_df.index,name='note_mod_dur')
        self.note_df=pd.concat([self.note_df,mod_dur],axis=1)
        
        try:
                # path=write_path+tnow.strftime("/%Y/%m/%d")
                # os.makedirs(path, exist_ok=True)
                # tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # note_file=path+'/'+'notes_'+tnow_str+'.txt'
                # # We do not need the whole file.
                # self.note_df[["note_cusip","note_maturity_date",
                #               "market_price","market_yield",
                #               "note_accrued_interest"]
                #              ].to_csv(note_file,sep=',')
                
            write_dataframe_to_file(write_to_file=write_to_file,
                                        df=self.note_df[
                    ["note_cusip","note_maturity_date",
                     "note_issue_date","market_price","market_yield",
                                  "note_accrued_interest"]],
                    filename='notes')
            print('Data successfully printed to file.')
        except:
            print('Something bad happened, I dunno. Your file didnt save.')
        
        return note_data,self.note_df
    
    def get_bonds(self,write_path='/Users/jeff/Desktop/finance/data/bonds',
                  write_to_file=False):
        """

        Parameters
        ----------
        write_path : TYPE, optional
            DESCRIPTION. The default is '/Users/jeff/Desktop/finance/data/bonds'.
        write_to_file : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        
        market_data=marketwatch_treasury_scraper('US',self.bond_df.bond_cusip,
                                 self.bond_df.bond_maturity_date)
        
        tnow=pd.to_datetime('today').now()
        
        # Calculate accrued interest here. Should this go into class method?
        # Does not seem like a great idea to put here
        # Have to add the offset because otherwise the first payment will get 
        # changed
        most_recent_payment=(self.bond_df.bond_first_payment
                             + pd.DateOffset(days=0))
        most_recent_payment[(tnow-self.bond_df.bond_second_payment
                             )/np.timedelta64(1,'D')>0
                            ]=self.bond_df.bond_second_payment[
                            (tnow-self.bond_df.bond_second_payment
                             )/np.timedelta64(1,'D')>0]
        # What if tnow is less than BOTH first and second payment??
        # We need to handle this case also.
        most_recent_payment[(tnow<self.bond_df.bond_first_payment)&(
            tnow<self.bond_df.bond_second_payment)]=most_recent_payment[
                (tnow<self.bond_df.bond_first_payment)&(
                tnow<self.bond_df.bond_second_payment)]-pd.DateOffset(months=6)                        
        
        next_payment=most_recent_payment+pd.DateOffset(months=6)
        
        
        coupon_period=(next_payment-most_recent_payment)/np.timedelta64(1,'D')
        
        # Divide by 2, because it is a semiannual coupon
        ai=(tnow-most_recent_payment
            )/np.timedelta64(1,'D')/coupon_period*self.bond_df.bond_coupon/2
        ai.rename("bond_accrued_interest",axis=1,inplace=True)
        
        # Update note dataframe with yields and prices from Marketwatch data
        # Raise error is smarter here instead of just plowing ahead
        self.bond_df=pd.concat([self.bond_df,ai,market_data],axis=1)
        
        # We should calculate Macaulay duration here.
        # Need to re-calculate prices; I don't trust market_price
        mac_dur=np.zeros(len(self.bond_df))
        for counter,cusip_row in enumerate(self.bond_df.index):
            fact=self.maturity_df[str(cusip_row)
                                ].dropna().values*self.cashflow_df[
                str(cusip_row)].dropna().values
            d=1/(1+self.bond_df.market_yield[cusip_row]/200)**(
                    2*self.maturity_df[str(cusip_row)].dropna().values)
            price=np.sum(self.cashflow_df[str(cusip_row)].dropna().values*d)
            # print(price)
            # price from scraping; I do not trust it 
            # price=self.bond_df.market_price[cusip_row]
            mac_dur[counter]=np.sum(fact*d)/(price 
                            + self.bond_df.bond_accrued_interest[cusip_row])
        
        mac_dur=pd.Series(data=mac_dur,index=self.bond_df.index,
                          name='bond_mac_dur')
        # Update with Macaulay duration 
        self.bond_df=pd.concat([self.bond_df,mac_dur],axis=1)
        
        # Include also Modified duration!
        mod_dur=pd.Series(data=mac_dur/(1+self.bond_df.market_yield/200.),
                          index=self.bond_df.index,name='bond_mod_dur')
        self.bond_df=pd.concat([self.bond_df,mod_dur],axis=1)
        
        try:
                # path=write_path+tnow.strftime("/%Y/%m/%d")
                # os.makedirs(path, exist_ok=True)
                # tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # bond_file=path+'/'+'bonds_'+tnow_str+'.txt'
                # # We do not need the whole file.
                # self.bond_df[["bond_cusip","bond_maturity_date",
                #               "market_price","market_yield",
                #               "bond_accrued_interest"]
                #              ].to_csv(bond_file,sep=',')
                
            write_dataframe_to_file(write_to_file=write_to_file,
                                        df=self.bond_df[
                    ["bond_cusip","bond_maturity_date",
                     "bond_issue_date","market_price","market_yield",
                                  "bond_accrued_interest"]],
                    filename='bonds')
                
            print('Data successfully printed to file.')
        except:
            print('Something bad happened, I dunno. Your file didnt save.')
        
        return market_data,self.bond_df
    
    
    def get_tips(self,write_path='/Users/jeff/Desktop/finance/data/bonds',
                  write_to_file=False):
        """

        Parameters
        ----------
        write_path : TYPE, optional
            DESCRIPTION. The default is '/Users/jeff/Desktop/finance/data/bonds'.
        write_to_file : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        
        market_data=marketwatch_treasury_scraper('US',self.tips_df.tips_cusip,
                                 self.tips_df.tips_maturity_date)
        
        tnow=pd.to_datetime('today').now()
        
        # Calculate accrued interest here. Should this go into class method?
        # Does not seem like a great idea to put here
        # Have to add the offset because otherwise the first payment will get 
        # changed
        most_recent_payment=(self.tips_df.tips_first_payment
                             + pd.DateOffset(days=0))
        most_recent_payment[(tnow-self.tips_df.tips_second_payment
                             )/np.timedelta64(1,'D')>0
                            ]=self.tips_df.tips_second_payment[
                            (tnow-self.tips_df.tips_second_payment
                             )/np.timedelta64(1,'D')>0]
        # What if tnow is less than BOTH first and second payment??
        # We need to handle this case also.
        most_recent_payment[(tnow<self.tips_df.tips_first_payment)&(
            tnow<self.tips_df.tips_second_payment)]=most_recent_payment[
                (tnow<self.tips_df.tips_first_payment)&(
                tnow<self.tips_df.tips_second_payment)]-pd.DateOffset(months=6)                        
        
        next_payment=most_recent_payment+pd.DateOffset(months=6)
        
        
        coupon_period=(next_payment-most_recent_payment)/np.timedelta64(1,'D')
        
        # Divide by 2, because it is a semiannual coupon
        ai=(tnow-most_recent_payment
            )/np.timedelta64(1,'D')/coupon_period*self.tips_df.tips_coupon/2
        ai.rename("tips_accrued_interest",axis=1,inplace=True)
        
        # Update note dataframe with yields and prices from Marketwatch data
        # Raise error is smarter here instead of just plowing ahead
        self.tips_df=pd.concat([self.tips_df,ai,market_data],axis=1)
        
        # We should calculate Macaulay duration here.
        # Need to re-calculate prices; I don't trust market_price
        # mac_dur=np.zeros(len(self.tips_df))
        # for counter,cusip_row in enumerate(self.tips.index):
        #     fact=self.maturity_df[str(cusip_row)
        #                         ].dropna().values*self.cashflow_df[
        #         str(cusip_row)].dropna().values
        #     d=1/(1+self.tips_df.market_yield[cusip_row]/200)**(
        #             2*self.maturity_df[str(cusip_row)].dropna().values)
        #     mac_dur[counter]=np.sum(fact*d)/(
        #         self.tips_df.market_price[cusip_row]
        #         + self.tips_df.bond_accrued_interest[cusip_row])
        
        # mac_dur=pd.Series(data=mac_dur,index=self.tips_df.index,
        #                   name='tips_mac_dur')
        # # Update with Macaulay duration 
        # self.tips_df=pd.concat([self.tips_df,mac_dur],axis=1)
        
        
        try:
                # path=write_path+tnow.strftime("/%Y/%m/%d")
                # os.makedirs(path, exist_ok=True)
                # tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # file=path+'/'+'tips_'+tnow_str+'.txt'
                # # We do not need the whole file.
                # self.tips_df[["tips_cusip","tips_maturity_date",
                #               "market_price","market_yield",
                #               "tips_accrued_interest"]
                #              ].to_csv(file,sep=',')
                
            write_dataframe_to_file(write_to_file=write_to_file,
                                        df=self.tips_df[
                    ["tips_cusip","tips_maturity_date",
                     "tips_issue_date","market_price","market_yield",
                                  "tips_accrued_interest"]],
                    filename='tips')
                
            print('Data successfully printed to file.')
        except:
            print('Something bad happened, I dunno. Your file didnt save.')
        
        return market_data,self.tips_df
    
    
    def use_only_notes(self):
        # Replace the cashflow and maturity dataframes with only data from 
        # notes
        self.cashflow_df,self.maturity_df=cashflows_from_securities(
                self.note_df.index,
                self.note_df.note_coupon,
                self.note_df.note_first_payment,
                self.note_df.note_second_payment,
                self.note_df.note_maturity_date)
        
        # dirty_price=(self.note_df.market_price+
        #              self.note_df.note_accrued_interest)
        # # make sure to zero out any rows with only accrued interest.
        # dirty_price[self.note_df.market_price==0]=0
        
        self.market_df=pd.concat([self.note_df.note_maturity_date,
                                  self.note_df.market_yield,
                                  self.note_df.market_price,
                                  self.note_df.note_accrued_interest],
                                 axis=1).rename(columns={
                                'note_maturity_date':'maturity_date',
                                'note_accrued_interest':'accrued_interest'})
        
        return
    
    def use_notes_and_bonds(self):
        # Assemble cashflow dataframe for notes
        note_cashflow_df,note_maturity_df=cashflows_from_securities(
                self.note_df.index,
                self.note_df.note_coupon,
                self.note_df.note_first_payment,
                self.note_df.note_second_payment,
                self.note_df.note_maturity_date)
        # Assemble cashflow dataframe for bonds
        bond_cashflow_df,bond_maturity_df=cashflows_from_securities(
                self.bond_df.index,
                self.bond_df.bond_coupon,
                self.bond_df.bond_first_payment,
                self.bond_df.bond_second_payment,
                self.bond_df.bond_maturity_date)
        
        # Assemble market data for notes.
        note_market_df=pd.concat([self.note_df.reset_index()['CUSIP Index'],
                                  self.note_df.reset_index().note_cusip,
                                  self.note_df.reset_index().note_maturity_date,
                                  self.note_df.reset_index().market_yield,
                                  self.note_df.reset_index().market_price,
                                  self.note_df.reset_index().note_accrued_interest],
                                 axis=1).rename(columns={
                                'note_maturity_date':'maturity_date',
                                'note_cusip':'cusip',
                                'note_accrued_interest':'accrued_interest'})
        # Assemble market data for notes.
        bond_market_df=pd.concat([self.bond_df.reset_index()['CUSIP Index'],
                                  self.bond_df.reset_index().bond_cusip,
                                  self.bond_df.reset_index().bond_maturity_date,
                                  self.bond_df.reset_index().market_yield,
                                  self.bond_df.reset_index().market_price,
                                  self.bond_df.reset_index().bond_accrued_interest],
                                 axis=1).rename(columns={
                                'bond_maturity_date':'maturity_date',
                                'bond_cusip':'cusip',
                                'bond_accrued_interest':'accrued_interest'})
        
        # I think this might work.                             
        combined_market_data=note_market_df.merge(bond_market_df,how='outer')
        # sort the index by maturity date; this will interleave the note and
        # bond column data in the cashflow by ascending maturity date. 
        combined_market_data.set_index('maturity_date',inplace=True) 
        combined_market_data.sort_index(inplace=True)   
        self.market_df=combined_market_data                       
        
        cashflow_df=pd.concat([note_cashflow_df,bond_cashflow_df],axis=1)
        self.cashflow_df=cashflow_df[
            pd.Index(combined_market_data['CUSIP Index'].astype(str))]
        
        maturity_df=pd.concat([note_maturity_df,bond_maturity_df],axis=1)
        self.maturity_df=maturity_df[
            pd.Index(combined_market_data['CUSIP Index'].astype(str))]
        
        
        
        return
    
    # Make a method to do the standard treatment: Remove on the run, first off
    # the run, all bills, all notes/bonds with less than 3 months to maturity
    # (get rid of 2 most recent issues of 2,3,5,7,10,20,30 year tenors)
    # By default, the statement of public debt does not include newest runs
    def standard_treatment(self):
        
        return
    
    def get_on_the_runs(self,
                        write_path='/Users/jeff/Desktop/finance/data/bonds',
                        write_to_file=False):
        # A method to scrape information for on-the-run securities, which are
        # not in the statement of the public debt.
        
        otrs=['01m','03m','06m','01y','02y','03y','05y','07y','10y','20y','30y']
        
        base_url='https://www.marketwatch.com/investing/bond/'
        preamble='tmubmusd'
        suffix='?countrycode=bx'
        
         # Ignore SSL Certificate errors
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Set up arrays for the data we need:
        y=np.zeros(len(otrs))
        price=np.zeros(len(otrs))
        coupon=np.zeros(len(otrs))
        mat=[]
        
        tnow=pd.to_datetime('today').now()
        
        for counter,otr in enumerate(otrs):
            url=base_url+preamble+otr+suffix  
            
            # Use try/except block to skip past possible errors
            try:
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                webpage = urlopen(req).read()
                soup=BeautifulSoup(webpage, 'html5lib')
                # get the yield, in %
                y[counter]=float(soup.find('td',{"class": "table__cell u-semi"}
                                              ).get_text().replace('%',''))
                coupon[counter]=float(soup.select('.kv__item .primary'
                                        )[6].string.replace('%',''))
                mat.append(pd.to_datetime(
                                soup.select('.kv__item .primary')[7].string))
                # try to get price; this command should get everything out of the 
                # table
                #soup.select('.kv__item .primary')
                p_str=soup.select('.kv__item .primary')[3].string.rsplit()
                if counter<3:
                    price[counter]=float(p_str[0].rsplit('/')[0])/float(
                                        p_str[0].rsplit('/')[1])
                else:
                    price[counter]=(float(p_str[0])+
                              float(p_str[1].rsplit('/')[0])/
                              float(p_str[1].rsplit('/')[1]))
             
                print("Successfully scraped on the run security: " +  str(otr))
                # I just want to make it wait a short amount of time to 
                # minimize the chance that Marketwatch rejects my scraping.
                time.sleep(1)
            except:
                print("Failed to scrape on the run security: "+ str(otr))
            
        # make data series out of this:
        y=pd.Series(data=y,index=pd.DatetimeIndex(mat),
                        name='yield')  
        y.index.rename('Maturity',inplace=True) 
        # Probably not necessary to record the price, but doing so anyway for 
        # completeness
        price=pd.Series(data=price,
                            index=pd.DatetimeIndex(mat),
                            name='price')
        price.index.rename('Maturity',inplace=True) 
        coupon=pd.Series(data=coupon,
                             index=pd.DatetimeIndex(pd.to_datetime(mat)),
                             name='coupon')
        coupon.index.rename('Maturity')
    
    
        otrs_df=pd.DataFrame(data={'market_yield':y.values,
                                'market_price':price.values,
                                'coupon':coupon.values},
                          index=pd.DatetimeIndex(mat))
            
        
        try:
                # path=write_path+tnow.strftime("/%Y/%m/%d/")
                # os.makedirs(path, exist_ok=True)
                # tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # otrs_df.to_csv(path
                #                 + 'us_treasury_otrs'
                #                 + tnow_str+'.csv')
                
            write_dataframe_to_file(write_to_file=write_to_file,
                                        df=otrs_df,
                    filename='us_treasury_otrs')
            print('Data successfully printed to file.')
        except:
            print('Something bad happened, and your plot did not save.')
        
        return otrs_df
    
    def plot_notes_and_bonds(self,ctds=[],
                        plot_otrs=False,
                        write_path='/Users/jeff/Desktop/finance/data/bonds',
                        write_to_file=False):
        
        # Note: it would be better to use the last scrape time as the label 
        # instead of generating at plot time.
        tnow=pd.to_datetime('today').now()
        #tstr=tnow.strftime("%Y-%m-%d %H:%M")
        tstr=tnow.strftime("%Y-%b-%d %H:%M")
        
        plt.figure(figsize=(18, 6));
        plt.title('US Note and Bond Yields as of: '+tstr)
        plt.plot(pd.to_datetime(self.note_df.note_maturity_date),
                 self.note_df.market_yield,'.',markersize=2,label='Notes')
        plt.plot(pd.to_datetime(self.bond_df.bond_maturity_date),
                 self.bond_df.market_yield,
                     '.',markersize=2,label='Bonds')
        plt.xlim(tnow,pd.to_datetime(self.bond_df.bond_maturity_date[
                self.bond_df.bond_maturity_date.index[-1]]))
        plt.xlabel('Maturity Date')
        plt.ylabel('Yield (%)')
        #plt.ylim()
        # Plot the otrs, if the option is selected.
        if plot_otrs:
            otrs_df=self.get_on_the_runs()
            plt.plot(otrs_df.market_yield,'kd',markersize=3,
                     label='OTR Yields')
            plt.xlim(tnow,otrs_df.index[-1])
        # Put the CTD section here; check if ctds list is empty
        if not not ctds:
            # For now, we have to assume the user puts the ctds in ascending
            # order in the list, but this is not guaranteed
            label_array=['TU','Z3N','FV','TY','TN','US','TWE','UB']
            for count,ctd in enumerate(ctds):
                if ctd in self.note_df.note_cusip.values:
                    plt.plot(pd.to_datetime(self.note_df.note_maturity_date[
                        self.note_df.note_cusip==ctd]),
                        self.note_df.market_yield[
                            self.note_df.note_cusip==ctd],'*',
                        label=label_array[count])
                elif ctd in self.bond_df.bond_cusip.values:
                    plt.plot(pd.to_datetime(self.bond_df.bond_maturity_date[
                        self.bond_df.bond_cusip==ctd]),
                        self.bond_df.market_yield[
                            self.bond_df.bond_cusip==ctd],'*',
                        label=label_array[count])
        
        
        plt.legend(loc='best')
        plt.tight_layout()

        # plt.savefig('/Users/jeff/Desktop/finance/data/bonds/'+'ytm_curve'
        #             +tnow.strftime("%Y_%m_%d_%H_%M")+'.png')
        
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d/")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # We do not need the whole file.
                plt.savefig(path
                    + 'us_treasury_ytm_curve'
                    + tnow_str+'.png')
                print('Data successfully printed to file.')
            except:
                print('Something bad happened, and your plot did not save.')

        
        return
    
    def plot_notes_and_bonds_outstanding(self):
        # small test method for producing the type of plots seen in Burghardt
        # treasury bond basis, page 30.
        # This should probably done for each note/bond contract?
        note_df=self.note_df.copy(deep=True)
        note_df=note_df.merge(self.strips_df[['security_class2_desc',
            'portion_unstripped_amt','portion_stripped_amt']],
            how='left',left_on='note_cusip',right_on='security_class2_desc')
        
        bond_df=self.bond_df.copy(deep=True)
        bond_df=bond_df.merge(self.strips_df[['security_class2_desc',
            'portion_unstripped_amt','portion_stripped_amt']],
            how='left',left_on='bond_cusip',
            right_on='security_class2_desc')
        
        # What about stripped tips??
        tips_df=self.tips_df.copy(deep=True)
        tips_df=tips_df.merge(self.strips_df[['security_class2_desc',
            'portion_unstripped_amt','portion_stripped_amt']],
            how='left',left_on='tips_cusip',right_on='security_class2_desc')
        
        # Amounts are typically listed in millions, so scale appropriately
        fig, ax1 = plt.subplots(figsize=(18, 6))
        ax1.bar(note_df.note_maturity_date, note_df.portion_unstripped_amt,
                width=10,label='Unstripped Notes',color='darkgray')
        ax1.bar(note_df.note_maturity_date, note_df.portion_stripped_amt,
                bottom=note_df.portion_unstripped_amt,
                width=10,label='Stripped Notes',color='lightgray')
        # the stripped/unstripped amounts don't add properly for bonds, because
        # of the introduction of 20 year bond; how can I fix this?
        ax1.bar(bond_df.bond_maturity_date, bond_df.portion_unstripped_amt,
                width=10,label='Unstripped Bonds',color='darkgray',hatch='+')
        ax1.bar(bond_df.bond_maturity_date, bond_df.portion_stripped_amt,
                bottom=bond_df.portion_unstripped_amt,
                width=10,label='Stripped Bonds',color='lightgray',hatch='/')
        ax1.set_xlabel('Maturity Date')
        ax1.set_ylabel('Amount Outstanding (millions)',color='darkgray')
        ax1.tick_params(axis ='y', labelcolor = 'darkgray') 
        # the twin, for yields
        ax2 = ax1.twinx()
        ax2.set_ylabel('Yield (%)')
        
        # lns = plot_1 + plot_2
        # labels = [l.get_label() for l in lns]
        # plt.legend(lns, labels, loc=0)
        plt.tight_layout()
        # return the figure?
        return
    
    def plot_tips(self,plot_otrs=False,
                        write_path='/Users/jeff/Desktop/finance/data/bonds',
                        write_to_file=False):
        
        
        tnow=pd.to_datetime('today').now()
        #tstr=tnow.strftime("%Y-%m-%d %H:%M")
        tstr=tnow.strftime("%Y-%b-%d %H:%M")
        
        plt.figure(figsize=(18, 6));
        plt.title('US TIPS Yields as of: '+tstr)
        plt.plot(pd.to_datetime(self.tips_df.tips_maturity_date),
                 self.tips_df.market_yield,'.',markersize=4,label='TIPS')
        plt.xlim(tnow,pd.to_datetime(self.tips_df.tips_maturity_date[
                self.tips_df.tips_maturity_date.index[-1]]))
        plt.xlabel('Maturity Date')
        plt.ylabel('Real Yield (%)')
        # Plot the otrs, if the option is selected.
        # Need to adapt get_on_the_runs() for tips!
        if plot_otrs:
            # otrs_df=self.get_on_the_runs()
            # plt.plot(otrs_df.market_yield,'kd',markersize=3,
            #          label='OTR Yields')
            # plt.xlim(tnow,otrs_df.index[-1])
            print('Not implemented yet.')
        
        plt.legend(loc='best')
        plt.tight_layout()
        
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d/")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # We do not need the whole file.
                plt.savefig(path
                    + 'us_treasury_tips_curve'
                    + tnow_str+'.png')
                print('Data successfully printed to file.')
            except:
                print('Something bad happened, and your plot did not save.')    
        return
# Is there a treasury futures yield curve? I think there should be...
# In fact, maybe it is a subclass of USYieldCurve?
# Because we will need to be able to get the full list of US treasuries
# What else will we need?
# Get prices for all futures contracts!
# get_cfs(), conversion factors from CME!
# calculate_cfs()
# UPDATE: These conversion factors can be calculated from formulas given by
# CME
# Quickly calculate IRRs! (need CTD bond price and corresponding future)
# Make a yield curve based on futures prices
#class USTreasuryFutures(USYieldCurve): 
# Possible methods:
# All of the methods from USYieldCurve and also
# Get ctd info from CME; this may be another instance attribute?
# Or, I can just calculate for myself!
# Calculate implied repo rate
# Futures term structure, so all contracts?
# probability of ctd switching?
# What are other, possible attributes?
# This class demonstrates how to use a factory method in a derived class
# that reuses a factory method from the base class
# New attributes: 
class USTreasuryFutures(USYieldCurve):
    def __init__(self,
                 issuer,
                 cashflow_df,
                 maturity_df,
                 market_df,
                 public_debt,
                 bill_df,
                 note_df,
                 bond_df,
                 strips_df,
                 frn_df,
                 tips_df,
                 futures_df):
       
        # Some of these attributes are not strictly needed, but maybe they
        # could be useful in the future.
        # Also, I want this derived class to have all the same functionality
        # as the base class
        # 2022 june 18: I was so sure I had figured this out and simplified
        # everything, but this is not working. I have made adjustments
        # super(USTreasuryFutures,self).__init__(issuer,
        #                                       cashflow_df,
        #                                       maturity_df,
        #                                       market_df,
        #                                       public_debt,
        #                                       bill_df,
        #                                       note_df,
        #                                       bond_df,
        #                                       strips_df,
        #                                       frn_df,
        #                                       tips_df) 
        
        # Use the original class method to fill these in
        self.issuer=issuer
        self.cashflow_df=cashflow_df
        self.maturity_df=maturity_df
        self.market_df=market_df
        self.public_debt=public_debt
        self.bill_df=bill_df
        self.note_df=note_df
        self.bond_df=bond_df
        self.strips_df=strips_df
        self.frn_df=frn_df
        self.tips_df=tips_df
       
        # Additional attributes can go here if needed
        # Here is a possible attribute, for the futures dataframe:
        self.futures_df=futures_df
        # An attribute for the deliverable basket?
    
    @classmethod
    def get_treasuries_details(cls):
        
        # Get all of the attributes needed for a USYieldCurve object 
        # 3 June 2022: get_us_public_debt will be deprecated  
        # Why does super not seem to work here? I thought I had figured this 
        # out months ago
        
        # treasuries = super().get_us_public_debt()     
        treasuries = USYieldCurve.get_mspd_with_api()
        
        # Include any other attributes that are needed below, like setting up
        # a dataframe for a futures dataframe?
        futures_df=order_delivery_months()
        
        # Since we have an instance of the base class, USYieldCurve, can we
        # use that to establish the delivery basket for each treasury future?
        delivery_basket=pd.DataFrame()
        for row in futures_df.iloc:
            # Here are all the conditions for specifying the delivery basket
            # for each futures contract type. Make sure to drop reopenings.
            # How can I do this?
            if row.cme_code=='tu':
                tu_basket=treasuries.note_df[
                    ((treasuries.note_df.note_maturity_date
                     -treasuries.note_df.note_issue_date
                     )/np.timedelta64(1,'D')<=5.25*365.24)&((
                    treasuries.note_df.note_maturity_date
                    -row.delivery_month_end_date
                    )/np.timedelta64(1,'D')<=2*365.24)&((
                    treasuries.note_df.note_maturity_date
                    -row.cf_calc_date)/np.timedelta64(1,'D')>=1.75*365.24)]
                tu_basket['contract_code']=row.name
                delivery_basket=pd.concat([delivery_basket,tu_basket],axis=0)
            elif row.cme_code=='z3n':
                # z3n_basket=treasuries.note_df[
                #     ((treasuries.note_df.note_maturity_date
                #       -treasuries.note_df.note_issue_date
                #       )/np.timedelta64(1,'D')<=7*365.24)&((
                #     treasuries.note_df.note_maturity_date
                #     -row.delivery_month_end_date
                #     )/np.timedelta64(1,'D')<=3*365.24)&((
                #     treasuries.note_df.note_maturity_date
                #     -row.cf_calc_date)/np.timedelta64(1,'D')>=2.75*365.24)]
                z3n_basket=treasuries.note_df[
                    (year_delta(treasuries.note_df.note_issue_date,
                      treasuries.note_df.note_maturity_date
                      )<=7)&((
                    treasuries.note_df.note_maturity_date
                    -row.delivery_month_end_date
                    )/np.timedelta64(1,'D')<=3*365.24)&((
                    treasuries.note_df.note_maturity_date
                    -row.cf_calc_date)/np.timedelta64(1,'D')>=2.75*365.24)]
                z3n_basket['contract_code']=row.name
                delivery_basket=pd.concat([delivery_basket,z3n_basket],axis=0)
            elif row.cme_code=='fv':
                fv_basket=treasuries.note_df[
                    ((treasuries.note_df.note_maturity_date
                     -treasuries.note_df.note_issue_date
                     )/np.timedelta64(1,'D')<=5.25*365.24)&((
                    treasuries.note_df.note_maturity_date
                    -row.cf_calc_date)/np.timedelta64(1,'D')>=(4+1/6.)*365.24)]
                fv_basket['contract_code']=row.name
                delivery_basket=pd.concat([delivery_basket,fv_basket],axis=0)
            elif row.cme_code=='ty':
                ty_basket=treasuries.note_df[
                    ((treasuries.note_df.note_maturity_date
                    -row.cf_calc_date)/np.timedelta64(1,'D')>=6.5*365.24)
                    &((treasuries.note_df.note_maturity_date
                    -row.cf_calc_date)/np.timedelta64(1,'D')<=10.*365.24)]
                ty_basket['contract_code']=row.name
                delivery_basket=pd.concat([delivery_basket,ty_basket],axis=0)
            elif row.cme_code=='us':
                us_basket=treasuries.bond_df[
                    ((treasuries.bond_df.bond_maturity_date
                    -row.cf_calc_date)/np.timedelta64(1,'D')>=15.*365.24)
                    &((treasuries.bond_df.bond_maturity_date
                    -row.cf_calc_date)/np.timedelta64(1,'D')<25*365.24)]
                us_basket['contract_code']=row.name
                delivery_basket=pd.concat([delivery_basket,us_basket],axis=0)
            elif row.cme_code=='ub':
                ub_basket=treasuries.bond_df[
                    ((treasuries.bond_df.bond_maturity_date
                    -row.cf_calc_date)/np.timedelta64(1,'D')>=25.*365.24)]
                ub_basket['contract_code']=row.name
                delivery_basket=pd.concat([delivery_basket,ub_basket],axis=0)
        
        # How to organize this data?
        # how about concatenating futures_df to the right of the above,
        # duplicating the repeated data? Maybe groupby contract symbol
        # when getting the implied repo rate
            
        # or a left join?
        # This used to be delivery month dataframe, but I changed it to
        # futures_df
        futures_df=pd.merge(delivery_basket,futures_df,
                                     left_on='contract_code',right_index=True)
         
        # convenient to make a few columns here for the futures_df:
        futures_df['basis']=np.nan
        futures_df['irr']=np.nan
        futures_df['gross_basis']=np.nan
        futures_df['market_yield']=np.nan
        futures_df['market_price']=np.nan
        futures_df['settlement_price']=np.nan
        futures_df['intra_day_price']=np.nan
        futures_df['open_interest']=np.nan
        futures_df['mac_dur']=np.nan
        futures_df['mod_dur']=np.nan
        # Boolean column for whether a bond is cheapest to deliver
        futures_df['is_ctd']=False
        futures_df['futures_scrape_time']=pd.NaT
        futures_df['bond_scrape_time']=pd.NaT
        # Need to make one for cusip?
        # Also, make some useful columns for clean and dirty price
        futures_df['treasury_clean_price']=np.nan
        futures_df['treasury_dirty_price']=np.nan
        
            
            
        # put all the attributes together, correctly!
        # result=cls(treasuries.issuer,
        #            treasuries.cashflow_df,
        #            treasuries.maturity_df,
        #            treasuries.market_df,
        #            treasuries.public_debt,
        #            treasuries.bill_df,
        #            treasuries.note_df,
        #            treasuries.bond_df,
        #            treasuries.strips_df,
        #            treasuries.frn_df,
        #            treasuries.tips_df,
        #            futures_df)
        
        return cls(treasuries.issuer,
                   treasuries.cashflow_df,
                   treasuries.maturity_df,
                   treasuries.market_df,
                   treasuries.public_debt,
                   treasuries.bill_df,
                   treasuries.note_df,
                   treasuries.bond_df,
                   treasuries.strips_df,
                   treasuries.frn_df,
                   treasuries.tips_df,
                   futures_df)
        
    # Calculate conversion factor for all contracts; delivery basket is 
    # already constructed
    # This should also be its own function!
    def calculate_conversion_factor(self):
        
        tnow=pd.to_datetime('today').now()
        
        # 19 June 2022:
        # possible to sidestep problems below by creating new columns, but
        # I don't know how I feel about this approach.
        self.futures_df['coupon']=pd.concat(
            [self.futures_df['note_coupon'].dropna(),
             self.futures_df['bond_coupon'].dropna()])
        # Same thing for issue date
        self.futures_df['issue_date']=pd.concat(
            [self.futures_df['note_issue_date'].dropna(),
             self.futures_df['bond_issue_date'].dropna()])
        # Same thing for maturity_date
        self.futures_df['maturity_date']=pd.concat(
            [self.futures_df['note_maturity_date'].dropna(),
             self.futures_df['bond_maturity_date'].dropna()])
        # Also needed for cusip
        self.futures_df['cusip']=pd.concat(
            [self.futures_df['note_cusip'].dropna(),
             self.futures_df['bond_cusip'].dropna()])
        # Also good for note and bond payments
        self.futures_df['first_payment']=pd.concat(
            [self.futures_df['note_first_payment'].dropna(),
             self.futures_df['bond_first_payment'].dropna()])
        # Also good for note and bond payments
        self.futures_df['second_payment']=pd.concat(
            [self.futures_df['note_second_payment'].dropna(),
             self.futures_df['bond_second_payment'].dropna()])
        
        # calculations for five year note; extend this for all the other
        # maturities! Also, resolve note/bond names for columns
        # There are also problems with duplicate cusips, I think, this should
        # be resolved earlier!
        # n is the number of whole years from the first day of the delivery 
        # month to the maturity (or call) date of the bond or note
        n=np.floor((pd.to_datetime(self.futures_df['maturity_date'])
                -self.futures_df.cf_calc_date)/np.timedelta64(1,'D')/365.24)
        
        # The number of whole months between n and the maturity (or call) date 
        # rounded down to the nearest quarter for the 10-Year U.S. Treasury 
        # Note and 30-Year U.S. Treasury Bond futures contracts, and to the 
        # nearest month for the 2-Year, 3-Year and 5-Year U.S. Treasury Note 
        # futures contracts.  
        # Calculation for TY, T bond, and ultra bond
        
        long_contract_condition=((self.futures_df.cme_code!='tu')
                    &(self.futures_df.cme_code!='z3n')
                    &(self.futures_df.cme_code!='fv'))
        short_contract_condition=((self.futures_df.cme_code!='ty')
                    &(self.futures_df.cme_code!='us')
                    &(self.futures_df.cme_code!='ub'))
        
        z=3*np.floor(4*((pd.to_datetime(self.futures_df['maturity_date'])
                -self.futures_df.cf_calc_date)/np.timedelta64(1,'D')/365.24-n))
        
        # Same calculation for 2-year, 3 year, 5 year Treasury Note Futures:
        z.loc[short_contract_condition]=np.floor(
            12*((pd.to_datetime(self.futures_df['maturity_date'].loc[
                    short_contract_condition])
                -self.futures_df.cf_calc_date.loc[
                    short_contract_condition]
                )/np.timedelta64(1,'D')/365.24-
                n.loc[short_contract_condition]))
        
        # v = { z……if z < 7 or { 3……if z ≥ 7 (for US and TY)
        v=z*(z<7.0)+(3.0)*(z>=7)
        # or { ( z – 6 )……if z ≥ 7 (for TU, 3YR, and FV)
        v.loc[short_contract_condition]=(
                    z.loc[short_contract_condition]*(
                        z.loc[short_contract_condition]<7.0)
                    +(z.loc[short_contract_condition]-6.0)*(
                        z.loc[short_contract_condition]>=7))
        a=1/1.03**(v/6.0)
        b=(self.futures_df['coupon']/200)*(6-v)/6
        c=(1/1.03**(2*n))*(z<7)+(1/1.03**(2*n+1))*(z>=7)
        d=self.futures_df['coupon']/100/0.06*(1-c)
        # conversion factor must be rounded to 4 decimal places
        # I get a strange error if I do not force the cf to be float; Like 
        # there is an integer somewhere; I think this comes from the coupon
        # column. I may need to look into this, could be a source of trouble
        # later.
        cf=(a*((self.futures_df['coupon']/200)+c+d)-b).astype(float).round(4)
        
        self.futures_df['conversion_factor']=cf
        
        return cf
    
    # one method to get a bond cash prices and futures prices for all contracts
    # for a given contract code?
    # For default setting, pick the tbond contract.
    # 23 June 2022:
    # May have to produce mac_dur, mod_dur and other columns!
    def get_irr(self,futures_df_row,irr_date='last_delivery_date'):
        
        # since we are only looking at one row here, the cusip_row is given
        # by:
        cusip_row=futures_df_row.name
        
        # get the note/bond details for one cusip only. This must be a cusip
        # in the basket!
        
        # The irr calculation:
            
        # ((futures_price*cf+Ad)-(b+As)+IC)/(
        #   (b+As)*yf-sum(IC)*yf)
        # b - bond price
        # As - accrued interest on settlement date
        # Ad - accrued interest on delivery date
        # IC - interim coupons
        # yf - year fraction to delivery date, or dte/365, dte/360?
        # b - bond price 
        # cf - conversion factor

        # Cost of Carry = (Ad+IC-As)-b*yf*repo_rate
        # From Choudry:
        # irr = (dirty_futures_price*cf-dirty_price)/dirty_price/yf * 100
        
        cf=futures_df_row.conversion_factor
        
        # calculate accrued interest before scraping market watch; the price 
        # data will be the most time sensitive data.
        # In order to work with the function, it has to be a pandas series
        # You have to add one day for the calculation date, because it takes
        # 1 day for the bond to settle.
        # 7 August 2022:
        # Bloomberg does not use 1 day for settlement, so I have dropped it
        # for now
        ai=calculate_accrued_interest(
                            pd.Series(futures_df_row['first_payment']),
                            pd.Series(futures_df_row['second_payment']),
                            calculation_date=pd.to_datetime('today').now()
                            +pd.DateOffset(days=0),
                            interest_rate=futures_df_row['coupon'])
        # just take the first element of the pandas series.
        ai=ai[0]
        
        # Accrued interest on delivery date:
        # First step:
        # reorder payment dates to coincide with the delivery date
        first_payment,second_payment=reorder_interest_payments(
            pd.Series(futures_df_row['first_payment']),
            pd.Series(futures_df_row['second_payment']),
            calculation_date=futures_df_row[irr_date])
        
        ad=calculate_accrued_interest(first_payment,second_payment,
                        pd.Series(futures_df_row['coupon']),
                        calculation_date=futures_df_row[irr_date])
        # just take the first element of the pandas series.
        ad=ad[0]
        
        # Interim coupons between settlement and delivery.
        # There are only up to 4 quarterly contract dates at any given time for
        # US Treasury futures,so I think that means there can be at most 2 
        # iterim coupons.
        # 1 August 2022: I think this is not correct; may need the reordered
        # payments??
        # ic=(futures_df_row['coupon']/2*(
        #     (futures_df_row.first_payment<futures_df_row[irr_date])&
        #     ((futures_df_row.first_payment+pd.DateOffset(months=6))
        #      >futures_df_row[irr_date]))
        #     +futures_df_row['coupon']*((
        #     futures_df_row.second_payment<futures_df_row[irr_date]))
        #     &((futures_df_row.first_payment+pd.DateOffset(months=6))
        #      >futures_df_row[irr_date]))
        
        ic_first=futures_df_row['coupon']/2*(
            futures_df_row.first_payment<futures_df_row[irr_date])
        ic_second=futures_df_row['coupon']/2*(
            futures_df_row.second_payment<futures_df_row[irr_date])
    
        first_payment_days=(futures_df_row[irr_date]
                        -futures_df_row.first_payment)/np.timedelta64(1,'D')
        second_payment_days=(futures_df_row[irr_date]
                        -futures_df_row.second_payment)/np.timedelta64(1,'D')
        delivery_days=(futures_df_row[irr_date]
                       -pd.to_datetime('today').now())/np.timedelta64(1,'D')

        # Should probably calculate price somewhere here, because the price
        # quote from marketwatch is not reliable
        bond_scrape_time=pd.to_datetime('today').now()
        y_pct,price_quote,coupon,maturity=marketwatch_bond_scraper(
                        futures_df_row.cusip
                        +isin_checksum(self.issuer,futures_df_row.cusip))
        
        futures_df_row['market_yield']=y_pct
        # Really need to calculate bond price here, instead of relying on the
        # quote. See earlier examples
        # fact is needed here to do the Macaulay/modified duration calculation
        fact=self.maturity_df[str(cusip_row)
                                ].dropna().values*self.cashflow_df[
                str(cusip_row)].dropna().values
        # 2023-08-13: Realization: This calculation should be done in the 
        # YieldCurve class, possibly as a method.
        # I think that I make this calculation many times in several places;  
        # just do it once! Same for calculation of accrued interest, needed as
        # an input for bond pricing.
        d=1/(1+futures_df_row['market_yield']/200)**(
                    2*self.maturity_df[str(cusip_row)].dropna().values)
        # you need to subtract accrued interest to get the clean price.
        # 2023-08-23:
        # Remember, need to implement the change here where we substract the
        # ai from the first discounted cashflow!
        ai_correction=np.zeros(
            len(self.cashflow_df[str(cusip_row)].dropna().values))
        ai_correction[0]=ai
        b=np.sum((self.cashflow_df[str(cusip_row)].dropna().values
                  -ai_correction)*d)
        # 2023-08-23:
        # This was the original code, in case I need to revert:
        # b=np.sum((self.cashflow_df[str(cusip_row)].dropna().values)*d)-ai
        
        futures_df_row['market_price']=b
        # Need 2 columns to discriminate between clean and dirty price!
        futures_df_row['treasury_clean_price']=b
        futures_df_row['treasury_dirty_price']=b+ai
        
        # Calculate durations here.
        # futures_df_row['mac_dur']=np.sum(fact*d)/(b+ai)
        futures_df_row['mac_dur']=np.sum(fact*d)/(b)
        
        # Include also Modified duration!
        futures_df_row['mod_dur']=futures_df_row['mac_dur']/(
            1+futures_df_row['market_yield']/200.)

        # get the futures price for the contract corresponding to the 
        # note/bond above
        futures_scrape_time=pd.to_datetime('today').now()
        settle_price,intra_day_price,oi,_=marketwatch_futures_scraper(
            futures_df_row.contract_code)
        # 
        futures_df_row['futures_scrape_time']=futures_scrape_time
        futures_df_row['bond_scrape_time']=bond_scrape_time
        
        # Store this information.
        futures_df_row['settlement_price']=settle_price
        futures_df_row['intra_day_price']=intra_day_price
        futures_df_row['open_interest']=oi
        
        # Use 360 or actual/365?
        # 25 June 2022:
        # I am going to go with 360 for now, but may revise later.
        # Bloomberg and Burghardt use 360, so that is probably correct.
        # yf=(futures_df_row[irr_date]
        #     -futures_scrape_time)/np.timedelta64(1,'D')/360.
        
        # Calculate Implied Repo Rate, and place in dataframe row.
        # I think I do not need the "sum over ic" that I see in:
        # https://www.factset.com/hubfs/Resources%20Section/White%20Papers/Bond%20Future%20White%20Paper.pdf
        # because of how I calculate the first and second payments
        # futures_df_row['irr']=100*((intra_day_price*cf+ad)-(b+ai)+ic)/(
        #     (b+ai)*yf-ic*yf)
        
        # I think I do not need the "sum over ic" that I see in:
        # https://www.factset.com/hubfs/Resources%20Section/White%20Papers/Bond%20Future%20White%20Paper.pdf
        # because of how I calculate the first and second payments
        futures_df_row['irr']=100*(intra_day_price*cf+ad+ic_first+ic_second
                 -(b+ai))*360./((b+ai)*delivery_days
                    -ic_first*first_payment_days
                    -ic_second*second_payment_days)
        
        # Calculate the basis!
        futures_df_row['gross_basis']=(futures_df_row['treasury_clean_price']
                                       -futures_df_row['conversion_factor'
                                        ]*futures_df_row['intra_day_price'])
        # calculate the basis net of carry:
        
        # Calculate the carry?
        # or a column for coupon income?
        
        return futures_df_row
    
    def find_ctd(self,futures_code,ctd_date='last_delivery_date'):
        
        subframe=self.futures_df.loc[
                        self.futures_df.contract_code==futures_code]
        
        # I think you can get away with dropping cusip duplicates and only
        # keeping the first; this should be the original and not a reopening
        for index in (subframe.drop_duplicates(subset='cusip')).index:   
            # remove duplicate cusips!
            subframe.loc[index]=self.get_irr(subframe.loc[index],
                                             irr_date=ctd_date)
            
        subframe.is_ctd.loc[subframe.irr==subframe.irr.max()]=True
        
        self.futures_df.loc[self.futures_df.contract_code==futures_code
                                                                ]=subframe
        # Maybe just call the closest_bill method here?
        subframe=self.get_closest_bill(futures_code,comparison_date=ctd_date)
        # put the closest bill information into the portion of the dataframe
        # apportioned to a given futures code
        # self.futures_df.loc[self.futures_df.contract_code==futures_code
        #                                                         ]=subframe
        
        # There must be an easier way, but here is how I append the columns of
        # the subframe:
        future_df_columns=self.futures_df.columns.to_list()
        subframe_columns=subframe.columns.to_list()
        if set(subframe_columns).issubset(set(future_df_columns)):
            self.futures_df.loc[self.futures_df.contract_code==futures_code
                                                                ]=subframe
        else:
            # This is actually the leftover columns, the columns in the 
            # closest bill subframe that are not contained in future_df.
            disjoint_columns=list(set(subframe_columns)-set(future_df_columns))
            for col in disjoint_columns:
                self.futures_df[col]=np.nan
            self.futures_df.loc[self.futures_df.contract_code==futures_code
                                                                ]=subframe
        
        return subframe
    
    def get_closest_bill(self,futures_code,
                         comparison_date='last_delivery_date'):
        # should this assume that bills are already scraped?
        subframe=self.futures_df.loc[
                        self.futures_df.contract_code==futures_code]
        # it might need to be the nearest maturing bill that has not yet 
        # matured
        # What if the date is arbitrary and not a column? this needs to be 
        # handled.
        tdiff=abs(subframe[comparison_date].iloc[0]
                  -self.bill_df.bill_maturity_date.loc[
                      self.bill_df.bill_maturity_date
                      >subframe[comparison_date].iloc[0]]).sort_values()
        # Get a sorted list of the bill cusips
        cusip_list=self.bill_df.bill_cusip.loc[tdiff.index]
        # keep track of when the bill yield was scraped; should be close in
        # time to when the futures and the ctd note/bond was scraped
        subframe['bill_scrape_time']=pd.to_datetime('today').now()
      
        # if there are multiple cusips, find the cheapest one (highest yield)
        # In principle, it is possible to have different yields on the same
        # date, but to make it easier this will be neglected. Just find the
        # yield for the closest tbill to the comparison date as possible.
        y_arr=np.zeros(len(cusip_list))
        maturity=[]
        # What if there are no details? Scrape the next nearest one
        # Maybe use a while loop for this?
        for no,bill_cusip in enumerate(cusip_list):
            y_arr[no],price_quote,coupon,tbill_mat=(
                    marketwatch_bond_scraper(bill_cusip
                        +isin_checksum(self.issuer,bill_cusip)))
            maturity.append(tbill_mat)
            # if we find a non-nan yield, we are done scraping
            if ~np.isnan(y_arr[no]):
                yclosest=y_arr[no] 
                break
        
        subframe['closest_bill']=cusip_list[no]
        subframe['closest_bill_yield']=yclosest
        # should be okay to take the first element; the dates should be 
        # constructed to all be the same.
        subframe['closest_bill_maturity']=maturity[no]
        subframe['closest_bill_tdelta']=(subframe['closest_bill_maturity']
                                        -subframe[comparison_date])
    
        # calculate spread to irr??
        if 'irr' in subframe.columns:
            subframe['irr_minus_closest_bill_yield']=(subframe['irr']
                        -subframe['closest_bill_yield'])
        else:
            subframe['irr_minus_closest_bill_yield']=np.nan
                   
        return subframe
    
    # Input the 1,3,6,12 month SOFR Term rates.
    def get_spread_to_sofr(self,term_sofr=[5,5,5,5,5],
                         comparison_date='last_delivery_date'):
        
        fp=np.array(term_sofr)
        # In case I just want to keep it simple, number of days until end of
        # each term:
        xp=np.array([0,30,91,182,365])
        
        # Line of code in case we use cubic spline instead:
        cs=CubicSpline(xp,fp)
        
        tnow=pd.to_datetime('today').now()
        
        time_array=np.array([pd.DateOffset(months=0),
                             pd.DateOffset(months=1),
                             pd.DateOffset(months=3),
                             pd.DateOffset(months=6),
                             pd.DateOffset(months=12)])
        
        sofr_tenors=(tnow+time_array)
        
        # should this assume that bills are already scraped?
        # subframe=self.futures_df.loc[
        #                 self.futures_df.contract_code==futures_code]
        
        time_to_comparison=(self.futures_df[comparison_date]-tnow).dt.days
        
        # self.futures_df['interpolated_sofr']=time_to_comparison.apply(
        #                                     lambda x: np.interp(x,xp,fp))
        
        self.futures_df['interpolated_sofr']=time_to_comparison.apply(
                                            lambda x: cs(x))
        self.futures_df['irr_minus_interp_sofr']=(self.futures_df['irr']
                                        -self.futures_df['interpolated_sofr'])
    
        return
    
    # Useful to increase the display width when outputting the info for pasting
    # pd.set_option('display.width', 250)
    # pd.set_option('display.max_columns', 10)
    def all_ctds(self,ctd_date='last_delivery_date',write_to_file=False):
        
        # Initialize converstion factor, or do it as part of initialization?
        conversion_factor=self.calculate_conversion_factor()
        
        # Get a list of all contracts
        # consider an option where we only look at nearest contract, drop first
        #subset=self.futures_df.cme_code.drop_duplicates(keep='first').tolist()
        all_contracts=self.futures_df.contract_code.unique().tolist()
        
        # option to get spread to interpolated SOFR (simple method)
        # self.get_spread_to_sofr()
        
        for contract in all_contracts:
            print("Finding IRRs and CTD for contract: "+contract)
            # The ctd_frame is just for a single contract
            ctd_frame=self.find_ctd(futures_code=contract,ctd_date=ctd_date)
            
        
        write_dataframe_to_file(write_to_file=write_to_file,
                                    df=self.futures_df,filename='futures_df')
            
        # Show the output of the important columns:
        self.futures_df.loc[self.futures_df.is_ctd==True][
            ['cusip','contract_code','irr','irr_minus_closest_bill_yield',
             'treasury_clean_price','treasury_dirty_price',
             'intra_day_price','gross_basis','open_interest']]
        
        return self.futures_df
    
    def futures_implied_yield(self):
        # This method will be used to calculate the forward yields for the
        # various futures contracts/ctds
        pass
    
    def payoff_diagram(self,futures_code,subset=[]):
        
        subframe=self.futures_df.loc[
                        self.futures_df.contract_code==futures_code]
        
        # In case no subset is defined by the user:
        if not subset:
            subset=[*range(len(subframe.drop_duplicates(subset='cusip')))]
                                
        
        # lower_yield=2.245
        # upper_yield=20
        
        # # The CTD when yields are >6%
        # cusip_row='404'
        # tmax_arr=np.asmatrix(2*tf.maturity_df[str(cusip_row)].dropna().values)
        # cmax_arr=np.asmatrix(tf.cashflow_df[str(cusip_row)].dropna().values)
        # # Array of yields
        # ymax_arr=((subframe.loc[str(cusip_row)]['market_yield']
        #       +np.arange(lower_yield,upper_yield,0.1)))
        
        # ai=(subframe.loc[str(cusip_row)]['treasury_dirty_price']
        #     -subframe.loc[str(cusip_row)]['treasury_clean_price'])
        
        # # The discount array
        # dmax_arr=np.exp(np.asmatrix(np.log(1/(1+ymax_arr/200))).T*tmax_arr)
    
        # # you need to subtract accrued interest to get the clean price
        # bmax=(np.squeeze(np.asarray(dmax_arr*cmax_arr.T)))
        # ctd_price=bmax/subframe.loc[str(cusip_row)]['conversion_factor']
        
        # # original CTD
        # cusip_row='364'
        # tarr=np.asmatrix(2*tf.maturity_df[str(cusip_row)].dropna().values)
        # carr=np.asmatrix(tf.cashflow_df[str(cusip_row)].dropna().values)
        # # Array of yields
        # yarr=((subframe.loc[str(cusip_row)]['market_yield']
        #       +np.arange(lower_yield,upper_yield,0.1)))
        
        # ai=(subframe.loc[str(cusip_row)]['treasury_dirty_price']
        #     -subframe.loc[str(cusip_row)]['treasury_clean_price'])
        
        # # The discount array
        # darr=np.exp(np.asmatrix(np.log(1/(1+yarr/200))).T*tarr)
        # # you need to subtract accrued interest to get the clean price
        # barr=np.squeeze(np.asarray(darr*carr.T))
        # bond_profit=barr-subframe.loc[str(cusip_row)]['treasury_dirty_price']
        # futures_profit=subframe.loc[str(cusip_row)]['conversion_factor']*(
        #     subframe.loc[str(cusip_row)]['intra_day_price']-ctd_price)
        
        # # payoff figure:
        # plt.figure();
        # plt.plot(yarr,(bond_profit+futures_profit)/subframe.loc[str(cusip_row)]['treasury_dirty_price'])
        # plt.title("Payoff of CUSIP: "
        #           +subframe.loc[str(cusip_row)]['cusip']
        #           +" into futures contract: "
        #           +futures_code)
        # plt.xlabel('Yield')
        # plt.ylabel('Payoff per $100 Face Value (%)')
        
        # # exhibit 2.5 from Burghardt
        # plt.figure();plt.plot(ymax_arr,ctd_price);
        # plt.ylabel('Price/CF')
        # plt.xlabel('Yield')
        # plt.plot(yarr,barr/subframe.loc[str(cusip_row)]['conversion_factor'])
        
        lower_yield=-3
        upper_yield=20
        
        # number of interrogation points
        yield_shift=np.arange(lower_yield,upper_yield,0.05)
        n=len(yield_shift)
        # number of bonds in delivery basket
        # if you want to use subset:
        # subset=[0,4,-1]
        # m=len((subframe.drop_duplicates(subset='cusip')).index)
        m=len((subframe.drop_duplicates(subset='cusip')).index[subset])
        
        bprofit=np.zeros((m,n))
        bmatrix=np.zeros((m,n))
        reduced_price=np.zeros((m,n))
       
        
        # for no,cusip_row in enumerate(
        #         (subframe.drop_duplicates(subset='cusip')).index):
        for no,cusip_row in enumerate(
                (subframe.drop_duplicates(subset='cusip')).index[subset]):
            tarr=np.asmatrix(2*self.maturity_df[str(cusip_row)].dropna().values)
            carr=np.asmatrix(self.cashflow_df[str(cusip_row)].dropna().values)
            # Array of yields
            yarr=((subframe.loc[str(cusip_row)]['market_yield']
                  +yield_shift))
            
            ai=(subframe.loc[str(cusip_row)]['treasury_dirty_price']
                -subframe.loc[str(cusip_row)]['treasury_clean_price'])
            
            # The discount array
            darr=np.exp(np.asmatrix(np.log(1/(1+yarr/200))).T*tarr)
        
            # you need to subtract accrued interest to get the clean price
            barr=np.squeeze(np.asarray(darr*carr.T))#-ai
            
            # bond_profit=barr-subframe.loc[str(cusip_row)]['treasury_clean_price']
            bond_profit=barr-subframe.loc[str(cusip_row)]['treasury_dirty_price']
            
            # need also futures profit, which is cf*intra_day_price
            #futures_profit=subframe.loc[str(cusip_row)]['conversion_factor']*subframe.loc[str(cusip_row)]['intra_day_price']
            # print(subframe.loc[str(cusip_row)]['treasury_dirty_price'])
            
            bmatrix[no,:]=barr
            bprofit[no,:]=bond_profit
            reduced_price[no,:]=barr/subframe.loc[str(cusip_row)][
                                                        'conversion_factor']
            print(cusip_row)
            
            
        # in reality I have to calculate the ctd using irr, but this is a 
        # shortcut for now using Burghardt as a guide
        ctd=reduced_price[reduced_price==np.min(reduced_price,axis=0)]
        
        cfs=np.matrix(subframe.drop_duplicates(subset='cusip')[
                                        'conversion_factor'][subset].values)
        
        initial_cost=np.matrix(subframe.drop_duplicates(subset='cusip')[
                                        'treasury_dirty_price'][subset].values)
        
        futures_profit=cfs.T*np.asmatrix(
            subframe.loc[str(cusip_row)]['intra_day_price']-ctd)
        
        total_profit=bprofit+futures_profit
        
        plt.figure(figsize=(9,9));
        plt.title('Basis Optionality for: '+futures_code)
        labels=subframe.drop_duplicates(subset='cusip')['cusip'][subset].to_list()
        # labels=subframe.drop_duplicates(subset='cusip')['cusip'].to_list()
        plt.plot(yarr,100*(bprofit+futures_profit).T/initial_cost,label=labels)
        ylims=plt.gca().get_ylim()
        plt.vlines(subframe.loc[str(cusip_row)]['market_yield'], 
                   ylims[0], ylims[-1],linestyle='dashed',color='red',
                   label='Present Yield = '
                   +str(subframe.loc[str(cusip_row)]['market_yield']))
        plt.ylim(ylims[0],ylims[-1])
        plt.legend(loc='best')
        plt.xlabel('Yield')
        plt.ylabel('Payoff per $100 Face Value (%)')
        plt.tight_layout()
        
        plt.figure(figsize=(9,9));
        plt.plot(yarr,reduced_price.T,label=labels)
        plt.ylabel('Price/CF')
        plt.xlabel('Yield')
        plt.legend(loc='best')
        
        return

class EurodollarFutures(YieldCurve):
    def __init__(self, 
                 issuer,
                 cashflow_df,
                 maturity_df,
                 market_df):
        
        self.issuer='US'
        self.cashflow_df=cashflow_df
        self.maturity_df=maturity_df
        self.market_df=market_df
        
    @classmethod
    def get_eurodollar_futures(cls,
                        write_path='/Users/jeff/Desktop/finance/data/bonds',
                        write_to_file=False):
        # Use Marketwatch to scrape fed funds futures prices.
        # Consider generalizing this approach, because I will need to do
        # something similar for SOFR futures and possibly other rate futures
        
        # Should be a way to go to FRBNY to get last night's fed funds rate 
        # for the t=1 day point, see below.
        
        # First, generate all available Fed Funds futures quotes based on 
        # the current day.
        # There are 36 months of contracts open at any time
        # However, I see marketwatch give contracts out five years or so,
        # what gives?
        tnow=pd.to_datetime('today').now()
        
        tend=tnow-pd.DateOffset(months=1)+pd.DateOffset(years=10)
        
        query_dates=pd.date_range(start=tnow-pd.DateOffset(tnow.day),
                                  end=tend,freq='Q')
        
        
        #futures_months=[1,2,3,4,5,6,7,8,9,10,11,12]
        #futures_codes=['F','G','H','J','K','M','N','Q','U','V','X','Z']
        futures_codes=['f','g','h','j','k','m','n','q','u','v','x','z']
        
        #closest_month=min(futures_months,key=lambda x:(tnow.month-x)>0)

        
        query_string=['ed'+(str(futures_codes[date.month-1])+
                            str(date.year)[2:]) for date in query_dates]
        
        base_url='https://www.marketwatch.com/investing/future/'
        
        # Ignore SSL Certificate errors
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        price=np.zeros(len(query_string))
        
        for j in range(len(query_string)):
            url=base_url+query_string[j]
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            webpage = urlopen(req).read()
            soup=BeautifulSoup(webpage, 'html5lib')
            try:
                price[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                                              ).get_text().replace('$',''))
                print("Succesfully scaped data for Eurodollar contract: " +
                      query_string[j])
            except:
                print("Unable to obtain data for Eurodollar contract: " +
                      query_string[j])
            

        # I assume the yields are quoted on an annualized basis.
        #ff_rate=100-price
        
        # Following Hull for converting ed futures forward price to a 
        # continuous compounding rate
        ed_rate=12*np.log(1+(100-price)/100/12)
        
        
        
        # The query_date array needs to be modified to correspond to the 
        # futures expiration date, which is the last business day of the month?
        settlement_date=pd.date_range(start=tnow,
                                  end=tend+pd.DateOffset(months=3),freq='Q')
        
        t_settlement=(settlement_date-tnow).days/365.24
        
        # This looks too difficult for me to tackle at this time; use the Fred
        # API instead.
        # dff=fred_api(series_id='DFF',
        #              realtime_start=(tnow-pd.DateOffset(years=1)
        #                              ).strftime('%Y-%m-%d'),
        #              realtime_end=tnow.strftime('%Y-%m-%d'))
        
        # Find the annualized volatility in the fed funds rate.
        # sigma_fedfunds_1year=dff.std()
        
        # fill in the most recent overnight rate from FRBNY, maybe scrape this
        # using my fred_api function/class. Insert most recent overnight rate
        # in front of the data, with date=tnow and t_settlement=0
        #frbny_url='https://www.newyorkfed.org/markets/reference-rates/effr'
        #req = Request(frbny_url, headers={'User-Agent': 'Mozilla/5.0'})
        #webpage = urlopen(req).read()
        #soup=BeautifulSoup(webpage, 'html5lib')
        
        
        # Include ff_forward once fred_api is online.
        # Follow Hull here to make convexity adjustment to the futures price
        # and turn it into a forward
        # Insert fedfunds date from yesterday
        ed_rate=np.insert(ed_rate,0,dff[-1]/100)
        # setting this as the value for price is meaningless, but I need a 
        # value to put here; it is essentially the spot price
        price=np.insert(price,0,100-dff[-1])
        # Insert the spot price to the list of futures contracts.
        query_string.insert(0,'spot_price')
        t_settlement=np.insert(t_settlement,0,0)
        settlement_date=settlement_date.insert(0,dff.index[-1])
        # Convexity bias correction?
        #ff_forward=ff_rate-0.5*sigma_fedfunds_1year*T_1*T_2
        
        # Initialize yield array for the loop
        y=np.zeros(len(query_string))
        y[0]=ed_rate[0]
        
        
        for index in range(len(y)-1):
            y[index+1]=(ff_rate[index]*(t_settlement[index+1]-
                        t_settlement[index])+y[index]*t_settlement[index])/(
                        t_settlement[index+1])
        
        
        
        # How to handle cashflow for futures? I left it at 0 for now.
        cashflow_df=0
        # Something like this; maybe a column for each futures contract but
        # it will just be a "diagonal" data frame
        maturity_df=pd.DataFrame(data=t_settlement,index=settlement_date,
                        columns=['t_settlement'])
        # I am using market_df as placeholder for all the data for now
        market_df=pd.DataFrame(data={'ed_contract':query_string,
                                     'ed_price':price,
                                     'ed_rate':ff_rate,
                                     'implied_yield':y,
                                     't_settlement':t_settlement},
                                   index=pd.DatetimeIndex(settlement_date))
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                file=path+'/'+'eurodollar_futures_'+tnow_str+'.txt'
                # We do not need the whole file.
                market_df.to_csv(file,sep=',')
                print('Data successfully printed to file.')
            except:
                print('Something bad happened, and your file did not save.')
        
        return cls('US',
            cashflow_df,
            maturity_df,
            market_df)        

class FedFundsFutures(YieldCurve):
    def __init__(self, 
                 issuer,
                 cashflow_df,
                 maturity_df,
                 market_df):
        
        self.issuer='US'
        self.cashflow_df=cashflow_df
        self.maturity_df=maturity_df
        self.market_df=market_df
        
    @classmethod
    def get_fedfunds_futures(cls,
                        write_path='/Users/jeff/Desktop/finance/data/bonds',
                        write_to_file=False):
        # Use Marketwatch to scrape fed funds futures prices.
        # Consider generalizing this approach, because I will need to do
        # something similar for SOFR futures and possibly other rate futures
        
        # Should be a way to go to FRBNY to get last night's fed funds rate 
        # for the t=1 day point, see below.
        
        # First, generate all available Fed Funds futures quotes based on 
        # the current day.
        # There are 36 months of contracts open at any time
        # However, I see marketwatch give contracts out five years or so,
        # what gives?
        tnow=pd.to_datetime('today').now()
        
        tend=tnow-pd.DateOffset(months=1)+pd.DateOffset(years=5)
        
        query_dates=pd.date_range(start=tnow-pd.DateOffset(tnow.day),
                                  end=tend,freq='MS')
        
        
        #futures_months=[1,2,3,4,5,6,7,8,9,10,11,12]
        #futures_codes=['F','G','H','J','K','M','N','Q','U','V','X','Z']
        futures_codes=['f','g','h','j','k','m','n','q','u','v','x','z']
        
        #closest_month=min(futures_months,key=lambda x:(tnow.month-x)>0)

        
        query_string=['ff'+(str(futures_codes[date.month-1])+
                            str(date.year)[2:]) for date in query_dates]
        
        base_url='https://www.marketwatch.com/investing/future/'
        
        # Ignore SSL Certificate errors
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        price=np.zeros(len(query_string))
        
        for j in range(len(query_string)):
            url=base_url+query_string[j]
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            webpage = urlopen(req).read()
            soup=BeautifulSoup(webpage, 'html5lib')
            try:
                price[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                                              ).get_text().replace('$',''))
                print("Succesfully scraped data for FEDFUNDS contract: " +
                      query_string[j])
            except:
                print("Unable to obtain data for FEDFUNDS contract: " +
                      query_string[j])
            

        # I assume the yields are quoted on an annualized basis.
        # It might be necessary to use 360 day count convention!
        # See the CBOT rules;
        # ff_rate=(100-price)/3600.
        #ff_rate=100-price
        
        # Following Hull for converting fed futures forward price to a 
        # continuous compounding rate
        ff_rate=12*np.log(1+(100-price)/100/12)
        
        
        
        # The query_date array needs to be modified to correspond to the 
        # futures expiration date, which is the last business day of the month?
        settlement_date=pd.date_range(start=tnow,
                                  end=tend+pd.DateOffset(months=1),freq='BM')
        
        # Does this need to be fixed?
        t_settlement=(settlement_date-tnow).days/365.24
        
        # This looks too difficult for me to tackle at this time; use the Fred
        # API instead.
        dff=fred_api(series_id='DFF',
                     realtime_start=(tnow-pd.DateOffset(years=1)
                                     ).strftime('%Y-%m-%d'),
                     realtime_end=tnow.strftime('%Y-%m-%d'))
        
        # Find the annualized volatility in the fed funds rate.
        dff=dff.loc[pd.to_datetime('today').now()
                    -pd.DateOffset(years=1):pd.to_datetime('today').now()]
        sigma_fedfunds_1year=dff.std()
        
        # fill in the most recent overnight rate from FRBNY, maybe scrape this
        # using my fred_api function/class. Insert most recent overnight rate
        # in front of the data, with date=tnow and t_settlement=0
        #frbny_url='https://www.newyorkfed.org/markets/reference-rates/effr'
        #req = Request(frbny_url, headers={'User-Agent': 'Mozilla/5.0'})
        #webpage = urlopen(req).read()
        #soup=BeautifulSoup(webpage, 'html5lib')
        
        
        # Include ff_forward once fred_api is online.
        # Follow Hull here to make convexity adjustment to the futures price
        # and turn it into a forward
        # Insert fedfunds date from yesterday
        ff_rate=np.insert(ff_rate,0,dff[-1]/100)
        # setting this as the value for price is meaningless, but I need a 
        # value to put here; it is essentially the spot price
        price=np.insert(price,0,100-dff[-1])
        # Insert the spot price to the list of futures contracts.
        query_string.insert(0,'spot_price')
        t_settlement=np.insert(t_settlement,0,0)
        settlement_date=settlement_date.insert(0,dff.index[-1])
        # Convexity bias correction?
        #ff_forward=ff_rate-0.5*sigma_fedfunds_1year*T_1*T_2
        
        # Initialize yield array for the loop
        y=np.zeros(len(query_string))
        y[0]=ff_rate[0]
        
        
        for index in range(len(y)-1):
            y[index+1]=(ff_rate[index]*(t_settlement[index+1]-
                        t_settlement[index])+y[index]*t_settlement[index])/(
                        t_settlement[index+1])
        
        
        
        # How to handle cashflow for futures? I left it at 0 for now.
        cashflow_df=0
        # Something like this; maybe a column for each futures contract but
        # it will just be a "diagonal" data frame
        maturity_df=pd.DataFrame(data=t_settlement,index=settlement_date,
                        columns=['t_settlement'])
        # I am using market_df as placeholder for all the data for now
        market_df=pd.DataFrame(data={'ff_contract':query_string,
                                     'ff_price':price,
                                     'ff_rate':ff_rate,
                                     'implied_yield':y,
                                     't_settlement':t_settlement},
                                   index=pd.DatetimeIndex(settlement_date))
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                file=path+'/'+'fedfunds_futures_'+tnow_str+'.txt'
                # We do not need the whole file.
                market_df.to_csv(file,sep=',')
                print('Data successfully printed to file.')
            except:
                print('Something bad happened, and your file did not save.')
        
        return cls('US',
            cashflow_df,
            maturity_df,
            market_df)
    
    def plot_fedfunds_zero_curve(self,
                        write_path='/Users/jeff/Desktop/finance/data/bonds',
                        write_to_file=False):
        # First check if there are any elements in the cheapest to deliver list.
        
        tnow=pd.to_datetime('today').now()
        tstr=tnow.strftime("%Y-%b-%d %H:%M")
        
        plt.figure();
        plt.title('FedFunds zero curve as of: '+tstr)
        plt.plot(pd.to_datetime(self.market_df.index),
                 100*self.market_df.implied_yield,'.',markersize=4,
                 label='FedFunds Implied Yield')
        # Maybe it is good to also plot the "forward" rate?
        # plt.plot(pd.to_datetime(self.market_df.index),
        #          100*self.market_df.ff_rate,'.',markersize=2,
        #          label='FedFunds Forward Rate')
        plt.xlim(tnow,pd.to_datetime(self.market_df.index[-1]))
        #plt.ylim()
        plt.ylabel('Yield (%)')
        plt.xlabel('Maturity Date')
        plt.legend(loc='best')
        plt.tight_layout()
        
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d/")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # We do not need the whole file.
                plt.savefig(path
                    + 'fedfunds_zero_curve'
                    + tnow_str+'.png')
                print('Data successfully printed to file.')
            except:
                print('Something bad happened, and your plot did not save.')
        

        
        return
   
# We need a class for SOFR futures, 1 month and 3 month?
#class SOFRFutures(YieldCurve):
    # typical sr1 symbol: sr1cm22 (Sofr futures go out about 1 year)
    # typical sr3 symbol: sr3cm22
class SOFRFutures(YieldCurve):
    
    def __init__(self, 
                 issuer,
                 cashflow_df,
                 maturity_df,
                 market_df):
        
        self.issuer='US'
        self.cashflow_df=cashflow_df
        self.maturity_df=maturity_df
        self.market_df=market_df
        
    @classmethod
    def get_sofr_futures(cls,
                        calculation_date=pd.to_datetime('today').now(),
                        write_path='/Users/jeff/Desktop/finance/data/bonds',
                        write_to_file=False,
                        sofr_history_months=1,
                        save_sofr_history=False):
        # If, for any reason, calculation_date needs to be different than tnow
        tnow=pd.to_datetime('today').now()
        
        # Need a calendar to handle US business holidays!
        cal = USFederalHolidayCalendar()
        # Business month begin and end dates will be useful
        start_offset=pd.tseries.offsets.CustomBusinessMonthBegin(calendar=cal)
        end_offset=pd.tseries.offsets.CustomBusinessMonthEnd(calendar=cal)
        
        
        # This link might be helpful for getting volatility for each contract:
        # Separate method for getting the volatility of each contract?
        # sr3=pd.read_csv('https://www.marketwatch.com/investing/future/sr3cz22/downloaddatapartial?startdate=06/19/2022%2000:00:00&enddate=07/19/2022%2023:59:59&daterange=d30&frequency=p1d&csvdownload=true&downloadpartial=false&newdates=false')
        # or 1 year:
        #sr3=pd.read_csv('https://www.marketwatch.com/investing/future/sr3cu27/downloaddatapartial?startdate=06/20/2022%2000:00:00&enddate=07/20/2022%2023:59:59&daterange=d30&frequency=p1d&csvdownload=true&downloadpartial=false&newdates=false')
    
        # Laziest method to get approximate volatility: the annualized volatility
        # from Fred?
        sofr_fred=fred_api(series_id='SOFR',
                    realtime_start=(calculation_date-pd.DateOffset(years=1)
                                      ).strftime('%Y-%m-%d'),
                    realtime_end=calculation_date.strftime('%Y-%m-%d'))
        # If you don't use this data for volatility, still need it for the 
        # SOFR rate for today (use the last value, sofr_fred[-1] for t0.)
        spot_sofr=sofr_fred[-1]
        # Fred data may also be useful to fill in the missing fraction of a
        # 3 month sofr contract?
        # To be consistent, I think we should calculate the geometric average
        # of the sofr rate for the missing fraction of the contract?
        # See below.
        
        # 21-July 2022: The annualized volatility from fred sofr is way too
        # high; probably best to pick last month of data for a middle contract
        # and use the volatility from it as a proxy
        # Find the annualized volatility in the sofr rate.
        sofr_last_month=sofr_fred.loc[pd.to_datetime('today').now()
                    -pd.DateOffset(months=1):pd.to_datetime('today').now()
                    ].resample('D').asfreq().fillna(method='ffill')
        # Need to use the same convention as for the futures constracts.
        # This is the standard deviation of the log returns, using the most
        # recent data.
        # I think it is best to use the previous month volatility
        # sigma_sofr_1year=sofr_fred.std()
        sigma_sofr=np.sqrt(252)*np.std(np.log(
                    (100-sofr_last_month[1:].values)/
                    (100-sofr_last_month[:-1].values)))
      
        # Figure out what is the front month contract, based on the calculation
        # date:
        minus_q=WeekOfMonth(week=2,weekday=2).rollback(
                        QuarterEnd(0).rollback(calculation_date))
        plus_q=(WeekOfMonth(week=2,weekday=2).rollback(
                        QuarterEnd(0).rollforward(calculation_date))
                        -pd.DateOffset(days=1))
        
        if (calculation_date+QuarterEnd(0)>plus_q)&(
                calculation_date<=plus_q):
            tstart=minus_q-MonthBegin()
        else:
            tstart=calculation_date
        
        # Get quarterely contracts listed for 39 consecutive serial contract 
        # months; should we use the 4 serial contracts too?
        # First pass: get the quarterly months.
        tend=tstart+pd.DateOffset(months=121)
        
        query_dates=pd.date_range(
            start=tstart,end=tend,freq='QS')-pd.DateOffset(months=1)
        # Trading in an expiring contract shall terminate at the close of 
        # trading on the Business Day immediately preceding the third 
        # Wednesday of the contract delivery month.
        # Trading concludes and the reference period ends on the day 
        # preceeding
        ref_start=pd.DatetimeIndex(
            [WeekOfMonth(week=2,weekday=2).rollforward(date) 
             for date in query_dates])
        # The reference quarter starts 1 quarter earlier!
        expiration_dates=ref_start+pd.DateOffset(months=2)+MonthBegin(0)
        expiration_dates=pd.DatetimeIndex(
            [WeekOfMonth(week=2,weekday=2).rollforward(date) 
             -pd.DateOffset(days=1)
             for date in expiration_dates])
        
        # Needed to calculate compounded forward rates!
        day_count=(expiration_dates-ref_start).days.values

        # Need logic for the 4 nearest monthly contracts:
        futures_codes=['f','g','h','j','k','m','n','q','u','v','x','z']
        
        query_string=['sr3c'+(str(futures_codes[date.month-1])+
                            str(date.year)[2:]) for date in query_dates]
        # Ready to scrape contracts now.
        settlement_price=np.empty(len(query_string))
        settlement_price[:]=np.nan
        futures_price=np.empty(len(query_string))
        futures_price[:]=np.nan
        oi=np.empty(len(query_string))
        oi[:]=np.nan
        sofr_vol=np.empty(len(query_string))
        sofr_vol[:]=np.nan
        
        # prepare a dataframe to concatenate each price_df
        # It might also be good to have an option to save to file the
        # sofr price history
        for no,fut_symb in enumerate(query_string):
            settlement_price[no],futures_price[no],oi[no],price_df=(
                marketwatch_futures_scraper(futures_symbol=fut_symb,
                                            calculation_date=calculation_date,
                                            price_history=True,
                                            price_history_months
                                            =sofr_history_months,
                                            save_history=save_sofr_history))
            # sometimes there is no price data, so just use the volatility
            # of the previous contract
            try:
                price_df.sort_values('Date',inplace=True)
                sofr_vol[no]=np.sqrt(252)*np.std(np.log(
                    (price_df.Close[1:].values)/(
                        price_df.Close[:-1].values)))
                
            except:
                print('No price data for futures symbol: '
                      +fut_symb+" So, using previous contract volatility.")
                sofr_vol[no]=sofr_vol[no-1]
            
        # Now that tstart is known, calculate the current geometric average
        # of sofr rate from ref_start until now.
        # What if the fred data stops before a weekend?
        # If the last measurement is July 28, but current date is July 30?
        running_sofr=sofr_fred.loc[
            ref_start[0].strftime('%Y-%m-%d'):calculation_date
            ].resample('D').asfreq().fillna(method='ffill')
        # Is a plus one needed here or no for running days and remaining days?
        running_days=(running_sofr.index
            -pd.to_datetime(ref_start[0].date())).days+1
        # days remaining in the front month contract:
        remaining_days=(expiration_dates[0]-calculation_date).days+1
        # This formula is for geometrical average for the reference period
        sofr_ga=((1+(1/360.)*running_sofr/100).prod()-1
                 )*360./running_days[-1]*100
        # Knowing the running sofr and the current spot rate, what does 
        # the geometrical average have to be for the rest of the front month
        # contract to be consistent with the rate from futures??
        # Try weighted geometrical average to get the forward rate:
        front_sofr=np.exp((running_days[-1]+remaining_days)*np.log(
            100-futures_price[0])/(remaining_days)
            -1.0*running_days[-1]/remaining_days*np.log(sofr_ga))
        
        # Use the volatility of the middle contract as a proxy? Adjust as 
        # necessary
        # sr3_temp=pd.read_csv('https://www.marketwatch.com/investing/future/'
        #                 +query_string[20]
        #                 +'/downloaddatapartial?startdate='
        #                 +(tnow-pd.DateOffset(months=1)).strftime('%m/%d/%Y')
        #                 +'&enddate='+tnow.strftime('%m/%d/%Y')
        #                 +'&daterange=d30&frequency=p1d&csvdownload=true'
        #                 +'&downloadpartial=false&newdates=false')
        # Get the daily returns; This follows 2009 Frank J. Fabozzi, and I 
        # think it should be consistent with Hull but I would like to check
        # again. These are daily volatilities, so multiply by sqrt(252) to 
        # get an annualized volatility.
        # 23 July 2022: check back from time to time to see if this is still a
        # reasonable approximation for the convexity adjustment; implied
        # volatility for the contracts would be better but it is harder to 
        # find.
        # sofr_vol=np.sqrt(252)*np.std(np.log(
        #     sr3_temp.Close[1:].values/sr3_temp.Close[:-1].values))
        
        # Time to reference date, in years
        t_ref=(ref_start-tnow).days/365.24
        # Time to expiration, in years
        t_exp=(expiration_dates-tnow).days/365.24
        # Now ready to calculate the forward rate,convert to continuous 
        # compounding, and how do we manage the fact that sofr is in arrears?
        # I used: Fabio Mercurio's 2018 seminar
        # SOFR convexity correction goes like sigma**2/2*T**2
        sofr_rate=100-futures_price
        # First element of what will become the sofr forward rate array
        sofr_rate[0]=front_sofr
        # Now, the convexity adjustment, following 2018_Mercurio:
        sofr_rate=sofr_rate-100*(sofr_vol)**2/2*t_exp**2
        
        
        # setting this as the value for price is meaningless, but I need a 
        # value to put here; it is essentially the spot price
        futures_price=np.insert(futures_price,0,100-spot_sofr)
        # Insert SOFR volatility from Fred?
        sofr_vol=np.insert(sofr_vol,0,sigma_sofr)
        # Insert the spot price to the list of futures contracts.
        query_string.insert(0,'spot_price')
        # insert sofr rate from most previous measurement (hopefully yesterday)
        sofr_rate=np.insert(sofr_rate,0,spot_sofr)
        # same for continuous compounded version?
        # 31 July 2022: I suspect this is wrong, because the sofr rate from
        # futures is compounded daily. Therfore, converting to continuous
        # compounding should be quite close, the 360 day convention 
        # notwithstanding.
        # convert to continuous compounding
        # sofr_rate=(-3600/(day_count))*np.log(1-day_count/3600*(sofr_rate))
        # 2023-08-16:
        # I think this variable name is confusing; shouldn't it be called the 
        # the continuously compounded forward rate?
        sofr_zero_rate=36500*np.log(1+sofr_rate/36000)
        # The spot sofr rate has 1 day to maturity
        t_exp=np.insert(t_exp,0,1/365.24)
        expiration_dates=expiration_dates.insert(0,sofr_fred.index[-1])
        # Need to do something for 'ref_start'. I don't know what, so I just
        # did this for now, need to rethink this
        ref_start=ref_start.insert(0,sofr_fred.index[-1])
        # spot quantities for everything else has been inserted, so insert
        # np.nan for sofr open interest, at least for now
        oi=np.insert(oi,0,np.nan)
        
        # Initialize yield array for the zero-coupon rate determination loop
        y=np.zeros(len(sofr_rate))
        y[0]=sofr_rate[0]

        # This is the same procedure shown in Hull for Eurodollar futures.
        # Use day_count array here for t_i+1-t_i instead!
        for index in range(len(y)-1):
            y[index+1]=(sofr_zero_rate[index+1]*(t_exp[index+1]-t_exp[index])
                        +y[index]*t_exp[index])/(t_exp[index+1])
    
        # How to handle the cashflow_df object attribute for futures? 
        # I left it at 0 for now.
        cashflow_df=0
        # Something like this for the maturity_df object attribute; 
        # maybe a column for each futures contract but it will just be a 
        # "diagonal" data frame
        maturity_df=pd.DataFrame(data=t_exp,index=expiration_dates,
                        columns=['t_settlement'])
        # market_df holds all the data for now
        market_df=pd.DataFrame(data={'sofr_contract':query_string,
                                     'ref_start':ref_start,
                                     'sofr_price':futures_price,
                                     'sofr_oi':oi,
                                     'sofr_vol':sofr_vol,
                                     'sofr_rate':sofr_rate,
                                     'sofr_zero_rate':sofr_zero_rate,
                                     'implied_yield':y,
                                     't_expiration':t_exp},
                                     index=expiration_dates)
        
        try:
            # path=write_path+tnow.strftime("/%Y/%m/%d")
            write_dataframe_to_file(write_to_file=write_to_file,
                                        df=market_df,
                                        filename='sofr_futures')
        except:
            print('Something bad happened, and your file did not save.')
        
        return cls('US',
            cashflow_df,
            maturity_df,
            market_df) 
    
    def plot_sofr_curves(self,
                write_path='C:/Users/31643/Desktop/finance_2023/data/bonds',
                write_to_file=False):
      
        tnow=pd.to_datetime('today').now()
        tstr=tnow.strftime("%Y-%b-%d %H:%M")
        
        # plt.figure();
        fig,ax1=plt.subplots(figsize=(18, 6))
        ax1_color='lightgray'
        ax2_color='cornflowerblue'
        ax1.set_ylabel('Open Interest (Contracts)',color=ax1_color)
        ax1.bar(self.market_df.index,self.market_df.sofr_oi,width=45,
                label='Open Interest',color=ax1_color)
        ax1.set_yscale('log')
        ax1.set_xlabel('Contract Expiration Date')
        ax1.tick_params(which='both',axis='y',labelcolor=ax1_color,
                        color=ax1_color)
        #
        ax2=ax1.twinx()
        ax2.set_title('SOFR Yield Curves as of: '+tstr) 
        ax2.plot(pd.to_datetime(self.market_df.index),
                  (100-self.market_df.sofr_price),'-s',markersize=4,
                  color='navy',
                  label='100-SOFR Futures Price')
        # Maybe it is good to also plot the "forward" rate?
        ax2.plot(pd.to_datetime(self.market_df.index),
                  self.market_df.sofr_rate,'-D',markersize=4,
                  color='mediumblue',
                  label='SOFR Forward Rate after Convexity Adjustment')
        ax2.plot(pd.to_datetime(self.market_df.index),
                  self.market_df.sofr_zero_rate,'-H',markersize=4,
                  color='royalblue',
                  label='SOFR Continuously Compounded Forward Rate')
        ax2.plot(pd.to_datetime(self.market_df.index),
                 self.market_df.implied_yield,'-o',markersize=4,
                 color='cornflowerblue',
                 label='SOFR Implied Zero Coupon Yield') 
        ax2.set_xlim(tnow,pd.to_datetime(self.market_df.index[-1]))
        #plt.ylim()
        ax2.set_ylabel('Yield (%)',color=ax2_color)
        # ax2.set_xlabel('Maturity Date')
        ax2.tick_params(which='both',axis='y',labelcolor=ax2_color,
                        color=ax2_color)  
        ax2.grid(color=ax2_color,linestyle=':')
        ax2.legend(loc='best')
        plt.tight_layout()
        
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d/")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                # We do not need the whole file.
                plt.savefig(path
                    + 'sofr_curves_'
                    + tnow_str+'.png')
                print('Data successfully printed to file.')
            except:
                print('Something bad happened, and your plot did not save.')
        

        # I tried returning the figure, but I don't understand what is
        # happening.
        return 
    
    def write_sofr_data_to_file(self):
        
        write_dataframe_to_file(write_to_file=True,df=self.market_df,
                          filename='sofr_data')
        
        # Maybe a separate write to file for market data, if the option was
        # selected?
        
        return
    
    
    
    