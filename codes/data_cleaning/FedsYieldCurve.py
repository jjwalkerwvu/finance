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
import requests
import io
from scipy.optimize import newton
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

def payment_time_array(years_to_maturity):
    # time until each payment, in years
    # December 1, 2021: This appears to work, but maybe I did not test
    # enough!
    # Does not work for age with exactly .5
    # December 2, 2021: NOT WORKING FOR GREATER THAN .5 INCREMENTS!
    # Date unknown: Seems to work fine now.
    # For more realism, you may want to incorporate actual coupon payment 
    # dates, but this should be close enough.
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

# Note that this function assumes semi-annual compounding.
def get_ytm(y,c,nperiods,bond_price):
    
    par_val=1000.0
    
    # the function we need to set equal to 0
    # f=(c*par_val*np.sum(np.exp(-year_arr*y))+par_val*np.exp(-yarr[-1]*y)-
    #    bond_price)
    
    f=(2*c*par_val/y*(1-(1+y/2)**(-2*nperiods))
       + par_val/(1+y/2)**(2*nperiods)
       - bond_price)
    
    return f

# A standalone function that computes the spread for a given maturity 
# note/bond
# The numbers are the mean % spread, taken from Pasquariello, 2009, but these
# are just-off-the-run! Need fully off the run spreads.
# See also 2003 Fleming
def bid_ask_spread(years_to_maturity,strips=False):
    # The output is in percent!
    
    # Fill this in as I get better data
    spread_percentage=(0.275*((years_to_maturity>=1.) & 
                              (years_to_maturity<=1.75))
                      +0.017*((years_to_maturity>1.75) & 
                              (years_to_maturity<=3.25))
                      +0.03*((years_to_maturity>3.25) & 
                             (years_to_maturity<=7.5))
                      +0.054*(years_to_maturity>7.5))
    
    # The strips spread is much greater than the above, like 0.5% of the 
    # purchase value
    if strips==True:
        # OTR strips have a 0.5% spread, but others may be even worse!
        spread_percentage=0.5
        
    return spread_percentage

class FedsYieldCurve:

    def __init__(self,data):
        
        self.data=data

    # This is working, for now
    # Initialize like: a=FedsYieldCurve.get_data()
    @classmethod
    def get_data(cls,header_line=7):
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
            print('Reading the url with pandas failed. Trying again with requests')
            try:
                response = requests.get(
                    'https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv')
                file_object = io.StringIO(response.content.decode('utf-8'))
                # for some reason the header changed from 7 to zero?
                zc=pd.read_csv(file_object,sep=',',header=header_line)
                print('Data retrieved Successfully.')
                zc['Date']=pd.to_datetime(zc.Date,infer_datetime_format=True)
                zc.set_index('Date',inplace=True)
                # Here is an idea, to allow for arbitrary return periods;
                # Do a daily resample with forward fill.
                zc=zc.resample('D').asfreq().fillna(method='ffill')
                print('Please note: the data has been resampled to daily '+
                  'frequency, which means that weekends and non-business days'+
                  ' are now included.')
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
    
    def instantaneous_forward_rate(self,tarr,beta3=True):
        
        term1=np.asmatrix(self.data.BETA0).T*np.asmatrix(np.ones(len(tarr)))

        # The rate of convergence of the curve to the long term trend
        term2=(np.array(np.asmatrix(self.data.BETA1).T*np.asmatrix(
            np.ones(len(tarr))))*
                  np.array(np.exp(-np.asmatrix(1/self.data.TAU1).T*(
                      np.asmatrix(tarr)))))
                          
        # The size and shape of the first hump
        term3=(np.array(np.asmatrix(self.data.BETA2).T*np.asmatrix(
            np.ones(len(tarr))))*
                  np.array(np.exp(-np.asmatrix(1/self.data.TAU1).T*(
                      np.asmatrix(tarr))))*np.array(
                          np.asmatrix(1/self.data.TAU1).T*np.asmatrix(tarr)))   
                          
        # The size and shape of the second hump
        if beta3==True:
            term4=(np.array(np.asmatrix(self.data.BETA3).T*np.asmatrix(
                np.ones(len(tarr))))*
                  np.array(np.exp(-np.asmatrix(1/self.data.TAU2).T*(
                      np.asmatrix(tarr))))*np.array(
                          np.asmatrix(1/self.data.TAU2).T*np.asmatrix(tarr))) 
        else:
            term4=0
    
        # Just calculate the continuous yields, there is no real need to waste
        # time converting to coupon equivalent.
        # Also, ycont is no longer in percent if we divide by 100
        f=(term1+term2+term3+term4)/100
        # An additional idea: make sure that ycont matrix elements are returned
        # with their respective dates!
        # 2 December 2021: It does appear to work, so far.
        f=pd.DataFrame(data=f,index=self.data.index)
        return f
    
    def forward_yields(self,n,m):
        # Fill in the equation to get forward yields later.
        # This will be the n-by-m forward rate, not instantaneous forward rate
        
        # n_period forward:
        yn=self.zero_yields(np.array([n]))
        ymn=self.zero_yields(np.array([m+n]))
        fnm=(1/m)*((n+m)*ymn-n*yn)
        
        # Just a line of code I have demonstrating how to make returns from 
        # carry (possibly)
        # plt.figure();plt.plot(zc.forward_yields(9.75,0.25));plt.plot(5*zc.forward_yields(2,0.25)-4*zc.zero_yields(np.array([0.25])))
        
        return fnm
    
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
    
    # Not implemented!
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
    
    # 2023-06-30: This needs testing for the new feature: improved duration
    # calculations
    # Need to also get rid of the 1 day settlement!
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
        # An additional idea: make sure that ycont matrix elements are 
        # returned with their respective dates!
        # 2 December 2021: It does appear to work, so far.
        yield_arr=pd.DataFrame(data=yield_arr,index=self.data.index)
                
        # A possible option is to enforce a trading cost every time the bond 
        # is "rolled"
        
        # 2022-Feb-01: This does not seem to work to get the return correctly;
        # Cumulative return is far too large. Try to find the error and correct
        # BE AWARE: coupon here is the actual dollar amount of money paid;
        # A par equivalent yield bond would use rate/2 to get the coupon here.
        # I think this is correct now; quarterly return now looks reasonable.
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
        
        # Maybe here is where we impose the cost of the spread.
        bond_price[buy_dates]=bond_price[buy_dates]*(
                                        1+bid_ask_spread(years_to_mat)/200)
        
        bond_price[sell_dates]=bond_price[sell_dates]*(
                                        1-bid_ask_spread(years_to_mat)/200)
        
        quarterly_return=bond_price[sell_dates]/bond_price[buy_dates].values
        
        
        # Here is my solution, assuming bond is sold on sell date, bought on
        # buy date (I currently wait 1 day to settle. May want to adjust this
        # to same day, which simulates margin settlement, or something else)
        daily_return=np.zeros(len(bond_price)-1)
        dr_iter_start=0
        for i in range(len(buy_dates)):
            # Should probably use .loc here
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
                                        
            # mac_dur should use ytm.
            # Test this out before implementing!
            # mac_dur[counter]=np.sum(payment_array*np.array(
            #                     year_arr[counter,:])*np.exp(
            #                         -np.array(
            #                         (2*(np.log(1+ytm[counter]/2))))*np.array(
            #                         year_arr[counter,:])))/(
            #                             price-ai.values[counter])
            
            
            # Hopefully this modified duration calculation is correct!
            # k=2 for semi-annual compounding
            k=2
            mod_dur[counter]=mac_dur[counter]/(1+ytm[counter]/k)
         
        # turn ytm into a data series
        ytm=pd.Series(data=ytm,index=self.data.index)
        # Macaulay and Modified duration need to be turned into data series
        mac_dur=pd.Series(data=mac_dur,index=self.data.index)
        mod_dur=pd.Series(data=mod_dur,index=self.data.index)
    
        return bond_price,ytm,daily_return,quarterly_return,mac_dur,mod_dur
    
    
    # Need to also get rid of the 1 day settlement!
    # Same as bond_price_quarterly_reset, but for STRIPS (zero-coupon bonds)
    def strips_price_quarterly_reset(self,years_to_mat,par_val=1000,nss=True):
    
        buy_yield=self.zero_yields(tarr=np.array([years_to_mat]))
        
        buy_yield_quarterly=buy_yield.resample('QS').asfreq()[
                                self.data.index[0]:self.data.index[-1]]
        
        first_quarter=buy_yield_quarterly.index[0]
        
        # reindex non-quarter start dates to nans
        buy_yield_quarterly=buy_yield_quarterly.reindex(self.data.index)
        
        # Set all data in the first quarter equal to the first yield value
        buy_yield_quarterly[0][:first_quarter][:-1]=buy_yield[0][0]
        
        # The buy price; impose the bid-ask spread
        # buy_price=par_val*np.exp(-buy_yield*years_to_mat
        #                     ).resample('QS').asfreq()[self.data.index[0]:
        #                     self.data.index[-1]]*(
        #                     1+bid_ask_spread(years_to_mat,strips=False)/200)
                    
                        
        buy_dates=buy_yield.resample('QS').asfreq()[self.data.index[0]:
                                                        self.data.index[-1]
                                                        ].index[:-1].insert(
                                                    0,buy_yield.index[0])                                                   
         
        hold_period=(buy_yield.resample('QS').asfreq()[
                        self.data.index[0]:self.data.index[-1]].index[1:]
                        -buy_yield.resample('QS').asfreq()[
                            self.data.index[0]:self.data.index[-1]].index[:-1]
                        ).days.values    

        # How to make the year array?
        year_arr=np.empty(len(self.data))
        # What if there are days before the first quarter starts?
        # You need to subtract 1 to get this to work out!
        underhang=len(self.data[buy_yield.index[0]:first_quarter])-1
        year_arr[0:underhang]=years_to_mat-np.arange(underhang)/365.24
                    
        
        index_tracker=underhang
        for period in hold_period:
            year_arr[index_tracker:index_tracker+period]=(years_to_mat
                            -np.arange(period)/365.24)
            index_tracker=index_tracker+period
        # Need to fix the "overhang"; fill in data corresponding to the 
        # current month/quarter which has not finished
        overhang=len(self.data)-index_tracker
        #overhang_period=np.arange(overhang)      
        year_arr[index_tracker:index_tracker+overhang]=(years_to_mat
                                                -np.arange(overhang)/365.24)
           
         
        # arg1=np.array(np.asmatrix(1/self.data.TAU1).T*np.asmatrix(
        #             np.ones(1)))*np.array(year_arr)
        
        arg1=(1/self.data.TAU1)*year_arr
        
        # arg2=np.array(np.asmatrix(1/self.data.TAU2).T*np.asmatrix(
        #             np.ones(1)))*np.array(year_arr)
        arg2=(1/self.data.TAU2)*year_arr
                  
        # Construct the zero yields for all elements in parr and for all dates
        # term1=np.array(
        #     np.asmatrix(self.data.BETA0).T*np.asmatrix(np.ones(1)))
        term1=self.data.BETA0
        
        # term2=np.array(
        #     np.asmatrix(self.data.BETA1).T*np.asmatrix(np.ones(1)))*(
        #         1-np.exp(-arg1))/arg1
        term2=self.data.BETA1*(1-np.exp(-arg1))/arg1
        
        # term3=np.array(
        #     np.asmatrix(self.data.BETA2).T*np.asmatrix(np.ones(1)))*(
        #         (1-np.exp(-arg1))/arg1-np.exp(-arg1))
        term3=self.data.BETA2*((1-np.exp(-arg1))/arg1-np.exp(-arg1))
                
        # term4=np.array(
        #     np.asmatrix(self.data.BETA3).T*np.asmatrix(np.ones(1)))*(
        #         (1-np.exp(-arg2))/arg2-np.exp(-arg2)) 
        term4=self.data.BETA3*((1-np.exp(-arg2))/arg2-np.exp(-arg2))  
                
        yield_arr=(term1+term2+term3+term4)/100
       
        #sell_price=par_val*np.exp                                                   
    
        p_principal=par_val*(self.data.BETA0**0*(np.squeeze(np.array(
            np.exp(-yield_arr.values*np.squeeze(
                np.array(year_arr)))))))
        
        bond_price=p_principal
        
        sell_dates=(buy_dates[1:].append(self.data.index[-1:])
                        -pd.DateOffset(days=1))
        
        # Maybe here is where we impose the cost of the spread.
        bond_price[buy_dates]=bond_price[buy_dates]*(
                1+0*bid_ask_spread(years_to_mat,strips=False)/200)
        
        bond_price[sell_dates]=bond_price[sell_dates]*(
                1-0*bid_ask_spread(years_to_mat,strips=False)/200)
        
        quarterly_return=bond_price[sell_dates]/bond_price[buy_dates].values
        
        # Here is my solution, assuming bond is sold on sell date, bought on
        # buy date (I currently wait 1 day to settle. May want to adjust this
        # to same day, which simulates margin settlement, or something else)
        daily_return=np.zeros(len(bond_price)-1)
        dr_iter_start=0
        for i in range(len(buy_dates)):
            # Should probably use .loc here
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
        
        mac_dur=pd.Series(data=year_arr,index=self.data.index)
        # modified duration and Macaulay duration should be equal for the zero
        # coupon bond, because the yield is expressed continuously compounded
        mod_dur=mac_dur
        # yield to maturity should just be the yield array, calculated earlier
        ytm=yield_arr
    
        return bond_price,ytm,daily_return,quarterly_return,mac_dur,mod_dur
    
    def bond_price_quarterly_reset_to_dataframe(self,years_to_mat=5,
                                                par_val=1000,nss=True,
                                                write_to_file=False,
                                                path='/Users/31643/Desktop/finance_2023/data/bonds/'):
        
        ytm_str=str(years_to_mat)
        
        bond_price,ytm,daily_return,quarterly_return,mac_dur,mod_dur=(
        self.bond_price_quarterly_reset(years_to_mat,par_val=par_val,nss=nss))
        
        # make a column for the return of 1 dollar?
        return_of_1_dollar=daily_return.cumprod()
        
        df=pd.concat([ytm,bond_price,daily_return,quarterly_return,
                      mac_dur,mod_dur],axis=1)
        
        df.rename(columns=dict(zip(df.columns.to_list(),
                                   [ytm_str+"y_yield",
                                    ytm_str+"y_parbond_price",
                                    ytm_str+"y_daily_return",
                                    ytm_str+"y_quarterly_return",
                                    ytm_str+"y_mac_dur",
                                    ytm_str+"y_mod_dur"])),inplace=True)
        
        df[ytm_str+"y_return_of_1_dollar"]=return_of_1_dollar
        
        filename=path+ytm_str.replace('.','_')+'y_maturity.csv'
        if write_to_file==True:
            df.to_csv(filename,index=False)
        
        return df
    
    def strips_price_quarterly_reset_to_dataframe(self,years_to_mat=5,
                                                par_val=1000,nss=True,
                                                write_to_file=False,
                                                path='/Users/31643/Desktop/finance_2023/data/bonds/'):
        
        ytm_str=str(years_to_mat)
        
        bond_price,ytm,daily_return,quarterly_return,mac_dur,mod_dur=(
        self.strips_price_quarterly_reset(years_to_mat,par_val=par_val,nss=nss))
        
        # make a column for the return of 1 dollar?
        return_of_1_dollar=daily_return.cumprod()
        
        df=pd.concat([ytm,bond_price,daily_return,quarterly_return,
                      mac_dur,mod_dur],axis=1)
        
        df.rename(columns=dict(zip(df.columns.to_list(),
                                   [ytm_str+"y_yield",
                                    ytm_str+"y_parbond_price",
                                    ytm_str+"y_daily_return",
                                    ytm_str+"y_quarterly_return",
                                    ytm_str+"y_mac_dur",
                                    ytm_str+"y_mod_dur"])),inplace=True)
        
        df[ytm_str+"y_return_of_1_dollar"]=return_of_1_dollar
        
        filename=path+ytm_str.replace('.','_')+'y_maturity.csv'
        if write_to_file==True:
            df.to_csv(filename,index=False)
        
        return df
    
    # 2023-06-30: This needs testing for the new feature:
    # calculating the par yield when a coupon bond has accrued interest
    def par_yield(self,years_to_mat,nss=True):
        # I think this should work! Seems to work for any maturity
        parr=payment_time_array(years_to_maturity=years_to_mat)
        yield_arr=self.zero_yields(tarr=parr,beta3=nss)
        # Compute the par equivalent yield; I think this is correct
        # A par yield should be the same as a constant maturity yield at t=0
        ypar=2*(1-np.exp(-parr[-1]*yield_arr.values[:,-1]))/(
            np.exp(-yield_arr*parr).sum(axis=1))
        
        # 2023-05-14: 
        # I'm not sure, but I think the above expression needs to be modified 
        # when there is accrued interest.
        # Need to test and check this, but this should be the correction:
        # ypar=2*(1-np.exp(-parr[-1]*yield_arr.values[:,-1]))/(
        #     np.exp(-yield_arr*parr).sum(axis=1)+(1-2*parr[0]))
        
        # I think it makes the most sense to use the clean price for 
        # Macaulay duration.
        # mac_dur=np.sum(payment_array*np.array(parr)*np.exp(-np.array(
        #                      yield_arr)*np.array(parr[counter,:])))/(price)
        # Hopefully this calculation is correct!
        # mod_dur[counter]=mac_dur[counter]/(1+ypar/2)
        
        return ypar
    
    def par_yield_curve(self,tarr,nss=True):
        
        # For now, I have to restrict the tarr to years>=0.5
        rarr=tarr[tarr>=0.5]
        # Initiate the dataframe with the first maturity
        par_curve=self.par_yield(rarr[0]).to_frame(name=str(float(rarr[0])))
        
        for t in rarr[1:]:
            par_curve[str(float(t))]=self.par_yield(t)
            
        # Make sure to also calculate the durations!
                
        return par_curve
    
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
    
    # 2023-06-30:
    # Not implemented; consider deleting this method because the idea was 
    # already better implemented in bond_price_quarterly_reset and 
    # strips_price_quarterly_reset
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
    
    # Not implemented, consider deleting this method, and the output is likely
    # unrealistic
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
    
    
    def plot_curves(self,tmeas=pd.to_datetime('today').now(),
                    tarr=np.arange(1,31),n=1):
        
        # The default measurement date is the latest date in the data, but we
        # should allow for any arbitrary date
        tmeas=pd.to_datetime(tmeas)
        if tmeas not in self.data.index:
            tmeas=self.data.index[-1]
            
        # tmeas=self.data.index[-1]
        
        # time in seconds:
        tsec=tarr*365.24*24*3600
        
        time_index=pd.DatetimeIndex([tmeas+relativedelta(seconds = int(ysec)) 
                              for ysec in tarr*365.24*24*3600])
    
        # par equivalent yield curve; redo this to be consistent with the
        # tenors in tarr
        par_curve=self.data.loc[tmeas][37:67].values
        # need separate array for the par curve right now
        par_arr=np.arange(1,31)
        parr_index=pd.DatetimeIndex([tmeas+relativedelta(seconds = int(ysec))  
                              for ysec in par_arr*365.24*24*3600])
        
        
        # zero coupon curve at the reference
        zc=100*self.zero_yields(tarr).loc[tmeas]
        # instantaneous forward rate
        inst_forward=100*self.instantaneous_forward_rate(tarr).loc[tmeas]
        # n_period forward:
        yn=100*self.zero_yields(np.array([n])).loc[tmeas]
        n_period_forward=1/(tarr-n)*(tarr*zc-n*yn[0]) 
        # 2023-06-21:
        # Put the m-year rate, beginning in n-years in a separate method?
        # I just put in here and commented out for now.
        # m=10 for the example below.
        #m_year_forward=1/(10)*((10+tarr)*yield_curve.zero_yields(10+tarr)-tarr*yield_curve.zero_yields(tarr))
        # Get rid of any entries that are less than the n-period
        n_period_forward=n_period_forward[tarr>n]
        n_forward_time=pd.DatetimeIndex(
                        [tmeas+relativedelta(seconds = int(ysec)) for 
                              ysec in (tarr[tarr>n]-n)*365.24*24*3600])
        
            
        plt.figure(figsize=(18, 6))
        plt.title('Off-The-Run Treasury Yield Curves as of: '+tmeas.strftime("%Y-%m-%d"))
        plt.ylabel('Yield (%)')
        plt.xlabel('Maturity Date')
        plt.plot(parr_index,par_curve,label='Par-Equivalent Yield Curve')
        plt.plot(time_index,zc,label='Zero-Coupon Rate')
        plt.plot(time_index,inst_forward,label='Instantaneous Forward Rate')
        plt.plot(n_forward_time,n_period_forward,'--',
                 label='Zero-Coupon Rate,'+' '+str(n)+'-year(s) forward')  
        plt.xlim(tmeas)
        plt.legend(loc='best')
        plt.tight_layout()
        # need option to save the figure!
        
        return
    
    # A method to plot multiple curves:
    def multi_plot(self,
                   tsnapshots=[
                       pd.to_datetime('today').now(),
                       pd.to_datetime('today').now()-pd.DateOffset(months=1),
                       pd.to_datetime('today').now()-pd.DateOffset(months=6)],
                   tarr=np.arange(1,31)):
        
        plt.figure(figsize=(18, 6))
        plt.title('Off-The-Run Zero Coupon Treasury Yield Curves')
        plt.ylabel('Yield (%)')
        plt.xlabel('Time to Maturity')
        for t in tsnapshots:
            zc=100*self.zero_yields(tarr).loc[t]
            # time_index=pd.DatetimeIndex([t+relativedelta(seconds=int(ysec)) 
            #                       for ysec in tarr*365.24*24*3600])
            plt.plot(tarr,zc,label="As of: "+t.strftime("%Y-%m-%d"))
        plt.xlim(0)
        plt.legend(loc='best')
        plt.tight_layout()   
        
        # Plot the forward rate curves, also
        plt.figure(figsize=(18, 6))
        plt.title('Off-The-Run Treasury Instantaneous Forward Rate Curves')
        plt.ylabel('Yield (%)')
        plt.xlabel('Time to Maturity')
        for t in tsnapshots:
            zc=self.data[self.data.columns[7:37]].loc[t].values
            plt.plot(tarr,zc,label="As of: "+t.strftime("%Y-%m-%d"))
        plt.xlim(0)
        plt.legend(loc='best')
        plt.tight_layout()  
        
        return
    
    # A method to plot the 3d yield surface
    def plot_surface(self,tarr=np.arange(1,31)):
        
        # zero coupon curve at the reference
        zc=100*self.zero_yields(tarr)  
        #
        index_value=np.arange(len(self.data.index))
        
        # convert data values to 2d arrays:
        x,y=np.meshgrid(tarr,index_value)
        
        fig=plt.figure()
        ax=plt.axes(projection='3d')
        ax.plot_surface(x,y,zc,cmap='viridis',edgecolor='none')
        plt.show()

        return
    
    # A method to calculate the expected return of a m-duration zero, held for 
    # some period thold, then sold and a new m-duration zero purchased, with
    # this process going on for invest_period (in years).
    # By expected return, I mean that this is the return you would get directly
    # from the yield curve.
    # Not implemented.
    def predicted_roll_return(self,m=5.125,thold=0.25,invest_period=10,
                              tmeas=pd.to_datetime('today').now()):
        
        # The default measurement date is the latest date in the data, but we
        # should allow for any arbitrary date
        tmeas=pd.to_datetime(tmeas)
        if tmeas not in self.data.index:
            tmeas=self.data.index[-1]
        
        # round number of rolls down
        n=np.floor(invest_period/thold)
        
        buy_arr=thold*np.arange(n)
        sell_arr=thold*np.arange(n)+thold
            
        # zero coupon curve at the reference
        zc_buy=100*self.zero_yields(buy_arr+m).loc[tmeas]
        zc_sell=100*self.zero_yields(buy_arr+m-thold).loc[tmeas]
        
        buy_fwd=1/m*(((buy_arr+m))*zc_buy-buy_arr*zc_buy)
        sell_fwd=1/(m-thold)*(((sell_arr+m-thold))*zc_sell
                              -(sell_arr)*zc_sell)
        
        return
    
    