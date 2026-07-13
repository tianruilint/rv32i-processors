# v0.5 Verification Plan and Evidence

## Layers and responsibilities

- `tb/test_alu.py`: independent Python arithmetic/logic expectations, including
  directed and seeded vectors, for the ALU component.
- Other component tests check register-file, PC, immediate, and decoder behavior.
- Core tests drive instructions and inspect architectural register/PC/memory
  results, with some control and internal-hierarchy checks.
- `tb/test_program.py` adds PC-indexed instruction fetch and external memory
  behavior; its Python loop simulates cycles rather than computing the DUT's sum.
- `scripts/run_regression.py` schedules existing tests and collects results. It
  is not a CPU reference model or a replacement for the testbenches.

There is no independent whole-core ISA interpreter, formal proof, or automated
functional/line/branch coverage measurement in this checkpoint.

## Core cases and architectural expectations

| Case | Main observation |
| --- | --- |
| test_arithmetic_chain | ADD/ADDI/SUB/AND/ANDI/OR/ORI/SLT/SLTI results, PC progression, x0 protection |
| test_reset_blocks_register_write | Existing x13 value survives an attempted write while reset forces PC=0 |
| test_lw_sw | Store 42 at byte address 72 and load 42 into x3 |
| test_subword_load_store | LB/LBU/LH/LHU/SB/SH behavior, sign/zero extension, lane-aligned stores, and byte preservation |
| test_subword_lane_boundaries | All four byte lanes, both aligned halfword lanes, and load-side lane selection |
| test_beq | Taken +8, not taken, negative -12 branch; a taken BEQ's write enables are checked inactive |
| test_bne | Equal operands not taken and unequal operands taken; both branch write enables inactive |
| test_blt_bge | Signed -1 versus 1: BLT taken and BGE not-taken; both branch write enables inactive |
| test_bltu_bgeu | Unsigned 0xffffffff versus 1: BLTU not-taken and BGEU taken; both branch write enables inactive |
| test_program | Fetch at PC 0/4/8; final x3=12, PC=12 |
| test_program2 | Current initial-0 program exits loop, stores/loads 0 at byte address 64, ends at PC=32 |
| test_xor_sltu_instrs | XOR/XORI and SLTU/SLTIU results, including unsigned ordering and sign-extended immediate behavior |
| test_shift_instrs | SLL/SLLI, SRL/SRLI, SRA/SRAI; shift amount 31, register source 32, final PC=52, and `data_write_en=0` |
| test_upper_immediate_instrs | LUI at PC 0 and AUIPC at PC 4; expected x1/x2 values and no memory-write side effect |
| test_jal_jalr_control_flow | PC path `0,4,8,16,20,40`, JAL/JALR links, odd-target bit-0 clearing, skipped destinations unchanged, and no memory write |

This exercises the 37 supported instruction types, but does not prove all their
input combinations or all side effects under every condition. In particular,
not every unsupported encoding, reset/memory interaction, or misaligned
halfword/word access is tested. The relational branch reverse directions and
equality boundaries are not tested. The integrated jump test uses one positive
JAL offset and one forward JALR target. A negative J immediate is checked at
the component level, but a negative taken JAL, target bit 1 behavior, and an
instruction-address-misalignment exception are not integrated/verified.
Current tests inspect internal register
storage for some assertions; that hierarchy is a test dependency, not a stable
external hardware interface.

## Memory-model ordering

The test supplies `instr`, lets combinational signals settle, converts DUT
addresses with `int(...)`, and supplies aligned little-endian load data before
the rising edge. It captures store address/data/enable/strobe for the
committing edge and updates only the selected bytes in the Python dictionary.
After the edge, it allows signal updates to settle before inspecting
architectural state. `read_word` assembles an aligned 32-bit word and
`apply_write` preserves bytes whose strobe bits are zero.

No real SRAM, memory latency, ready/valid handshake, cross-word assembly/split,
or alignment exception is modeled. Literal machine words are embedded in
Python; no assembler/program-image build is run. LB/LBU/SB may use any byte
address; LH/LHU/SH require bit 0 clear; LW/SW require bits [1:0] clear.

## Runner behavior and limitations

Each Make target removes its previous XML before its normal simulation. The
runner handles a nonzero Make return code as target failure without parsing
that target's XML. If Make succeeds, it parses testcase elements and rejects
missing/malformed XML, zero cases, failures/errors, or skipped cases. It
continues to the remaining targets for these handled failures.

Consequently, printed case totals cover successfully parsed reports only;
`Failed targets` and the exit status determine whole-run success. A failed
build with no parsed report must not be interpreted as zero failures overall.

The complete runner error-path matrix has not been dynamically validated.

Logs: `reports/regression/<target>.log`, stdout and stderr combined, overwritten
per target. XML remains directly under `reports/`. No per-run manifest or
immutable run archive is generated. A failure opening a log or launching Make
is not handled by the report-parsing exception handler.

`--seed` is parsed by the runner and passed through the subprocess environment
as `COCOTB_RANDOM_SEED`.
`random.Random(20260906)` in the ALU test is independently seeded. Reproduction
also requires the same source, test selection, and compatible toolchain; the
seed alone is not a complete environment record.

## Waveform reproduction

```sh
make waves-core
gtkwave waves/core.fst
```

To focus on the currently saved zero-initialized program:

```sh
make waves-core CORE_TEST_MODULES=test_program COCOTB_TEST_FILTER=test_program2
```
