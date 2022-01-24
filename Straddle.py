from kiteutils import kitelogin, get_symbol_token_list, set_symbol_token
# from kiteutils import on_ticks, on_connect, on_close
from kiteutils import short_market_order
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

### Skip the below code, more for seeing if the symbol value is created correctly.

# frame[((frame.strike == atm))]
# instrument_token	exchange_token	tradingsymbol	name	last_price	expiry	strike	tick_size	lot_size	instrument_type

# atm call and put option with latest weekly expiry dates
    # skip this as the code was not working well.
    # bnf_ce_symbol = "BANKNIFTY" + expiry + str(strike) + "CE"
    # bnf_pe_symbol = "BANKNIFTY" + expiry + str(strike) + "PE"

    # bnf_ce_symbol, = kite.ltp("NFO:"+bnf_ce_symbol)["NFO:"+bnf_ce_symbol]['instrument_token']

# at the money call and put option of the current weekly options.

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
    time.sleep(5)
              


"""
# have to add the second leg call/put option additional after the SL has hit.
else:

    print('Entering a position in the 2nd leg: {}'.format(leg))
    strike = kite.1tp(bnf_symbol)[bnf_symbol][‘last_price’]
    strike = int(round(strike, -2))

    expiry = weekly_expiry(kite)

    bnf_leg_ symbol = “BANKNIFTY” + expiry + str(strike) + leg

bnf_leg_token =kite.ltp("NFO:“+bnf_leg_symbol)[“NFO:"+bnf_leg_symbol][‘instrument_token’ ]
print('Banknifty 2nd leg option (symbol, token): ({}, {})'.format(bnf_leg symbol, bnf_leg token) )

kws.subscribe([bnf_leg token])
kws.set_mode(kws.MODE_LTP, [bnf_leg_token])

leg_short_order_id = short_market_order(kite, bnf_ce_symbol, 25)
time.sleep(5)
print('2nd leg short order placed’)

#### 

print(‘2nd leg short order placed’)

orders = kite.orders()
leg_short_order = next(order for order in orders if order['order_id’] == leg_short_order_id)
while not leg_short_order['status'] == ‘COMPLETE":
time.sleep(1)
print(‘2nd leg short order completed’)

leg_entry_price = leg short_order['average_price’]
leg_stoploss = leg_entry_price * 1.2

stoploss_exit2 = @

print("2nd leg short entry price:", leg_entry_price)
print("2nd leg stoploss price:", leg_stoploss)

while dt.datetime.today() < dt.datetime.combine(dt.datetime.today(), TRADER_STOP_TIME):

if ltp_dict[bnf_leg token] > leg_stoploss:
print(‘Exiting 2nd leg short position due to stoploss hit’)
leg_squareoff_order_id = squareoff_market_order(kite, bnf_leg symbol, 25)
stoploss_exit2 = 1
kws.unsubscribe([bnf_leg_token])
time.sleep(S)
break
else:
time.sleep(1)

if not stoploss_exit2:

print("Exiting 2nd leg short | ition due to trader's sto;

############# leg_entry_price = leg _short_order['average_price']
leg_stoploss = leg_entry_price * 1.2

stoploss_exit2 = @

print("2nd leg short entry price:", leg _entry_price)
print("2nd leg stoploss price:", leg _stoploss)

while dt.datetime.today() < dt.datetime.combine(dt.datetime.today(), TRADER_STOP_TIME):

if ltp_dict{bnf_leg_ token] > leg_stoploss:
print("Exiting 2nd leg short position due to stoploss hit‘)
leg_squareoff_order_id = squareoff_market_order(kite, bnf_leg symbol, 25)
stoploss_exit2 = 1
kws.unsubscribe([bnf_leg_ token])
time.sleep(S)
break
else:
time.sleep(1)

if not stoploss_exit2:
print("Exiting 2nd leg short position due to trader's stop time exceeded”)
leg_squareoff_order_id = squareoff_market_order(kite, bnf_leg_symbol, 25)
kws.unsubscribe([bnf_leg_token])
time.sleep(5)

"""
