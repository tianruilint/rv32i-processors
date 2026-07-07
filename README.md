# RV32I Single-Cycle Processor

An owner-written educational 32-bit single-cycle CPU with automated
SystemVerilog/Verilator/cocotb verification.

## Implemented scope

The integrated core supports these **12 instruction types**:

- ADD, ADDI, SUB
- AND, ANDI, OR, ORI
- SLT, SLTI
- LW, SW
- BEQ

`rtl/rv32i_core.sv` connects the PC, decoder, register file, immediate generator,
ALU, load/store interface, writeback selection, and BEQ path. Instruction and
data memories are **external Python models**, not synthesized RAM modules.
The program tests fetch instruction words using the DUT's `current_pc`.

The ALU also implements XOR, shifts, and unsigned comparison at component level.
Their CPU instruction decoding is not implemented in v0.1.
Read the [specification](docs/specification.md),
[datapath diagram](docs/datapath.md), and
[control table](docs/control_table.md) for the precise boundary.

## Quick start

For a fresh Python environment only:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Do not recreate an existing working environment. Normal checks are:

```sh
make env
make lint-core
make regression SEED=20260915
```

`make regression` runs all seven test groups, reports case counts and failed
targets, and returns a nonzero status on a detected failure. It must run from
the repository root. `make test` alone still tests **only the full adder**.

## Targeted tests and waveforms

```sh
make test-alu
make test-register-file
make test-pc
make test-immediate-generator
make test-decoder
make test-core
make waves-core
```

`test-core` and `waves-core` select
`test_core,test_lw_sw,test_beq,test_program`. Wave generation is explicit, not
automatic on failure. `waves-core` writes `waves/core.fst`; inspect it with
GTKWave. Run waveform targets serially: they use the shared `dump.fst` name.

## Repository map

| Path | Purpose |
| --- | --- |
| `rtl/` | Owner-written components and integrated core |
| `tb/` | cocotb component, instruction, and program tests |
| `scripts/run_regression.py` | Test scheduling, XML statistics, logs, seed forwarding |
| `docs/` | Implemented specification, architecture, verification, and debug evidence |
| `build/`, `reports/`, `waves/` | Reproducible generated artifacts, ignored by Git |

- Only the 12 listed instruction types are supported; no jump, upper-immediate,
  subword memory, remaining branch, CSR, trap, interrupt, or privileged support.
- Memory has no ready/valid protocol or variable latency; tests supply reads
  before the committing clock edge and model writes at the edge.
- Tests use aligned instructions and word accesses. Alignment/access faults
  are not implemented; byte ordering is not verified by a word-only model.
- No whole-core ISA reference interpreter or formal verification is claimed.
- Programs are literal machine words in Python; assembler-to-image automation
  is deferred.

## References and attribution

Instruction semantics follow the
[RISC-V unprivileged ISA specification](https://docs.riscv.org/reference/isa/v20240411/unpriv/rv32.html).

Generated simulator output, reports, caches, and waveforms are ignored by Git.
