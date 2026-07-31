# cases.py — IEEE 754 binary64 deterministic case definitions
# stdlib only

CASES = [
    # representation error — classic surprises
    {"id": "repr_0_1", "x": 0.1, "tag": "representation_error", "desc": "0.1 not exact in binary64", "expected_exact": False, "decimal_str": "0.1"},
    {"id": "repr_0_2", "x": 0.2, "tag": "representation_error", "desc": "0.2 not exact", "expected_exact": False, "decimal_str": "0.2"},
    {"id": "repr_0_1_plus_0_2", "x": 0.1 + 0.2, "cmp": 0.3, "tag": "representation_error", "desc": "0.1+0.2 != 0.3", "expected_eq": False},
    {"id": "repr_0_3", "x": 0.3, "tag": "representation_error", "desc": "0.3 not exact", "expected_exact": False, "decimal_str": "0.3"},

    # rounding — representation-driven surprises (binary approximation, NOT true ties)
    {"id": "round_repr_2_675", "x": 2.675, "tag": "rounding_repr", "desc": "round(2.675,2)==2.67 — stored value < 2.675", "round_digits": 2, "round_expected": 2.67},
    {"id": "round_repr_1_15", "x": 1.15, "tag": "rounding_repr", "desc": "round(1.15,1)==1.1 — stored value < 1.15", "round_digits": 1, "round_expected": 1.1},
    {"id": "round_repr_1_35", "x": 1.35, "tag": "rounding_repr", "desc": "round(1.35,1)==1.4 — stored value > 1.35", "round_digits": 1, "round_expected": 1.4},

    # rounding — true ties-to-even (exactly representable halfway values)
    {"id": "round_tie_1_25", "x": 1.25, "tag": "rounding_ties", "desc": "1.25 exact, round(1.25,1)==1.2 — ties to even", "round_digits": 1, "round_expected": 1.2},
    {"id": "round_tie_2_5", "x": 2.5, "tag": "rounding_ties", "desc": "round(2.5,0)==2 — ties to even", "round_digits": 0, "round_expected": 2.0},
    {"id": "round_tie_3_5", "x": 3.5, "tag": "rounding_ties", "desc": "round(3.5,0)==4 — ties to even", "round_digits": 0, "round_expected": 4.0},
    {"id": "round_tie_2_125", "x": 2.125, "tag": "rounding_ties", "desc": "2.125 exact, round(2.125,2)==2.12 — ties to even", "round_digits": 2, "round_expected": 2.12},

    # decimal tie-looking values (representation error)
    {"id": "repr_0_55", "x": 0.55, "tag": "representation_error", "desc": "0.55", "expected_exact": False, "decimal_str": "0.55"},
    {"id": "repr_1_005", "x": 1.005, "tag": "representation_error", "desc": "1.005", "expected_exact": False, "decimal_str": "1.005"},
    {"id": "repr_4_35", "x": 4.35, "tag": "representation_error", "desc": "4.35", "expected_exact": False, "decimal_str": "4.35"},

    # precision boundary — 2**53 consecutive-integer exactness boundary
    {"id": "prec_2_53", "x": float(2**53), "tag": "precision_boundary", "desc": "2**53 — last integer where consecutive integers are all representable"},
    {"id": "prec_2_53_plus_1", "x": float(2**53 + 1), "cmp": float(2**53), "tag": "precision_boundary", "desc": "2**53 + 1 == 2**53 (ulp=2, consecutive-integer boundary crossed)", "expected_eq": True},
    {"id": "prec_2_53_plus_2", "x": float(2**53 + 2), "cmp": float(2**53), "tag": "precision_boundary", "desc": "2**53 + 2 != 2**53", "expected_eq": False},
    {"id": "prec_2_54", "x": float(2**54), "tag": "precision_boundary", "desc": "2**54 — ulp=4, every 4th integer representable"},
    {"id": "prec_2_54_plus_1", "x": float(2**54 + 1), "cmp": float(2**54), "tag": "precision_boundary", "desc": "2**54 + 1 == 2**54 (ulp=4)", "expected_eq": True},

    # subnormals
    {"id": "sub_min", "x": 5e-324, "tag": "subnormal", "desc": "smallest positive subnormal"},
    {"id": "sub_near_min", "x": 1e-320, "tag": "subnormal", "desc": "subnormal ~1e-320"},
    {"id": "sub_largest", "x": 2.225073858507201e-308, "tag": "subnormal", "desc": "largest subnormal / min normal boundary"},

    # signed zero
    {"id": "zero_pos", "x": 0.0, "tag": "signed_zero", "desc": "+0.0"},
    {"id": "zero_neg", "x": -0.0, "tag": "signed_zero", "desc": "-0.0"},
    {"id": "zero_signbit", "x": -0.0, "tag": "signed_zero", "desc": "copysign distinguishes -0.0"},

    # infinities
    {"id": "inf_pos", "x": float("inf"), "tag": "infinity", "desc": "+inf"},
    {"id": "inf_neg", "x": float("-inf"), "tag": "infinity", "desc": "-inf"},
    {"id": "inf_add", "x": float("inf") + 1e308, "tag": "infinity", "desc": "inf + finite = inf"},
    {"id": "inf_inf_sub", "x": 0.0, "tag": "infinity", "desc": "inf - inf = nan", "make_nan": "inf_inf_sub"},

    # NaN
    {"id": "nan_q", "x": float("nan"), "tag": "nan", "desc": "quiet NaN"},
    {"id": "nan_ne_self", "x": float("nan"), "tag": "nan", "desc": "nan != nan", "expected_eq_self": False},

    # adjacent floats / ulp
    {"id": "nextafter_1_up", "x": 1.0, "tag": "adjacent", "desc": "nextafter(1.0, +inf)"},
    {"id": "nextafter_1_down", "x": 1.0, "tag": "adjacent", "desc": "nextafter(1.0, -inf)"},
    {"id": "ulp_1", "x": 1.0, "tag": "adjacent", "desc": "ulp at 1.0 = 2**-52"},
    {"id": "ulp_large", "x": 1e16, "tag": "adjacent", "desc": "ulp at 1e16"},

    # overflow / underflow
    {"id": "overflow_exp", "x": 1e308, "tag": "overflow", "desc": "1e308 * 10 overflows", "overflow_op": "mul10"},
    {"id": "underflow_tiny", "x": 1e-320, "tag": "underflow", "desc": "tiny * tiny underflows", "underflow_op": True},

    # non-associativity
    {"id": "assoc_large_small", "tag": "non_assoc", "desc": "(1e16+1)-1e16, associativity demo", "a": 1e16, "b": 1.0, "c": -1e16, "expect_left": 0.0, "expect_right": 0.0},
    {"id": "assoc_sum_order", "tag": "non_assoc", "desc": "sum order matters", "vals": [1e16, 1.0, -1e16, 1.0]},

    # catastrophic cancellation
    {"id": "cancel_sqrt", "tag": "cancellation", "desc": "sqrt(x+1)-sqrt(x) loss", "x_val": 1e12},
    # quadratic formula: x^2 - 1e8*x + 1 = 0, small root suffers cancellation
    # naive: (-b - sqrt(b^2-4ac)) / 2a  loses precision when b > 0 and |b| ~ sqrt(b^2-4ac)
    # stable: c / (a * x1)  or  2c / (-b + sqrt(...))
    {"id": "cancel_quad", "tag": "cancellation", "desc": "quadratic formula cancellation", "quad_a": 1.0, "quad_b": -1e8, "quad_c": 1.0},

    # accumulated error
    {"id": "accum_0_1_ten", "tag": "accumulated_error", "desc": "sum([0.1]*10) == 1.0 (error cancels out)", "n": 10, "step": 0.1, "expected_sum": 1.0, "expected_eq": True},
    {"id": "accum_0_1_hundred", "tag": "accumulated_error", "desc": "sum([0.1]*100)", "n": 100, "step": 0.1, "expected_sum": 10.0, "expected_eq": True},

    # precision loss at different magnitudes
    {"id": "large_small_add", "tag": "precision_loss", "desc": "1e16 + 1 == 1e16", "a": 1e16, "b": 1.0, "expected_eq_a": True},
    {"id": "large_small_add2", "tag": "precision_loss", "desc": "1e16 + 100 != 1e16 (100 > ulp)", "a": 1e16, "b": 100.0, "expected_eq_a": False},

    # decimal / fractions exact comparison
    {"id": "dec_0_1_exact", "x": 0.1, "tag": "decimal_compare", "desc": "Decimal('0.1') != float(0.1)"},
    {"id": "frac_0_1_exact", "x": 0.1, "tag": "decimal_compare", "desc": "Fraction(0.1) gives binary rational"},

    # binary representation error — more decimals
    {"id": "repr_0_125", "x": 0.125, "tag": "representation_error", "desc": "0.125 = 1/8 exact", "expected_exact": True, "decimal_str": "0.125"},
    {"id": "repr_0_5", "x": 0.5, "tag": "representation_error", "desc": "0.5 exact", "expected_exact": True, "decimal_str": "0.5"},
    {"id": "repr_0_75", "x": 0.75, "tag": "representation_error", "desc": "0.75 exact", "expected_exact": True, "decimal_str": "0.75"},
    {"id": "repr_0_1_0_1_0_1", "tag": "representation_error", "desc": "0.1+0.1+0.1", "op": "sum_three_tenths"},
    {"id": "repr_0_7", "x": 0.7, "tag": "representation_error", "desc": "0.7", "expected_exact": False, "decimal_str": "0.7"},

    # exact integer ratio
    {"id": "ratio_0_1", "x": 0.1, "tag": "exact_ratio", "desc": "as_integer_ratio for 0.1"},
    {"id": "ratio_0_5", "x": 0.5, "tag": "exact_ratio", "desc": "as_integer_ratio for 0.5"},

    # frexp / ldexp round-trip
    {"id": "frexp_0_1", "x": 0.1, "tag": "frexp_ldexp", "desc": "math.frexp / math.ldexp round-trip"},
    {"id": "frexp_pi", "x": 3.141592653589793, "tag": "frexp_ldexp", "desc": "math.frexp / math.ldexp round-trip for pi"},

    # 1.0/10.0 representation
    {"id": "div_10", "x": 1.0, "tag": "representation_error", "desc": "1.0/10.0", "divisor": 10.0, "expected_exact": False, "decimal_str": "0.1"},

    # fsum vs sum
    {"id": "fsum_demo", "tag": "accumulated_error", "desc": "math.fsum vs sum", "vals": [1e16, 1.0, -1e16], "expect_fsum": 1.0, "expect_sum": 1.0},
]

# filter out skipped
CASES = [c for c in CASES if not c.get("skip")]
