#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  1 22:36:06 2022

@author: jeff
    fred_api.py
        This function uses FRED's API to retrieve data.
"""

import pandas as pd

def fred_api(series_id,realtime_start='1776-07-04',realtime_end='9999-12-31',
             key='0588ecec1c9cbf3d37c551e9f821a1c9'):

    #tnow=pd.to_datetime('today').now()

    #key='0588ecec1c9cbf3d37c551e9f821a1c9'

    #series_id='DFF'

    #realtime_start=(tnow-pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    #realtime_end=tnow.strftime('%Y-%m-%d')

    # Use 1776-07-04 as default start
    # 9999-12-31 as default end
    #&realtime_start=1776-07-04&realtime_end=9999-12-31&


    url=('https://api.stlouisfed.org/fred/series/observations?series_id='+
        series_id+
        '&realtime_start='+realtime_start+
        '&realtime_end='+realtime_end+
        '&api_key='+key+'&file_type=json')

    # The more basic query url:
        # url_ex=('https://api.stlouisfed.org/fred/series?series_id='+
        #         series_id+'&api_key='+
        #         key+'&file_type=json')

    json_data=pd.read_json(url)

    nobs=len(json_data['observations'])

    dates=[]
    values=[]

    for obs in range(nobs-365,nobs):
        values.append(float(json_data['observations'][obs]['value']))
        dates.append(json_data['observations'][obs]['date'])
   
    series_data=pd.Series(data=values,index=pd.to_datetime(dates),name='DFF')
    
    return series_data