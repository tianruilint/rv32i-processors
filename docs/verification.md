# Verification

## Regression

Latest verified default run: 2026-10-06, Verilator 5.050 and cocotb 2.0.1.
Exact source/runner hashes, commands, tool versions, UTC start/end times and
output hashes are recorded in the
[run manifest](../reports/verification/20261006T102942Z/manifest.json).

```sh
make regression SEED=20261006
```

All 17 targets passed: **74 cases, 74 passed, 0 failed, 0 skipped**.

The 74 cases break down as:

| Category | Cases | Definition |
| --- | ---: | --- |
| Module-level | 44 | 43 CPU module cases + 1 full-adder bootstrap |
| Single-cycle integration/benchmarks | 20 | 17 in test-core + 3 single-cycle matched benchmarks |
| Pipeline integration | 10 | 10 in test-pipeline-core |
| Total | 74 | |

`test-core` comprises 7 core, 3 load/store, 4 branch and 3 program cases.
The three separate single-cycle benchmark cases bring the category to 20.
Forwarding, hazard, x0 and reset are intersecting checks, not additional
cases. The 17 targets and 74 cases are listed below.

| Make target | XML under build/reports/ | Cases |
| --- | --- | ---: |
| `test` | full_adder.xml | 1 |
| `test-alu` | alu.xml | 2 |
| `test-register-file` | register_file.xml | 5 |
| `test-pc` | pc.xml | 3 |
| `test-immediate-generator` | immediate_generator.xml | 1 |
| `test-decoder` | decoder.xml | 1 |
| `test-core` | core.xml | 17 |
| `test-single-cycle-benchmark` | single_cycle_benchmark.xml | 3 |
| `test-pipeline-frontend` | pipeline_frontend.xml | 1 |
| `test-pipeline-id` | pipeline_id.xml | 5 |
| `test-pipeline-id-ex` | pipeline_id_ex.xml | 1 |
| `test-pipeline-ex` | pipeline_ex.xml | 13 |
| `test-pipeline-ex-mem` | pipeline_ex_mem.xml | 5 |
| `test-pipeline-hazard` | pipeline_hazard.xml | 2 |
| `test-pipeline-mem` | pipeline_mem.xml | 3 |
| `test-pipeline-mem-wb` | pipeline_mem_wb.xml | 1 |
| `test-pipeline-core` | pipeline_core.xml | 10 |

The ALU's two cases contain 19 directed and 2,000 seeded input vectors.
The immediate and decoder cases contain 13 and 42 vectors respectively.
These vector counts, the 37 supported instruction types, and dynamic retired
instruction counts are separate from the 74 cocotb cases.

## Test structure

| Layer | Source | Checks |
| --- | --- | --- |
| Shared components | `test_alu.py`, `test_register_file.py`, `test_pc.py`, `test_immediate_generator.py`, `test_decoder.py` | Independent ALU expectations, x0/write enable, PC control, I/S/B/U/J fields, decode qualification |
| Single-cycle core | `test_core.py`, `test_lw_sw.py`, `test_beq.py`, `test_program.py` | Register/PC results, memory lanes, branch outcomes, jump links, reset |
| Pipeline units | `test_pipeline_*.py` excluding `test_pipeline_core.py` | Stage-register reset/bubbles, bypass/forwarding priority, hazards, EX redirects, MEM lane selection, write gating |
| Pipeline programs | `test_pipeline_core.py` | Register and byte-memory results, retirement-PC traces, stalls, redirects, and in-flight reset |
| Matched benchmarks | `test_single_cycle_benchmark.py`, `test_pipeline_core.py` | Same machine-code programs on both cores, final state and cycle counts |

The integrated pipeline cases cover:

- EX/MEM and MEM/WB forwarding, including LUI and link values.
- Load-to-ALU, load-to-store, and load-to-branch dependencies.
- Taken branch, JAL, and JALR redirects; wrong-path stores/register writes.
- All six branch conditions across unit and program tests.
- Byte/halfword sign and zero extension, byte preservation, x0, and reset while
  a store is in flight.
- Signed/unsigned comparisons, logical/arithmetic shifts, upper immediates,
  and a backward-branch loop.

The single-cycle cases additionally check each relational branch with both
operand orders and equality, register shifts using 31 and 32, a negative JAL
target, and loop counters initialized to zero and one. Passing these directed
cases does not establish exhaustive instruction or input coverage.

## Memory and sampling

The testbench supplies `instr` for the fetch PC, waits for combinational
outputs to settle, and supplies an aligned 32-bit little-endian read word.
Before the rising edge it captures store address, data, enable, and strobes.
At the edge the Python model writes only selected bytes; after settling it
checks architectural state. Simulator address values are converted with
`int(...)` before dictionary access.

Each independent case establishes its own reset, inputs, and register
preconditions. The register-file array has no reset. Pipeline program and
benchmark memory helpers return zero for absent bytes; that is a testbench
choice, not an architectural guarantee about uninitialized memory.

The WB→ID bypass case explicitly writes x5=0 through WB before checking
its old value. This fixes a test assumption about simulator initialization,
not an RTL reset requirement. The corrected five-case ID group also passed
with Verilator `--x-initial unique --x-assign unique` and runtime seed
20261006. That repeat is not added to the default 74.

Pipeline program fetch uses an ADDI x0,x0,0 outside the supplied program while
the pipeline drains. Completion is the retirement of a designated terminal
instruction; the CPU itself has no halt port or halt instruction.

## Cycle and CPI measurements

The matched programs are in `test_single_cycle_benchmark.py` and
`test_pipeline_core.py`. They check the same register/memory results.
The single-cycle harness counts committing edges through its terminal
instruction. The pipeline harness counts from the first non-reset edge
through retirement of the terminal instruction and checks `retired_count`
against the observed retirement trace.

| Program | Retired instructions | Single-cycle cycles | Pipeline cycles | Load-use stalls | Taken redirects |
| --- | ---: | ---: | ---: | ---: | ---: |
| ALU dependencies | 8 | 8 | 12 | 0 | 0 |
| Subword memory | 10 | 10 | 16 | 2 | 0 |
| Loop sum 1..5 | 22 | 22 | 35 | 1 | 4 |

For these programs the pipeline counts satisfy
`cycles = retired + 4 + load_use_stalls + 2 * taken_redirects`.
The four extra cycles fill the pipeline. Each load-use hazard inserts one
bubble, and each taken EX redirect discards two younger slots.
CPI is `cycles / retired`: 1.5000, 1.6000, and 1.5909 for the pipeline;
1.0000 for the single-cycle core.

These measurements use zero-wait memory. They do not measure execution time
at a physically achievable clock frequency.

## Optional longer matched programs

```sh
make benchmark SEED=20261006
```

`tb/test_benchmarks_extended.py` runs four independent cases on each core.
`scripts/run_benchmarks.py` checks 4+4 XML results and matching machine-code
and complete retirement-PC trace hashes. It binds actual RTL/test/runner
hashes to `build/benchmarks/summary.json`; reset is excluded from the window,
which ends at the designated terminal instruction's commit/retirement.
Each benchmark target regenerates its XML, and the runner rejects a report
that was not written during the current execution.

| Workload | N | SC cycles | Pipeline cycles | CPI | L | R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Independent ALU | 512 | 512 | 516 | 1.0078125 | 0 | 0 |
| Dependent ALU | 512 | 512 | 516 | 1.0078125 | 0 | 0 |
| Branch loop | 771 | 771 | 1,285 | 1.666667 | 0 | 255 |
| Repeated load-use | 259 | 259 | 391 | 1.509653 | 128 | 0 |

These **8 optional cases are not in the default 17-target/74-case inventory**.
For these workloads, hazard cycles match `C=N+4+L+2R`. The 512/516
examples establish the no-stall fill baseline, not a performance optimization.
IPC is `N/C`; execution time still needs a defensible clock period.

The optional checks establish all checked register preconditions, final
register values, complete retirement sequences, zero unexpected stores,
and exact stall/redirect/counter values. They remain directed expectations,
not an independent whole-core ISA interpreter.

## Reports and reproduction

The [2026-10-06 published run](../reports/verification/20261006T102942Z/)
contains the raw regression logs/XML, matched-benchmark results, the separate
five-case WB→ID initialization repeat, synthesis logs and both STA reports.
It was produced by one invocation of

```sh
python3 scripts/record_run.py --seed 20261006
```

which runs every command listed in its manifest in order, stops on the first
failure, and records tool versions and SHA-256 hashes of the sources and of
every saved output. OpenSTA must be on `PATH` as `sta`, and the Nangate45
Liberty file must be in `build/timing/` (see [synthesis.md](synthesis.md)).

Each target overwrites its XML under `build/reports/`. The runner combines
stdout/stderr in `build/reports/regression/<target>.log`, also overwritten per
target. Benchmark lines in the two core benchmark logs contain cycles,
retired instructions, and CPI.

A nonzero Make return code fails the target. After a successful command the
runner rejects missing/malformed XML, zero cases, failures/errors, and skipped
cases. Printed totals include only parsed reports, so the failed-target list
and process status determine whether the complete run passed.

The runner supplies `COCOTB_RANDOM_SEED` through `SEED`. The ALU vector
generator separately uses `random.Random(20260906)`. Source, tool versions,
and test selection are also required to reproduce results.

```sh
make test-pipeline-core
make test-single-cycle-benchmark
make waves-core
gtkwave build/waves/core.fst
```

To isolate the single-cycle zero-initialized loop:

```sh
make waves-core CORE_TEST_MODULES=test_program COCOTB_TEST_FILTER='test_program2$'
```

Waveforms are generated only by explicit waveform targets, saved under
`build/waves/`, and ignored by Git. Wave targets share the temporary
`dump.fst` name and must run serially. The count of saved traces is not a
test-coverage metric.

The output layout is:

| Path | Contents |
| --- | --- |
| `build/reports/*.xml` | Latest cocotb results per target |
| `build/reports/regression/*.log` | Latest regression stdout/stderr per target |
| `build/waves/*.fst` | Waveforms generated on request |
| `reports/timing/*.txt` | Two saved STA analysis reports |
| `reports/verification/<UTC>/` | Dated run manifest, raw logs/XML and benchmark results |

`make clean` clears generated simulation products, test reports, and waveforms.
It preserves `build/timing/` dependencies and the saved `reports/timing/`
evidence. STA constraints and interpretation are in [synthesis.md](synthesis.md).

## Verification limits

The optional `make test-isa-reference` target uses a separate Python
interpreter to decode instruction words and compare both cores against its
architectural state after each retired instruction. It checks retirement PCs,
initialized integer registers, ordered byte-write events, and final memory.
The 64 deterministic generated programs exercise the supported 37 instructions.
A separate case checks all 256 FENCE predecessor/successor masks only under the
existing strongly ordered memory model; FENCE remains outside the supported
instruction claim. These four cocotb cases are separate from the default 74.
The additional reference run on 2026-10-06 passed all four cases;
[raw XML and per-program records](../reports/verification/20261006T102942Z/isa-reference/)
are saved separately.
XML results and per-program JSON records are written to `build/isa-reference/`.

This custom model is not an external ISS or ISA compliance suite. It assumes
naturally aligned accesses and zero-wait memory, without traps, interrupts,
CSRs, caches, MMIO, or external observers. There is no formal proof, gate-level
equivalence result, or automated coverage percentage. The default program
checks still use directed expected values and selected retirement traces.

Unsupported/misaligned instructions, every reset interaction, variable-latency
memory, and all runner error paths are not exhaustively tested. Some assertions
inspect internal register storage and therefore depend on the RTL hierarchy.
