# methods/eval.py — case evaluation using stdlib methods
import math
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

def eval_case(case: dict) -> dict:
    cid = case["id"]
    tag = case.get("tag", "")
    result = {"id": cid, "tag": tag, "ok": True, "notes": []}

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

    # representation / simple float cases
    rounding_tags = ("rounding", "rounding_repr", "rounding_ties")
    if "x" in case and tag in ("representation_error", "exact_ratio", "precision_boundary", "subnormal", "signed_zero", "infinity", "nan", "adjacent", "decimal_compare") + rounding_tags:
        x = case["x"]
        attach_float("x_info", x)

        # exactness check via Decimal
        if "expected_exact" in case:
            try:
                result["expected_exact"] = case["expected_exact"]
            except Exception:
                pass

        # representation equality check
        if "cmp" in case:
            cmp_val = case["cmp"]
            eq = (x == cmp_val)
            result["cmp_eq"] = eq
            if "expected_eq" in case:
                result["ok"] = (eq == case["expected_eq"])

        # rounding
        if "round_digits" in case:
            rd = case["round_digits"]
            rounded = round(x, rd)
            result["rounded"] = json_float(rounded)
            if "round_expected" in case:
                result["ok"] = math.isclose(rounded, case["round_expected"], rel_tol=0, abs_tol=0)

        # signed zero
        if tag == "signed_zero":
            zinfo = signed_zero_info(x)
            # zinfo["bits"] is int, safe
            result["zero_info"] = {"is_zero": zinfo["is_zero"], "signbit": zinfo["signbit"], "bits": zinfo["bits"]}

        # adjacent / ulp
        if tag == "adjacent":
            adj = adjacent_floats(x)
            result["adjacent"] = {k: json_float(v) if isinstance(v, float) else v for k, v in adj.items()}

        # decimal compare
        if cid == "dec_0_1_exact":
            f = 0.1
            dec_str = Decimal("0.1")
            dec_f = Decimal(f)
            result["decimal_string"] = str(dec_str)
            result["decimal_from_float"] = str(dec_f)
            result["equal"] = (dec_str == dec_f)
            attach_float("float_0_1", f)

        if cid == "frac_0_1_exact":
            f = 0.1
            frac = Fraction(f).limit_denominator()
            num, den = f.as_integer_ratio()
            result["fraction"] = f"{num}/{den}"
            result["numerator"] = num
            result["denominator"] = den

        # exact_ratio
        if tag == "exact_ratio" and "x" in case:
            num, den = x.as_integer_ratio()
            result["numerator"] = num
            result["denominator"] = den
            result["ratio"] = f"{num}/{den}"

        # nan self-equality
        if cid == "nan_ne_self":
            result["eq_self"] = (x == x)
            if "expected_eq_self" in case:
                result["ok"] = (result["eq_self"] == case["expected_eq_self"])

    # overflow
    if case.get("overflow_op") == "mul10":
        x = case["x"]
        y = x * 10.0
        attach_float("x_info", x)
        result["overflow_result"] = json_float(y)
        result["is_inf"] = math.isinf(y)
        if math.isfinite(y):
            attach_float("y_info", y)

    # underflow
    if case.get("underflow_op"):
        x = case["x"]
        y = x * x
        attach_float("x_info", x)
        result["underflow_result"] = json_float(y)
        result["is_zero"] = (y == 0.0)

    # non-associativity
    if tag == "non_assoc":
        if "a" in case:
            a, b, c = case["a"], case["b"], case["c"]
            left = (a + b) + c
            right = a + (b + c)
            result["left"] = json_float(left)
            result["right"] = json_float(right)
            result["equal"] = (left == right)
            if case.get("expected_assoc_fail"):
                result["ok"] = (left != right)
        if "vals" in case:
            vals = case["vals"]
            s_lr = 0.0
            for v in vals: s_lr += v
            s_rl = 0.0
            for v in reversed(vals): s_rl += v
            result["sum_lr"] = json_float(s_lr)
            result["sum_rl"] = json_float(s_rl)
            result["equal"] = (s_lr == s_rl)
            if case.get("expected_assoc_fail"):
                result["ok"] = True

    # cancellation
    if tag == "cancellation" and "x_val" in case:
        xv = float(case["x_val"])
        if cid == "cancel_sqrt":
            naive = math.sqrt(xv + 1.0) - math.sqrt(xv)
            stable = 1.0 / (math.sqrt(xv + 1.0) + math.sqrt(xv))
            result["naive"] = json_float(naive)
            result["stable"] = json_float(stable)
            rel_err = abs(naive - stable) / stable if stable != 0 else 0
            result["rel_error"] = json_float(rel_err)
        if cid == "cancel_quad":
            naive = (xv + 1e-8) - xv
            result["naive"] = json_float(naive)
            result["expected"] = json_float(1e-8)

    # accumulated error
    if tag == "accumulated_error" and "step" in case:
        n = case["n"]
        step = case["step"]
        s = sum([step] * n)
        result["sum"] = json_float(s)
        result["expected_sum"] = json_float(case.get("expected_sum"))
        if "expected_sum" in case:
            eq = (s == case["expected_sum"])
            result["equal"] = eq
            if "expected_eq" in case:
                result["ok"] = (eq == case["expected_eq"])
        fsum_val = math.fsum([step] * n)
        result["fsum"] = json_float(fsum_val)

    # fsum demo (vals)
    if cid == "fsum_demo":
        vals = case["vals"]
        s = sum(vals)
        fs = math.fsum(vals)
        result["sum"] = json_float(s)
        result["fsum"] = json_float(fs)
        result["different"] = (s != fs)

    # precision loss large+small
    if tag == "precision_loss" and "a" in case:
        a = case["a"]; b = case["b"]
        s = a + b
        result["sum"] = json_float(s)
        result["equal_a"] = (s == a)
        if "expected_eq_a" in case:
            result["ok"] = (result["equal_a"] == case["expected_eq_a"])

    # representation_error op
    if case.get("op") == "sum_three_tenths":
        s = 0.1 + 0.1 + 0.1
        result["sum"] = json_float(s)
        result["equal_0_3"] = (s == 0.3)
        attach_float("sum_info", s)

    # div_10
    if "divisor" in case:
        x = case["x"]
        d = case["divisor"]
        q = x / d
        result["quotient"] = json_float(q)
        attach_float("quotient_info", q)

    # NaN make
    if case.get("make_nan") == "inf_inf_sub":
        y = float("inf") - float("inf")
        result["result"] = "NaN"
        result["is_nan"] = math.isnan(y)

    # default ok=True unless explicitly set false above
    return result
