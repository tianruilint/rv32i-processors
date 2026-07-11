# v0.3 Decoder and Core Control Table

## Encoding qualification

All fields below are binary. R-type uses opcode `0110011`; I-type arithmetic
uses `0010011`; LW uses `0000011`; SW uses `0100011`; the branch group uses
`1100011`.

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
| LW | load | `010` | Not checked |
| SW | store | `010` | Not checked |
| BEQ | branch | `000` | Not checked |
| BNE | branch | `001` | Not checked |
| BLT | branch | `100` | Not checked |
| BGE | branch | `101` | Not checked |
| BLTU | branch | `110` | Not checked |
| BGEU | branch | `111` | Not checked |

## Decoder outputs

`alu_src`: 0 selects rs2, 1 selects the immediate.
`result_src`: 0 selects the ALU result, 1 selects external memory read data.
`imm_type`: I=`00`, S=`01`, B=`10`; I is the default even when unused.
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
| LW | 1 | 1 | 0 | 1 | 0 | I | ADD `0000` |
| SW | 0 | 1 | 1 | 0 | 0 | S | ADD `0000` |
| BEQ | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BNE | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BLT | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BGE | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BLTU | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| BGEU | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| Unsupported/invalid | 0 | 0 | 0 | 0 | 0 | I | ADD `0000` |

All outputs receive defaults before the opcode case. Empty/default branches
retain these assignments, rather than retaining a previous instruction's state.

## Core qualification and side effects

- `rf_we` is `reg_write` gated off by reset. The register file separately rejects
  writes to destination x0.
- `data_write_en` is `mem_write` gated off by reset.
- `branch_type` uses `NONE=000`, `BEQ=001`, `BNE=010`, `BLT=011`, `BGE=100`,
  `BLTU=101`, and `BGEU=110`. `branch_taken` is `branch` plus the selected
  equality, signed-less-than, unsigned-less-than, or inverse comparison; it
  feeds `take_target`.
- PC reset takes priority over `take_target` inside `pc.sv`.
- Branches do not depend on the selected ALU SUB result for the comparison.
- Shift-immediate upper-field values are checked before enabling SLLI, SRLI, or
  SRAI. Invalid combinations have no register/memory write or branch side effect,
  but PC advances by four when not in reset. No illegal-instruction trap exists.

The decoder unit test is one cocotb case containing 29 legal and boundary
vectors; it is not exhaustive. Valid OR/SLT and other architectural outcomes
are also exercised by the integrated arithmetic chain;
see [verification_plan.md](verification_plan.md) for the evidence boundary.
