# RV32I Single-Cycle Processor

This repository is a work-in-progress educational project for building an
RV32I single-cycle processor and verifying its RTL with automated tests.

The processor does **not** exist yet. This bootstrap checkpoint contains only
the repository infrastructure and an intentionally incomplete one-bit full
adder smoke test. The full-adder outputs are left as a student TODO, so the
functional test is expected to fail until `rtl/full_adder.sv` is implemented.

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

`make lint` deliberately prints warnings caused by the unimplemented
full-adder. `make test` must compile the design, start Verilator and cocotb,
exercise all eight input combinations, and then report functional mismatches
until the TODO is completed.

After implementing the full adder manually, run:

```sh
make clean && make lint && make test && make waves
```

Generated simulator output, reports, caches, and waveforms are ignored by Git.
