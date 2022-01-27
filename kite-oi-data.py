# https://tradingqna.com/t/is-the-live-open-interest-oi-data-being-provided-by-exchanges-correct/7208
# OI differences
# we can add max OI per 15 minutes and store to a pandas frame and much more, but hope this framework, gives you an idea on usage of Zerodha API

from kiteutils import kitelogin, get_symbol_token_list, set_symbol_token
import time
import pandas as pd
import numpy as np
import datetime

print( 'login')
kite, kws = kitelogin() # parameters are present in the import
print( 'Login successful')

exchange = 'NSE'
instrument = 'NIFTY BANK' # 'NIFTY 50'
bnf_symbol = exchange + ':' + instrument
print ('BankNify Index Symbol : {}'.format(bnf_symbol))
atm = kite.ltp(bnf_symbol)[bnf_symbol]['last_price']
atm = int(round(atm,-2))
print ('At the Money Rounded Strike {}'.format(atm))
frame = get_symbol_token_list("BANKNIFTY")

# The next three lines are output, to get an idea of what the code on top does and gives as output
# BankNify Index Symbol : NSE:NIFTY BANK
# At the Money Rounded Strike 37100
# Selected expiry : 2022-01-27

# print('symbol current ATM is:' ,atm)
# can add time here and then run per a time, while loop will have only few strikes and we will keep checking OI

Strike_Range = 9 # Range for which you want to do the sum

# sort the frame to get the strike_increments
x = frame[frame['instrument_type'] == 'PE'].sort_values('strike')

# Strike_increments = 100 # for Nifty the +- would be of 50
Strike_increments = int(x.iloc[1]['strike'] - x.iloc[0]['strike'])
UpperStrike = atm + (Strike_Range * Strike_increments)
LowerStrike = atm - (Strike_Range * Strike_increments)

# create the range, if we want to do this for individual stocks, find atm strike
# then location of pandas frame for that stock strike, then move +- on location basis if sorting is done on strikes.
RangeOI = frame[((frame.strike >= LowerStrike) & (frame.strike <= UpperStrike))]
# since we wanted to get OI, this will always be for NFO segment
quote_tradingsymbol_list = ('NFO:' + RangeOI['tradingsymbol'].astype(str)).to_list()

# loop for 15 minutes

while True:
    
    ## current ATM and then print the OI details
    curr_atm = kite.ltp(bnf_symbol)[bnf_symbol]['last_price']
    curr_atm = int(round(curr_atm,-2))
    
    data = kite.quote(quote_tradingsymbol_list)
    #df = pd.DataFrame.from_dict(data, orient='columns', dtype=None)
    df = pd.DataFrame.from_dict(data, orient='index', dtype=None)
    #ce_sum = df['oi'].sum()
    pe_sum = df[df.index.str.endswith('PE',na=False)]['oi'].sum()
    ce_sum = df[df.index.str.endswith('CE',na=False)]['oi'].sum()
    print ("CE sum OI:{} , PE sum OI:{}, diff: {}, curr_amt:{} ".format(ce_sum, pe_sum, (pe_sum - ce_sum), curr_atm))
    time.sleep(900)
