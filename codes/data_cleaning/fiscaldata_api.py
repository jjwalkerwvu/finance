#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 29 20:38:02 2022

@author: jeff

    fiscaldata_api.py
        This is a module to make requests to the treasury.fiscaldata website
"""

import pandas as pd
import json
from urllib.request import urlopen
from pandas.tseries.offsets import MonthEnd
import calendar



# Example request:
url='https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/rates_of_exchange?fields=country_currency_desc, exchange_rate,record_date&filter=country_currency_desc:in:(Canada-Dollar,Mexico-Peso), record_date:gte:2020-01-01'

# remove whitespace 
url = url.replace(" ", "")


mspd_base='https://api.fiscaldata.treasury.gov/services/api/fiscal_service'

marketable_treasuries='/v1/debt/mspd/mspd_table_3_market'

# I think you have to use end of month most recent past month for the record 
# date.
record_date='?filter=record_date:eq:2022-04-30'

# small number of records, to speed up this initial request
page_no_size=',page[number]=1&page[size]=5'

url=mspd_base+marketable_treasuries+record_date

# fd_json = pd.read_json(url)


response = urlopen(url+page_no_size)
# lastPage = response.get('meta').get('pagination').get('lastPage')

fd_json=json.loads(response.read())

# From this first request,
# get the last page?
# or get total count?
total_count=fd_json['meta']['total-count']
total_pages=fd_json['meta']['total-pages']

#redo the request with the total-pages?
# Make it one page but with all the records
page_no_size=',page[number]=1&page[size]='+str(total_count)
# page_no_size=',page[number]=1&page[size]='+str(50)

response = urlopen(url+page_no_size)

fd_json=json.loads(response.read())

# could use something like this for the columns
columns=fd_json['data'][0].keys()
# 'security_class1_desc' is the type, bills, notes, bonds, tips, frns

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
    report_date=(tnow-pd.DateOffset(months=1)+MonthEnd()
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
    except:
        report_date=(tnow-pd.DateOffset(months=1)+MonthEnd()
                     -pd.DateOffset(months=1)).date().strftime('%Y-%m-%d')
        record_date='?filter=record_date:eq:'+report_date
        url=mspd_base+marketable_treasuries+record_date
        print('Retrieving Statement of US Public Debt for date: ' +
                  two_months_ago.strftime('%Y-%m'))
        response = urlopen(url)
        
    print('Data Retrieved, now parsing.')
    
    fd_json=json.loads(response.read())
    
    total_count=fd_json['meta']['total-count']
    # total_pages=fd_json['meta']['total-pages']
    
    # Now that we have the metadata for the most recent record date, get all
    # marketable treasuries.
    page_no_size=',page[number]=1&page[size]='+str(total_count)
    
    response = urlopen(url+page_no_size)
    
    fd_json=json.loads(response.read())
    
    # get the strips_df now?
    strips_df=0
    
    # collect the columns, possibly needed later for compatibility
    # columns=fd_json['data'][0].keys()
    
    treasury_df=pd.DataFrame.from_dict(fd_json['data'])
    # I think src_line_nbr should be the index, and it should tie in with 
    # previous code/solution.
    treasury_df.set_index('src_line_nbr',inplace=True)
    # drop some of the columns that are not needed; bring back if needed
    treasury_df.drop(columns=['security_type_desc',
                              'series_cd'
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
    if calendar.isleap(int(year)):
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








