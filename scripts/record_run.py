"""Run lint, regression, reference checks, benchmarks, synthesis and STA, and
save the raw outputs with a hash manifest under reports/verification/<UTC>/."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
LIBERTY = "build/timing/NangateOpenCellLibrary_typical.lib"
CORE = "rtl/rv32i_core.sv rtl/pc.sv rtl/decoder.sv rtl/register_file.sv rtl/immediate_generator.sv rtl/alu.sv"
PIPELINE = ("rtl/rv32i_pipeline_core.sv rtl/pipeline_frontend.sv rtl/pipeline_id.sv rtl/pipeline_id_ex.sv "
            "rtl/pipeline_ex.sv rtl/pipeline_ex_mem.sv rtl/pipeline_hazard.sv rtl/pipeline_mem.sv "
            "rtl/pipeline_mem_wb.sv rtl/decoder.sv rtl/immediate_generator.sv rtl/register_file.sv rtl/alu.sv")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    paths = sorted((ROOT / "rtl").glob("*.sv")) + sorted((ROOT / "tb").glob("*.py"))
    paths += sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "timing").glob("*"))
    paths += [ROOT / "Makefile", ROOT / "requirements.txt"]
    return {str(path.relative_to(ROOT)): digest(path) for path in paths}


def mapped(top, files, netlist):
    return (f"read_liberty -lib -ignore_miss_func {LIBERTY}; read_verilog -sv {files}; "
            f"hierarchy -check -top {top}; synth -top {top} -flatten; dfflibmap -liberty {LIBERTY}; "
            f"abc -liberty {LIBERTY}; clean; check -assert; stat -liberty {LIBERTY}; "
            f"write_verilog -noattr -noexpr -nodec {netlist}")


def steps(seed):
    unique = "--Wall -Wno-fatal --x-initial unique --x-assign unique"
    return [
        ("lint", ["make", "lint-core", "lint-pipeline"]),
        ("regression", ["make", "regression", f"SEED={seed}"]),
        ("isa-reference", ["make", "test-isa-reference"]),
        ("benchmarks", ["make", "benchmark", f"SEED={seed}"]),
        ("wb-id-unique-initialization", ["make", "-B", "test-pipeline-id", f"COMPILE_ARGS={unique}",
                                         f"SIM_ARGS=+verilator+seed+{seed}"]),
        ("single-cycle-generic", ["yosys", "-Q", "-T", "-p", f"read_verilog -sv {CORE}; synth -top rv32i_core; "
                                  "check -assert; stat; write_verilog -noattr build/synthesis/rv32i_core.v"]),
        ("pipeline-generic", ["yosys", "-Q", "-T", "-p", f"read_verilog -sv {PIPELINE}; synth -top rv32i_pipeline_core "
                              "-flatten; check -assert; stat; write_verilog -noattr build/synthesis/rv32i_pipeline_core.v"]),
        ("single-cycle-mapped", ["yosys", "-Q", "-T", "-p",
                                 mapped("rv32i_core", CORE, "build/timing/rv32i_core_nangate45.v")]),
        ("pipeline-mapped", ["yosys", "-Q", "-T", "-p",
                             mapped("rv32i_pipeline_core", PIPELINE, "build/timing/rv32i_pipeline_core_nangate45.v")]),
        ("single-cycle-sta", ["sta", "-no_init", "-no_splash", "-exit", "timing/run_sta.tcl"]),
        ("pipeline-sta", ["sta", "-no_init", "-no_splash", "-exit", "timing/run_pipeline_sta.tcl"]),
    ]


def collect(name, out):
    build = ROOT / "build"
    if name == "regression":
        shutil.copytree(build / "reports", out / "regression-reports")
    elif name == "isa-reference":
        shutil.copytree(build / "isa-reference", out / "isa-reference")
    elif name == "benchmarks":
        shutil.copytree(build / "benchmarks", out / "benchmarks")
    elif name == "wb-id-unique-initialization":
        shutil.copy2(build / "reports/pipeline_id.xml", out / (name + ".xml"))
    elif name == "single-cycle-sta":
        shutil.copy2(out / (name + ".log"), ROOT / "reports/timing/core_setup_nangate45_typ_10ns.txt")
    elif name == "pipeline-sta":
        shutil.copy2(out / (name + ".log"), ROOT / "reports/timing/pipeline_setup_nangate45_typ_10ns.txt")


def cases(paths):
    total = failed = skipped = 0
    for path in paths:
        for case in ET.parse(path).getroot().iter("testcase"):
            total += 1
            failed += case.find("failure") is not None or case.find("error") is not None
            skipped += case.find("skipped") is not None
    return total, failed, skipped


def version(command):
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout.strip().splitlines()[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261006)
    args = parser.parse_args()
    if not (ROOT / LIBERTY).is_file():
        raise SystemExit(f"Missing {LIBERTY}; see docs/synthesis.md")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "reports/verification" / stamp
    out.mkdir(parents=True)
    for path in ["build/reports", "build/isa-reference", "build/benchmarks"]:
        shutil.rmtree(ROOT / path, ignore_errors=True)
    (ROOT / "build/synthesis").mkdir(parents=True, exist_ok=True)
    before = sources()
    manifest = {"started_utc": now(), "source_sha256": before, "seed": args.seed, "commands": []}
    for name, command in steps(args.seed):
        record = {"name": name, "command": command, "started_utc": now()}
        tick = time.monotonic()
        with (out / (name + ".log")).open("w") as log:
            process = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        record.update(exit_code=process.returncode, elapsed_seconds=round(time.monotonic() - tick, 3),
                      ended_utc=now())
        manifest["commands"].append(record)
        print(name, "PASS" if process.returncode == 0 else "FAIL", record["elapsed_seconds"], flush=True)
        if process.returncode:
            raise SystemExit(f"{name} failed; see {out / (name + '.log')}")
        collect(name, out)
    regression = sorted((out / "regression-reports").glob("*.xml"))
    total, failed, skipped = cases(regression)
    reference = cases(sorted((out / "isa-reference").glob("*.xml")))
    if failed or skipped or reference[1] or reference[2]:
        raise SystemExit("Failed or skipped cases in the recorded reports")
    manifest.update(
        library_sha256=digest(ROOT / LIBERTY),
        tools={"verilator": version(["verilator", "--version"]), "yosys": version(["yosys", "-V"]),
               "opensta": version(["sta", "-version"]), "python": version([".venv/bin/python", "--version"]),
               "cocotb": version([".venv/bin/cocotb-config", "--version"])},
        regression={"targets": len(regression), "cases": total, "passed": total - failed - skipped,
                    "failed": failed, "skipped": skipped},
        additional_reference_cases=reference[0],
        source_unchanged_during_run=before == sources(),
        ended_utc=now())
    files = sorted(p for p in out.rglob("*") if p.is_file())
    files += sorted((ROOT / "reports/timing").glob("*.txt"))
    manifest["files"] = {str(p.relative_to(ROOT)): digest(p) for p in files}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if not manifest["source_unchanged_during_run"]:
        raise SystemExit("Source changed during the run")
    print(f"RECORD_PASS report={out.relative_to(ROOT)} cases={total} targets={len(regression)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
