# =======================================================
# FULL TREND ENGINE (UP⇄DOWN)
# AUTO DETECT + ANCHOR MATRIX + 3-RULE BOUNDARY ORDER
# =======================================================

import pandas as pd
import numpy as np
from google.colab import files

uploaded = files.upload()
filename = list(uploaded.keys())[0]
df = pd.read_csv(filename)

df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
df["local_time"] = pd.to_datetime(
    df["local_time"],
    format="%d.%m.%Y %H:%M:%S.%f GMT%z",
    dayfirst=True
)

# =======================================================
# FVG HELPERS
# =======================================================
def is_bearish_fvg(df, c1):
    if c1 < 0 or c1 + 2 >= len(df):
        return False
    return df.iloc[c1]["low"] > df.iloc[c1 + 2]["high"]

def is_bullish_fvg(df, c1):
    if c1 < 0 or c1 + 2 >= len(df):
        return False
    return df.iloc[c1]["high"] < df.iloc[c1 + 2]["low"]

def bearish_fvgs_between(df, start_idx, end_idx):
    for i in range(start_idx, end_idx - 1):
        if is_bearish_fvg(df, i):
            return True
    return False

def bullish_fvgs_between(df, start_idx, end_idx):
    for i in range(start_idx, end_idx - 1):
        if is_bullish_fvg(df, i):
            return True
    return False

# =======================================================
# SWING HELPERS
# =======================================================
def detect_swing_lows(df):
    out = []
    for i in range(1, len(df) - 1):
        if df.iloc[i]["low"] < df.iloc[i-1]["low"] and df.iloc[i]["low"] < df.iloc[i+1]["low"]:
            out.append(i)
    return out

def detect_swing_highs(df):
    out = []
    for i in range(1, len(df) - 1):
        if df.iloc[i]["high"] > df.iloc[i-1]["high"] and df.iloc[i]["high"] > df.iloc[i+1]["high"]:
            out.append(i)
    return out

def is_bullish(row):
    return row["close"] > row["open"]

def is_bearish(row):
    return row["close"] < row["open"]

# =======================================================
# OC HELPERS (BOUNDARY CONFIRMATION)
# Swing candle itself can be OC if opposite color
# =======================================================
def has_bearish_after(df, idx):
    for j in range(idx + 1, len(df)):
        if is_bearish(df.iloc[j]):
            return True
    return False

def has_bullish_after(df, idx):
    for j in range(idx + 1, len(df)):
        if is_bullish(df.iloc[j]):
            return True
    return False

def oc_for_high(df, sh_idx):
    # UP boundary OC = bearish at swing or after swing
    return is_bearish(df.iloc[sh_idx]) or has_bearish_after(df, sh_idx)

def oc_for_low(df, sl_idx):
    # DOWN boundary OC = bullish at swing or after swing
    return is_bullish(df.iloc[sl_idx]) or has_bullish_after(df, sl_idx)

# =======================================================
# FIRST LEG BUILDERS (3-RULE ORDER)
# FVG -> SWING -> OC
# =======================================================
def build_first_bearish_leg(df):
    # 1) First bearish FVG
    first_fvg = None
    for i in range(len(df) - 2):
        if is_bearish_fvg(df, i):
            first_fvg = i
            break
    if first_fvg is None:
        return None

    # 2) Swing lows AFTER the FVG
    swing_lows = detect_swing_lows(df)
    sl_candidates = [i for i in swing_lows if i > first_fvg]
    if not sl_candidates:
        return None

    for sl_idx in sl_candidates:
        # 3) OC must confirm this low
        if not oc_for_low(df, sl_idx):
            continue

        # High boundary before FVG (unchanged)
        swing_highs = detect_swing_highs(df)
        sh_before = [i for i in swing_highs if i < first_fvg]
        if not sh_before:
            leg_high_idx = df.iloc[:first_fvg].high.idxmax()
        else:
            leg_high_idx = max(sh_before)

        return {"high_index": leg_high_idx, "low_index": sl_idx, "fvg_c1": first_fvg}

    return None


def build_first_bullish_leg(df):
    # 1) First bullish FVG
    first_fvg = None
    for i in range(len(df) - 2):
        if is_bullish_fvg(df, i):
            first_fvg = i
            break
    if first_fvg is None:
        return None

    # 2) Swing highs AFTER the FVG
    swing_highs = detect_swing_highs(df)
    sh_candidates = [i for i in swing_highs if i > first_fvg]
    if not sh_candidates:
        return None

    for sh_idx in sh_candidates:
        # 3) OC must confirm this high
        if not oc_for_high(df, sh_idx):
            continue

        # Low boundary before FVG (unchanged)
        swing_lows = detect_swing_lows(df)
        sl_before = [i for i in swing_lows if i < first_fvg]
        if not sl_before:
            leg_low_idx = df.iloc[:first_fvg].low.idxmax()
        else:
            leg_low_idx = max(sl_before)

        return {"low_index": leg_low_idx, "high_index": sh_idx, "fvg_c1": first_fvg}

    return None

# =======================================================
# BREAK LOGIC (UNCHANGED)
# =======================================================
def bearish_wait_break(df, leg):
    hi = df.iloc[leg["high_index"]]["high"]   # protected (DOWN)
    lo = df.iloc[leg["low_index"]]["low"]    # non-protected
    start = leg["low_index"] + 1
    for i in range(start, len(df)):
        if df.iloc[i]["high"] > hi:
            return i, "up"     # reversal to UP
        if df.iloc[i]["low"] < lo:
            return i, "down"   # continuation DOWN
    return None, None

def bullish_wait_break(df, leg):
    lo = df.iloc[leg["low_index"]]["low"]    # protected (UP)
    hi = df.iloc[leg["high_index"]]["high"] # non-protected
    start = leg["high_index"] + 1
    for i in range(start, len(df)):
        if df.iloc[i]["low"] < lo:
            return i, "down"   # reversal to DOWN
        if df.iloc[i]["high"] > hi:
            return i, "up"     # continuation UP
    return None, None

# =======================================================
# NEXT LEG BUILDERS (3-RULE ORDER)
# FVG -> SWING -> OC within anchor range
# =======================================================
def build_next_bearish_leg(df, anchor_start, break_idx):
    # Swing lows AFTER break
    swing_lows = detect_swing_lows(df)
    sl_candidates = [i for i in swing_lows if i > break_idx]

    for sl_idx in sl_candidates:
        # 1) Bearish FVG must exist BEFORE this swing low inside anchor range
        if not bearish_fvgs_between(df, anchor_start, sl_idx):
            continue

        # choose most recent bearish FVG before swing low in that window
        chosen_fvg = None
        for i in range(anchor_start, sl_idx - 1):
            if is_bearish_fvg(df, i):
                chosen_fvg = i
        if chosen_fvg is None:
            continue

        # 2) Swing low is already verified by sl_idx candidate
        # 3) OC must confirm low
        if not oc_for_low(df, sl_idx):
            continue

        # High boundary before chosen FVG (unchanged, but limited to anchor window)
        swing_highs = detect_swing_highs(df)
        sh_before = [i for i in swing_highs if anchor_start <= i < chosen_fvg]
        if not sh_before:
            leg_high_idx = df.iloc[anchor_start:chosen_fvg].high.idxmax()
        else:
            leg_high_idx = max(sh_before)

        return {"high_index": leg_high_idx, "low_index": sl_idx, "fvg_c1": chosen_fvg}

    return None


def build_next_bullish_leg(df, anchor_start, break_idx):
    # Swing highs AFTER break
    swing_highs = detect_swing_highs(df)
    sh_candidates = [i for i in swing_highs if i > break_idx]

    for sh_idx in sh_candidates:
        # 1) Bullish FVG must exist BEFORE this swing high inside anchor range
        if not bullish_fvgs_between(df, anchor_start, sh_idx):
            continue

        # choose most recent bullish FVG before swing high in that window
        chosen_fvg = None
        for i in range(anchor_start, sh_idx - 1):
            if is_bullish_fvg(df, i):
                chosen_fvg = i
        if chosen_fvg is None:
            continue

        # 2) Swing high is already verified by sh_idx candidate
        # 3) OC must confirm high
        if not oc_for_high(df, sh_idx):
            continue

        # Low boundary before chosen FVG (unchanged, but limited to anchor window)
        swing_lows = detect_swing_lows(df)
        sl_before = [i for i in swing_lows if anchor_start <= i < chosen_fvg]
        if not sl_before:
            leg_low_idx = df.iloc[anchor_start:chosen_fvg].low.idxmax()
        else:
            leg_low_idx = max(sl_before)

        return {"low_index": leg_low_idx, "high_index": sh_idx, "fvg_c1": chosen_fvg}

    return None

# =======================================================
# AUTO DETECT FIRST FVG → START TREND
# =======================================================
def auto_detect_trend(df):
    for i in range(len(df) - 2):
        if is_bearish_fvg(df, i):
            return "down", i
        if is_bullish_fvg(df, i):
            return "up", i
    return None, None

# =======================================================
# MASTER ENGINE (ANCHOR MATRIX)
# =======================================================
legs = []

trend, first_fvg_index = auto_detect_trend(df)
if trend is None:
    raise ValueError("No FVG found to start trend.")

# First leg based on auto-detect
if trend == "down":
    leg = build_first_bearish_leg(df)
else:
    leg = build_first_bullish_leg(df)

if leg is None:
    raise ValueError("Failed to build first leg.")

leg["leg"] = 1
legs.append(leg)
current = leg
leg_num = 1

# Main loop
while True:

    if trend == "up":
        break_idx, direction = bullish_wait_break(df, current)
        if break_idx is None:
            break

        # UP anchor rules:
        # - reversal (UP low breaks)  => anchor = prev UP high
        # - continuation (UP high breaks) => anchor = prev UP low
        if direction == "down":  # reversal to DOWN
            anchor = current["high_index"]
            trend = "down"
            nxt = build_next_bearish_leg(df, anchor, break_idx)
        else:                    # continuation UP
            anchor = current["low_index"]
            nxt = build_next_bullish_leg(df, anchor, break_idx)

    else:  # trend == "down"
        break_idx, direction = bearish_wait_break(df, current)
        if break_idx is None:
            break

        # DOWN anchor rules:
        # - reversal (DOWN high breaks) => anchor = prev DOWN low
        # - continuation (DOWN low breaks) => anchor = prev DOWN high
        if direction == "up":    # reversal to UP
            anchor = current["low_index"]
            trend = "up"
            nxt = build_next_bullish_leg(df, anchor, break_idx)
        else:                    # continuation DOWN
            anchor = current["high_index"]
            nxt = build_next_bearish_leg(df, anchor, break_idx)

    if nxt is None:
        break

    leg_num += 1
    nxt["leg"] = leg_num
    legs.append(nxt)
    current = nxt

# =======================================================
# OUTPUT
# =======================================================
print("============ ALL LEGS DETECTED ============")
for L in legs:
    print(f"\nLeg {L['leg']}:")
    print(f"  LOW    = {df.iloc[L['low_index']]['low']} @ {df.iloc[L['low_index']]['local_time']}")
    print(f"  HIGH   = {df.iloc[L['high_index']]['high']} @ {df.iloc[L['high_index']]['local_time']}")
    print(f"  FVG C1 = {L['fvg_c1']} @ {df.iloc[L['fvg_c1']]['local_time']}")
