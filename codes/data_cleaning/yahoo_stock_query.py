#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 22:35:38 2021

@author: jeff

    yahoo_stock_query.py
        This function is an extension of yahoo_csv_reader, but can query json
        format data from yahoo in addition to csv (to be implemented later)
        
        2021 December 12: It appears that this is no longer working for tickers
        like vfinx, etc., can only get data back to 2019 and no dividends.
        ^SP500TR is still available
        
        I will need to add additional arguments/options later, these are
        the current function inputs
        
        ticker      -   The ticker you want to query. Needs to be a valid 
                        ticker symbol; indices have '^' in front
        filename    -   The filename you want to read from, or write to. Set
                        to '' as a default, since the default is to query the
                        yahoo website, and not a file
        query       -   Boolean argument for whether to grab data from the 
                        website or read from file; default is True, so it 
                        queries the website by default.
                    
        dividends   -   Boolean argument for whether to retrieve dividend data;
                        default set to False
        
        
"""
import pandas as pd
import numpy as np
import datetime
from datetime import datetime
import os
import sys

def yahoo_stock_query(ticker,
                      filename='/Users/jeff/Desktop/finance/data/stocks',
                      query=True,dividends=False,write_file=False):
    
    ## the base url
    host='https://query1.finance.yahoo.com' 
    #host='query2.finance.yahoo.com'
    
    tnow=pd.to_datetime('today').now()

    ## the ticker to use
    #ticker='^GSPC'



    ## fundamental data
    #fund_data='/v10/finance/quoteSummary/'+ticker+'?'

    ## modules
    #modules='modules='
    # [
    #        'assetProfile',
    #        'summaryProfile',
    #        'summaryDetail',
    #        'esgScores',
    #        'price',
    #        'incomeStatementHistory',
    #        'incomeStatementHistoryQuarterly',
    #        'balanceSheetHistory',
    #        'balanceSheetHistoryQuarterly',
    #        'cashflowStatementHistory',
    #        'cashflowStatementHistoryQuarterly',
    #        'defaultKeyStatistics',
    #        'financialData',
    #        'calendarEvents',
    #        'secFilings',
    #        'recommendationTrend',
    #        'upgradeDowngradeHistory',
    #        'institutionOwnership',
    #        'fundOwnership',
    #        'majorDirectHolders',
    #        'majorHoldersBreakdown',
    #        'insiderTransactions',
    #        'insiderHolders',
    #        'netSharePurchaseActivity',
    #        'earnings',
    #        'earningsHistory',
    #        'earningsTrend',
    #        'industryTrend',
    #        'indexTrend',
    #        'sectorTrend']
    
    ## example url:
    ## The %2C is the Hex representation of , and needs to be inserted between 
    ## each module you request.
    #example_url='https://query2.finance.yahoo.com/v10/finance/quoteSummary/AAPL?modules=assetProfile%2CsummaryProfile%2CsummaryDetail%2CesgScores%2Cprice%2CincomeStatementHistory%2CincomeStatementHistoryQuarterly%2CbalanceSheetHistory%2CbalanceSheetHistoryQuarterly%2CcashflowStatementHistory%2CcashflowStatementHistoryQuarterly%2CdefaultKeyStatistics%2CfinancialData%2CcalendarEvents%2CsecFilings%2CrecommendationTrend%2CupgradeDowngradeHistory%2CinstitutionOwnership%2CfundOwnership%2CmajorDirectHolders%2CmajorHoldersBreakdown%2CinsiderTransactions%2CinsiderHolders%2CnetSharePurchaseActivity%2Cearnings%2CearningsHistory%2CearningsTrend%2CindustryTrend%2CindexTrend%2CsectorTrend'


    ## price example:
    ## Possible inputs for &interval=: 1m, 5m, 15m, 30m, 90m, 1h, 1d, 5d, 1wk, 1mo, 
    ## 3mo
    ## m (minute) intervals are limited to 30days with period1 and period2 spaning 
    ## a maximum of 7 days per/request. Exceeding either of these limits will 
    ## result in an error and will not round

    ## h (hour) interval is limited to 730days with no limit to span. Exceeding 
    ## this will result in an error and will not round

    ## period1=: UNIX timestamp representation of the date you wish to start at.
    ## d (day), wk (week), mo (month) intervals with values less than the initial 
    ## trading date will be rounded up to the initial trading date.

    ## period2=: UNIX timestamp representation of the date you wish to end at.
    ## For all intervals: values greater than the last trading date will be 
    ## rounded down to the most recent timestamp available.

    #price_example='/v8/finance/chart/AAPL?symbol=AAPL&period1=0&period2=9999999999&interval=3mo'
    #https://query1.finance.yahoo.com/v7/finance/download/AAPL?period1=From&period2=To&interval=1d&events=div&includeAdjustedClose=true
    
    if dividends==True:
        price_example=('/v8/finance/chart/'+ticker+
                   '?symbol=^GSPC&period1=0&period2=9999999999&interval=1d')
        
        dividend_command='&events=div&includeAdjustedClose=true'
        url=host+price_example+dividend_command

        json_data=pd.read_json(url)
    
        ## All of the price data
        close=np.array(json_data.chart.result[0]['indicators']['quote'][0]['close'])
        volume=np.array(json_data.chart.result[0]['indicators']['quote'][0]['volume'])
        open_price=np.array(json_data.chart.result[0]['indicators']['quote'][0]['open'])
        low=np.array(json_data.chart.result[0]['indicators']['quote'][0]['low'])
        high=np.array(json_data.chart.result[0]['indicators']['quote'][0]['high'])
    
    
        ## take care of the timestamp, turn into datetime, but 
        utc_timestamp=np.array([datetime.utcfromtimestamp(d) 
                    for d in json_data.chart.result[0]['timestamp']])
        ## We can leave the time if necessary, but for now just use the date only;
        ## change later as needed
        time_data=pd.DatetimeIndex(pd.DatetimeIndex(utc_timestamp).date)
        
        df=pd.DataFrame(data=np.vstack((close,volume,open_price,low,high)).transpose(),
                    index=time_data,
                    columns=['Close','Volume','Open','Low','High'])
        
        amount=np.array(
            [json_data.chart.result[0]['events']['dividends'][key]['amount'] 
             for key in json_data.chart.result[0]['events']['dividends']])
        div_date=pd.DatetimeIndex(pd.DatetimeIndex(np.array(
            [datetime.utcfromtimestamp(
                json_data.chart.result[0]['events']['dividends'][key]['date']) 
                    for key in 
                    json_data.chart.result[0]['events']['dividends']])).date)
        # I can make a series quickly:
        div_series=pd.Series(amount,index=div_date)
        # Adjusted close is quite useful.
        df['adjclose']=np.array(
            json_data.chart.result[0]['indicators']['adjclose'][0]['adjclose'])
        
        df['dividends']=div_series
        
    else:
        price_example=('/v8/finance/chart/'+ticker+
                   '?symbol=^GSPC&period1=0&period2=9999999999&interval=1d')

        ## Add pre & post market data
        #'&includePrePost=true'

        ##Add dividends & splits
        #'&events=div%7Csplit'

        #'%7C' is hex for |. , will work but internally yahoo uses pipe

        ## Example URL:

        #https://query1.finance.yahoo.com/v8/finance/chart/AAPL?symbol=AAPL&period1=0&period2=9999999999&interval=1d&includePrePost=true&events=div%7Csplit
        ## The above request will return all price data for ticker AAPL on a 1-day 
        ## interval including pre and post-market data as well as dividends and splits.

        url=host+price_example

        json_data=pd.read_json(url)
    
        ## All of the price data
        close=np.array(json_data.chart.result[0]['indicators']['quote'][0]['close'])
        volume=np.array(json_data.chart.result[0]['indicators']['quote'][0]['volume'])
        open_price=np.array(json_data.chart.result[0]['indicators']['quote'][0]['open'])
        low=np.array(json_data.chart.result[0]['indicators']['quote'][0]['low'])
        high=np.array(json_data.chart.result[0]['indicators']['quote'][0]['high'])
    
    
        ## take care of the timestamp, turn into datetime, but 
        utc_timestamp=np.array([datetime.utcfromtimestamp(d) 
                    for d in json_data.chart.result[0]['timestamp']])
        ## We can leave the time if necessary, but for now just use the date only;
        ## change later as needed
        time_data=pd.DatetimeIndex(pd.DatetimeIndex(utc_timestamp).date)
    
    

        df=pd.DataFrame(data=np.vstack((close,volume,open_price,low,high)).transpose(),
                    index=time_data,
                    columns=['Close','Volume','Open','Low','High'])
    
    
        if write_file==True:
            path=(filename+tnow.strftime("/%Y/%m/%d"))
            # path=('/Users/jeff/Desktop/finance/data/stocks/'+
            #     tnow.strftime("/%Y/%m/%d"))
            os.makedirs(path, exist_ok=True)

            ## convert tnow, the time at which the data was retrieved, into a 
            ## string for a filename.
            
            tnow_str=tnow.strftime("%Y_%m_%d_%H_%M")
            file=path+'/'+ticker+'_'+tnow_str+'.txt'
            df.to_csv(file,sep=',')
    
    return df






