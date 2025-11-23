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

# FVG duration and position

def fvg_until_candidate(df, mrb_idx, candidate_idx, trend):
    """
    Returns True if ANY valid FVG exists between:
        MRB  →  candidate swing
    """
    check = is_bearish_fvg if trend == "down" else is_bullish_fvg
    
    for i in range(mrb_idx, candidate_idx - 1):
        if check(df, i):
            return True
    
    return False
