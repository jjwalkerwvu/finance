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
        
        maturity_start=(maturity_date-start_date).days
        maturity_end=(maturity_date-end_date).days
        
        return
    
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
    
    
    