'''

iv_test.py

1 September 2019
Jeffrey J. Walker

A simple test of the implied_volatility function.

'''

from implied_volatility import implied_volatility

strike=290.0
St=292.45
rfr=(1.933)/100
texp=3/365.0
sig=(23.5665/100)
otype='c'
oprice=3.235

iv=implied_volatility(o_price=oprice,S=St,K=strike,r=rfr,T=texp,sigma=sig,o_type=otype)

print("Implied Volatility:"+str(iv))
