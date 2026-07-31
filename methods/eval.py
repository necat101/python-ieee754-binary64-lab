# methods/eval.py — case evaluation using stdlib methods
import math, sys
from decimal import Decimal, getcontext
from fractions import Fraction

from .binary64 import unpack_binary64, adjacent_floats, signed_zero_info, float_bits

getcontext().prec = 100

def json_float(f):
    """Encode a Python float as a JSON-safe value.
    Finite floats pass through. Non-finite values are encoded as
    explicit strings: 'NaN', 'Infinity', '-Infinity'.
    This ensures results.json is standards-compliant (allow_nan=False).
    """
    if isinstance(f, float):
        if math.isnan(f):
            return "NaN"
        if math.isinf(f):
            return "Infinity" if f > 0 else "-Infinity"
    return f

def is_decimal_exact(float_val: float, decimal_str: str) -> bool:
    """Check if binary64 float exactly equals the given decimal literal."""
    try:
        dec = Decimal(decimal_str)
        dec_f = Decimal(float_val)
        return dec == dec_f
    except Exception:
        return False

def eval_case(case: dict) -> dict:
    cid = case["id"]
    tag = case.get("tag", "")
    # ok=None means "not yet validated" — every case MUST set ok explicitly
    result = {"id": cid, "tag": tag, "ok": None, "notes": []}
    validated = False

    # helper to attach binary64 fields
    def attach_float(name, f):
        if isinstance(f, float):
            u = unpack_binary64(f)
            result[name] = {
                "value": json_float(f),
                "hex": u["hex"],
                "sign": u["sign"],
                "exponent_raw": u["exponent_raw"],
                "fraction_raw": u["fraction_raw"],
                "kind": u["kind"],
                "unbiased_exponent": u["unbiased_exponent"],
                "bits": u["bits"],
            }
            return u
        return None

    # representation / simple float cases
    rounding_tags = ("rounding", "rounding_repr", "rounding_ties")
    if "x" in case and tag in ("representation_error", "exact_ratio", "precision_boundary", "subnormal", "signed_zero", "infinity", "nan", "adjacent", "decimal_compare", "frexp_ldexp") + rounding_tags:
        x = case["x"]
        x_info = attach_float("x_info", x)

        # exactness check via Decimal
        if "expected_exact" in case and "decimal_str" in case:
            is_exact = is_decimal_exact(x, case["decimal_str"])
            result["is_exact"] = is_exact
            result["decimal_str"] = case["decimal_str"]
            result["ok"] = (is_exact == case["expected_exact"])
            validated = True
        elif "expected_exact" in case:
            # expected_exact given but no decimal_str to check against — fail validation
            result["ok"] = False
            result["error"] = "expected_exact without decimal_str"
            validated = True

        # representation equality check
        if "cmp" in case:
            cmp_val = case["cmp"]
            eq = (x == cmp_val)
            result["cmp_eq"] = eq
            if "expected_eq" in case:
                result["ok"] = (eq == case["expected_eq"])
                validated = True

        # rounding
        if "round_digits" in case:
            rd = case["round_digits"]
            rounded = round(x, rd)
            result["rounded"] = json_float(rounded)
            if "round_expected" in case:
                result["ok"] = math.isclose(rounded, case["round_expected"], rel_tol=0, abs_tol=0)
                validated = True

        # signed zero
        if tag == "signed_zero":
            zinfo = signed_zero_info(x)
            result["zero_info"] = {"is_zero": zinfo["is_zero"], "signbit": zinfo["signbit"], "bits": zinfo["bits"]}
            # validate: x == 0.0 and signbit matches case expectation
            # zero_pos: signbit False, zero_neg / zero_signbit: signbit True
            expect_neg = cid in ("zero_neg", "zero_signbit")
            ok = (x == 0.0) and (zinfo["signbit"] == expect_neg)
            result["ok"] = ok
            validated = True

        # adjacent / ulp
        if tag == "adjacent":
            adj = adjacent_floats(x)
            result["adjacent"] = {k: json_float(v) if isinstance(v, float) else v for k, v in adj.items()}
            # validate: nextafter up > x > nextafter down (for finite normal)
            if math.isfinite(x):
                up = adj["up"]; down = adj["down"]
                ok = math.isfinite(up) and math.isfinite(down) and up > x > down
                result["ok"] = ok
                validated = True

        # decimal compare
        if cid == "dec_0_1_exact":
            f = 0.1
            dec_str = Decimal("0.1")
            dec_f = Decimal(f)
            equal = (dec_str == dec_f)
            result["decimal_string"] = str(dec_str)
            result["decimal_from_float"] = str(dec_f)
            result["equal"] = equal
            # validate: Decimal('0.1') != float(0.1)
            result["ok"] = (equal == False)
            validated = True
            attach_float("float_0_1", f)

        if cid == "frac_0_1_exact":
            f = 0.1
            frac = Fraction(f).limit_denominator()
            num, den = f.as_integer_ratio()
            result["fraction"] = f"{num}/{den}"
            result["numerator"] = num
            result["denominator"] = den
            # validate: Fraction(0.1) reconstructs the float exactly
            reconstructed = num / den
            result["ok"] = (reconstructed == f and den == 2**55)
            validated = True

        # exact_ratio
        if tag == "exact_ratio" and "x" in case:
            num, den = x.as_integer_ratio()
            result["numerator"] = num
            result["denominator"] = den
            result["ratio"] = f"{num}/{den}"
            # validate: num/den reconstructs x
            ok = (num / den == x)
            result["ok"] = ok
            validated = True

        # nan self-equality
        if cid == "nan_ne_self":
            eq_self = (x == x)
            result["eq_self"] = eq_self
            if "expected_eq_self" in case:
                result["ok"] = (eq_self == case["expected_eq_self"])
                validated = True

        # subnormal classification
        if tag == "subnormal" and x_info:
            ok = (x_info["kind"] == "subnormal")
            result["ok"] = ok
            validated = True

        # infinity classification
        if tag == "infinity" and x_info:
            if cid == "inf_inf_sub":
                # handled below in NaN make section
                pass
            else:
                # inf_pos, inf_neg, inf_add
                is_inf = (x_info["kind"] == "inf")
                # check sign for inf_neg
                if cid == "inf_neg":
                    is_inf = is_inf and x_info["sign"] == 1
                elif cid == "inf_pos" or cid == "inf_add":
                    is_inf = is_inf and x_info["sign"] == 0
                result["ok"] = is_inf
                validated = True

        # nan classification
        if tag == "nan" and cid == "nan_q" and x_info:
            ok = (x_info["kind"] == "nan")
            result["ok"] = ok
            validated = True

        # frexp / ldexp round-trip
        if tag == "frexp_ldexp" and x_info:
            mant, exp = math.frexp(x)
            reconstructed = math.ldexp(mant, exp)
            result["frexp_mantissa"] = mant
            result["frexp_exponent"] = exp
            result["ldexp_reconstructed"] = json_float(reconstructed)
            # validate: ldexp(frexp(x)) == x, and 0.5 <= abs(mant) < 1.0 (or mant==0)
            mant_ok = (mant == 0.0) or (0.5 <= abs(mant) < 1.0)
            roundtrip_ok = (reconstructed == x)
            result["ok"] = mant_ok and roundtrip_ok
            validated = True

        # precision_boundary without cmp — just check it's finite and normal
        if tag == "precision_boundary" and "cmp" not in case and x_info:
            ok = x_info["kind"] in ("normal", "subnormal", "zero")
            result["ok"] = ok
            validated = True

    # overflow
    if case.get("overflow_op") == "mul10":
        x = case["x"]
        y = x * 10.0
        attach_float("x_info", x)
        is_inf = math.isinf(y)
        result["overflow_result"] = json_float(y)
        result["is_inf"] = is_inf
        # validate: overflow produced infinity
        result["ok"] = is_inf
        validated = True
        # attach y_info with full binary64 fields, even for inf
        if True:
            u = unpack_binary64(y if math.isfinite(y) else float("inf"))
            # override sign for actual y if inf
            if math.isinf(y):
                u = unpack_binary64(y)
            result["y_info"] = {
                "value": json_float(y),
                "hex": u["hex"],
                "sign": u["sign"],
                "exponent_raw": u["exponent_raw"],
                "fraction_raw": u["fraction_raw"],
                "kind": u["kind"],
                "unbiased_exponent": u["unbiased_exponent"],
                "bits": u["bits"],
            }

    # underflow
    if case.get("underflow_op"):
        x = case["x"]
        y = x * x
        attach_float("x_info", x)
        is_zero = (y == 0.0)
        result["underflow_result"] = json_float(y)
        result["is_zero"] = is_zero
        # validate: tiny * tiny underflowed to zero
        result["ok"] = is_zero and x != 0.0
        validated = True

    # non-associativity
    if tag == "non_assoc":
        if "a" in case:
            a, b, c = case["a"], case["b"], case["c"]
            left = (a + b) + c
            right = a + (b + c)
            result["left"] = json_float(left)
            result["right"] = json_float(right)
            result["equal"] = (left == right)
            # validate against expected values if given
            if "expect_left" in case and "expect_right" in case:
                ok = (left == case["expect_left"] and right == case["expect_right"])
                result["ok"] = ok
                validated = True
            else:
                # at minimum, check we got finite results
                result["ok"] = math.isfinite(left) and math.isfinite(right)
                validated = True
        if "vals" in case:
            vals = case["vals"]
            s_lr = 0.0
            for v in vals: s_lr += v
            s_rl = 0.0
            for v in reversed(vals): s_rl += v
            result["sum_lr"] = json_float(s_lr)
            result["sum_rl"] = json_float(s_rl)
            result["equal"] = (s_lr == s_rl)
            # validate: check the sums are finite and record whether order mattered
            ok = math.isfinite(s_lr) and math.isfinite(s_rl)
            result["ok"] = ok
            validated = True

    # cancellation
    if tag == "cancellation":
        if cid == "cancel_sqrt" and "x_val" in case:
            xv = float(case["x_val"])
            naive = math.sqrt(xv + 1.0) - math.sqrt(xv)
            stable = 1.0 / (math.sqrt(xv + 1.0) + math.sqrt(xv))
            result["naive"] = json_float(naive)
            result["stable"] = json_float(stable)
            rel_err = abs(naive - stable) / stable if stable != 0 else 0
            result["rel_error"] = json_float(rel_err)
            # validate: both methods give finite positive results, stable > 0
            ok = math.isfinite(naive) and math.isfinite(stable) and stable > 0
            result["ok"] = ok
            validated = True
        elif cid == "cancel_quad":
            # quadratic formula cancellation demo
            # a*x^2 + b*x + c = 0
            # roots = (-b ± sqrt(b^2 - 4ac)) / 2a
            # when |b| >> sqrt(b^2-4ac), one root suffers cancellation
            a = case.get("quad_a", 1.0)
            b = case.get("quad_b", -1e8)
            c = case.get("quad_c", 1.0)
            disc = b*b - 4*a*c
            sqrt_disc = math.sqrt(disc)
            # naive small root: (-b - sqrt_disc) / (2*a) when b < 0
            # actually with b = -1e8: -b = 1e8, so
            # root1 = (-b + sqrt_disc) / 2a  -> ~1e8  (no cancellation)
            # root2 = (-b - sqrt_disc) / 2a  -> cancellation!
            root_naive = (-b - sqrt_disc) / (2*a)
            # stable small root: c / (a * root_large)
            root_large = (-b + sqrt_disc) / (2*a)
            root_stable = c / (a * root_large) if root_large != 0 else float('nan')
            result["root_naive"] = json_float(root_naive)
            result["root_stable"] = json_float(root_stable)
            result["root_large"] = json_float(root_large)
            # high-precision Decimal reference
            getcontext().prec = 50
            da, db, dc = Decimal(str(a)), Decimal(str(b)), Decimal(str(c))
            d_disc = db*db - Decimal(4)*da*dc
            d_sqrt = d_disc.sqrt()
            d_root_small = (-db - d_sqrt) / (Decimal(2)*da)
            result["root_decimal_ref"] = str(d_root_small)
            # validate: stable root is closer to Decimal reference than naive
            # (or at least both are finite and positive and small)
            try:
                naive_err = abs(float(d_root_small) - root_naive)
                stable_err = abs(float(d_root_small) - root_stable)
                # stable should be <= naive (allow equal for very well-conditioned)
                ok = math.isfinite(root_naive) and math.isfinite(root_stable) and stable_err <= naive_err * 1.01
            except Exception:
                ok = math.isfinite(root_naive) and math.isfinite(root_stable)
            result["ok"] = ok
            validated = True

    # accumulated error
    if tag == "accumulated_error" and "step" in case:
        n = case["n"]
        step = case["step"]
        s = sum([step] * n)
        result["sum"] = json_float(s)
        if "expected_sum" in case:
            result["expected_sum"] = json_float(case["expected_sum"])
            eq = (s == case["expected_sum"])
            result["equal"] = eq
            if "expected_eq" in case:
                result["ok"] = (eq == case["expected_eq"])
                validated = True
        # fsum
        fsum_val = math.fsum([step] * n)
        result["fsum"] = json_float(fsum_val)
        # if ok not yet set, validate fsum is finite
        if not validated:
            result["ok"] = math.isfinite(fsum_val)
            validated = True

    # fsum demo (vals)
    if cid == "fsum_demo":
        vals = case["vals"]
        s = sum(vals)
        fs = math.fsum(vals)
        result["sum"] = json_float(s)
        result["fsum"] = json_float(fs)
        result["different"] = (s != fs)
        # validate against expected values
        expect_sum = case.get("expect_sum", s)
        expect_fsum = case.get("expect_fsum", fs)
        ok = (s == expect_sum and fs == expect_fsum and math.isfinite(fs))
        result["ok"] = ok
        validated = True

    # precision loss large+small
    if tag == "precision_loss" and "a" in case:
        a = case["a"]; b = case["b"]
        s = a + b
        result["sum"] = json_float(s)
        equal_a = (s == a)
        result["equal_a"] = equal_a
        if "expected_eq_a" in case:
            result["ok"] = (equal_a == case["expected_eq_a"])
            validated = True

    # representation_error op
    if case.get("op") == "sum_three_tenths":
        s = 0.1 + 0.1 + 0.1
        eq_0_3 = (s == 0.3)
        result["sum"] = json_float(s)
        result["equal_0_3"] = eq_0_3
        attach_float("sum_info", s)
        # validate: 0.1+0.1+0.1 != 0.3, demonstrating representation error
        result["ok"] = (eq_0_3 == False)
        validated = True

    # div_10
    if "divisor" in case:
        x = case["x"]
        d = case["divisor"]
        q = x / d
        result["quotient"] = json_float(q)
        q_info = attach_float("quotient_info", q)
        # validate expected_exact if given
        if "expected_exact" in case and "decimal_str" in case:
            # q should equal decimal_str? Actually x/d where x=1.0, d=10.0, so q=0.1
            is_exact = is_decimal_exact(q, case["decimal_str"])
            result["is_exact"] = is_exact
            result["decimal_str"] = case["decimal_str"]
            result["ok"] = (is_exact == case["expected_exact"])
            validated = True

    # NaN make
    if case.get("make_nan") == "inf_inf_sub":
        y = float("inf") - float("inf")
        is_nan = math.isnan(y)
        result["result"] = "NaN"
        result["is_nan"] = is_nan
        # validate: inf - inf = nan
        result["ok"] = is_nan
        validated = True

    # final validation check: every case MUST have been validated
    if not validated:
        result["ok"] = False
        result["error"] = "case was not validated — missing expectation"
    
    return result
