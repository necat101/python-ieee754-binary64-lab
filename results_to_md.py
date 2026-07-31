#!/usr/bin/env python3
# results_to_md.py — render RESULTS.md from results.json
import json, sys

with open("results.json") as f:
    rows = json.load(f)

ok_count = sum(1 for r in rows if r.get("ok"))
total = len(rows)

out = []
out.append("# RESULTS — python-ieee754-binary64-lab\n")
out.append(f"**{ok_count}/{total} cases ok**\n")
out.append("| id | tag | ok | notes |")
out.append("|---|---|:---:|---|")
for r in rows:
    notes = []
    # pull a few interesting fields
    if "x_info" in r:
        xi = r["x_info"]
        notes.append(f"`{xi.get('hex','')}`")
        notes.append(xi.get("kind",""))
    if r.get("cmp_eq") is not None:
        notes.append(f"eq={r['cmp_eq']}")
    if "rounded" in r:
        notes.append(f"round→{r['rounded']}")
    if "sum" in r:
        notes.append(f"sum={r['sum']}")
    if "fsum" in r:
        notes.append(f"fsum={r['fsum']}")
    note_str = ", ".join(str(x) for x in notes if x)[:120]
    out.append(f"| {r['id']} | {r['tag']} | {'✓' if r['ok'] else '✗'} | {note_str} |")

out.append("")
out.append(f"_Generated from {total} deterministic IEEE 754 binary64 cases._\n")

with open("RESULTS.md", "w") as f:
    f.write("\n".join(out))

print(f"Wrote RESULTS.md ({ok_count}/{total} ok)")
