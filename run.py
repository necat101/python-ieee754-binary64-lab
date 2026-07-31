# run.py — run all IEEE 754 binary64 cases, emit results.json / results.csv
import json, csv, sys

# Require Python 3.12+ — sum() changed to a more accurate algorithm in 3.12,
# so sum-based case outputs differ from 3.11 and earlier.
if sys.version_info < (3, 12):
    print(f"ERROR: Python 3.12+ required, found {sys.version}", file=sys.stderr)
    sys.exit(2)

from cases import CASES
from methods.eval import eval_case

def main():
    rows = []
    for case in CASES:
        r = eval_case(case)
        r["case_desc"] = case.get("desc", "")
        # fail fast if case was not validated
        if r.get("ok") is None:
            print(f"ERROR: case {r['id']} was not validated (ok=None)", file=sys.stderr)
            return 2
        rows.append(r)

    # results.json — standards-compliant, allow_nan=False, no default=str
    runtime_info = {
        "python_version": sys.version,
        "float_info": {
            "max": sys.float_info.max,
            "max_exp": sys.float_info.max_exp,
            "max_10_exp": sys.float_info.max_10_exp,
            "min": sys.float_info.min,
            "min_exp": sys.float_info.min_exp,
            "min_10_exp": sys.float_info.min_10_exp,
            "dig": sys.float_info.dig,
            "mant_dig": sys.float_info.mant_dig,
            "epsilon": sys.float_info.epsilon,
            "radix": sys.float_info.radix,
            "rounds": sys.float_info.rounds,
        }
    }
    output = {
        "runtime": runtime_info,
        "cases": rows,
    }
    with open("results.json", "w") as f:
        json.dump(output, f, indent=2, allow_nan=False)

    # results.csv – flattened
    fieldnames = ["id", "tag", "ok", "case_desc"]
    with open("results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({
                "id": r["id"],
                "tag": r["tag"],
                "ok": r["ok"],
                "case_desc": r.get("case_desc", ""),
            })

    passed = sum(1 for r in rows if r["ok"])
    print(f"{passed}/{len(rows)} cases ok")
    return 0 if passed == len(rows) else 1

if __name__ == "__main__":
    sys.exit(main())
