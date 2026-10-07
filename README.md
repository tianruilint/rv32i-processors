# RV32I Single-Cycle and Five-Stage Pipeline Processors

SystemVerilog implementations of a **37-instruction RV32I subset**, with
single-cycle and five-stage pipeline cores, automated cocotb verification,
and reproducible cycle/CPI comparisons.

## Architecture

- Separate `rv32i_core` and `rv32i_pipeline_core` tops sharing the ALU,
  decoder, register file, and immediate generator.
- IF, ID, EX, MEM, and WB stages with EX/MEM and MEM/WB forwarding and
  WB-to-ID bypass.
- One-cycle load-use stalls; EX-resolved branches, JAL, and JALR with
  two-slot flushes.
- Valid/reset-gated writes and little-endian byte-write strobes for
  byte, halfword, and word memory accesses.

See the [datapath diagrams](docs/datapath.md) and
[control table](docs/control_table.md).

## Verification

Latest full regression, matched benchmarks, synthesis and STA rerun:
**2026-10-06**. The
[dated run manifest](reports/verification/20261006T102942Z/manifest.json)
records source hashes, tool versions, commands and raw outputs.

`make regression` runs **74 cocotb cases across 17 Verilator targets**:
44 module-level, 20 single-cycle integration/benchmark and 10 pipeline
integration cases. Tests check instruction results, x0, reset, subword
memory, forwarding, load-use stalls, and suppression of wrong-path
register/memory writes.

Both cores passed Yosys structural checks. Detailed test assertions,
vector counts, and reproduction instructions are in
[verification](docs/verification.md); mapped results and STA are in
[synthesis and timing](docs/synthesis.md).

## Cycle and CPI comparison

Measured cycles on hazard workloads match the zero-wait-memory model
`C = N + 4 + L + 2R`: retired instructions, four fill cycles, one cycle per
load-use stall, and two per taken EX redirect. The same machine-code programs
and retirement-PC sequences run on both cores. Cycles exclude reset.

| Optional matched workload | N | Single-cycle cycles | Pipeline cycles | L | R |
| --- | ---: | ---: | ---: | ---: | ---: |
| Independent ALU | 512 | 512 | 516 | 0 | 0 |
| Dependent ALU | 512 | 512 | 516 | 0 | 0 |
| Branch loop | 771 | 771 | 1,285 | 0 | 255 |
| Repeated load-use | 259 | 259 | 391 | 128 | 0 |

`make benchmark SEED=20261006` runs these four workloads on each core
(separate from the default 74). With no hazards the pipeline needs only the
four fill cycles (512 → 516); each taken branch costs two cycles and each
load-use pair one. See the [measurement method](docs/verification.md#cycle-and-cpi-measurements).

## Synthesis and STA

Yosys maps both cores to Nangate45 (typical corner); OpenSTA analyses them
core-only and pre-layout at a 10 ns ideal clock (0.1 ns setup uncertainty,
0.5 ns I/O delay):

| Metric | Single-cycle | Pipeline |
| --- | ---: | ---: |
| Worst setup slack | +5.202 ns | +6.181 ns |
| Critical arrival / required | 4.198 / 9.400 ns | 3.676 / 9.857 ns |
| Mapped cells | 6,267 | 9,556 |
| Liberty cell-area sum | 12,737.410 | 17,515.302 |
| Max-slew violating report rows | 49 | 1,576 |
| Max-capacitance violating report rows | 91 | 84 |

Critical paths: instruction input `instr[21]` through decode, register read
and store-data selection to `data_write_data[10]` (single-cycle); IF/ID rs1
address bit → register-file read mux → ID/EX `rs1_data[0]` (pipeline).
The worst max-slew violators are the register-address flops (e.g. the rs1
address bit above) that fan out across the 32-entry register-file read mux;
these still need buffering or upsizing, so the slack is not quoted as an Fmax.

## Supported instructions

- Arithmetic/logic: ADD, ADDI, SUB, AND, ANDI, OR, ORI, XOR, XORI
- Comparisons: SLT, SLTI, SLTU, SLTIU
- Shifts: SLL, SLLI, SRL, SRLI, SRA, SRAI
- Memory: LB, LBU, LH, LHU, LW, SB, SH, SW
- Branches: BEQ, BNE, BLT, BGE, BLTU, BGEU
- Upper immediates/jumps: LUI, AUIPC, JAL, JALR

## Known limitations

- Excluded RV32I base instructions: FENCE, ECALL, EBREAK.
- Also unsupported: Zicsr CSR instructions, Zifencei FENCE.I, privileged MRET,
  exceptions/traps and interrupts.
- External zero-wait memory models; naturally aligned halfword/word accesses
  and four-byte-aligned instruction addresses.
- STA is typical-corner, core-only, and pre-layout, with unresolved electrical
  constraints; no achievable Fmax or physical signoff is claimed.

The [specification](docs/specification.md) defines the complete interface
contract. Detailed [verification limits](docs/verification.md#verification-limits)
and [timing limits](docs/synthesis.md#interpretation) accompany the results.

## Documentation

| Document | Contents |
| --- | --- |
| [Specification](docs/specification.md) | Instruction semantics, interfaces, reset, and memory contract |
| [Datapath](docs/datapath.md) | Pipeline boundaries, forwarding, and single-cycle architecture |
| [Control table](docs/control_table.md) | Decode qualification and control-signal encodings |
| [Verification](docs/verification.md) | Tests, benchmarks, sampling, and reproduction |
| [Synthesis and timing](docs/synthesis.md) | Tools, library identity, constraints, and reports |
| [Debugging notes](docs/debugging_notes.md) | Symptoms, root causes, fixes, and verification |

Source is under `rtl/`, tests under `tb/`, and timing constraints/scripts
under `timing/`. Generated test results and waveforms stay under ignored
`build/`; `reports/timing/` contains the two saved STA analysis reports.

## Quick start

Run from the repository root on Linux or WSL Ubuntu with Python 3.12,
GNU Make, and Verilator. The recorded simulator version is Verilator 5.050;
Python dependencies are pinned in `requirements.txt`.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
make lint-core lint-pipeline
make regression SEED=20261006
make benchmark SEED=20261006
```

`make test-pipeline-core` runs the
integrated pipeline tests; `make test` alone runs only the full-adder component.
Waveform instructions are in [verification](docs/verification.md#reports-and-reproduction).

## License and references

Project source is available under the [MIT License](LICENSE).
EDA tools and cell libraries are obtained separately and retain their own
licenses; they are not bundled with this repository.

Instruction semantics follow the
[RISC-V unprivileged ISA specification](https://docs.riscv.org/reference/isa/v20240411/unpriv/rv32.html).
