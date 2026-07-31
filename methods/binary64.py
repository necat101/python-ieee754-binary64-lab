# methods/binary64.py — IEEE 754 binary64 field inspection (stdlib only)
import struct
import math

def float_bits(f: float) -> int:
    """big-endian IEEE 754 binary64 raw bits"""
    return struct.unpack(">Q", struct.pack(">d", f))[0]

def unpack_binary64(f: float) -> dict:
    """return sign, exponent, fraction fields and decoded values"""
    bits = float_bits(f)
    sign = (bits >> 63) & 0x1
    exponent = (bits >> 52) & 0x7FF
    fraction = bits & ((1 << 52) - 1)
    # classification
    if exponent == 0x7FF:
        kind = "nan" if fraction != 0 else "inf"
    elif exponent == 0:
        kind = "subnormal" if fraction != 0 else "zero"
    else:
        kind = "normal"
    # unbiased exponent
    if exponent == 0:
        unbiased = -1022
    elif exponent == 0x7FF:
        unbiased = None
    else:
        unbiased = exponent - 1023
    return {
        "bits": bits,
        "sign": sign,
        "exponent_raw": exponent,
        "fraction_raw": fraction,
        "kind": kind,
        "unbiased_exponent": unbiased,
        "hex": f.hex(),
    }

def is_exact_binary64_decimal_str(d: str) -> bool:
    """check if decimal string round-trips exactly via float"""
    from decimal import Decimal, getcontext
    getcontext().prec = 60
    dec = Decimal(d)
    f = float(dec)
    # back via Decimal(float) to see binary value
    dec_f = Decimal(f)
    return dec == dec_f

def adjacent_floats(f: float) -> dict:
    up = math.nextafter(f, math.inf)
    down = math.nextafter(f, -math.inf)
    return {"up": up, "down": down, "ulp_up": up - f if math.isfinite(up) and math.isfinite(f) else None,
            "ulp_down": f - down if math.isfinite(down) and math.isfinite(f) else None}

def signed_zero_info(f: float) -> dict:
    return {
        "is_zero": f == 0.0,
        "signbit": math.copysign(1.0, f) < 0,
        "bits": float_bits(f),
    }
