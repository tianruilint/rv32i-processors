"""Merge Verilator coverage from `make coverage` and write text reports.

Two merges are produced: the default regression alone (the 74 cases) and the
default regression plus the separate ISA reference run.

Verilator's own summary counts every instance separately, so a point missed by
a unit-test instance stays uncovered even when the same RTL line is covered
inside a core. The "by design unit" table merges instances: a point counts as
covered when any instance of that module hit it.
"""
import collections
import re
import subprocess
import sys
import tempfile
from pathlib import Path

POINT = re.compile(r"^[+-](\d+)\s+point: type=(\w+) comment=(.*?) hier=\S+")
TYPES = ("line", "branch", "expr", "toggle")


def unit_points(merged):
    """Return {(file, type): {point_key: covered}} merged across instances."""
    points = collections.defaultdict(dict)
    with tempfile.TemporaryDirectory() as out:
        subprocess.run(
            ["verilator_coverage", "--annotate", out, "--annotate-points",
             "--annotate-all", str(merged)],
            check=True, capture_output=True,
        )
        for path in sorted(Path(out).glob("*.sv")):
            line_no = 0
            for text in path.read_text().splitlines():
                match = POINT.match(text)
                if match is None:
                    line_no += 1
                    continue
                count, kind, comment = int(match[1]), match[2], match[3]
                key = (line_no, comment)
                seen = points[(path.name, kind)]
                seen[key] = seen.get(key, False) or count > 0
    return points


def unit_table(points):
    rows = []
    files = sorted({f for f, _ in points})
    totals = {t: [0, 0] for t in TYPES}
    for name in files:
        cells = []
        for kind in TYPES:
            seen = points.get((name, kind), {})
            hit, total = sum(seen.values()), len(seen)
            totals[kind][0] += hit
            totals[kind][1] += total
            cells.append(f"{100 * hit / total:5.1f}% ({hit}/{total})" if total else "-")
        rows.append(f"  {name:28} " + "  ".join(f"{c:>18}" for c in cells))
    total_cells = [f"{100 * h / t:5.1f}% ({h}/{t})" if t else "-" for h, t in totals.values()]
    header = f"  {'file':28} " + "  ".join(f"{t:>18}" for t in TYPES)
    rows.append(f"  {'TOTAL':28} " + "  ".join(f"{c:>18}" for c in total_cells))
    return "\n".join([header, *rows])


def missed(points):
    lines = []
    for (name, kind), seen in sorted(points.items()):
        if kind == "toggle":
            continue
        for (line_no, comment), covered in sorted(seen.items()):
            if not covered:
                lines.append(f"  {name}:{line_no} {kind} {comment}")
    return "\n".join(lines) or "  (none)"


def merge(root, name, dats):
    merged = root / f"{name}.dat"
    subprocess.run(
        ["verilator_coverage", "--write", str(merged), *map(str, dats)], check=True
    )
    report = subprocess.run(
        ["verilator_coverage", "--report", "summary,hier", str(merged)],
        check=True, capture_output=True, text=True,
    ).stdout
    subprocess.run(
        ["verilator_coverage", "--annotate", str(root / f"annotated_{name}"),
         "--annotate-min", "1", str(merged)],
        check=True, capture_output=True,
    )
    points = unit_points(merged)
    by_unit = unit_table(points)
    text = (
        "Per-instance (Verilator):\n" + report
        + "\nBy design unit, instances merged:\n" + by_unit
        + "\n\nUncovered line/branch/expr points (instances merged):\n" + missed(points) + "\n"
    )
    (root / f"{name}.txt").write_text(text)
    return report.split("Hierarchy Coverage Summary:")[0], by_unit


def main():
    root = Path(sys.argv[1])
    dats = sorted((root / "dat").glob("*.dat"))
    default = [d for d in dats if not d.stem.startswith("test-isa-reference")]
    if not default:
        sys.exit("no coverage data under " + str(root / "dat"))

    for name, group in (("default", default), ("with_isa_reference", dats)):
        summary, by_unit = merge(root, name, group)
        print(f"== {name}: {len(group)} targets")
        print("Per-instance (Verilator):")
        print(summary.split("Coverage Summary:")[1].rstrip())
        print("By design unit, instances merged:")
        print(by_unit)
    print(f"Reports and annotated sources: {root}")


if __name__ == "__main__":
    main()
