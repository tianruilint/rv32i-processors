#!/usr/bin/env python3
"""Print the clock-sweep table from the saved OpenROAD-flow-scripts results.

Reads reports/pnr/<variant>/{6_report.json,6_final.sdc,route_drc_count.txt,
lec_result.txt} and prints a Markdown table, fastest-closing clock last.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
PNR = REPO / "reports" / "pnr"


def period_ns(sdc: Path) -> float:
    m = re.search(r"-period\s+([0-9.]+)", sdc.read_text())
    return float(m.group(1))


rows = []
for d in PNR.iterdir():
    rpt = d / "6_report.json"
    if not rpt.is_file():
        continue
    m = json.loads(rpt.read_text())
    g = lambda k: m["finish__" + k]
    period = period_ns(d / "6_final.sdc")
    rows.append({
        "period": period,
        "mhz": 1000.0 / period,
        "wns": g("timing__setup__ws"),
        "tns": g("timing__setup__tns"),
        "hold": g("timing__hold__ws"),
        "slew": g("timing__drv__max_slew"),
        "cap": g("timing__drv__max_cap"),
        "power_mw": g("power__total") * 1000.0,
        "area": g("design__instance__area__stdcell"),
        "repair": g("design__instance__count__class:timing_repair_buffer"),
        "drc": int((d / "route_drc_count.txt").read_text().strip()),
        "lec": (d / "lec_result.txt").read_text().strip(),
    })

rows.sort(key=lambda r: -r["period"])
print("| Clock | Freq | WNS (ns) | TNS (ns) | Hold WS (ns) | Max-slew / max-cap viol. "
      "| Route DRC | Power | Std-cell area (µm²) | Repair buffers | LEC |")
print("| ---: | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | --- |")
for r in rows:
    met = "met" if r["wns"] >= 0 else "**violated**"
    lec = "equivalent" if "IDENTICAL" in r["lec"] else r["lec"]
    print(f"| {r['period']:.1f} ns | {r['mhz']:.0f} MHz | {r['wns']:+.3f} ({met}) | {r['tns']:.3f} "
          f"| {r['hold']:+.3f} | {r['slew']} / {r['cap']} | {r['drc']} | {r['power_mw']:.2f} mW "
          f"| {r['area']:,.0f} | {r['repair']} | {lec} |")
