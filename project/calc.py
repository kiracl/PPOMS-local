from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _parse_non_negative(text: str):
    t = (text or "").strip()
    if not t:
        return None
    try:
        v = Decimal(t)
    except InvalidOperation:
        return None
    if v < 0:
        return None
    return v


def calc_total(unit_price_text: str, qty_text: str):
    p = _parse_non_negative(unit_price_text)
    q = _parse_non_negative(qty_text)
    if p is None or q is None:
        return "", False
    total = (p * q).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(total, "f"), True

