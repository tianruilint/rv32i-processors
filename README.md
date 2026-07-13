# RV32I Single-Cycle Processor

An owner-written educational 32-bit single-cycle CPU with automated
SystemVerilog/Verilator/cocotb verification.

## Implemented scope

The integrated core supports these **37 instruction types**:

- ADD, ADDI, SUB
- AND, ANDI, OR, ORI, XOR, XORI
- SLT, SLTI, SLTU, SLTIU
- SLL, SLLI, SRL, SRLI, SRA, SRAI
- LB, LBU, LH, LHU, LW
- SB, SH, SW
- BEQ, BNE, BLT, BGE, BLTU, BGEU
- LUI, AUIPC, JAL, JALR

`rtl/rv32i_core.sv` connects the PC, decoder, register file, immediate generator,
ALU, load/store interface, writeback selection, and branch comparison path. Instruction and
data memories are **external Python models**, not synthesized RAM modules.
The program tests fetch instruction words using the DUT's `current_pc`.

The v0.2 decoder selects XOR/XORI, unsigned comparisons, and register or
immediate shifts. The v0.3 decoder adds `branch_type` selection for BNE, BLT,
BGE, BLTU, and BGEU. The v0.4 decoder adds the byte/halfword load/store
encodings. Immediate shifts qualify the upper immediate bits according to the
RV32I encoding; ordinary I-type arithmetic continues to treat those bits as
immediate data.

The v0.5 path adds U- and J-type immediate generation, PC as an optional ALU
operand, `PC+4` link writeback, and direct/indirect jump target selection. JAL
uses `current_pc + Jimm`; JALR uses `(rs1 + Iimm) & ~1`. Instructions skipped
by a jump do not commit register or memory side effects in the directed test.

The data interface uses a full 32-bit byte address and an aligned 32-bit
little-endian `data_read_data` word supplied by the external Python model.
`data_write_strb[3:0]` selects the written byte lanes, and
`data_write_data` places SB/SH payload bytes in those lanes. LB/LBU/SB may use
any byte address; LH/LHU/SH require address bit 0 to be zero; LW/SW require
address bits [1:0] to be zero. Misaligned halfword/word accesses that span two
aligned words are unsupported and unverified; no misalignment trap exists.
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
make regression SEED=20260921
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
`test_core,test_lw_sw,test_beq,test_program`; the new subword cases are already
included through the existing `test_lw_sw` module. Wave generation is explicit, not
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

- Only the 37 listed instruction types are supported; there is no FENCE,
  system/CSR, trap, interrupt, or privileged support.
- Memory has no ready/valid protocol or variable latency; tests supply reads
  before the committing clock edge and model writes at the edge.
- Byte accesses may use any byte address. Halfword accesses are supported only
  at even addresses, and word accesses only at four-byte-aligned addresses.
  Misaligned halfword/word accesses are not assembled/split across words and
  have no access-fault or misalignment exception; they are unsupported and
  unverified.
- No whole-core ISA reference interpreter or formal verification is claimed.
- Programs are literal machine words in Python; assembler-to-image automation
  is deferred.

## References and attribution

Instruction semantics follow the
[RISC-V unprivileged ISA specification](https://docs.riscv.org/reference/isa/v20240411/unpriv/rv32.html).

Generated simulator output, reports, caches, and waveforms are ignored by Git.
