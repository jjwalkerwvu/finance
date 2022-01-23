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
import numpy as np
import matplotlib.pyplot as plt
#import requests
import ssl
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
#from bs4 import Comment
#import re
import os
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/Users/Jeff/Desktop/finance/codes/data_cleaning')
from fred_api import fred_api

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
    # price of bill/note/bond
    price=np.zeros(len(security_cusips.values))
    # Array for time to maturity
    # tmat=np.array((pd.to_datetime(security_maturities.values)-
    #                 pd.to_datetime('today').now())/np.timedelta64(1,'D')
    #               )/365.2425

    # Maybe there should be a way to eliminate duplicates?
    cusip_check=security_cusips.drop_duplicates().index.values
    # get bill data
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
                # get the yield, in %
                y[j]=float(soup.find('td',{"class": "table__cell u-semi"}
                                              ).get_text().replace('%',''))
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

def cashflows_from_securities(securities_index,coupon_payment,
                              first_payment,second_payment,
                              maturity_date):
    # can bypass dataframe, if we have the index, first and second payments,
    # and maturity date
    
    tnow=pd.to_datetime('today').now()
    face_val=100
    # Try with note coupon dataframe first.
    coupon_df=[]
    maturity_df=[]
    for index in securities_index:
    
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


class YieldCurve(object):
    """ Class docstring goes here?
    """
    # Do I need the init statement or not?
    def __init__(self, issuer, cashflow_df, maturity_df,market_df):
        self.issuer=issuer
        #self.security_cusips=security_cusips
        self.cashflow_df=cashflow_df
        self.maturity_df=maturity_df
        self.market_df=market_df
                 
    
    
    def analytical_bootstrap(self):
        # This method should be inherited by all subclasses!
        # Consider a simple interpolation for gaps between maturities?
        # Seems to be working reasonably, 2021 December 26
        tnow=pd.to_datetime('today').now()
        
        cash_subframe=self.cashflow_df[self.cashflow_df.index>tnow]    
        mat_subframe=self.maturity_df[self.maturity_df.index>tnow]
        
        # Let us try to calculate market prices from the quoted yield, and
        # compare to the market price; perhaps the price is note listed
        # properly?
        
        # tolerance between coupons; in years
        tol=31/365.24
        # "preallocate" for the spot yield?
        s=np.zeros(len(self.market_df))
        #s_ask=np.zeros(len(self.note_df))
        # or, use length of the cash_subframe?
        #salt=np.zeros(len(cash_subframe))
        # this actually works, unlike my implementation for s so far.
        salt=np.zeros(len(self.market_df))
        # maturity array?
        mat=np.zeros(len(self.market_df))
        
        ncols=len(cash_subframe.columns)
        for col in range(ncols):
            # Find number of coupon payments remaining
            npayments=len(cash_subframe[cash_subframe.columns[col]].dropna())
            
            # This statement allows us to compute spot rates at start of the 
            # bootstrap
            if (npayments==1) and (self.market_df.market_price.iloc[col]!=0):
                mat[col]=mat_subframe[mat_subframe.columns[col]].dropna()
                s[col]=np.log((cash_subframe[cash_subframe.columns[col]
                                            ].dropna().values)/(
                            self.market_df.market_price.iloc[col]+
                            self.market_df.accrued_interest.iloc[col]))/(
                                mat[col])
                                
                # Very simple solution; just convert the market yields of 
                # "zero-coupon" notes/bonds to exponential
                salt[col]=2*np.log(1+self.market_df.market_yield.iloc[col]/200)
            # What to do when we get past the "zero coupon" notes?
            elif (npayments>1) and (self.market_df.market_price.iloc[col]!=0):
                mat[col]=mat_subframe[mat_subframe.columns[col]].dropna()[-1]
                coupon_maturities=mat_subframe[
                                    mat_subframe.columns[col]].dropna().values
                # There must be a better way to do this, with a np method
                closest_indices=[]
                for elapsed_time in coupon_maturities[:-1]:
                    # Maybe pick highest yield from securities available, if
                    # there is more than one match?
                    match=abs(mat-elapsed_time).argmin()
                    closest_indices.append(match)
                
                if np.all(abs(coupon_maturities[:-1]-mat[closest_indices])<
                          tol):
                    price_from_yield=(np.sum(cash_subframe[
                        cash_subframe.columns[col]].dropna().values/(
                        1+self.market_df.market_yield.iloc[col]/200)**(
                            2*coupon_maturities))-
                            self.market_df.accrued_interest.iloc[col])
                
            
                
                    # Now that closest time indices are known, we can solve for 
                    # the spot rate
                    s[col]=np.log((cash_subframe[cash_subframe.columns[col]
                                            ].dropna().values[-1])/(
                            self.market_df.market_price.iloc[col]+
                               self.market_df.accrued_interest.iloc[col]-
                               np.sum(cash_subframe[cash_subframe.columns[col]
                                            ].dropna().values[:-1]*np.exp(-
                                                s[closest_indices]*mat[
                                                closest_indices]))))/(mat[col])
                                                                          
                    salt[col]=np.log((cash_subframe[cash_subframe.columns[col]
                                            ].dropna().values[-1])/(
                            price_from_yield+
                               self.market_df.accrued_interest.iloc[col]-
                               np.sum(cash_subframe[cash_subframe.columns[col]
                                            ].dropna().values[:-1]*np.exp(-
                                                salt[closest_indices]*mat[
                                                closest_indices]))))/(mat[col]) 
                else:
                    mat[col]=0
        
        return mat,s,salt
    
    # simple linear interpolation instance method here to get zero coupon bonds
    # between maturity dates; call the method above to get the values
    #def analytical_bootstrap_linear_interpolate():
    
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
    def get_us_public_debt(cls):
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
            print('Retrieving Statement of US Public Debt for date: ' + 
                  one_month_ago.strftime('%Y-%m'))
            df=pd.read_excel(tr_url_base+year+'/opdm'+last_month+year+'.xls',
                     sheet_name=None)
            
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
        note_payable_dates=note_df[note_df.columns[8]].str.split(' ',3,expand=True
                    ).replace(to_replace=[None],value=np.nan)+'/'+year[2:]                
        note_payable_dates.columns=['first_payment','second_payment']
        note_first_payment=pd.to_datetime(note_payable_dates['first_payment'], 
                                  dayfirst=True,errors='coerce').ffill()
        note_second_payment=pd.to_datetime(
                                note_payable_dates['second_payment'], 
                                  dayfirst=True,errors='coerce').ffill()
        # This is my best guess as to how to interpret the spreadsheet;
        # Since no year is given, I assume that if the first listed payment occurs
        # at a greater month than the second payment, then the second payment 
        # corresponds to the following calendar year.
        # If the first listed payment happens at a lower month, than the second
        # payment date, I presume the first payment has already occurred.
        note_second_payment[
            note_first_payment>note_second_payment]=note_second_payment[
                note_first_payment>note_second_payment]+pd.DateOffset(years=1)
        
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
        bond_second_payment[
            bond_first_payment>bond_second_payment]=bond_second_payment[
                bond_first_payment>bond_second_payment]+pd.DateOffset(years=1)
        
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
        tips_second_payment[
            tips_first_payment>tips_second_payment]=tips_second_payment[
                tips_first_payment>tips_second_payment]+pd.DateOffset(years=1)
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
        
        # Try with note coupon dataframe first.
        # note_coupon_df=[]
        # note_maturity_df=[]
        # for index in note_df.index:
    
        #     if note_df.note_first_payment[index].is_month_end:
        #         note_coupon_dates=(
        #             pd.date_range(start=note_df.note_first_payment[index],
        #                         end=note_df.note_maturity_date[index],
        #                         freq='6M'))
        #     # I think that if coupon payments are not at a month end, then they are
        #     # Always on the 15th of a month. 
        #     # IF THIS TURNS OUT TO NOT BE TRUE, THIS MUST BE CHANGED!
        #     else:
        #         note_coupon_dates=(pd.date_range(
        #             start=note_df.note_first_payment[index]-
        #             pd.DateOffset(15),
        #             end=note_df.note_maturity_date[index]+pd.DateOffset(15),
        #             freq='6M')+pd.DateOffset(15))
    
    
    
        #     # In case the first payment has already occurred:
        #     # Use greater than or equal, or just greater than?
        #     note_coupon_dates=note_coupon_dates[note_coupon_dates>=tnow]
        #     # placeholder vector array
        #     note_coupons=np.ones((np.size(note_coupon_dates))
        #                          )*note_df.note_coupon[index]/2
        #     # This a placeholder vector array for the maturities of each cash 
        #     # flow; Remember that we do need to use actual/actual convention
        #     note_mat_values=((note_coupon_dates-tnow)/np.timedelta64(1,'D')
        #              ).values/365.2425
        #     # if you want to add the principal here
        #     note_coupons[-1]=note_coupons[-1]+face_val
        #     note_coupon_series=pd.Series(note_coupons,index=note_coupon_dates)
        #     #
        #     note_mat_series=pd.Series(note_mat_values,note_coupon_dates)
        #     note_coupon_df.append(note_coupon_series)
        #     #
        #     note_maturity_df.append(note_mat_series)
        # # And this is the resulting dataframe for all coupon payments, with the 
        # # (slightly modified) spreadsheet number as column number
        # note_coupon_df=pd.concat(note_coupon_df, axis=1, 
        #         keys=[item for item in note_df.index.astype(str)])
        # note_maturity_df=pd.concat(note_maturity_df, axis=1, 
        #         keys=[item for item in note_df.index.astype(str)])
        
        note_coupon_df,note_maturity_df=cashflows_from_securities(
                note_df.index,
                note_df.note_coupon,
                note_df.note_first_payment,
                note_df.note_second_payment,
                note_df.note_maturity_date)
        
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
        
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                bill_file=path+'/'+'bills'+tnow_str+'.txt'
                # We do not need the whole file.
                self.bill_df[["bill_cusip","bill_maturity_date",
                              "market_price","market_yield"]
                             ].to_csv(bill_file,sep=',')
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
        most_recent_payment=self.note_df.note_first_payment
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
        
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                note_file=path+'/'+'notes_'+tnow_str+'.txt'
                # We do not need the whole file.
                self.note_df[["note_cusip","note_maturity_date",
                              "market_price","market_yield",
                              "note_accrued_interest"]
                             ].to_csv(note_file,sep=',')
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
        most_recent_payment=self.bond_df.bond_first_payment
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
        
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                bond_file=path+'/'+'bonds_'+tnow_str+'.txt'
                # We do not need the whole file.
                self.bond_df[["bond_cusip","bond_maturity_date",
                              "market_price","market_yield",
                              "bond_accrued_interest"]
                             ].to_csv(bond_file,sep=',')
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
        most_recent_payment=self.tips_df.tips_first_payment
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
        
        if write_to_file==True:
            try:
                path=write_path+tnow.strftime("/%Y/%m/%d")
                os.makedirs(path, exist_ok=True)
                tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
                file=path+'/'+'tips_'+tnow_str+'.txt'
                # We do not need the whole file.
                self.tips_df[["tips_cusip","tips_maturity_date",
                              "market_price","market_yield",
                              "tips_accrued_interest"]
                             ].to_csv(file,sep=',')
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
                print("Succesfully scaped data for FEDFUNDS contract: " +
                      query_string[j])
            except:
                print("Unable to obtain data for FEDFUNDS contract: " +
                      query_string[j])
            

        # I assume the yields are quoted on an annualized basis.
        #ff_rate=100-price
        
        # Following Hull for converting fed futures forward price to a 
        # continuous compounding rate
        ff_rate=12*np.log(1+(100-price)/100/12)
        
        
        
        # The query_date array needs to be modified to correspond to the 
        # futures expiration date, which is the last business day of the month?
        settlement_date=pd.date_range(start=tnow,
                                  end=tend+pd.DateOffset(months=1),freq='BM')
        
        t_settlement=(settlement_date-tnow).days/365.24
        
        # This looks too difficult for me to tackle at this time; use the Fred
        # API instead.
        dff=fred_api(series_id='DFF',
                     realtime_start=(tnow-pd.DateOffset(years=1)
                                     ).strftime('%Y-%m-%d'),
                     realtime_end=tnow.strftime('%Y-%m-%d'))
        
        # Find the annualized volatility in the fed funds rate.
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
    
        
    
        