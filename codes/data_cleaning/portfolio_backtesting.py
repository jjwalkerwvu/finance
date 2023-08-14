# -*- coding: utf-8 -*-
"""
Created on Sun May 21 18:24:41 2023

    This module is meant to house common portfolio backtesting functions,
    data retrieval, with the possibility of a builder pattern for the class:
    PortfolioBacktest

@author: 31643
"""

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.holiday import get_calendar,HolidayCalendarFactory,GoodFriday
import numpy as np
import matplotlib.pyplot as plt
import sys
## import the csv reader for FRED data, yahoo, etc.
sys.path.insert(1, '/Users/31643/Desktop/finance_2023/codes/data_cleaning/')
from fred_csv_reader import fred_csv_reader
from shiller_excel_reader import shiller_excel_reader 
from yahoo_stock_query import yahoo_stock_query
from yahoo_csv_reader import yahoo_csv_reader
from FedsYieldCurve import FedsYieldCurve
from fred_api import fred_api

cal = USFederalHolidayCalendar()

# get nearest valid dates
def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

# A nice function to CORRECTLY splice sp500 from various data sources
def splice_gspc():
    # Maybe an even better idea than sp500tr is to use vfinx, since this was
    # an actual investible instrument with an expense ratio.
    # They are pretty close, however.
    #sp500tr=yahoo_stock_query('vfinx',dividends=True)
    sp500tr=yahoo_stock_query('^SP500TR')
    # or get from my github
    gspc=yahoo_csv_reader(
        filename='/Users/31643/Desktop/finance_2023/data/stocks/^GSPC', 
        ticker='^GSPC')
    
    shiller=shiller_excel_reader(
        '/Users/31643/Desktop/finance_2023/data/stocks/ie_data.xls')
    
    # dividend pay dates:
    shiller_div=shiller.D/12.0
    shiller_index=shiller_div.index
    replacement_dates=[]
    # sp500tr begins at 1988-01-04, so I think I can safely disregard the 
    # shiller dividend for 1988 January
    # 20 June 2022: This takes too long, there must be a better way.
    # Maybe do something with index intersection?
    for date in shiller_div[gspc.index[0]:'1988-02'].index:
        replacement_dates.append(nearest(gspc.index,date))
        
        
    div_series=pd.Series(data=shiller_div.loc[
        shiller_div[gspc.index[0]:'1988-03'].index[:-1]].values,
        index=replacement_dates)
    
    # Abbreviate the div_series so that it ends at 1988-01-04, which is the 
    # date that the sp500tr series begins
    #div_series=div_series[:'1988-01-04']
    
    # Correct way to add the dividends? Just a simple addition for now; we can
    # do this for the returns.
    div_added=(gspc.Close+div_series.resample('D').asfreq().fillna(0)
                 ).dropna()
    # Now abbreviate this series so that it ends at 1988-01-04, which is the 
    # date that the sp500tr series begins
    div_added=div_added[:'1988-01-04']
    # Interesting that the last price in this series is 255.94, as compared to
    # the sp500tr series, which starts at 256.02 at the same date. Less than
    # 0.03% difference. Maybe I don't even have to bother forcing the start
    # date of sp500tr to be equal to the end date of the gspc + shiller div
    # series??
    
    # Another calculation to get the correct returns from dividends
    div_added_ret=div_added[1:]/(gspc.Close[:'1988-01-04'][:-1].values)
    
    # get the returns from the sp500tr series:
    sp500tr_ret=sp500tr.Close[1:]/sp500tr.Close[:-1].values
    
    # Need to stitch the div_added series and the sp500tr 1988 series
    
    # And now:
    gspc_ret=pd.concat([div_added_ret,sp500tr_ret])
    
    return gspc_ret



# print("Warning: Running GSPC Splice, which takes some time")
# # Another attempt for valid dates: just use the datetime index from the 
# # spliced gspc_ret series
# # The date 1928-04-04 is chosen because this is when my stitched Fed funds 
# # series starts.
# gspc_ret=splice_gspc()

# # Use FedsYieldCurve class to get the yield curve based on off the run issues
# yield_curve=FedsYieldCurve.get_data()

# nber_recession_dates=fred_api("USREC")

# # Function needed to get duration, various returns from fred data
   
# dtb3=fred_api(series_id='DTB3',
#               realtime_start=(pd.to_datetime('today').now()
#                         -pd.DateOffset(years=1)).strftime('%Y-%m-%d'),
#               realtime_end=pd.to_datetime('today').now().strftime('%Y-%m-%d'))


# # Might consider fed funds for borrowing rate?
# # fedfunds=fred_csv_reader('/Users/jeff/Desktop/finance/data/bonds/FEDFUNDs')
# fedfunds=fred_api(series_id='DFF',
#               realtime_start=(pd.to_datetime('today').now()
#                         -pd.DateOffset(years=1)).strftime('%Y-%m-%d'),
#               realtime_end=pd.to_datetime('today').now().strftime('%Y-%m-%d'))


# # pick what to use as the borrow rate.
# cash=dtb3
# borrow_rate=cash+0.0

# asset_rebalance_freq='M'
# leverage_rebalance_freq='Q'

# start_date='1972-11'
# end_date='2023-04'


# # 15y:   
# ltt_df=yield_curve.strips_price_quarterly_reset_to_dataframe(15.125)

# # 10y:
# y10_price,y10_ytm,y10_dr,y10_qr,y10_mac_dur,y10_mod_dur=(
#      yield_curve.strips_price_quarterly_reset(10.125))

# # 7y:
# y7_price,y7_ytm,y7_dr,y7_qr,y7_mac_dur,y7_mod_dur=(
#       yield_curve.strips_price_quarterly_reset(7.125))   

# # 5y:
# itt_df=yield_curve.strips_price_quarterly_reset_to_dataframe(5.125)

# # 2y:
# stt_df=yield_curve.strips_price_quarterly_reset_to_dataframe(2.125)

def calculate_duration_multiplier(reference_duration,duration_series):  
    duration_multiplier=reference_duration/duration_series
    
    return duration_multiplier

def determine_allowed_timeframe(series_list,
                                rebalance_freq='M',
                                leverage_freq='Q'):
    
    start_date=series_list[0].index[0]
    end_date=series_list[0].index[-1]
    
    # make sure the series list is a list first!
    # Also, there appears to be a problem if there is only element in the list
    for series in series_list[1:]:
        if series.index[0]>start_date:
            start_date=series.index[0]
        if series.index[-1]<end_date:
            end_date=series.index[-1]
    
    # timeframe also needs to include only datetimes that all assets have in
    # common!
    # remove datetimes that are not present in both datasets
    timeframe=series_list[0].loc[start_date:end_date].index
    
    # It does not matter which series we pick, because they should now all be
    # the same length
    rebalance_dates=series_list[0].resample(rebalance_freq).last().index
    
    leverage_dates=series_list[0].resample(leverage_freq).last().index
    
    return start_date,end_date,timeframe,rebalance_dates,leverage_dates

def initialize_start_quantities():
    
    
    return

# use returns flag: allows you to use a price series or a return series!
def run_backtest(asset_list,
                 allocation_list,
                 borrow_cost_list,
                 timeframe,
                 rebal_dates,
                 leverage_dates,
                 start_cash=1e4,
                 use_returns=False):
    
    # verify that asset_list, allocation_list, and borrow_cost_list all have
    # the same number of elements; otherwise return error!
    
    # If the borrow_cost_list is empty,
    
    # Check the sum of the allocation list.
    # If the sum of the allocations is greater than 100%, leverage is required.
    # The borrow cost is needed for each!
    
    start_date=timeframe[0]
    end_date=timeframe[-1]
    
    # assume that asset_list has already been constrained to fit within the
    # timeframe?
    backtest=pd.Series(data=np.zeros(len(asset_list[0])),index=timeframe)
    # Do we need a series for the debt?
    debt=pd.Series(data=np.zeros(len(asset_list[0])),index=timeframe)
    # We should have a series for the total portfolio leverage.
    leverage=pd.Series(data=np.zeros(len(asset_list[0])),index=timeframe)
    
    
    # initialize portfolio?
    backtest.loc[start_date]=start_cash
    # initial leverage, because this is allowed to drift:
    total_alloc=0
    # initialze the floating allocation weights
    alloc_weights=np.zeros(len(allocation_list))
    for no,alloc in enumerate(allocation_list):
        total_alloc=total_alloc+alloc
    for no,alloc in enumerate(allocation_list): 
        alloc_weights[no]=alloc.loc[start_date]/total_alloc.loc[start_date]
    leverage.loc[start_date]=total_alloc-1
    # initial debt?
    debt.loc[start_date]=leverage.loc[start_date]*start_cash
    prev_debt=debt.loc[start_date]
    
    # loop through each step of the timeframe?
    # impossible to avoid, if there are rebalance or leverage reset triggers!
    # (as far as I can tell)
    
    rebal_frame=pd.DataFrame(data=rebal_dates,index=range(len(rebal_dates)))
    lev_frame=pd.DataFrame(
        data=leverage_dates,index=range(len(leverage_dates)))
    
    date_frame=pd.merge(rebal_frame,lev_frame,how='outer',sort=True)
      
    date_series=date_frame[date_frame.columns[0]]    
    
    # Idea: only want to make calculations at a rebalance date; not every day!
    # Impossible to avoid if there are custom triggers, right?
    previous_date=timeframe[0]
    previous_leverage_date=timeframe[0]
    for i in range(1,len(timeframe)):
        date=timeframe[i]
        # print(date)
        # Need the final asset prices in order to calculate the new 
        # weights
        final_asset_prices=np.zeros(len(alloc_weights))
        ndays=(date-previous_date).days
        for no,asset in enumerate(asset_list):
            # This only works if using a price series, not a return series!
            if use_returns==False:
                asset_ret=asset.loc[date]/asset.loc[previous_date]-1
            elif use_returns==True:
                asset_ret=asset.loc[date]
            else:
                print("You did not choose a valid option for use_returns.")
                print("use_returns=True or use_returns=False")
                break
            # the cost of borrowing for this asset; why don't I have to input
            # the leverage multiplier here like I have to do for an letf?
            # Do I need the leverage multiplier, and is this correct?
            # try testing with a known asset!
            finance_cost=prev_debt*ndays/36000*alloc_weights[no]*(
                borrow_cost_list[no].loc[previous_leverage_date])
            # print(asset_ret*(
            #     1+leverage.loc[previous_date])+1)
            # Need to subtract off the borrow_cost associated with this
            # asset!
            final_asset_price=(((1+leverage.loc[previous_date])*asset_ret)+1)*(
                alloc_weights[no]*(backtest.loc[previous_date]))-finance_cost
            # print(final_asset_price)
            final_asset_prices[no]=final_asset_price
            
            # print(final_asset_price)
            # print(finance_cost)
            
            backtest.loc[date]=(backtest.loc[date]+final_asset_price)
            
            # For now, my solution is to "pro-rate" the debt.
            # This is the running debt since the last leverage reset.
            # debt.loc[date]=(
            #     debt.loc[previous_date]
            #     +prev_debt*(
            #         ndays/36000*alloc_weights[no]*borrow_cost_list[no].loc[
            #             previous_leverage_date]))
            debt.loc[date]=(debt.loc[previous_date]+finance_cost)
            
        # subtract the debt off here?
        # backtest.loc[date]=backtest.loc[date]-debt.loc[date]
            
        # calculate the allocation fraction, which may have drifted    
        alloc_weights=final_asset_prices/backtest.loc[date]
            
        # recalculate leverage every time step, because it is allowed to float!
        # remember: this is leverage above 100%!   
        leverage.loc[date]=(debt.loc[date]/(backtest.loc[date]))
        # print(leverage.loc[date])
         
        if date in leverage_dates:
            
            # When we reset the leverage, this is when we subtract the debt?
            # backtest.loc[date]=backtest.loc[date]-debt.loc[date]
            # Reset the debt; I think this is correct!
            debt.loc[date]=(total_alloc.loc[date]-1)*backtest.loc[date]
            #
            prev_debt=debt.loc[date]
            # Recalculate total portfolio leverage
            leverage.loc[date]=(debt.loc[date]/(backtest.loc[date])-1)
            
            previous_leverage_date=date
        
        elif date in rebal_dates:
            # Reset allocations, moving forward.
            for no,asset in enumerate(asset_list):
                alloc_weights[no]=allocation_list[no].loc[date]/(
                    total_alloc.loc[date])
          
        if backtest.loc[date]<0:
            break
        previous_date=date
        
    
    
    # 2023-06-19
    # Previous attempt; trying to minimize the number of times through the 
    # loop, but I think stepping through each timestamp is unavoidable.
    # I wanted to have greater speed, but maybe I just cannot do it this way.
    # Fill in the backtest with backtest.loc[previous_date:date]
    # previous_date=start_date
    # previous_rebal_date=start_date
    # previous_leverage_date=start_date
    # for date in date_series:
    #     # dates within timeframe; do not use the rightmost datetime
    #     # cutoff_date=asset_list[0].loc[previous_date:date].index[-2]
    #     # Is the cutoff date needed?
    #     cutoff_date=date
    #     # do rebalance stuff!
    #     if date in rebal_dates:
    #         # number of days since previous leverage or allocation balance
    #         ndays=(cutoff_date-previous_date).days
    #         # initialize the bulk of the debt as the debt determined the last
    #         # time in the leverage date condition.
    #         # The principal debt comes from the previous leverage reset
    #         prev_debt=debt.loc[previous_leverage_date]
    #         debt.loc[previous_date:cutoff_date]=(
    #                                     debt.loc[previous_date])
    #         # Need the final asset prices in order to calculate the new 
    #         # weights
    #         final_asset_prices=np.zeros(alloc_weights)
    #         # calculate the performance of the portfolio:
    #         for no,asset in enumerate(asset_list):
    #             # Use this approach if I decide to use returns as the series 
    #             # list:
    #             cumulative_ret=asset.loc[previous_date:cutoff_date].cumprod()
    #             # subtract the "debt" corresponding to each asset, based on
    #             # specific borrow rates
    #             # The borrow cost is from the previous leverage reset; that 
    #             # rate was "locked in" on that previous date
    #             final_asset_price=(cumulative_ret*alloc_weights[no]*(
    #                 1+leverage.loc[previous_date])*backtest.loc[previous_date])
    #             # final_asset_price=(cumulative_ret*alloc_weights[no]*(
    #             #     1+leverage.loc[previous_date])*backtest.loc[previous_date]
    #             #     -prev_debt*(
    #             #         ndays/3600*alloc_weights[no]*borrow_cost_list[no].loc[
    #             #             previous_leverage_date]))
                
    #             final_asset_prices[no]=final_asset_price.loc[cutoff_date]
                
    #             backtest.loc[previous_date:cutoff_date]=(
    #                 backtest.loc[previous_date:cutoff_date]
    #                 +final_asset_price)
                
    #             # For now, my solution is to "pro-rate" the debt.
    #             # This is the running debt since the last leverage reset.
    #             debt.loc[previous_date:cutoff_date]=(
    #                 debt.loc[previous_date:cutoff_date]
    #                 +prev_debt*(
    #                     ndays/3600*alloc_weights[no]*borrow_cost_list[no].loc[
    #                         previous_leverage_date]))
                            
    #             # Reset allocations, moving forward.
    #             alloc_weights[no]=allocation_list[no].loc[cutoff_date]/(
    #                 total_alloc.loc[cutoff_date])
             
    #         # Don't subtract the debt yet??
    #         # Need to subtract off the debt now!
    #         # backtest.loc[previous_date:cutoff_date]=(
    #         #     backtest.loc[previous_date:cutoff_date]
    #         #     -debt[previous_date:cutoff_date])
            
    #         # remember: this is leverage above 100%!   
    #         leverage.loc[previous_date:cutoff_date]=(
    #             debt.loc[previous_date:cutoff_date]/(
    #                 backtest.loc[previous_date:cutoff_date])-1)
             
    #         # reset the previous_date, which is the previous date that the
    #         # portfolio allocation was rebalanced
    #         previous_rebal_date=date
            
    #     # do leverage rebalance stuff!
    #     elif date in leverage_dates:
    #         # number of days since previous asset allocation rebalance
    #         ndays=(cutoff_date-previous_leverage_date).days
    #         # I think this only makes sense when leverage is reset
    #         debt.loc[previous_date:cutoff_date]=leverage.loc[
    #                                 previous_date]*backtest.loc[previous_date]
            
    #         # calculate the asset allocation weights, which may have drifted
    #         final_asset_prices=np.zeros(alloc_weights)
    #         for no,asset in enumerate(asset_list):
    #             cumulative_ret=asset.loc[previous_date:cutoff_date].cumprod() 
    #             final_asset_price=cumulative_ret*alloc_weights[no]*(
    #                 1+leverage.loc[previous_date])*backtest.loc[previous_date]
                
    #             final_asset_prices[no]=final_asset_price.loc[cutoff_date]
                
    #             backtest.loc[previous_date:cutoff_date]=(
    #                 backtest.loc[previous_date:cutoff_date]
    #                 +final_asset_price)
 
    #         # calculate the allocation fraction, which may have drifted    
    #         new_weights=final_asset_prices/backtest.loc[cutoff_date]
            
    #         for no,asset in enumerate(asset_list):
    #             # For now, my solution is to "pro-rate" the debt.
    #             # This is the running debt since the last leverage reset.
    #             debt.loc[previous_date:cutoff_date]=(
    #                 debt.loc[previous_date:cutoff_date]
    #                 +debt.loc[previous_leverage_date]*(
    #                     ndays/3600*alloc_weights[no]*borrow_cost_list[no].loc[
    #                         previous_leverage_date]))
                
    #             # debt.loc[previous_date:cutoff_date]=(
    #             #     debt.loc[previous_date:cutoff_date]
    #             #     +debt.loc[previous_leverage_date]*(
    #             #         ndays/3600*borrow_cost_list[no])/(
    #             #             alloc_weights[no]/total_alloc))
            
    #         # Subtract the debt off now!
    #         backtest.loc[previous_date:cutoff_date]=(
    #                                 backtest.loc[previous_date:cutoff_date]
    #                                 -debt.loc[previous_date:cutoff_date])
             
    #         # Reset the allocation weights, which may have drifted               
    #         alloc_weights=1.0*new_weights
            
    #         previous_leverage_date=date
        
    #     previous_date=date
        
            
            
    
    return backtest,leverage,debt

class PortfolioBacktest(object):
    
    def __init__(self,
                 start_date,
                 end_date,
                 equity_data,
                 bond_data,
                 equity_allocation,
                 bond_allocation,
                 rebalance_dates,
                 leverage_rebalance_dates,
                 monthly_contribution):
        
        self.start_date=start_date
        self.end_date=end_date
        self.equity_data=equity_data 
        self.equity_allocation=equity_allocation
        self.bond_data=bond_data
        self.bond_allocation=bond_allocation
        self.rebalance_dates=rebalance_dates
        self.leverage_rebalance_dates=leverage_rebalance_dates
        self.monthly_contribution=monthly_contribution
        # self.sharpe=sharpe

    @classmethod
    def backtest_constant_duration(cls,
                       equity_series,
                       bond_list,
                       borrow_series,
                       equity_alloc=1.65,
                       bond_alloc=1.35,
                       rebal_freq='M',
                       leverage_freq='M',
                       monthly_contr=0,
                       start_cash=1e4):
        
        # check integrity of all the data series?
        # Make a list with all time series data and dataframes!
        series_lst=bond_list.copy()
        series_lst.insert(0,equity_series)
        series_lst.insert(0,borrow_series)
        
        # find the shortest time series, this constrains the start and end 
        # dates
        start_date,end_date,timeframe,rebal_dates,leverage_dates=(
            determine_allowed_timeframe(series_list=series_lst))
        
      
        
        previous_date=start_date
        
        debt1=pd.Series(np.zeros(len(equity_series)),timeframe)
        debt1[0]=-(1-equity_alloc-bond_alloc)*start_cash
        
        for date in rebal_dates[1:]:
            port1=(equity_alloc*equity_series[previous_date:date]
                   +bond_alloc*dur_multiplier*bond_series[previous_date:date])
            
            debt1=0
            
            profit=port1[-1]-port1[0]
        
            previous_date=date
        
        return cls(equity_list,
                   bond_list,
                   equity_alloc,
                   bond_alloc,
                   rebal_dates,
                   leverage_dates,
                   monthly_contr)
    
    
    
    def run_backtest(self):
        
        
        
        return