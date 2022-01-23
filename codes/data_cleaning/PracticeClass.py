#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 16:03:26 2021

@author: jeff
"""

class PracticeClass:
    def __init__(self,issuer,cashflow_df):
        self.issuer=issuer
        self.cashflow_df
        
    def main_method(self):
        print_string='0'
        return print_string
        
        
class PracticeOne(PracticeClass):
    def __init__(self,issuer,extra_variable,cashflow_df):
        self.issuer='US'
        self.extra_variable=extra_variable
        self.cashflow_df=cashflow_df
        super().__init__(issuer, cashflow_df)
        
    @classmethod
    def get_extra_variable(cls):
        
        variable='a_string'
        parent_attribute='attribute set successfully'
        
        return cls('US',variable,parent_attribute)
    
    def set_parent_attribute(self):
        
        self.cashflow_df='attribute reset with child method'
        
        return super().__init__(self.issuer, self.cashflow_df)