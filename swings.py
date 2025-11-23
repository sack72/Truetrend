
# -----------------------------
# Swing detection
# -----------------------------
def swing_lows(df):
    return [
        i for i in range(1, len(df)-1)
        if df.iloc[i]["low"] < df.iloc[i-1]["low"] and df.iloc[i]["low"] < df.iloc[i+1]["low"]
    ]

def swing_highs(df):
    return [
        i for i in range(1, len(df)-1)
        if df.iloc[i]["high"] > df.iloc[i-1]["high"] and df.iloc[i]["high"] > df.iloc[i+1]["high"]
    ]

# Precompute for speed + easy membership tests
SWING_LOWS_SET  = set(swing_lows(df))
SWING_HIGHS_SET = set(swing_highs(df))

# -----------------------------
# Confirmation with invalidation
# -----------------------------
def swing_low_confirmed_downtrend(df, sl_idx):
    """
    Valid only if bullish confirmation appears BEFORE price breaks below SL.
    """
    sl_price = df.iloc[sl_idx]["low"]

    # SL candle bullish?
    if df.iloc[sl_idx]["close"] > df.iloc[sl_idx]["open"]:
        return True

    for j in range(sl_idx+1, len(df)):
        # invalidated first
        if df.iloc[j]["low"] < sl_price - EPS:
            return False
        # confirmed
        if df.iloc[j]["close"] > df.iloc[j]["open"]:
            return True
    return False

def swing_high_confirmed_uptrend(df, sh_idx):
    """
    Valid only if bearish confirmation appears BEFORE price breaks above SH.
    """
    sh_price = df.iloc[sh_idx]["high"]

    # SH candle bearish?
    if df.iloc[sh_idx]["close"] < df.iloc[sh_idx]["open"]:
        return True

    for j in range(sh_idx+1, len(df)):
        # invalidated first
        if df.iloc[j]["high"] > sh_price + EPS:
            return False
        # confirmed
        if df.iloc[j]["close"] < df.iloc[j]["open"]:
            return True
    return False
