# kite documentation in this link - https://kite.trade/docs/pykiteconnect/v3/

from kiteconnect import KiteConnect,KiteTicker
import pandas as pd
import numpy as np
import sys
import time
import datetime
import pickle
import logging
import json

# adding the API key details, we can make the code changes to later get the data from S3 or other location.
# note all of this data needs to be added. 
api_k = 'x'
sec_k = 'x'
#access_tkn = 'x'
user_id = 'x'

def kitelogin():
    
    # print (req_tkn)
    # if a token is already generated, use it via the below commands.
    # there is a request token and access token, access token is a daily one to use. 
    # request token is for each subsequent session for any request, so may need to keep calling the token to get data.
    
    try:

        kite = KiteConnect(api_key = api_k)
        # access_tkn = 'XkoPkycVVdTsYEriVcHkn50XRwQzEsN7'
        # gen_ssn = kite.generate_session(request_token = req_tkn, api_secret = sec_k)
        # no need to generate the session as it was already done via TradeTron, we will try to resue it.
        # get from chalice app, create the gateway and then generate the token.
        kite.set_access_token(access_token=access_tkn)
        kws = KiteTicker(api_k,access_tkn)
        
        # Keep a userid string for later, so we know which login has completed
        
        print("Kite Session generated for {}".format(user_id))
        
        return kite, kws
    
    except Exception as e:
        print(e)
        raise
		
# see also another way to get weekly expiry, for OI data which has been caculated, that seemed more simple, but keep this for reference.
# parameter kite needs to be sent for fethching the data
# the below did not work, need to use the method shared by Jignesh Patel Code
# below code was taken from Fox Algo

def find_weekly_expiry(kite):
    try:
        data = kite.instruments('NFO')
    except:
        time.sleep(6)
        data = kite.instruments('NFO')
        
    x = []
    for i in range(len(data)):
        x.append(data[i]['expiry'])
        
    x = list(set(x))
    x.sort()
    
    if datetime.datetime.now().month <= x[0].month:
        expiry_date = x[0]
    
    if x[0].month == x[1].month:
        if x[0].month < 10:
            #23121
            expiry_date_month = str(x[0].month)
            return x[0].strftime('%y') + x[0].strftime('%#m') + x[0].strftime('%d')
        else:
            #23J21
            expiry_date_month = ((datetime.datetime.strptime(str(expiry_date.month), "%m")).strftime("%b"))[0]
            stringDate = str(expiry_date).split('-')
            formatedDate = f"{stringDate[0][2:]}{expiry_date_month.upper()}{stringDate[2]}"
    
    if x[0].month != x[1].month:
        #OCT21
        expiry_date_month = ((datetime.datetime.strptime(str(expiry_date.month), "%m")).strftime("%b"))
        stringDate = str(expiry_date).split('-')
        formatedDate = f"{stringDate[0][2:]}{expiry_date_month.upper()}"
        
    return formatedDate
	# need to check why this code was not giving the right results, note also the symbol fomation for OCT, NOV, DEC is differnt, check the expiry
	# check that code
	
def get_symbol_token_list(symbolName = "BANKNIFTY"):

    df = pd.read_csv("https://api.kite.trade/instruments/NFO")
    
    # remove futures segment, if need futures data , use segment "NFO-FUT"
    df = df[df['segment'] == "NFO-OPT"]
    
    if symbolName == "BANKNIFTY":
        df = df[df['tradingsymbol'].str.startswith("{}".format("BANKNIFTY"))]
    if symbolName == "NIFTY":
        df = df[~df['tradingsymbol'].str.startswith("{}".format("NIFTYIT"))]
        # above statement removes niftyIT symbol.
        df = df[df['tradingsymbol'].str.startswith("{}".format("NIFTY"))]
    else:
        df = df[df['tradingsymbol'].str.startswith("{}".format(symbolName))]

    df['expiry'] = pd.to_datetime(df['expiry'])
    expirylist = list(set(df[['tradingsymbol', 'expiry']].sort_values(by=['expiry'])['expiry'].values))
    expirylist = np.array([np.datetime64(x, 'D') for x in expirylist])
    expirylist = np.sort(expirylist)
    today = np.datetime64('today', 'D') + np.timedelta64(0,'D')
    expirylist = expirylist[expirylist >= today]
    expiry_index = 0
    next_expiry = expirylist[expiry_index]
    print("Selected expiry :", next_expiry)
    df = df[(df['expiry'] == next_expiry)]
    return df
    # retruns a dataframe, which we need to filter and get the needed strikes and instruments.
    # note the index of the DataFrame has the expiry date


def set_symbol_token(df_symbol,strike_price,instru_type):
    # return df_symbol[((df_symbol.strike == strike_price) & (df_symbol.instrument_type == instru_type))][['instrument_type','tradingsymbol']]
    return df_symbol[((df_symbol.strike == strike_price) & (df_symbol.instrument_type == instru_type))]



### Streaming tick data functions

def on_ticks(kws, ticks):
	for tick in ticks:
		ltp_dict[tick['instrument_token']] = float(tick['last_price'])
		
def on_connect(kws, response):
	print('socket is opened')
	
def on_close(kws, code, reason):
	print('socket is closed')


#### Placing Order functions



def short_market_order(kite, symbol, quantity):
    print(f'Placing market SELL order for {quantity} {symbol}')

    order_id = kite.place_order(variety = 'regular',
    exchange = 'NFO',
    tradingsymbol = symbol,
    transaction_type = "SELL",
    quantity = quantity,
    product='MIS',
    order_type='MARKET',
    validity='DAY')

    return order_id

def squareoff_market_order(kite, symbol, quantity):

    print(f'Placing market BUY order for {quantity} {symbol}')

    order_id = kite.place_order(variety = 'regular',
    exchange = 'NFO',
    tradingsymbol = symbol,
    transaction_type = 'BUY',
    quantity = quantity,
    product='MIS',
    order_type='MARKET',
    validity='DAY')

    return order_id

  
