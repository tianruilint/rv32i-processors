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

The component work is complete through DAY06:

- DAY01: a one-bit full adder with automated verification;
- DAY02: a 32-bit ALU with automated verification;
- DAY03: a 32 x 32-bit register file with two combinational read ports, one
  synchronous enabled write port, and architectural `x0` behavior;
- DAY04: a 32-bit program counter with synchronous active-high reset, sequential
  `+4`, target loading, reset priority, and natural wraparound;
- DAY05: an immediate generator for I-, S-, and B-type encodings, including
  sign extension and B-immediate alignment;
- DAY06: a decoder for R-type ADD/SUB/AND/OR/SLT, I-type
  ADDI/ANDI/ORI/SLTI, LW, SW, and BEQ, with safe defaults for unsupported
  encodings.

These are independently verified building blocks. U- and J-type immediate
generation, instruction memory, data memory, and an integrated CPU core have
not yet been implemented. The repository therefore does not yet execute or
claim end-to-end support for any RISC-V instruction.

## Current control encodings

The immediate generator and decoder use the following internal format codes:

- I-type: `2'b00`
- S-type: `2'b01`
- B-type: `2'b10`

These encodings are internal design choices. Their correctness depends on
consistent use across the decoder, immediate generator, and integration tests.

The decoder currently recognizes:

- R-type: ADD, SUB, AND, OR, SLT
- I-type arithmetic: ADDI, ANDI, ORI, SLTI
- Memory: LW, SW
- Branch: BEQ

Unsupported opcodes or invalid `funct3`/`funct7` combinations produce inactive
control defaults. This is a component-level contract, not yet an architectural
illegal-instruction mechanism.
