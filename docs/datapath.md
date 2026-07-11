# v0.3 Single-cycle Datapath

The boxes inside the core are synthesizable logic. Both memory models below
are cocotb/Python testbench components, not RTL RAMs.

The v0.3 datapath keeps the v0.1 single-cycle structure. The decoder selects
XOR, unsigned comparison, register/immediate shifts, and six branch types;
subword memory, jumps, and pipeline registers remain outside this checkpoint.

```mermaid
flowchart LR
    IM["External Python instruction memory"]
    DM["External Python data memory"]
    subgraph CORE["rv32i_core"]
        PC["PC register and next-PC selection"]
        DEC["decoder"]
        RF["register_file: 2 reads, 1 clocked write"]
        IMM["I/S/B immediate_generator"]
        BMUX["ALU operand-B MUX"]
        ALU["alu"]
        WB["writeback MUX"]
        CMP["equality, signed/unsigned compare, branch selection"]
        TARGET["current_pc + imm"]
    end
    PC -->|current_pc| IM
    IM -->|instr fields| DEC
    IM -->|rs1 / rs2 / rd addresses| RF
    IM -->|instr| IMM
    DEC -->|imm_type| IMM
    DEC -->|alu_src| BMUX
    DEC -->|alu_op| ALU
    DEC -->|result_src| WB
    DEC -->|register write, gated by reset| RF
    DEC -->|branch + branch_type| CMP
    DEC -->|memory write, gated by reset| DM
    RF -->|rs1_data| ALU
    RF -->|rs2_data| BMUX
    IMM -->|imm| BMUX
    BMUX -->|alu_b| ALU
    RF -->|rs1_data and rs2_data| CMP
    RF -->|data_write_data| DM
    ALU -->|data_addr| DM
    ALU -->|alu_result| WB
    DM -->|data_read_data| WB
    WB -->|rd_data at rising edge| RF
    PC -->|current_pc| TARGET
    IMM -->|imm| TARGET
    TARGET -->|target_pc| PC
    CMP -->|take_target| PC
```

PC's sequential alternative is `current_pc + 4`; reset overrides both choices
and sets PC to 0 at a rising edge. The register file has no reset. The diagram
omits the shared clock wiring and individual reset-gating gates for readability.

## Instruction-to-state sequence

1. The testbench reads `current_pc` and supplies the instruction word.
2. Instruction fields select register addresses and decoder controls. The
   immediate generator assembles the selected I/S/B immediate.
3. Register reads and operand selection settle combinationally. The ALU computes
   arithmetic/logical results or the LW/SW address.
4. For LW the environment supplies `data_read_data` before the rising edge.
   The writeback MUX selects that data; otherwise it selects the ALU result.
5. At the rising edge, enabled register writes and the PC update commit. The
   testbench applies an enabled SW using the transaction sampled for that edge.

This is an event sequence through one single-cycle datapath, not pipeline stages.

## Branch path

The core computes equality, signed less-than, and unsigned less-than directly.
`branch_type` selects BEQ, BNE, BLT, BGE, BLTU, or BGEU, with inverse
selection for the greater-or-equal forms. Although the decoder selects ALU SUB
for branches, the branch decision does not consume an ALU zero flag. The target
adder uses the **current branch PC** plus the B immediate. No supported branch
enables register-file or external data-memory writes.
