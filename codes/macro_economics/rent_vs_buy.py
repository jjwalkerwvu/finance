#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 15 15:06:34 2021

@author: jeff

A short script that calculates the cost of renting vs cost of our mortgage
"""

import numpy as np


## price of fixed mortgage; %2.05 and 440000 principal
mort=12*1635.14
principal=440e3
## Annual cost of maintenance, hoa, taxes (0.0428), maybe taxes will change, 
## I don't know.
## Original estimate from site (?) had %2.25
prop_tax=0.0428/100*principal
## cost per month multiplied by 12 months
hoa=175.03*12;
maintenance=0.01*principal
home_cost=prop_tax+hoa+maintenance
## include erfpacht?
## tax benefit? No inflation adjustment, I think.
tax_deduct=12*204.0
## I don't think the insurance is inflation adjusted?
insurance=12*14;

## initial capital needed to purchase the house
capital_outlay=20e3

## I checked breakeven inflation; it was %1.9 for May 2019 when we bought the
## house, which corresponds to %1.884 compounded monthly.
## Maybe annual compounding is fine? Since a lease adjusts annually.
inflation=0.019
## ~27 year break even from Germany (as a proxy for NL)
## Jul 4 2046 Maturity had yield 0.5 on 15 may 2019, when we bought the house
## ISIN: DE0001102341 WKN: 110234
## Closest Inflation linked bond: ISIN: DE0001030575, WKN: 103057 (30 yr)
## Maturity date: 14.04.2046
## Yield on reopening, date: 07.05.2019: -0.76
## (This bond had a maturity of ~27 years at this date)
## This gives a breakeven ~0.5-(-0.76)=1.26
## In the future: 
## Use bond data from this website:
## https://www.deutsche-finanzagentur.de/en/institutional-investors/federal-securities/list-of-tradable-securities/

## monthly rent, mortgage
## Monthly rent is based on ad I saw for an apartment in (our) Blok 17.
## 95 m^2, maybe slightly smaller but as close of a comparison as I could find
## The landlord specified a %2.5 annual increase in the rent, no utilities
## were provided.
## Problem with this, however, is that the landlord allows 2 year max stay,
## so tenant would have to move. Apartment is fully furnished.
## To be more generous to the renter case, back the rent up by 2 years'
## inflation
rent=12*1595/(1+0.025)**2
## security deposit:
deposit=2*rent/12


## long run sp500/total stock market performance, L O L
sp_growth=0.1

nyears=30
val=np.zeros(nyears);
pay=0;
sp_invest=np.zeros(nyears)
statement=False;
for i in range(nyears):
    val[i]=rent*(1+inflation)**i
    pay=mort-tax_deduct+insurance+(home_cost)*(1+inflation)**i
    #sp_invest=sp_invest*(1+0.0957/12)+(pay-val)*(pay>=val)
    sp_invest[i]=sp_invest[i-1]*(1+sp_growth)+(pay-val[i])*(pay>=val[i])
    #print(sp_invest)
    if (val[i]>=pay)&(statement==False):
        print(i)
        statement=True

## value of portfolio for the renter        
rent_value=sp_invest[-1]+(capital_outlay-deposit)*(1+sp_growth)**nyears
home_value=principal*(1+inflation)**nyears
## value for owner's portfolio, assuming only inflation rises the price
## (I THINK THIS ASSUMPTION MAY BE DUBIOUS)
print('Renter has: ~$'+str(rent_value))
print('Homeowner has: ~$'+str(home_value))