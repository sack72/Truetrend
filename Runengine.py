# -----------------------------
# Run Engine (UPDATED)
# -----------------------------
legs = []


# ---------------------------------------------
# 1) Detect initial trend from first FVG
# ---------------------------------------------
trend0 = detect_initial_trend(df)
if trend0 is None:
    raise ValueError("No FVG found to start the model.")


# ---------------------------------------------
# 2) Build the first leg
# ---------------------------------------------
leg = build_first_leg(df, trend0)
if leg is None:
    raise ValueError("Cannot build first leg — missing swing/OC/FVG structure.")

leg["leg"] = 1
legs.append(leg)

# Debug:
print(f"Leg 1 built: Trend={leg['trend']}  High={leg['high_index']}  Low={leg['low_index']}")


# ---------------------------------------------
# 3) Build all next legs until no more structure
# ---------------------------------------------
while True:

    nxt = build_next_leg(df, leg)

    # no new structure
    if nxt is None:
        break

    # number the new leg
    nxt["leg"] = legs[-1]["leg"] + 1
    legs.append(nxt)

    # Debug:
    print(f"Leg {nxt['leg']} built: Trend={nxt['trend']}  High={nxt['high_index']}  Low={nxt['low_index']}  Break={nxt['break_idx']}")

    # update the current leg pointer
    leg = nxt


# ---------------------------------------------
# DONE — all legs built
# ---------------------------------------------
print("\n============= ALL LEGS DETECTED =============")
for L in legs:
    hi = df.iloc[L["high_index"]]
    lo = df.iloc[L["low_index"]]
    print(f"\nLeg {L['leg']} ({L['trend'].upper()}):")
    print(f"  HIGH = {hi['high']} @ {hi['local_time']}")
    print(f"  LOW  = {lo['low']}  @ {lo['local_time']}")
