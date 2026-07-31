# python-ieee754-binary64-lab

Deterministic, stdlib-only Python lab inspecting IEEE 754 binary64 floating-point behavior in CPython.

Inspect Python's float runtime (`sys.float_info`), decode binary64 sign / exponent / fraction fields via `struct`, and demonstrate: representation error, subnormals, signed zero, infinities, NaN, adjacent floats (`math.nextafter`), rounding (ties-to-even and representation-driven surprises), the `2**53` consecutive-integer exactness boundary, overflow, underflow, non-associativity, catastrophic cancellation, accumulated error, `math.frexp` / `math.ldexp` round-trip, and decimal/fractions exact comparisons.

Requires **Python 3.12+**. Python 3.12 changed `sum()` to use a compensated summation algorithm (PEP 604 / GH-100425), so sum-based case outputs differ from Python 3.11 and earlier. Case expectations and artifact hashes are for Python 3.12+.

## Run

```sh
python3 run.py              # → results.json, results.csv
python3 -m unittest test_binary64 -v
python3 results_to_md.py    # → RESULTS.md (generated locally, gitignored)
```

## Cases (58)

**representation_error** (13): `repr_0_1`, `repr_0_2`, `repr_0_1_plus_0_2`, `repr_0_3`, `repr_0_55`, `repr_1_005`, `repr_4_35`, `repr_0_125`, `repr_0_5`, `repr_0_75`, `repr_0_1_0_1_0_1`, `repr_0_7`, `div_10`

**rounding_repr** (3) — representation-driven rounding surprises: `round_repr_2_675`, `round_repr_1_15`, `round_repr_1_35`. These values are not exactly representable in binary64; the stored approximation is slightly above/below the decimal literal, which affects `round()`.

**rounding_ties** (4) — true ties-to-even: `round_tie_1_25`, `round_tie_2_5`, `round_tie_3_5`, `round_tie_2_125`. Exactly representable halfway values demonstrating Python's round-half-to-even (banker's rounding).

**precision_boundary** (5): `2**53` consecutive-integer exactness boundary, `2**54` ULP transition — `prec_2_53`, `prec_2_53_plus_1`, `prec_2_53_plus_2`, `prec_2_54`, `prec_2_54_plus_1`

**subnormal** (3): min subnormal (5e-324), ~1e-320, largest subnormal boundary

**signed_zero** (3): +0.0, -0.0, copysign distinction

**infinity** (4): +inf, -inf, inf+finite, inf-inf → nan

**nan** (2): quiet NaN, nan != nan

**adjacent** (4): nextafter up/down at 1.0, ulp at 1.0 and 1e16

**overflow / underflow** (2): 1e308*10 → inf, 1e-320*1e-320 → 0

**non_assoc** (2): (1e16+1)-1e16 associativity, sum order

**cancellation** (2): sqrt(x+1)-sqrt(x), quadratic formula with stable root

**accumulated_error** (3): sum([0.1]*10), sum([0.1]*100), fsum vs sum

**precision_loss** (2): 1e16+1, 1e16+100

**decimal_compare** (2): Decimal('0.1') vs float(0.1), Fraction(0.1)

**exact_ratio** (2): as_integer_ratio for 0.1 and 0.5

**frexp_ldexp** (2): `math.frexp` / `math.ldexp` round-trip for 0.1 and pi

All 58 cases pass — surprising float behavior is expected and recorded, not a test failure. Every case executes at least one explicit validation; unvalidated cases fail the run.

## Binary64 layout

```
sign (1) | exponent (11) | fraction (52)
```

Extracted via `struct.pack(">d", f)` / `struct.unpack(">Q", …)`.

Primary inputs record the full binary64 encoding: sign bit, raw exponent, raw fraction, unbiased exponent, `float.hex()` representation, and classification (normal / subnormal / zero / inf / nan). Computed results include JSON-safe float values; see `results.json` for field-level detail per case.

## Methods (stdlib only)

- `struct` — sign/exp/fraction bit unpacking, hex float
- `math` — `isclose`, `nextafter`, `frexp`, `ldexp`, `fsum`, `copysign`, `isnan`, `isinf`, `sqrt`
- `decimal` — exact decimal reference values for comparison; also used for high-precision quadratic-formula reference
- `fractions` — exact rational representation
- `sys` — `sys.version`, `sys.float_info` (runtime metadata, recorded in `results.json`)

No external dependencies. No network calls. Deterministic on Python 3.12+.

Python's built-in `round()` uses round-half-to-even (banker's rounding). The runtime floating-point rounding mode is reported via `sys.float_info.rounds` (typically `1` = round-to-nearest). This lab does not change the binary floating-point environment rounding mode. Decimal context rounding modes, if demonstrated, are explicitly labeled as Decimal-only.

## results.json encoding

`results.json` is standards-compliant JSON with runtime metadata:

```json
{
  "runtime": {
    "python_version": "3.12.3 ...",
    "float_info": { "mant_dig": 53, "epsilon": 2.22e-16, "rounds": 1, ... }
  },
  "cases": [ ... ]
}
```

Non-finite float values (NaN, ±Infinity) are encoded as explicit strings `"NaN"`, `"Infinity"`, `"-Infinity"` — never as bare JSON-invalid constants. Serialization uses `json.dump(…, allow_nan=False)` with no `default=` fallback, so accidental non-standard values fail loudly. See `test_results_json_compliance` for independent verification.

## How this differs from python-floating-point-footgun-lab

[`python-floating-point-footgun-lab`](https://github.com/necat101/python-floating-point-footgun-lab) (48 cases) covers broad floating-point footguns and policy: `math` / `decimal` / `fractions` / `statistics` interactions, money rounding, summation order, integer-cents fixed-point, Decimal context precision/rounding/traps, percent/tax, and general "float is hard" practitioner advice.

This lab (`python-ieee754-binary64-lab`) is narrower and lower-level: it focuses specifically on **IEEE 754 binary64 encoding**:

- sign / exponent / fraction field decoding for primary inputs
- normal and subnormal encoding, including min subnormal (5e-324) and the normal/subnormal boundary
- ULP transitions at `2**53` (consecutive-integer exactness boundary) and `2**54`
- adjacent representable values via `math.nextafter`, explicit ULP measurements
- special encodings: signed zero (±0.0 distinct in bit pattern), infinities, NaN (with NaN != NaN)
- `float.hex()` for inspected values, `as_integer_ratio` exposing the exact binary rational
- representation-driven rounding surprises vs true ties-to-even, clearly separated
- `math.frexp` / `math.ldexp` round-trip

In short: footgun-lab teaches "how to avoid float traps in practice"; binary64-lab teaches "what the bits actually look like".

## Artifacts

- `results.json` — full per-case output with runtime metadata and binary64 fields (standards-compliant JSON)
- `results.csv` — summary table
- `RESULTS.md` — rendered summary, **generated locally, gitignored**

Run `python3 run.py && python3 results_to_md.py` to regenerate `RESULTS.md` from a fresh checkout.

## License

MIT
