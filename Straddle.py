# what is python stops and we restart, we need to track our orders and positions per strategy
# multiple users, multiple stratgies
# error handling and retry logic
# telegram alert
# paper trade option
# class strategy and execution of all of this.
# note in this case, on combined SL, we are exiting the straddle and creating a new leg on the one which is profitable.
# we can continue to keep the profit leg and add a new leg.

from kiteutils import kitelogin, get_symbol_token_list, set_symbol_token
# from kiteutils import on_ticks, on_connect, on_close
from kiteutils import short_market_order , squareoff_market_order
import time
import pandas as pd
import numpy as np
import datetime

TRADER_START_TIME = datetime.time(hour=9, minute=30)
TRADER_STOP_TIME = datetime.time(hour=15, minute=10)

if not datetime.datetime.combine(datetime.datetime.today(), TRADER_STOP_TIME) > datetime.datetime.today() > \
datetime.datetime.combine(datetime.datetime.today(), TRADER_START_TIME):
    print('Sleeping till valid trade time')
    while not datetime.datetime.combine(datetime.datetime.today(), TRADER_STOP_TIME) > datetime.datetime.today() > \
    datetime.datetime.combine(datetime.datetime.today(), TRADER_START_TIME):
        time.sleep(1)
print('Within valid trade time')

print( 'Performing login')
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


ce_frame = set_symbol_token(frame,atm,"CE")
pe_frame = set_symbol_token(frame,atm,"PE")

# set CE symbol and tokens

bnf_ce_symbol = ce_frame['tradingsymbol'].values[0]
bnf_ce_token = int(ce_frame['instrument_token'].values[0])

# set PE symbol and tokens

bnf_pe_symbol = pe_frame['tradingsymbol'].values[0]
bnf_pe_token = int(pe_frame['instrument_token'].values[0])

# token list to get the tick data from kite software

token_list = [bnf_ce_token,bnf_pe_token]
print('BankNifty Call option (symbol:token): ({}, {})'.format(bnf_ce_symbol, bnf_ce_token))
print('BankNifty Put option (symbol:token): ({}, {})'.format(bnf_pe_symbol, bnf_pe_token))

## bnf_pe_symbol  -- BANKNIFTY2212537600PE

# subscription of the tokens for the instruments to monitor ltp and to ensure we find the stop loss or MTM.
# note mtm - use the ltp, your orders values and calculate the PNL, not using position API from Kite
# the position API from kite has lag and may not provide real time PNL, per zerodha forum.

# stream prices

ltp_dict = dict()

### Streaming tick data functions

def on_ticks(kws, ticks):
    for tick in ticks:
        ltp_dict[tick['instrument_token']] = float(tick['last_price'])
        #print(tick)

def on_connect(kws, response):
    print('socket is opened')

def on_close(kws, code, reason):
    print('socket is closed')


kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# make the connection

kws.connect(threaded=True)
time.sleep(5)

kws.subscribe(token_list)
kws.set_mode(kws.MODE_LTP,token_list)

# Placing the orders

ce_short_order_id = short_market_order(kite, bnf_ce_symbol, 2500)
pe_short_order_id = short_market_order(kite, bnf_pe_symbol, 2500)
time.sleep(5)

print('Combined short straddle order placed')

orders = kite.orders()
ce_short_order = next(order for order in orders if order['order_id'] == ce_short_order_id)
pe_short_order = next(order for order in orders if order['order_id'] == pe_short_order_id)

while not (ce_short_order['status'] == 'COMPLETE' and pe_short_order['status'] == 'COMPLETE'):
    time.sleep(1)
print('Combined short straddle order completed')

combined_entry_price = ce_short_order['average_price'] + pe_short_order['average_price']
combined_stoploss = combined_entry_price * 1.1

print("Short straddle combined entry price:", combined_entry_price)
print("Short straddle combined stoploss price:", combined_stoploss)

stoploss_exit1 = 0

while datetime.datetime.today() < datetime.datetime.combine(datetime.datetime.today(), TRADER_STOP_TIME):

    if ltp_dict[bnf_ce_token] + ltp_dict[bnf_pe_token] > combined_stoploss:
        print('Exiting short straddle position due to combined stoploss hit')
        
        ce_squareoff_order_id = squareoff_market_order(kite, bnf_ce_symbol, 2500)
        pe_squareoff_order_id = squareoff_market_order(kite, bnf_pe_symbol, 2500)
        
        # Once combined SL is hit, we are squaring both the legs and then taking a new position.
        # below code is to understand which Leg we need to sell atm when this is hit.
        
        if ltp_dict[bnf_ce_token] > ce_short_order['average_price']:
            leg = 'PE'
        elif ltp_dict[bnf_pe_token] > pe_short_order['average _price']:
            leg = 'CE'

        stoploss_exit1 = 1
        kws.unsubscribe(token_list)
        time.sleep(5)
        break
    
    else:
        time.sleep(2)

if not stoploss_exit1:
    print('Exiting short straddle position due to trader''s stop time exceeded')
    ce_squareoff_order_id = squareoff_market_order(kite, bnf_ce_symbol, 2500)
    pe_squareoff_order_id = squareoff_market_order(kite, bnf_pe_symbol, 2500)
    kws.unsubscribe(token_list)
    #above is to unsubscribe all earlier tokens and take a new entry,
    #I would prefer to just add a new extra entry to the exisiting leg
    time.sleep(5)

# below is section for SL has been hit, take trades
else: 
    print('Entering a position in the 2nd leg: {}'.format(leg))
    # find new ATM   
    atm_leg = kite.ltp(bnf_symbol)[bnf_symbol]['last_price']
    atm_leg = int(round(atm,-2))
    print ('At the Money Rounded Strike {}'.format(atm_leg))
    
    leg_frame = set_symbol_token(frame,atm_leg,leg)
    # frame here has all the symbol, tokens taken up from earlier time.
    
    # set leg symbol and tokens

    bnf_leg_symbol = leg_frame['tradingsymbol'].values[0]
    bnf_leg_token = int(leg_frame['instrument_token'].values[0])
    
    # token_list = [bnf_ce_token,bnf_pe_token]
    # since only one leg, we will directly subscribe to only that one leg via kite API
    print('BankNifty New Leg option (symbol:token): ({}, {})'.format(bnf_leg_symbol, bnf_leg_token))
    
    kws.subscribe(bnf_leg_token)
    kws.set_mode(kws.MODE_LTP,bnf_leg_token)

    # Placing the order

    leg_short_order_id = short_market_order(kite, bnf_leg_symbol, 2500)
    time.sleep(5)
    print('2nd leg short order placed')
    
    orders = kite.orders()
    
    leg_short_order = next(order for order in orders if order['order_id'] == leg_short_order_id)
    while not leg_short_order['status'] == 'COMPLETE':
        time.sleep(1)
    print('2nd leg short order completed')

    leg_entry_price = leg_short_order['average_price']
    leg_stoploss = leg_entry_price * 1.2
    stoploss_exit2 = 0

    print("2nd leg short entry price:", leg_entry_price)
    print("2nd leg stoploss price:", leg_stoploss)

    while datetime.datetime.today() < datetime.datetime.combine(datetime.datetime.today(), TRADER_STOP_TIME):

        if ltp_dict[bnf_leg_token] > leg_stoploss:
            print('Exiting 2nd leg short position due to stoploss hit')
            leg_squareoff_order_id = squareoff_market_order(kite, bnf_leg_symbol, 2500)
            stoploss_exit2 = 1
            kws.unsubscribe([bnf_leg_token])
            time.sleep(5)
            break
        else:
            time.sleep(1)

    if not stoploss_exit2:
        print("Exiting 2nd leg short position due to trader's stop loss")
        leg_squareoff_order_id = squareoff_market_order(kite, bnf_leg_symbol, 2500)
        kws.unsubscribe([bnf_leg_token])
        time.sleep(5)
