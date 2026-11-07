import subprocess
import sys
import os
import argparse
import xml.etree.ElementTree as ET


def run_one(target, seed, log_path):
    env = os.environ.copy()
    env["COCOTB_RANDOM_SEED"] = str(seed)

    with open(log_path, "w", encoding="utf-8") as log_file:
        result = subprocess.run(
            ["make", target],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

    return result.returncode


def read_report(path):
    root = ET.parse(path).getroot()
    cases = root.findall(".//testcase")

    failed = 0
    skipped = 0

    for case in cases:
        if case.find("failure") is not None or case.find("error") is not None:
            failed += 1
        elif case.find("skipped") is not None:
            skipped += 1

    return len(cases), failed, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261006)
    parser.add_argument("--build-dir", default="build")
    args = parser.parse_args()
    reports = f"{args.build_dir}/reports"

    targets = {
        "test": f"{reports}/full_adder.xml",
        "test-alu": f"{reports}/alu.xml",
        "test-register-file": f"{reports}/register_file.xml",
        "test-pc": f"{reports}/pc.xml",
        "test-immediate-generator": f"{reports}/immediate_generator.xml",
        "test-decoder": f"{reports}/decoder.xml",
        "test-core": f"{reports}/core.xml",
        "test-single-cycle-benchmark": f"{reports}/single_cycle_benchmark.xml",
        "test-pipeline-frontend": f"{reports}/pipeline_frontend.xml",
        "test-pipeline-id": f"{reports}/pipeline_id.xml",
        "test-pipeline-id-ex": f"{reports}/pipeline_id_ex.xml",
        "test-pipeline-ex": f"{reports}/pipeline_ex.xml",
        "test-pipeline-ex-mem": f"{reports}/pipeline_ex_mem.xml",
        "test-pipeline-hazard": f"{reports}/pipeline_hazard.xml",
        "test-pipeline-mem": f"{reports}/pipeline_mem.xml",
        "test-pipeline-mem-wb": f"{reports}/pipeline_mem_wb.xml",
        "test-pipeline-core": f"{reports}/pipeline_core.xml",
    }

    os.makedirs(f"{reports}/regression", exist_ok=True)

    failed = []

    total_cases = 0
    total_failed = 0
    total_skipped = 0

    for target, report_path in targets.items():
        log_path = f"{reports}/regression/{target}.log"

        code = run_one(target, args.seed, log_path)
        if code != 0:
            print(target, "FAIL (make)", flush=True)
            failed.append(target)
            continue

        try:
            total, failed_count, skipped_count = read_report(report_path)
        except (OSError, ET.ParseError) as error:
            print(target, "FAIL (report):", error, flush=True)
            failed.append(target)
            continue

        passed_count = total - failed_count - skipped_count
        print(
            f"{target} passed {passed_count} failed {failed_count} skipped {skipped_count}",
            flush=True,
        )

        total_cases += total
        total_failed += failed_count
        total_skipped += skipped_count

        if total == 0 or failed_count > 0 or skipped_count > 0:
            failed.append(target)

    total_passed = total_cases - total_failed - total_skipped
    print(
        f"TOTAL: {total_cases} cases, {total_passed} passed, {total_failed} failed, {total_skipped} skipped",
        flush=True,
    )
    print(f"Failed targets: {failed}", flush=True)

    if len(failed) == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
