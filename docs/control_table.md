# Shared Decoder and Pipeline Control Table

Source: `rtl/decoder.sv`, `rtl/rv32i_core.sv`, and `rtl/rv32i_pipeline_core.sv`.
The instruction decode values are shared by the single-cycle and pipeline tops.
This table records implemented outputs, not proposed behavior.

## v2.0 control lifetime

| Control/data | ID/EX | EX/MEM | MEM/WB | Consumer |
| --- | --- | --- | --- | --- |
| `alu_op`, `alu_src`, `alu_a_pc`, operands, immediate | yes | result only | result only | EX ALU |
| `branch`, `branch_type`, `jump_type` | yes | no | no | EX redirect |
| `funct3` | yes | yes | no | MEM byte/half/word selection |
| `mem_write`, store data | yes | yes | no | MEM store interface |
| `reg_write`, `rd_addr`, `result_src` | yes | yes | yes | WB register write |
| `imm`, `pc_plus_4` | yes | yes | yes | LUI/link WB and forwarding |
| `valid` | yes | yes | yes | side-effect and retirement gating |

Hazard priority is reset > EX redirect/flush > load-use stall > normal
advance. An EX-stage load with nonzero rd matching an actual ID source holds
the frontend and inserts one invalid ID/EX bubble. EX/MEM forwards only
non-load writeback results; MEM/WB forwards all four result types. A taken
redirect flushes the two younger pipeline slots. The register file is written
only by valid WB, while stores commit only from valid MEM.

## Encoding qualification

All fields below are binary. R-type uses opcode `0110011`; I-type arithmetic
uses `0010011`; LW uses `0000011`; SW uses `0100011`; the branch group uses
`1100011`; LUI uses `0110111`; AUIPC uses `0010111`; JAL uses `1101111`;
and JALR uses `1100111`.

| Instruction | Class | funct3 | funct7 qualification |
| --- | --- | --- | --- |
| ADD | R | `000` | `0000000` |
| SUB | R | `000` | `0100000` |
| AND | R | `111` | `0000000` |
| OR | R | `110` | `0000000` |
| XOR | R | `100` | `0000000` |
| SLT | R | `010` | `0000000` |
| SLTU | R | `011` | `0000000` |
| SLL | R | `001` | `0000000` |
| SRL | R | `101` | `0000000` |
| SRA | R | `101` | `0100000` |
| ADDI | I | `000` | Not checked: these bits are immediate data |
| ANDI | I | `111` | Not checked: these bits are immediate data |
| ORI | I | `110` | Not checked: these bits are immediate data |
| XORI | I | `100` | Not checked: these bits are immediate data |
| SLTI | I | `010` | Not checked: these bits are immediate data |
| SLTIU | I | `011` | Not checked: these bits are immediate data |
| SLLI | I | `001` | Must be `0000000` |
| SRLI | I | `101` | Must be `0000000` |
| SRAI | I | `101` | Must be `0100000` |
| LB | load | `000` | Not checked |
| LH | load | `001` | Not checked |
| LW | load | `010` | Not checked |
| LBU | load | `100` | Not checked |
| LHU | load | `101` | Not checked |
| SB | store | `000` | Not checked |
| SH | store | `001` | Not checked |
| SW | store | `010` | Not checked |
| BEQ | branch | `000` | Not checked |
| BNE | branch | `001` | Not checked |
| BLT | branch | `100` | Not checked |
| BGE | branch | `101` | Not checked |
| BLTU | branch | `110` | Not checked |
| BGEU | branch | `111` | Not checked |
| LUI | U | Immediate bits, not checked | Immediate bits, not checked |
| AUIPC | U | Immediate bits, not checked | Immediate bits, not checked |
| JAL | J | Immediate bits, not checked | Immediate bits, not checked |
| JALR | I jump | `000` required | Not checked: these bits are immediate data |

## Decoder outputs

`alu_src`: 0 selects rs2, 1 selects the immediate.
`result_src`: `00` selects the ALU result, `01` external load data, `10` the
U immediate, and `11` `PC+4`. Existing table entries written as 0 or 1 mean
the two-bit values `00` or `01`.
`imm_type`: I=`000`, S=`001`, B=`010`, U=`011`, J=`100`; I is the default
even when unused.
`alu_a_pc`: 0 selects rs1 for ALU operand A; 1 selects current PC.
`jump_type`: none=`00`, JAL=`01`, JALR=`10`.
ALU operation codes here are internal, not ISA funct3 values.

| Instruction | reg_write | alu_src | mem_write | result_src | branch | imm_type | alu_op |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| ADD | 1 | 0 | 0 | 0 | 0 | I (unused) | ADD `0000` |
| SUB | 1 | 0 | 0 | 0 | 0 | I (unused) | SUB `0001` |
| AND | 1 | 0 | 0 | 0 | 0 | I (unused) | AND `0010` |
| OR | 1 | 0 | 0 | 0 | 0 | I (unused) | OR `0011` |
| XOR | 1 | 0 | 0 | 0 | 0 | I (unused) | XOR `0100` |
| SLT | 1 | 0 | 0 | 0 | 0 | I (unused) | SLT `1000` |
| SLTU | 1 | 0 | 0 | 0 | 0 | I (unused) | SLTU `1001` |
| SLL | 1 | 0 | 0 | 0 | 0 | I (unused) | SLL `0101` |
| SRL | 1 | 0 | 0 | 0 | 0 | I (unused) | SRL `0110` |
| SRA | 1 | 0 | 0 | 0 | 0 | I (unused) | SRA `0111` |
| ADDI | 1 | 1 | 0 | 0 | 0 | I | ADD `0000` |
| ANDI | 1 | 1 | 0 | 0 | 0 | I | AND `0010` |
| ORI | 1 | 1 | 0 | 0 | 0 | I | OR `0011` |
| XORI | 1 | 1 | 0 | 0 | 0 | I | XOR `0100` |
| SLTI | 1 | 1 | 0 | 0 | 0 | I | SLT `1000` |
| SLTIU | 1 | 1 | 0 | 0 | 0 | I | SLTU `1001` |
| SLLI | 1 | 1 | 0 | 0 | 0 | I | SLL `0101` |
| SRLI | 1 | 1 | 0 | 0 | 0 | I | SRL `0110` |
| SRAI | 1 | 1 | 0 | 0 | 0 | I | SRA `0111` |
| LB | 1 | 1 | 0 | 1 | 0 | I | ADD `0000` |
| LH | 1 | 1 | 0 | 1 | 0 | I | ADD `0000` |
| LW | 1 | 1 | 0 | 1 | 0 | I | ADD `0000` |
| LBU | 1 | 1 | 0 | 1 | 0 | I | ADD `0000` |
| LHU | 1 | 1 | 0 | 1 | 0 | I | ADD `0000` |
| SB | 0 | 1 | 1 | 0 | 0 | S | ADD `0000` |
| SH | 0 | 1 | 1 | 0 | 0 | S | ADD `0000` |
| SW | 0 | 1 | 1 | 0 | 0 | S | ADD `0000` |
| BEQ | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BNE | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BLT | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BGE | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BLTU | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BGEU | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| Unsupported/invalid | 0 | 0 | 0 | 0 | 0 | I | ADD `0000` |

All rows above have `alu_a_pc=0` and `jump_type=00`. Upper-immediate and
jump controls are:

| Instruction | reg_write | alu_src | mem_write | result_src | branch | imm_type | alu_op | alu_a_pc | jump_type |
| --- | ---: | ---: | ---: | --- | ---: | --- | --- | ---: | --- |
| LUI | 1 | 0 | 0 | `10` | 0 | U | ADD `0000` | 0 | `00` |
| AUIPC | 1 | 1 | 0 | `00` | 0 | U | ADD `0000` | 1 | `00` |
| JAL | 1 | 0 | 0 | `11` | 0 | J | ADD `0000` | 0 | `01` |
| JALR (`funct3=000`) | 1 | 1 | 0 | `11` | 0 | I | ADD `0000` | 0 | `10` |
| JALR (other funct3) | 0 | 0 | 0 | `00` | 0 | I | ADD `0000` | 0 | `00` |

All outputs receive defaults before the opcode case. Empty/default branches
retain these assignments, rather than retaining a previous instruction's state.

## Single-cycle qualification and side effects

- `rf_we` is `reg_write` gated off by reset. The register file separately rejects
  writes to destination x0.
- `data_write_en` is `mem_write` gated off by reset.
- `data_addr` is the full 32-bit effective byte address. The core's memory
  qualification uses `funct3` and the low address bits to select byte/halfword
  lanes and to form `data_write_data` and `data_write_strb[3:0]`.
- LB/LBU/SB select any byte lane. LH/LHU/SH select lanes 0/1 or 2/3 only;
  LW/SW select all four lanes only at a four-byte-aligned address. The strobe
  patterns are SB `0001/0010/0100/1000`, SH `0011/1100`, and SW `1111`.
- `data_write_data` is lane-aligned, and a Python memory model must preserve
  bytes whose strobe bits are zero. The one-word interface does not split or
  assemble misaligned halfword/word accesses and has no misalignment trap.
- `branch_type` uses `NONE=000`, `BEQ=001`, `BNE=010`, `BLT=011`, `BGE=100`,
  `BLTU=101`, and `BGEU=110`. `branch_taken` is `branch` plus the selected
  equality, signed-less-than, unsigned-less-than, or inverse comparison; it
  feeds `take_target`.
- JAL and JALR also feed `take_target`. JAL targets `current_pc + Jimm`; JALR
  targets the ALU sum with bit 0 cleared. Both write `current_pc + 4` to rd.
  LUI writes Uimm directly, while AUIPC adds Uimm to current PC.
- PC reset takes priority over `take_target` inside `pc.sv`.
- Branches do not depend on the selected ALU SUB result for the comparison.
- Shift-immediate upper-field values are checked before enabling SLLI, SRLI, or
  SRAI. Invalid combinations have no register/memory write or branch side effect,
  but PC advances by four when not in reset. No illegal-instruction trap exists.

The decoder unit test is one cocotb case containing 42 legal and boundary
vectors; it is not exhaustive. Its vectors include LUI, AUIPC, JAL, a
valid JALR with nonzero immediate upper bits, and an invalid JALR funct3. Valid
OR/SLT and other architectural outcomes
are also exercised by the integrated arithmetic chain;
see [verification.md](verification.md) for the evidence boundary.
