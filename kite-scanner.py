# stocks, will choose FNO initially for open = low or open = high. 
# dedicated to operator bhaiya and a friend who calls such large candles as tubelights (not on twitter, great trader)
# why this code, I was looking for coders to help me code something for my trading / testing, got very few responses
# few who posted on zerodha site saying can help coding, were expensive, I do not mind the cost, but quality was difficult to know

# What will you see in this code
# Login function being called
# usage of kite.quote api, get the data, at one second, you can get 500 quotes, we wont need so many
# pseudo code to check conditions, reason, I am not putting any conditions is due to skeptism of many that my strategy will be used by others.
# RSI, ATR all such indicators for python can be found online and it wont be part of this code.
# order slicing (I intend to trade 1 lot, so no scale is needed). This is a poor mans approch.
# only to show its possible to code a quick thing to help you.
# since many use tradetron or other algo platforms, they already have an API, so such code snipets can be used for stock scanners.
# we can use the timer code from straddle.py to time our running of the code after 9:16, 9:20, ...

# Reference
# https://stackoverflow.com/questions/39899005/how-to-flatten-a-pandas-dataframe-with-some-columns-as-json
# https://zhauniarovich.com/post/2021/2021-04-flattening-json-using-pandas/

# vote of thanks
# https://github.com/sreenivasdoosa/sdoosa-algo-trade-python/  -- Sreenivas
# https://github.com/jigneshpylab/ZerodhaPythonScripts -- Jignesh Patel
# Operator bhaiya ko bhi for the timing of jokes on spaces and some very good learning.

from kiteutils import kitelogin, get_symbol_token_list, set_symbol_token
import time
import pandas as pd
import numpy as np
import datetime
import json 

print( 'login')
kite, kws = kitelogin() # parameters are present in the import
print( 'Login successful')


get_kite_symbols = pd.read_csv("https://api.kite.trade/instruments/NFO")
# avoid using the getting symbols often. Use it once, keep the symbols, like once a day and refresh in the morning.
#df = df[df['segment'] == "NFO-OPT"]

# need to code to get the latest expiry for futures symbol
filter_expiry = '2022-01-27'
exchange = 'NFO:' # used in the quote API, for only cash, NSE or BSE will be needed. output get_kite_symbols for info.

get_kite_symbols = get_kite_symbols[((get_kite_symbols.segment == "NFO-FUT") & (get_kite_symbols.expiry == filter_expiry))]
# got 199 rows, this will also include NIFTY, NIFTYIT, BNF....

# next get quote for all of these symbols, lets use the quote API
# quote API uses exchange:tradingsymbol as a parameter example NSE:AARTIIND22JANFUT

quote_tradingsymbol_list = (exchange + get_kite_symbols['tradingsymbol'].astype(str)).to_list()

# symbol list looks like the next three lines, ignore the # 
# ['NSENIFTY22JANFUT',
# 'NSEBANKNIFTY22JANFUT',
# 'NSEAARTIIND22JANFUT', <all symbols of the list>....]

# to make this more efficient, we could only get the OHLC data.

quote_data = kite.ohlc(quote_tradingsymbol_list)


# needs more testing on edge cases of open = low or open = high conditions. Example open is 10.0, low is 9.98 (not covered)

raw_data = pd.DataFrame.from_dict(quote_data, orient='index', dtype=None)
# scanner = pd.json_normalize(raw_data['ohlc']), need to learn and test what is more efficient.
# https://stackoverflow.com/questions/39899005/how-to-flatten-a-pandas-dataframe-with-some-columns-as-json

# pd.json_normalize(raw_data['ohlc'])
json_normalized_ohlc = pd.json_normalize(raw_data['ohlc']).set_index(raw_data.index)
scanner = pd.concat([raw_data, json_normalized_ohlc], axis='columns')


#long scanner
scanner[(scanner['open'] == scanner['low']) & (scanner['last_price'] >= scanner['open'] * 1.03)]

#short scanner
scanner[(scanner['open'] == scanner['high']) & (scanner['last_price'] <= scanner['open'] * 0.97)]

# scanner.filter(like = 'TORNTPHARM', axis = 0) -- O- 2936.65 H- 2942.05 L- 2631.1 C- 3155.25
# used the filter function on the index of the dataframe

