# RV32I Single-Cycle Processor

This repository is a work-in-progress educational project for building an
RV32I single-cycle processor and verifying its RTL with automated tests.

The current checkpoint has completed DAY10 and integrates the program counter,
decoder, register file, immediate generator, ALU, load/store interface,
writeback selection, and BEQ branch path in `rtl/rv32i_core.sv`.

The instruction-level core currently supports this 12-instruction subset:

- ADD, ADDI, SUB
- AND, ANDI, OR, ORI
- SLT, SLTI
- LW, SW
- BEQ

This is not yet the formal P1 v0.1 release. The instruction is currently driven
through the core's external `instr` input, and cocotb supplies the external data
memory behavior. PC-indexed instruction-memory execution, program-level tests,
release documentation, and the initial synthesis pass remain future work.

## Environment

The project targets WSL2 Ubuntu, SystemVerilog, Verilator 5.036 or newer,
cocotb 2.0.1, pytest, GTKWave, Yosys, and the
`riscv64-unknown-elf` GCC/binutils toolchain. Python verification packages are
installed in the project-local `.venv`.

From the project root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
make env
make lint
make test
```

Current component verification targets are:

```sh
make lint
make test
make lint-alu
make test-alu
make test-register-file
make test-pc
make test-immediate-generator
make test-decoder
make lint-core
make test-core
make waves-core
```

`make test-core` runs the current integrated instruction-level regression.
The latest observed DAY10 run completed four cocotb test cases with four passes
and no failures. Those test cases collectively cover the 12 instruction types
listed above; four test cases must not be interpreted as 12 separate tests.

Generated simulator output, reports, caches, and waveforms are ignored by Git.
