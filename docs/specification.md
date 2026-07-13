# P1 v0.5 Implemented Processor Specification

## Scope

The design is a 32-bit, single-cycle, RV32I-subset core with an instruction
input and a separate external data-memory interface. The synthesized top is
`rv32i_core`; it instantiates `pc`, `decoder`, `register_file`,
`immediate_generator`, and `alu`.

Instruction and data memories are supplied by cocotb/Python. No RTL instruction
ROM, data RAM, SRAM macro, bus fabric, cache, or pipeline is part of v0.5.
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
| `data_addr` | output | 32 | ALU result; full effective byte address for memory accesses |
| `data_write_data` | output | 32 | Lane-aligned store payload for SB/SH/SW |
| `data_write_en` | output | 1 | Decoded store enable, forced low during reset |
| `data_write_strb` | output | 4 | Little-endian byte-lane write strobe; zero for loads and unsupported store alignment |

There is no read-enable, valid/ready, stall, access-fault/misalignment exception,
or halt port. The program test identifies load instructions from `instr` to
decide when to supply read data. For non-memory instructions, `data_addr`,
`data_write_data`, and `data_write_strb` may still change; they do not indicate
a memory operation without the relevant instruction or write enable.

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
- JAL selects `current_pc + sign_extended_J_immediate`. JALR selects
  `(rs1 + sign_extended_I_immediate) & 32'hfffffffe`.
- Reset has priority over branch/jump selection. Arithmetic and address results
  wrap modulo 2^32; no arithmetic-overflow exception is generated.
- The tests' 10 ns clock is a simulation stimulus setting, not a measured
  achievable clock period.

## Supported instruction semantics

`Iimm`, `Simm`, `Bimm`, and `Jimm` below are sign-extended 32-bit immediates.
`Uimm` is `instr[31:12]` followed by twelve zero bits.

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
| LB | `rd = sign_extend(external_byte[rs1 + Iimm])` |
| LBU | `rd = zero_extend(external_byte[rs1 + Iimm])` |
| LH | `rd = sign_extend(external_halfword[rs1 + Iimm])` |
| LHU | `rd = zero_extend(external_halfword[rs1 + Iimm])` |
| LW | `rd = external_word[rs1 + Iimm]` |
| SB | `external_byte[rs1 + Simm] = rs2[7:0]` |
| SH | `external_halfword[rs1 + Simm] = rs2[15:0]` |
| SW | `external_word[rs1 + Simm] = rs2` |
| BEQ | If rs1 equals rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BNE | If rs1 does not equal rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BLT | If signed rs1 is less than signed rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BGE | If signed rs1 is greater than or equal to signed rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BLTU | If unsigned rs1 is less than unsigned rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| BGEU | If unsigned rs1 is greater than or equal to unsigned rs2, next PC is current PC + Bimm; otherwise PC + 4 |
| LUI | `rd = Uimm` |
| AUIPC | `rd = current_pc + Uimm` |
| JAL | `rd = current_pc + 4`; next PC is `current_pc + Jimm` |
| JALR | For `funct3=000`, `rd = current_pc + 4`; next PC is `(rs1 + Iimm) & ~1` |

These grouped rows describe 37 instruction types. All register-writing
operations obey x0 behavior. Branches have no register or memory write side
effects. Jumps write only their link destination and do not write memory;
instructions skipped by the jump do not commit. Other supported non-branch
instructions advance PC by four. The load
extension rules are signed for LB/LH and zero-filled for LBU/LHU. ANDI and ORI
also use sign extension, not zero extension.

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

The external data model owns a byte-addressed, little-endian dictionary. The
core exports the full 32-bit effective byte address in `data_addr`. For a load,
the Python model aligns that address down to a four-byte base, assembles bytes
`base+0` through `base+3` into `data_read_data[31:0]`, and supplies the word
before the committing rising edge. The core selects the byte or aligned
halfword using `data_addr[1:0]`, then performs the specified sign or zero
extension. LW consumes the aligned 32-bit word.

For a store, the Python model samples settled `data_addr`, `data_write_data`,
`data_write_en`, and `data_write_strb` for the committing edge. It updates only
the byte lanes whose strobe bits are set; all other bytes in the aligned word
are preserved. `data_write_data` is lane-aligned: SB places `rs2[7:0]` in the
selected lane, SH places `rs2[15:0]` in lanes 0/1 or 2/3, and SW uses all four
lanes. Strobe bit 0 corresponds to the lowest-address byte, so the supported
patterns are SB `0001/0010/0100/1000`, SH `0011/1100`, and SW `1111`.

Alignment limits are part of the v0.5 contract: LB/LBU/SB may use any byte
address; LH/LHU/SH require `data_addr[0] == 0`; and LW/SW require
`data_addr[1:0] == 2'b00`. Misaligned halfword/word accesses may span two
aligned words. The current one-word external interface does not assemble or
split such transactions and the RTL has no misalignment or access-fault trap,
so those accesses are unsupported and unverified rather than supported
architectural behavior.

The RTL contains no instruction or data memory. Python owns dictionary contents,
word assembly, and strobe-preserving writes through the test helpers
`read_word` and `apply_write`. An uninitialized dictionary read is not defined
to return zero.

## Branch controls

The decoder outputs `branch_type` with project-local codes:
`NONE=000`, `BEQ=001`, `BNE=010`, `BLT=011`, `BGE=100`, `BLTU=101`, and
`BGEU=110`. The core computes equality, signed less-than, and unsigned
less-than explicitly, then selects or inverts the relevant result. `branch`
must be active before any branch type can take the target. All supported
branches leave register-file and external data-memory write enables inactive.
The core does not use an ALU zero flag as the branch decision.

## Upper-immediate and jump controls

LUI writes the U immediate directly. AUIPC selects `current_pc` as ALU operand
A and the U immediate as operand B, then writes the ALU sum. JAL and JALR select
`PC+4` as writeback data. `jump_type=01` selects the JAL target
`current_pc+imm`; `jump_type=10` selects the JALR target from the ALU sum with
bit 0 cleared. Both jump types assert `take_target` independently of the branch
comparison path.

JALR is accepted only when `funct3=000`. Its instruction bits [31:20] are the
I immediate, so the decoder does not qualify `funct7`. JAL has no funct3 or
funct7 qualification because those bit positions belong to its immediate.
The current instruction model uses four-byte-aligned addresses. JALR bit 0
clearing is implemented and tested, but a resulting target with bit 1 set does
not raise an instruction-address-misaligned exception and is unsupported and
unverified.

## Internal controls

The immediate generator and decoder use I=`000`, S=`001`, B=`010`, U=`011`,
and J=`100`.
These are project-local encodings, not ISA instruction encodings. The generator
provides an output on every combinational path; an unsupported `imm_type`
returns zero.

The two-bit writeback selection is ALU=`00`, load data=`01`, U immediate=`10`,
and `PC+4`=`11`. `alu_a_pc=1` selects current PC rather than rs1 for the ALU-A
input. `jump_type` is none=`00`, JAL=`01`, and JALR=`10`.

The core uses ALU ADD=`0000`, SUB=`0001`, AND=`0010`, OR=`0011`, XOR=`0100`,
SLL=`0101`, SRL=`0110`, SRA=`0111`, SLT=`1000`, and SLTU=`1001`. See
[control_table.md](control_table.md) for all v0.5 controls and encoding
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

- Misaligned halfword/word accesses that require two aligned external words;
  no split/assemble path or misalignment trap exists.
- Instruction-address-misaligned targets and the corresponding exception;
  targets with bit 1 set are unsupported/unverified.
- FENCE, ECALL, EBREAK, CSR/privileged/trap/interrupt machinery.
- Variable-latency memories, buses, caches, MMU, and pipeline hazards.
- Assembly-to-image automation, whole-core ISA reference interpreter, formal
  equivalence, technology-mapped PPA, and STA.
