# v0.1 Decoder and Core Control Table

## Encoding qualification

All fields below are binary. R-type uses opcode `0110011`; I-type arithmetic
uses `0010011`; LW uses `0000011`; SW uses `0100011`; BEQ uses `1100011`.

| Instruction | Class | funct3 | funct7 qualification |
| --- | --- | --- | --- |
| ADD | R | `000` | `0000000` |
| SUB | R | `000` | `0100000` |
| AND | R | `111` | `0000000` |
| OR | R | `110` | `0000000` |
| SLT | R | `010` | `0000000` |
| ADDI | I | `000` | Not checked: these bits are immediate data |
| ANDI | I | `111` | Not checked: these bits are immediate data |
| ORI | I | `110` | Not checked: these bits are immediate data |
| SLTI | I | `010` | Not checked: these bits are immediate data |
| LW | load | `010` | Not checked |
| SW | store | `010` | Not checked |
| BEQ | branch | `000` | Not checked |

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
| SLT | 1 | 0 | 0 | 0 | 0 | I (unused) | SLT `1000` |
| ADDI | 1 | 1 | 0 | 0 | 0 | I | ADD `0000` |
| ANDI | 1 | 1 | 0 | 0 | 0 | I | AND `0010` |
| ORI | 1 | 1 | 0 | 0 | 0 | I | OR `0011` |
| SLTI | 1 | 1 | 0 | 0 | 0 | I | SLT `1000` |
| LW | 1 | 1 | 0 | 1 | 0 | I | ADD `0000` |
| SW | 0 | 1 | 1 | 0 | 0 | S | ADD `0000` |
| BEQ | 0 | 0 | 0 | 0 | 1 | B | SUB `0001` |
| Unsupported/invalid | 0 | 0 | 0 | 0 | 0 | I | ADD `0000` |

All outputs receive defaults before the opcode case. Empty/default branches
retain these assignments, rather than retaining a previous instruction's state.

## Core qualification and side effects

- `rf_we` is `reg_write` gated off by reset. The register file separately rejects
  writes to destination x0.
- `data_write_en` is `mem_write` gated off by reset.
- `branch_taken` is `branch && (rs1_data == rs2_data)`; it feeds `take_target`.
- PC reset takes priority over `take_target` inside `pc.sv`.
- BEQ does not depend on the selected ALU SUB result for equality.
- Unsupported encodings have no register/memory write or branch side effect,
  but PC advances by four when not in reset. No illegal-instruction trap exists.

The nine-vector decoder unit test is not exhaustive. Valid OR/SLT and other
architectural outcomes are also exercised by the integrated arithmetic chain;
see [verification_plan.md](verification_plan.md) for the evidence boundary.
