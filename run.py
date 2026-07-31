# run.py — run all IEEE 754 binary64 cases, emit results.json / results.csv
import json, csv, sys
from cases import CASES
from methods.eval import eval_case

def main():
    rows = []
    for case in CASES:
        r = eval_case(case)
        r["case_desc"] = case.get("desc", "")
        rows.append(r)

    # results.json — standards-compliant, allow_nan=False
    with open("results.json", "w") as f:
        json.dump(rows, f, indent=2, default=str, allow_nan=False)

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
