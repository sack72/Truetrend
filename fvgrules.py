# ---------------------------------------------------------
# FVG rules
# ---------------------------------------------------------
def is_bearish_fvg(df, c1):
    return (
        c1 >= 0 and 
        c1+2 < len(df) and 
        df.iloc[c1]["low"] > df.iloc[c1+2]["high"]
    )

def is_bullish_fvg(df, c1):
    return (
        c1 >= 0 and 
        c1+2 < len(df) and 
        df.iloc[c1]["high"] < df.iloc[c1+2]["low"]
    )
