# https://kite.trade/forum/discussion/2359/working-with-quote-depths
# https://kite.trade/forum/discussion/9043/open-interest-for-multiple-instruments

df_inst = pd.read_csv("https://api.kite.trade/instruments")
def get_option_trading_symbol(underlyingPrice, symbolName = "BANKNIFTY", rangeFilter = True , steps = 20):
    df = df_inst[df_inst['segment'] == "NFO-OPT"]
    
    if symbolName == "BANKNIFTY":
        df = df[df['tradingsymbol'].str.startswith("{}".format("BANKNIFTY"))]
    if symbolName == "NIFTY":
        df = df[~df['tradingsymbol'].str.startswith("{}".format("NIFTYIT"))]
        # above statement removes niftyIT symbol.
        df = df[df['tradingsymbol'].str.startswith("{}".format("NIFTY"))]
    
    df['expiry'] = pd.to_datetime(df['expiry'])
    expirylist = list(set(df[['tradingsymbol', 'expiry']].sort_values(by=['expiry'])['expiry'].values))
    expirylist = np.array([np.datetime64(x, 'D') for x in expirylist])
    expirylist = np.sort(expirylist)
    today = np.datetime64('today', 'D') + np.timedelta64(0,'D')
    expirylist = expirylist[expirylist >= today]
    expiry_index = 0
    next_expiry = expirylist[expiry_index]
    print("Selected expiry :", next_expiry)
    print(underlyingPrice)
    df = df[(df['expiry'] == next_expiry)]
    
    if(rangeFilter):
        atm = underlyingPrice
        BNStrike =  int(round(atm,-2))
        Strike_Range = steps # Range for which you want to do the sum
        if symbolName == "BANKNIFTY":
            Strike_increments = 100 # for Nifty the +- would be of 50
        if symbolName == "NIFTY":
            Strike_increments = 50 # for Nifty the +- would be of 50
        UpperStrike = BNStrike + (Strike_Range * Strike_increments)
        LowerStrike = BNStrike - (Strike_Range * Strike_increments)

    RangeOI = df[((df.strike >= LowerStrike) & (df.strike <= UpperStrike))]
    return RangeOI
#return tradingsymbol,instrument_token
