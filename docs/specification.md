# Intended Project Specification

## Scope

The long-term goal is an educational, single-cycle processor implementing the
RV32I base integer instruction set in SystemVerilog. Automated RTL verification
will compare observable behavior against independently calculated expectations
and retain useful failure reports and waveforms outside version control.

## Engineering goals

- Keep the processor structure readable enough for instruction and review.
- Define architectural behavior before implementing each processor block.
- Add small, deterministic tests before integrating larger datapath features.
- Use Verilator and cocotb for repeatable automated verification.
- Use linting, waveforms, synthesis checks, and a bug diary as learning tools.
- Keep generated artifacts out of Git so a fresh clone is reproducible.

## Current checkpoint

This repository is only the Day 0/Day 1 bootstrap. No CPU core, decoder,
register file, instruction memory, data memory, or RISC-V instruction has been
implemented. The only RTL source is an intentionally incomplete full-adder
smoke test that the student must finish manually.
