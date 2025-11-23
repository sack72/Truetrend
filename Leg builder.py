# -----------------------------
# Next leg builder (UPDATED)
# -----------------------------
def build_next_leg(df, prev_leg):
    break_idx, brk, prev_leg_updated = wait_for_break_dynamic(df, prev_leg)
    if break_idx is None:
        return None

    prev_trend = prev_leg_updated["trend"]

    # -------------------------------------------------
    # Decide which direction we are TRYING to build
    # -------------------------------------------------
    if brk == "continuation_break":
        # continuation keeps same trend
        new_trend = prev_trend
    elif brk == "reversal_trigger":
        # reversal trigger starts opposite search, but
        # trend flips ONLY after we confirm the new leg
        new_trend = "down" if prev_trend == "up" else "up"
    else:
        # safety fallback (shouldn't happen)
        return None

    # -------------------------------------------------
    # MRB anchor from previous leg
    # MRB = most recent boundary in time
    # -------------------------------------------------
    mrb_idx = get_mrb_index(prev_leg_updated)

    # -------------------------------------------------
    # Candidate swings AFTER the break trigger
    # -------------------------------------------------
    if new_trend == "down":
        candidates = [i for i in SWING_LOWS_SET if i > break_idx]
        candidates.sort()
        confirm = swing_low_confirmed_downtrend
        check_fvg = is_bearish_fvg
        opposite_side_swings = SWING_HIGHS_SET
        opposite_side_price_col = "high"
    else:
        candidates = [i for i in SWING_HIGHS_SET if i > break_idx]
        candidates.sort()
        confirm = swing_high_confirmed_uptrend
        check_fvg = is_bullish_fvg
        opposite_side_swings = SWING_LOWS_SET
        opposite_side_price_col = "low"

    # -------------------------------------------------
    # Try candidates in time order
    # -------------------------------------------------
    for s_idx in candidates:

        # 1) swing + OC confirmation
        if not confirm(df, s_idx):
            continue

        # 2) FVG must exist anywhere from MRB -> candidate
        fvg_ok = False
        for i in range(mrb_idx, s_idx - 1):
            if check_fvg(df, i):
                fvg_ok = True
                break
        if not fvg_ok:
            continue

        # 3) Find opposite boundary for the new leg:
        #    look BACK from candidate to MRB and take
        #    the most recent opposite-side swing
        opp_swings = [i for i in opposite_side_swings if mrb_idx <= i < s_idx]
        if opp_swings:
            opp_idx = max(opp_swings)   # most recent in time before candidate
        else:
            # fallback to extreme between MRB and candidate
            window = df.iloc[mrb_idx:s_idx+1]
            if new_trend == "down":
                opp_idx = window[opposite_side_price_col].idxmax()
            else:
                opp_idx = window[opposite_side_price_col].idxmin()

        # 4) Assemble leg using MRB sequencing:
        if new_trend == "down":
            hi_idx = opp_idx
            lo_idx = s_idx
        else:
            lo_idx = opp_idx
            hi_idx = s_idx

        return {
            "trend": new_trend,
            "high_index": hi_idx,
            "low_index": lo_idx,
            # store the break trigger candle for reference/debug
            "break_idx": break_idx
        }

    return None
