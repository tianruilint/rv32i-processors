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

Tests check instruction results, x0, reset, subword memory, forwarding,
load-use stalls, and suppression of wrong-path register/memory writes.

## Cycle and CPI comparison

The same machine-code programs run on both cores with zero-wait memory.
Cycles exclude reset and include pipeline fill, stalls, and flushes.

Execution time also depends on clock period; frequency measurements are
outside this comparison. The [measurement method](docs/verification.md#cycle-and-cpi-measurements)
explains retirement boundaries and hazard penalties.

## Supported instructions

- Arithmetic/logic: ADD, ADDI, SUB, AND, ANDI, OR, ORI, XOR, XORI
- Comparisons: SLT, SLTI, SLTU, SLTIU
- Shifts: SLL, SLLI, SRL, SRLI, SRA, SRAI
- Memory: LB, LBU, LH, LHU, LW, SB, SH, SW
- Branches: BEQ, BNE, BLT, BGE, BLTU, BGEU
- Upper immediates/jumps: LUI, AUIPC, JAL, JALR

## Known limitations

- RV32I subset without FENCE, system/CSR instructions, exceptions, or interrupts.
- External zero-wait memory models; naturally aligned halfword/word accesses
  and four-byte-aligned instruction addresses.

The [specification](docs/specification.md) defines the complete interface
contract.

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
`build/`.

## Quick start

Run from the repository root on Linux or WSL Ubuntu with Python 3.12,
GNU Make, and Verilator. The recorded simulator version is Verilator 5.050;
Python dependencies are pinned in `requirements.txt`.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
make lint-core lint-pipeline
make regression SEED=20260924
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
