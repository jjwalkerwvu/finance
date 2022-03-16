#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 21:13:23 2021

    This module puts together all of my frequently used methods with 
    Gurkaynak et. al. yield curve dataset.
    
    

@author: jeff
"""

import pandas as pd
import numpy as np
from scipy.optimize import newton

def payment_time_array(years_to_maturity):
    # time until each payment, in years
    # December 1, 2021: This appears to work, but maybe I did not test
    # enough!
    # Does not work for age with exactly .5
    # December 2, 2021: NOT WORKING FOR GREATER THAN .5 INCREMENTS!
    if np.mod(years_to_maturity,0.5)!=0:
        if np.mod(years_to_maturity,np.floor(years_to_maturity))<0.5:
            time_array=(.5*np.arange(0,2*round(years_to_maturity)+1)+
                    years_to_maturity-np.floor(years_to_maturity*2)/2)
        else:
            time_array=(.5*np.arange(1,2*round(years_to_maturity)+1)+
                    years_to_maturity-np.ceil(years_to_maturity*2)/2)
    else:
        time_array=.5*np.arange(1,2*years_to_maturity+1)
    return time_array

def get_ytm(y,c,nperiods,bond_price):
    
    par_val=1000.0
    
    # the function we need to set equal to 0
    # f=(c*par_val*np.sum(np.exp(-year_arr*y))+par_val*np.exp(-yarr[-1]*y)-
    #    bond_price)
    
    f=(2*c*par_val/y*(1-(1+y/2)**(-2*nperiods))
       + par_val/(1+y/2)**(2*nperiods)
       - bond_price)
    
    return f

class FedsYieldCurve:
    
    #__data=object()
    
    def __init__(self,data):
        
        self.data=data
    
    
    # This is working, for now
    # Initialize like: a=FedsYieldCurve.get_data()
    @classmethod
    def get_data(cls):
        print('Retrieving NSS Data from federalreserve.gov')
        try:
            zc=pd.read_csv(
                'https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv'
                , sep=',',header=7)
            zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
            zc.set_index('Date',inplace=True)
            # Here is an idea, to allow for arbitrary return periods;
            # Do a daily resample with forward fill.
            zc=zc.resample('D').asfreq().fillna(method='ffill')
            print('Please note: the data has been resampled to daily '+
                  'frequency, which means that weekends and non-business days'+
                  ' are now included.')
            print('Data retrieved.')
        except:
            print('Data retrieval failed. Check Internet or Host connection.')
            zc=0
        return cls(zc)

    
    def zero_yields(self,tarr,beta3=True):
        # MUST do error checking for tarr, or possibly think how to use age 
        # here. What if we use age instead of tarr? then,
        #tarr=0.5*np.arange(1,2*np.ceil(2*age)/2+1)-(0.5-age%np.floor(age))
        # The asymptotic yield value
        term1=np.asmatrix(self.data.BETA0).T*np.asmatrix(np.ones(len(tarr)))

        # The rate of convergence of the curve to the long term trend
        term2=(np.array(np.asmatrix(self.data.BETA1).T*np.asmatrix(
            np.ones(len(tarr))))*
                  np.array((1-(np.exp(-np.asmatrix(1/self.data.TAU1).T*(
                      np.asmatrix(tarr))))))*np.array(
                          np.asmatrix(self.data.TAU1).T*(
                      np.asmatrix(1/(tarr)))))
                          
        # The size and shape of the first hump
        term3=(np.array(np.asmatrix(self.data.BETA2).T*np.asmatrix(
            np.ones(len(tarr))))*
                  ((np.array((1-(np.exp(-np.asmatrix(1/self.data.TAU1).T*(
                      np.asmatrix(tarr))))))*np.array(
                          np.asmatrix(self.data.TAU1).T*(
                      np.asmatrix(1/(tarr)))))-
                          np.array(np.exp(-np.asmatrix(1/self.data.TAU1).T*(
                             np.asmatrix(tarr))))))   
                          
        # The size and shape of the second hump
        if beta3==True:
            term4=(np.array(np.asmatrix(self.data.BETA3).T*np.asmatrix(
                np.ones(len(tarr))))*
                  ((np.array((1-(np.exp(-np.asmatrix(1/self.data.TAU2).T*(
                      np.asmatrix(tarr))))))*np.array(
                          np.asmatrix(self.data.TAU2).T*(
                      np.asmatrix(1/(tarr)))))-
                          np.array(np.exp(-np.asmatrix(1/self.data.TAU2).T*(
                             np.asmatrix(tarr)))))) 
        else:
            term4=0
    
        # Just calculate the continuous yields, there is no real need to waste
        # time converting to coupon equivalent.
        # Also, ycont is no longer in percent if we divide by 100
        ycont=(term1+term2+term3+term4)/100
        # An additional idea: make sure that ycont matrix elements are returned
        # with their respective dates!
        # 2 December 2021: It does appear to work, so far.
        ycont=pd.DataFrame(data=ycont,index=self.data.index)
        return ycont
    
    def forward_yields(self):
        # Fill in the equation to get forward yields later.
        # This will be the n-by-m forward rate, not instantaneous forward rate
        pass
    
    # We could even make a yield_curve animation with this data...
    
    def bond_price_from_zero_yields(self,years_to_mat,coupon,par_val=1000,
                                    nss=True):
        """

        Parameters
        ----------
        age : TYPE
            DESCRIPTION.
        coupon : TYPE
            DESCRIPTION.
        par_val : float, optional, default face value of bond is assumed to be 
            1000.
        nss : TYPE, optional
            DESCRIPTION. The default is True.

        Returns
        -------
        bond_price : TYPE
            DESCRIPTION.

        """
        
        # time until each payment, in years
        # December 1, 2021: This appears to work, but maybe I did not test
        # enough!
        # Does not work for age with exactly .5
        # if np.mod(age,0.5)!=0:
        #     parr=.5*np.arange(0,2*round(age)+1)+age-np.floor(age*2)/2
        # else:
        #     parr=.5*np.arange(1,2*age+1)
            
        parr=payment_time_array(years_to_maturity=years_to_mat)
        
        yield_arr=self.zero_yields(tarr=parr,beta3=nss)
        
        # BE AWARE: coupon here is the actual dollar amount of money paid;
        # A par equivalent yield bond would use rate/2 to get the coupon here.
        p_annuity=par_val*coupon*(np.sum(
            np.exp(-np.array(yield_arr)*np.array(
                np.asmatrix(np.ones(len(self.data))).T*np.asmatrix(parr))),
            axis=1)*self.data.BETA0**0)
        
        p_principal=par_val*(self.data.BETA0**0*(np.squeeze(np.array(
            np.exp(-yield_arr.values[:,-1]*parr[-1])))))
        
        bond_price=p_annuity+p_principal
        
        return bond_price
    
    def bond_price_from_issue(self,coupon_rate,issue_date,maturity_date,
                              start_date,end_date,nss=True):
        # This still needs to be fleshed out.
        # The idea is to input a specific bond details and get the daily price
        # performance.
        maturity_start=(maturity_date-start_date).days
        maturity_end=(maturity_date-end_date).days
        mat_years=(maturity_date-self.data.index[
                    (self.data.index>=start_date)&(self.data.index<=end_date)]
                       ).days.values/365.24
        
        bond_price=0
        
        return bond_price
    
    def bond_price_quarterly_reset(self,years_to_mat,par_val=1000,nss=True):
        # Idea here is pick a start date, let the bond age for one quarter,
        # then buy another one with the same years to maturity, but keep track
        # of its price the entire time
                
        #start_date=self.data.index[0]
        
        parr=payment_time_array(years_to_maturity=years_to_mat)
        # Get the par_yield, for the coupon:
        par_rate=self.par_yield(years_to_mat=years_to_mat,nss=nss)  
        
        par_rate_quarterly=par_rate.resample('QS').asfreq()[self.data.index[0]:
                                                        self.data.index[-1]]
        
        first_quarter=par_rate_quarterly.index[0]
        
        # reindex non-quarter start dates to nans
        par_rate_quarterly=par_rate_quarterly.reindex(self.data.index)
        
        par_rate_quarterly[:first_quarter][:-1]=par_rate[0]
        
        # resample to quarterly, because we buy a new par bond every quarter.
        # This will be used for the coupons.
        coupon=0.5*par_rate_quarterly.resample('D').asfreq(
            ).fillna(method='ffill')[self.data.index[0]:self.data.index[-1]]
        # hold period is the number of days between holding periods, in this
        # case 1 quarter. The hold period is variable, because not all quarters
        # months, etc. have the same number of days
        hold_period=(par_rate.resample('QS').asfreq()[
                        self.data.index[0]:self.data.index[-1]].index[1:]
                        -par_rate.resample('QS').asfreq()[
                            self.data.index[0]:self.data.index[-1]].index[:-1]
                        ).days.values
        
        #hold_period=np.arange(91)/365.24
        # Ugh, just terrible. Surely there is a better way to do this?
        year_arr=np.asmatrix(np.empty((len(self.data),len(parr))))
        # What if there are days before the first quarter starts?
        # You need to subtract 1 to get this to work out!
        underhang=len(self.data[par_rate.index[0]:first_quarter])-1
        year_arr[0:underhang,:]=(np.asmatrix(
                    [parr]*underhang)
                    -(np.asmatrix([np.arange(underhang)/365.24]*len(parr))).T)
        
        index_tracker=underhang
        for period in hold_period:
            year_arr[index_tracker:index_tracker+period,:]=(
                        np.asmatrix([parr]*period)
                        )-(np.asmatrix([np.arange(period)/365.24]*len(parr))).T
            index_tracker=index_tracker+period
        # Need to fix the "overhang"; fill in data corresponding to the current
        # month/quarter which has not finished
        overhang=len(self.data)-index_tracker
        #overhang_period=np.arange(overhang)      
        year_arr[index_tracker:index_tracker+overhang,:]=(np.asmatrix(
                    [parr]*overhang)
                    -(np.asmatrix([np.arange(overhang)/365.24]*len(parr))).T)
        
        #test=(np.asmatrix([parr]*len(hold_period))
        #      )-(np.asmatrix([hold_period]*len(parr))).T
        # Tile this result?
        
        #
        arg1=np.array(np.asmatrix(1/self.data.TAU1).T*np.asmatrix(
                    np.ones(len(parr))))*np.array(year_arr)
        
        arg2=np.array(np.asmatrix(1/self.data.TAU2).T*np.asmatrix(
                    np.ones(len(parr))))*np.array(year_arr)
                  
        # Construct the zero yields for all elements in parr and for all dates
        term1=np.array(
            np.asmatrix(self.data.BETA0).T*np.asmatrix(np.ones(len(parr))))
        
        term2=np.array(
            np.asmatrix(self.data.BETA1).T*np.asmatrix(np.ones(len(parr))))*(
                1-np.exp(-arg1))/arg1
        
        term3=np.array(
            np.asmatrix(self.data.BETA2).T*np.asmatrix(np.ones(len(parr))))*(
                (1-np.exp(-arg1))/arg1-np.exp(-arg1))
                
        term4=np.array(
            np.asmatrix(self.data.BETA3).T*np.asmatrix(np.ones(len(parr))))*(
                (1-np.exp(-arg2))/arg2-np.exp(-arg2))
         
        # This gives a weird numerical result that I don't understand;
        # higher yields at shorter maturities which does not agree with 
        # zero_yields
        yield_arr=(term1+term2+term3+term4)/100
        # An additional idea: make sure that ycont matrix elements are returned
        # with their respective dates!
        # 2 December 2021: It does appear to work, so far.
        yield_arr=pd.DataFrame(data=yield_arr,index=self.data.index)
                
        # A possible option is to enforce a trading cost every time the bond is
        # "rolled"
        
        # 2022-Feb-01: This does not seem to work to get the return correctly;
        # Cumulative return is far too large. Try to find the error and correct
        # BE AWARE: coupon here is the actual dollar amount of money paid;
        # A par equivalent yield bond would use rate/2 to get the coupon here.
        # I think this is correct now; quarterly return looks reasonable.
        p_annuity=par_val*coupon*np.sum(
                np.exp(-np.array(yield_arr)*np.array(year_arr)),axis=1)
        
        p_principal=par_val*(self.data.BETA0**0*(np.squeeze(np.array(
            np.exp(-yield_arr.values[:,-1]*np.squeeze(
                np.array(year_arr[:,-1])))))))
        
        bond_price=p_annuity+p_principal
        
        buy_dates=par_rate.resample('QS').asfreq()[self.data.index[0]:
                                                        self.data.index[-1]
                                                        ].index[:-1].insert(
                                                    0,par_rate.index[0])
        
        sell_dates=(buy_dates[1:].append(par_rate.index[-1:])
                        -pd.DateOffset(days=1))
        
        quarterly_return=bond_price[sell_dates]/bond_price[buy_dates].values
        
        
        # Here is my solution, assuming bond is sold on sell date, bought on
        # buy date (I currently wait 1 day to settle. May want to adjust this
        # to same day, which simulates margin settlement, or something else)
        daily_return=np.zeros(len(bond_price)-1)
        dr_iter_start=0
        for i in range(len(buy_dates)):
            daily_return[
                dr_iter_start:dr_iter_start+len(
                    bond_price[buy_dates[i]:sell_dates[i]])-1]=bond_price[
                                buy_dates[i]:sell_dates[i]].values[1:]/(
                            bond_price[buy_dates[i]:sell_dates[i]].values[:-1])
            
            # Okay, so this is somewhat confusing, but here is the solution:
            # make the last return factor equal to one for each iteration. 
            # This represents the one day we sit in cash waiting to buy the
            # next issue. 
            daily_return[dr_iter_start+len(
                    bond_price[buy_dates[i]:sell_dates[i]])-1]=1.0
            
            dr_iter_start=dr_iter_start+len(
                                bond_price[buy_dates[i]:sell_dates[i]])
                                    
        
        daily_return=pd.Series(data=daily_return,index=self.data.index[1:])
        
        # Need to return the duration as well...
        # Calculate ytm now:
        # Calculate accrued interest
        ai=coupon*par_val*(years_to_mat-np.squeeze(np.array(year_arr[:,-1])))
        ytm=np.zeros(len(bond_price))
        mac_dur=np.zeros(len(bond_price))
        mod_dur=np.zeros(len(bond_price))
        for counter, price in enumerate(bond_price):
            # We have to subtract the accrued interest from the bond price,
            # otherwise we do not have the clean yield.
            ytm[counter]=newton(func=get_ytm,x0=par_rate[counter], 
                 args=(coupon[counter],
                       np.squeeze(np.array(year_arr[counter,-1])),
                       price-ai.values[counter],))
            
            payment_array=par_val*coupon[counter]*np.ones(
                            len(np.squeeze(np.array(year_arr[counter,:]))))
            payment_array[-1]=payment_array[-1]+par_val
         
            # I think it makes the most sense to use the clean price for 
            # Macaulay duration.
            mac_dur[counter]=np.sum(payment_array*np.array(
                                year_arr[counter,:])*np.exp(
                                    -np.array(
                                    yield_arr.values[counter,:])*np.array(
                                    year_arr[counter,:])))/(
                                        price-ai.values[counter])
            # Hopefully this calculation is correct!
            mod_dur[counter]=mac_dur[counter]/(1+ytm[counter]/2)
         
        # Macaulay and Modified duration need to be turned into data series
        mac_dur=pd.Series(data=mac_dur,index=self.data.index)
        mod_dur=pd.Series(data=mod_dur,index=self.data.index)
    
        return bond_price,ytm,daily_return,quarterly_return,mac_dur,mod_dur
    
    def par_yield(self,years_to_mat,nss=True):
        # I think this should work! Seems to work for any maturity
        parr=payment_time_array(years_to_maturity=years_to_mat)
        yield_arr=self.zero_yields(tarr=parr,beta3=nss)
        # Compute the par equivalent yield; I think this is correct
        # A par yield should be the same as a constant maturity yield
        ypar=2*(1-np.exp(-parr[-1]*yield_arr.values[:,-1]))/(
            np.exp(-yield_arr*parr).sum(axis=1))
        
        return ypar
    
    def duration_from_par_yield(self,years_tm,use_full_nss=True):
        ypar=self.par_yield(years_to_mat=years_tm,nss=use_full_nss)
        # convert the par yield to exponentional, for easier calculation.
        # I should still test to make sure that I have correct modified 
        # duration; maybe calculate multiple durations here, like Macaulay,
        # modified, Fisher Weil, etc.
        yexp=(2*np.log(1+ypar/2))
        # We also need the time array for the cash flow
        parr=payment_time_array(years_to_maturity=years_tm)
        # I think this is calculated correctly!
        modified_duration=(yexp/2*np.squeeze(np.asarray((
                            np.exp(-np.asmatrix(yexp.values).T*
                            np.asmatrix(parr))*np.asmatrix(parr).T)))+
                               parr[-1]*np.exp(-parr[-1]*yexp))
        # Calculate Macaulay duration here.
        # Fisher Weil if I get around to it.
        return modified_duration
    
    def duration_from_coupon_and_ytm(self,years_to_mat,nss=True):
        # Consider a separate function to compute duration with an arbitrary
        # yield to maturity, provided the coupon is known.
        
        print('Not implemented yet.')
        duration=0
        return duration
    
    def cumulative_return(self,years_tm,hold_period=1/365.24,nss=True):
        # Also need a separate method for cumulative return for zero coupon
        # bonds!
        # Maybe just make this daily, and then the user can resample it 
        # themself?
        # This method assumes you can just sell the bond, aged buy the holding
        # period, and then buy another bond of the same maturity; this is 
        # obviously not always possible.
        
        # We need special logic if the return period occurs after a coupon!
        # i.e., perform error checking for hold_period!
        
        # Error checking for years to maturity is needed!
        
        
        parr=payment_time_array(years_to_maturity=years_tm)
        yield_arr=self.zero_yields(tarr=parr,beta3=nss)
        # First, calculate the bond price corresponding to the years to 
        # maturity.
        # What do we use for the coupon??
        # Maybe this can work, from 2006 Gurkaynak, even for arbitrary maturity 
        # (I divided equation 7 by 2)
        # c_payment=2*(1-np.exp(-parr[-1]*yield_arr.values[:,-1]))/(
        #     np.exp(-yield_arr*parr).sum(axis=1))
        c_payment=(1-np.exp(-parr[-1]*yield_arr.values[:,-1]))/(
            np.exp(-yield_arr*parr).sum(axis=1))
        
        # Calculate the price of a (par bond)? with time in years to maturity;
        # Should this not just be 1000??
        # p_buy=self.bond_price_from_zero_yields(years_to_mat=years_tm,
        #                                 coupon=c_payment,par_val=1,nss=True)
        
        #p_buy=self.data.BETA0**0
        
        # It looks like the coupon payment as written above works; can we
        # then just assume that p_buy=par_val?
        
        # hold period is how long the bond is held in years before being 
        # turned over into another bond with the same years to maturity as the
        # originally purchased issue.
        # 29 Jan 2022: I think shift() only works for hold period of 1 day
        p_sell=self.bond_price_from_zero_yields(
            years_to_mat=(years_tm-hold_period),
            coupon=c_payment.shift().values,par_val=1,nss=True)
        
        # A time series array of the return fraction.
        # The return is posted on the "sell" date, so the series gets shifted
        # forward by one frequency increment.
        #yreturn=p_sell[1:]/p_buy[:-1].values
        daily_return=p_sell
        
        cumulative_return=daily_return.cumprod()
        
        # Consider also returning the log returns??
    
        return daily_return,cumulative_return
    
    def cumulative_strips_return(self,maturity_years,hold_period=1/365.24,
                                 nss=True):
        # need logic for hold_period
        # Need error checking for maturity years; must be >0 and <30.
        ybuy=self.zero_yields(tarr=np.array([maturity_years]),beta3=nss)
        ysell=self.zero_yields(tarr=np.array([maturity_years-hold_period]),
                               beta3=nss)
        
        # May need to fix so that it is a series instead of dataframe with one
        # column
        daily_return=np.exp(ybuy[:-1].values*maturity_years)/(
            np.exp(ysell[1:]*(maturity_years-hold_period)))
            
        cumulative_return=daily_return.cumprod()
        
        # Consider also returning the log returns??
        
        return daily_return,cumulative_return
    
    
    