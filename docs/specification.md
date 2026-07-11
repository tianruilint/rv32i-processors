# P1 v0.3 Implemented Processor Specification

## Scope

The design is a 32-bit, single-cycle, RV32I-subset core with an instruction
input and a separate external data-memory interface. The synthesized top is
`rv32i_core`; it instantiates `pc`, `decoder`, `register_file`,
`immediate_generator`, and `alu`.

Instruction and data memories are supplied by cocotb/Python. No RTL instruction
ROM, data RAM, SRAM macro, bus fabric, cache, or pipeline is part of v0.3.
Automated tests check register values, memory values, PC, and selected control
signals. They do not establish complete ISA compliance.

## Core interface

Directions are relative to `rv32i_core`. Data/address ports are unsigned
`logic` vectors; signed operations are selected explicitly inside the ALU.

| Port | Direction | Width | Meaning |
| --- | --- | ---: | --- |
| `clk` | input | 1 | State commits on the rising edge |
| `reset` | input | 1 | Active-high synchronous PC reset; also gates write enables |
| `instr` | input | 32 | External instruction word for `current_pc` |
| `data_read_data` | input | 32 | External load data, stable before the commit edge |
| `current_pc` | output | 32 | Current instruction byte address |
| `data_addr` | output | 32 | ALU result; effective byte address for LW/SW |
| `data_write_data` | output | 32 | Current rs2 value, used by SW |
| `data_write_en` | output | 1 | Qualified SW write enable, forced low during reset |

There is no read-enable, valid/ready, byte-enable, stall, exception, or halt port.
The program test identifies LW from `instr` to decide when to supply read data.
For non-memory instructions, `data_addr` and `data_write_data` may still change;
they do not indicate a memory operation without the relevant instruction or
write enable.

## Architectural state and timing

- `x0` through `x31` are 32-bit architectural registers.
- The register file has two combinational read ports and one synchronous write
  port. Writes require `reg_write` and `rd_addr != 0`.
- Architectural reads of `x0` return zero; writes to `x0` are ignored. This does
  not require internal array element `registers[0]` itself to be initialized.
- The register file has no reset or initialization. Software/tests must write
  x1-x31 before relying on their values. PC reset does not clear these registers.
- On a rising edge with `reset=1`, PC becomes zero. Core register writes and
  memory writes are blocked while reset is high.
- Otherwise, one instruction commits per rising edge, assuming the environment
  has supplied stable instruction and load data. There is no latency handshake.
- Default next PC is `current_pc + 4`. A taken branch selects
  `current_pc + sign_extended_B_immediate`, not `PC+4+immediate`.
- Reset has priority over branch selection. Arithmetic and address results wrap
  modulo 2^32; no arithmetic-overflow exception is generated.
- The tests' 10 ns clock is a simulation stimulus setting, not a measured
  achievable clock period.

## Supported instruction semantics

`Iimm`, `Simm`, and `Bimm` below are sign-extended 32-bit immediates.

| Instruction | Implemented architectural action |
| --- | --- |
| ADD | `rd = rs1 + rs2` |
| ADDI | `rd = rs1 + Iimm` |
| SUB | `rd = rs1 - rs2` |
| AND / ANDI | Bitwise AND of rs1 with rs2 / Iimm |
| OR / ORI | Bitwise OR of rs1 with rs2 / Iimm |
| XOR / XORI | Bitwise XOR of rs1 with rs2 / Iimm |
| SLT / SLTI | Signed comparison of rs1 with rs2 / Iimm; rd is 0 or 1 |
| SLTU / SLTIU | Unsigned comparison of rs1 with rs2 / sign-extended Iimm; rd is 0 or 1 |
| SLL / SLLI | Logical left shift by `rs2[4:0]` / `shamt` |
| SRL / SRLI | Logical right shift by `rs2[4:0]` / `shamt` |
| SRA / SRAI | Arithmetic right shift by `rs2[4:0]` / `shamt` |
| LW | `rd = external_word[rs1 + Iimm]` |
| SW | `external_word[rs1 + Simm] = rs2` |
| BEQ | If rs1 equals rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BNE | If rs1 does not equal rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BLT | If signed rs1 is less than signed rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BGE | If signed rs1 is greater than or equal to signed rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BLTU | If unsigned rs1 is less than unsigned rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BGEU | If unsigned rs1 is greater than or equal to unsigned rs2, next PC is current PC + Bimm; otherwise PC + 4 |

These grouped rows describe 27 instruction types. All register-writing
operations obey x0 behavior. BEQ has no register or memory write side effects.
Supported non-branch instructions advance PC by four. ANDI and ORI also use
sign extension, not zero extension.

For RV32 register shifts, only the low five bits of the shift source are used.
Immediate shifts use the five-bit `shamt = instr[24:20]`. SLLI is legal only
when `instr[31:25] = 0000000`; SRLI is legal only with `0000000`; and SRAI is
legal only with `0100000`. Other shift-immediate upper-field values retain the
decoder's safe inactive defaults.

## Memory and alignment contract

The external instruction model maps byte addresses to 32-bit machine words.
Each iteration reads the DUT PC and supplies `imem[pc]`; the testbench does not
drive PC. An absent dictionary entry fails the Python test, not an architectural
fetch exception. Program-completion PC values are testbench sentinels; there is
no CPU halt instruction or halt mechanism.

The data model maps byte addresses to whole 32-bit words. For SW, the testbench
captures settled address/data/enable and applies the write at the associated
rising edge. For LW, it supplies the selected word before the rising edge so
the core can capture it in the register file. An uninitialized dictionary read
is not defined to return zero; the current program initializes its load address
with SW first.

v0.3 verification assumes 4-byte-aligned instructions, branch destinations,
and LW/SW addresses. RTL does not detect or trap misalignment or access faults.
B-immediate reconstruction fixes bit 0 to zero but does not enforce bit 1.
No byte-addressable storage layout or endianness test exists yet; v0.4 must
define that contract before adding subword accesses.

## Branch controls

The decoder outputs `branch_type` with project-local codes:
`NONE=000`, `BEQ=001`, `BNE=010`, `BLT=011`, `BGE=100`, `BLTU=101`, and
`BGEU=110`. The core computes equality, signed less-than, and unsigned
less-than explicitly, then selects or inverts the relevant result. `branch`
must be active before any branch type can take the target. All supported
branches leave register-file and external data-memory write enables inactive.
The core does not use an ALU zero flag as the branch decision.

## Internal controls

The immediate generator and decoder use I=`00`, S=`01`, B=`10`.
These are project-local encodings, not ISA instruction encodings. The generator
provides an output on every combinational path; an unsupported `imm_type`
returns zero. U/J formats are not implemented.

The core uses ALU ADD=`0000`, SUB=`0001`, AND=`0010`, OR=`0011`, XOR=`0100`,
SLL=`0101`, SRL=`0110`, SRA=`0111`, SLT=`1000`, and SLTU=`1001`. See
[control_table.md](control_table.md) for all v0.3 controls and encoding
qualification rules.

Unsupported opcodes or invalid combinations for the supported instruction
classes keep register write, memory write, and branch controls inactive. Other
defaults are ALU ADD, rs2 operand B, ALU-result writeback, and I-type immediate.
With reset low, PC still advances by four. This safe-default behavior is not
an architectural illegal-instruction trap, and complete invalid-encoding
coverage has not been established.

For ordinary I-type arithmetic, instruction bits [31:25] belong to the
immediate; they are not constrained as a register-register `funct7`. The
shift-immediate forms are the deliberate exception described above.

## Unsupported features and deferred work

- LB/LBU/LH/LHU/SB/SH and byte-write masks (v0.4).
- LUI/AUIPC/JAL/JALR and U/J immediates (v0.5).
- FENCE, ECALL, EBREAK, CSR/privileged/trap/interrupt machinery.
- Variable-latency memories, buses, caches, MMU, and pipeline hazards.
- Assembly-to-image automation, whole-core ISA reference interpreter, formal
  equivalence, technology-mapped PPA, and STA.
