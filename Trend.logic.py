# -----------------------------
# Updated: Wait for break (Option A logic)
# -----------------------------
def wait_for_break_dynamic(df, leg):
    """
    Frozen-leg behavior (updated with Option A):
    
    - Continuation-side wick → update extreme → wait for confirmed swing → continuation break.
    - Reversal-side full break → DO NOT flip leg immediately.
      Instead, trigger opposite-direction swing search:
          return (break_idx, "reversal_trigger", current_leg)
    
    Returns:
       (break_index, break_type, updated_leg)
    
    break_type:
       "continuation_break"  (confirmed)
       "reversal_trigger"    (start opposite-direction swing search)
    """
    
    trend = leg["trend"]
    hi_idx = leg["high_index"]
    lo_idx = leg["low_index"]

    hi_p = df.iloc[hi_idx]["high"]
    lo_p = df.iloc[lo_idx]["low"]

    start = max(hi_idx, lo_idx) + 1
    pending_continuation = False

    for i in range(start, len(df)):

        h = df.iloc[i]["high"]
        l = df.iloc[i]["low"]

        # ==========================================================
        # UP TREND LOGIC
        # ==========================================================
        if trend == "up":

            # -------------------------------------------
            # REVERSAL SIDE FULL BREAK (NO immediate flip)
            # -------------------------------------------
            if l < lo_p - EPS:
                return i, "reversal_trigger", {**leg, "high_index": hi_idx, "low_index": lo_idx}

            # -------------------------------------------
            # CONTINUATION SIDE WICK BREAK (update high)
            # -------------------------------------------
            if h > hi_p + EPS:
                hi_p = h
                hi_idx = i
                pending_continuation = True
                leg = {**leg, "high_index": hi_idx}
                continue

            # -------------------------------------------
            # CONTINUATION CONFIRMATION → Swing High
            # -------------------------------------------
            if pending_continuation and i in SWING_HIGHS_SET:
                if swing_high_confirmed_uptrend(df, i) and df.iloc[i]["high"] >= hi_p - EPS:
                    return i, "continuation_break", {**leg, "high_index": hi_idx, "low_index": lo_idx}


        # ==========================================================
        # DOWN TREND LOGIC
        # ==========================================================
        else:

            # -------------------------------------------
            # REVERSAL SIDE FULL BREAK (NO immediate flip)
            # -------------------------------------------
            if h > hi_p + EPS:
                return i, "reversal_trigger", {**leg, "high_index": hi_idx, "low_index": lo_idx}

            # -------------------------------------------
            # CONTINUATION SIDE WICK BREAK (update low)
            # -------------------------------------------
            if l < lo_p - EPS:
                lo_p = l
                lo_idx = i
                pending_continuation = True
                leg = {**leg, "low_index": lo_idx}
                continue

            # -------------------------------------------
            # CONTINUATION CONFIRMATION → Swing Low
            # -------------------------------------------
            if pending_continuation and i in SWING_LOWS_SET:
                if swing_low_confirmed_downtrend(df, i) and df.iloc[i]["low"] <= lo_p + EPS:
                    return i, "continuation_break", {**leg, "high_index": hi_idx, "low_index": lo_idx}

    return None, None, leg
