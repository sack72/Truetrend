# ---------------------------------------------------------
# MRB = Most Recent Structural Boundary
# ---------------------------------------------------------
def get_mrb_index(leg):
    """
    MRB = Most Recent Boundary of the leg.
    If leg is UP:  low(A) → high(B), B is MRB.
    If leg is DOWN: high(A) → low(B), B is MRB.

    leg = {"high_index": int, "low_index": int, "trend": "up" or "down"}
    """

    hi = leg["high_index"]
    lo = leg["low_index"]

    # MRB is whichever came LATER in time
    return hi if hi > lo else lo
