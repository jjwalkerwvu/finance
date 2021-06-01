#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  2 21:01:40 2021

@author: jeff
"""

import requests
import ssl
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from bs4 import Comment
import pandas as pd
import numpy as np
import re

# Ignore SSL Certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'}




url='http://www.wsj.com/market-data/bonds/treasuries'
response = requests.get(url,headers=headers)

req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()



#response.content
#soup = BeautifulSoup(response.text, 'lxml')
#html = soup.prettify('utf-8')
#soup=BeautifulSoup(html, 'html5lib')
soup=BeautifulSoup(webpage, 'html5lib')
#soup.find('script',text=re.compile("window.__STATE__"))
#"mdc_treasury_{\"treasury\":\"NOTES_AND_BONDS\"}":{"set":1619992158978,"ttl":90000,"data":{"id":"{\"treasury\":\"NOTES_AND_BONDS\"}","type":"mdc_treasury","data":{"instruments"

#results=re.findall(r"askYield",soup.body.script.text)
#re.findall(r"BILLS",stuff.body.script.text)
s_ind=np.array([])
e_ind=np.array([])
matches=re.finditer(r'instruments',soup.body.script.text)
matches_list=[i for i in matches]
for i in matches_list:
    s_ind.append(i.start())
    e_ind.append(i.end())
    
for match in re.finditer(r'instruments',soup.body.script.text):
    s=match.start()
    e=match.end()
    s_ind=np.append(s_ind,s)
    e_ind=np.append(e_ind,e)
    print(s,e)
    
    
    