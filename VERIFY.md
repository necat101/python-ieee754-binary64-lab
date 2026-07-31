# VERIFY.md — python-ieee754-binary64-lab

Verification run from a fresh detached checkout of the implementation commit.

## Implementation commit

```
aec62d81c5e6ae0575ef5cf737990dc541b6e411
https://github.com/necat101/python-ieee754-binary64-lab/commit/aec62d81c5e6ae0575ef5cf737990dc541b6e411
```

## Runtime

```
Python 3.12.3 (main, Jun 19 2026, 12:46:00) [GCC 13.3.0]
sys.float_info(max=1.7976931348623157e+308, max_exp=1024, max_10_exp=308, min=2.2250738585072014e-308, min_exp=-1021, min_10_exp=-307, dig=15, mant_dig=53, epsilon=2.220446049250313e-16, radix=2, rounds=1)
```

## Commands

```sh
git clone https://github.com/necat101/python-ieee754-binary64-lab.git /tmp/verify_ieee754
cd /tmp/verify_ieee754
git checkout --detach aec62d81c5e6ae0575ef5cf737990dc541b6e411
python3 run.py
python3 -m unittest test_binary64 -v
python3 results_to_md.py
```

## Test results

```
test_0_1_not_exact ... ok
test_0_1_plus_0_2 ... ok
test_bits_1_0 ... ok
test_bits_neg_zero ... ok
test_cancellation ... ok
test_fsum ... ok
test_inf ... ok
test_nan_ne_self ... ok
test_nextafter ... ok
test_non_assoc ... ok
test_overflow ... ok
test_precision_boundary_2_53 ... ok
test_results_json_compliance ... ok
test_round_2_675 ... ok
test_round_half_even ... ok
test_signed_zero_division ... ok
test_subnormal ... ok
----------------------------------------------------------------------
Ran 17 tests in 0.096s
OK
```

The `test_results_json_compliance` test independently verifies that `results.json` is standards-compliant (no bare NaN/Inf, `allow_nan=False`).

## Run results

```
56/56 cases ok
```

## Artifact hashes (run 1)

```
results.json  5cb93572b5ed214f6efa7aa3674a8dd0ca578d55292f51fadb5cb6f75bbf775e
results.csv   8d5e86988b106bfde4a9cc9bec97686e14f7ab5795b3a2197d660a7b31144667
RESULTS.md    2783fb0105af7a5fcb8511434eacad57fdfd81a1fa57931854f3e081ebcb57e1
```

## Determinism check (run 2)

The complete generation process was run a second time from the same detached implementation commit (`aec62d81c5e6ae0575ef5cf737990dc541b6e411`), with a clean working tree (`rm results.json results.csv RESULTS.md; rm -rf __pycache__`).

Artifact hashes (run 2):

```
results.json  5cb93572b5ed214f6efa7aa3674a8dd0ca578d55292f51fadb5cb6f75bbf775e
results.csv   8d5e86988b106bfde4a9cc9bec97686e14f7ab5795b3a2197d660a7b31144667
RESULTS.md    2783fb0105af7a5fcb8511434eacad57fdfd81a1fa57931854f3e081ebcb57e1
```

All three artifacts are byte-for-byte identical across both runs.

## Working-tree state

Generated artifacts (`results.json`, `results.csv`, `RESULTS.md`) are **gitignored** (see `.gitignore`) and were **not committed** in the implementation commit. The clean-working-tree check was performed with artifacts present but ignored:

```
git status --porcelain
(empty)
```

HEAD detached at `aec62d81c5e6ae0575ef5cf737990dc541b6e411`

## Wall time

Run 1 — `run.py`: real 0.08s, user 0.04s, sys 0.01s
Run 2 — `run.py`: real 0.10s, user 0.04s, sys 0.02s

## Failures / skips

- Case failures: 0
- Case skips: 0
- Test failures: 0
- Unittest: 17/17 pass

All 56 IEEE 754 binary64 cases pass. No external dependencies. Fully deterministic. `results.json` is standards-compliant (NaN/Inf encoded as strings, `allow_nan=False`).
