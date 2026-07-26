import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build/benchmarks"
WORKLOADS = ["independent_512", "dependent_512", "branch_loop_256", "load_use_128"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    paths = sorted((ROOT / "rtl").glob("*.sv")) + sorted((ROOT / "tb").glob("*.py"))
    paths += [ROOT / "Makefile", Path(__file__), ROOT / "scripts/run_regression.py", ROOT / "requirements.txt"]
    return {str(path.relative_to(ROOT)): digest(path) for path in paths}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261005)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    before = sources()
    env = os.environ.copy()
    env["COCOTB_RANDOM_SEED"] = str(args.seed)
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary = {
        "started_utc": start, "seed": args.seed,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": before, "runs": {}, "matched_workloads": [],
        "included_in_default_regression": False,
    }
    failures = []
    for core, target in [("single_cycle", "benchmark-single"), ("pipeline", "benchmark-pipeline")]:
        command = ["make", target]
        log = OUTPUT / (core + ".log")
        run_started = time.time()
        tick = time.monotonic()
        with log.open("w") as stream:
            stream.write("COMMAND: " + repr(command) + "\n")
            stream.flush()
            process = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        xml = OUTPUT / (core + ".xml")
        report = {"command": command, "exit_code": process.returncode,
                  "elapsed_seconds": round(time.monotonic() - tick, 3),
                  "log_sha256": digest(log)}
        try:
            cases = ET.parse(xml).getroot().findall(".//testcase")
            report.update(cases=len(cases),
                          failed=sum(c.find("failure") is not None or c.find("error") is not None for c in cases),
                          skipped=sum(c.find("skipped") is not None for c in cases), xml_sha256=digest(xml),
                          xml_written_during_run=xml.stat().st_mtime >= run_started)
        except (OSError, ET.ParseError) as error:
            report["report_error"] = str(error)
        if process.returncode or report.get("cases") != 4 or report.get("failed") or report.get("skipped") or not report.get("xml_written_during_run"):
            failures.append(target)
        summary["runs"][core] = report
        print(target, "FAIL" if target in failures else "4/4 PASS", flush=True)
    if not failures:
        for name in WORKLOADS:
            single = json.loads((OUTPUT / "results" / ("single_cycle_" + name + ".json")).read_text())
            pipeline = json.loads((OUTPUT / "results" / ("pipeline_" + name + ".json")).read_text())
            assert single["program_sha256"] == pipeline["program_sha256"]
            assert single["retirement_trace_sha256"] == pipeline["retirement_trace_sha256"]
            assert single["retired"] == pipeline["retired"]
            summary["matched_workloads"].append({"name": name, "single_cycle": single, "pipeline": pipeline})
            print(name, "N=", pipeline["retired"], "cycles=", pipeline["cycles"],
                  "L=", pipeline["stalls"], "R=", pipeline["redirects"], flush=True)
    summary["source_unchanged_during_run"] = before == sources()
    summary["failed_targets"] = failures
    summary["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2))
    if not summary["source_unchanged_during_run"]:
        failures.append("source changed during run")
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
