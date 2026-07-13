# v0.5 Single-cycle Datapath

The boxes inside the core are synthesizable logic. Both memory models below
are cocotb/Python testbench components, not RTL RAMs.

The v0.5 datapath keeps the v0.1 single-cycle structure. The decoder selects
XOR, unsigned comparison, register/immediate shifts, six branch types, and the
byte/halfword load/store group, plus LUI/AUIPC/JAL/JALR. Pipeline registers
remain outside this checkpoint.

```mermaid
flowchart LR
    IM["External Python instruction memory"]
    DM["External Python data memory"]
    subgraph CORE["rv32i_core"]
        PC["PC register and next-PC selection"]
        DEC["decoder"]
        RF["register_file: 2 reads, 1 clocked write"]
        IMM["I/S/B/U/J immediate_generator"]
        AMUX["ALU operand-A MUX: rs1 or current_pc"]
        BMUX["ALU operand-B MUX"]
        ALU["alu"]
        WB["writeback MUX: ALU, load, Uimm, or PC+4"]
        LANE["byte/halfword lane select and sign/zero extension"]
        CMP["equality, signed/unsigned compare, branch selection"]
        TARGET["current_pc + branch/J immediate"]
        LINK["current_pc + 4"]
        NEXT["branch/JAL/JALR target selection"]
    end
    PC -->|current_pc| IM
    IM -->|instr fields| DEC
    IM -->|rs1 / rs2 / rd addresses| RF
    IM -->|instr| IMM
    DEC -->|imm_type| IMM
    DEC -->|alu_a_pc| AMUX
    DEC -->|alu_src| BMUX
    DEC -->|alu_op| ALU
    DEC -->|result_src| WB
    DEC -->|register write, gated by reset| RF
    DEC -->|branch + branch_type| CMP
    DEC -->|memory write, gated by reset| DM
    RF -->|rs1_data| AMUX
    PC -->|current_pc| AMUX
    AMUX -->|alu_a| ALU
    RF -->|rs2_data| BMUX
    IMM -->|imm| BMUX
    BMUX -->|alu_b| ALU
    RF -->|rs1_data and rs2_data| CMP
    RF -->|lane-aligned data and strobe| DM
    ALU -->|data_addr| DM
    DEC -->|funct3| LANE
    ALU -->|data_addr and low bits| LANE
    ALU -->|alu_result| WB
    IMM -->|U immediate| WB
    PC -->|current_pc| LINK
    LINK -->|PC+4 link| WB
    DM -->|aligned data_read_data| LANE
    LANE -->|load_data| WB
    WB -->|rd_data at rising edge| RF
    PC -->|current_pc| TARGET
    IMM -->|imm| TARGET
    TARGET -->|branch/JAL target| NEXT
    ALU -->|JALR sum, bit 0 cleared| NEXT
    CMP -->|branch decision| NEXT
    DEC -->|jump_type| NEXT
    NEXT -->|take_target and target_pc| PC
```

PC's sequential alternative is `current_pc + 4`; reset overrides all choices
and sets PC to 0 at a rising edge. The register file has no reset. The diagram
omits the shared clock wiring and individual reset-gating gates for readability.

## Instruction-to-state sequence

1. The testbench reads `current_pc` and supplies the instruction word.
2. Instruction fields select register addresses and decoder controls. The
   immediate generator assembles the selected I/S/B/U/J immediate.
3. Register reads and operand selection settle combinationally. ALU operand A
   selects rs1 or current PC; operand B selects rs2 or the immediate. The ALU
   computes arithmetic/logical results or the memory effective byte address.
4. For a load, the environment aligns the effective address, assembles a
   little-endian 32-bit word, and supplies `data_read_data` before the rising
   edge. The lane selector chooses the byte/halfword and sign- or zero-extends
   it; LW uses the whole word.
5. For a store, the core places the payload in the selected byte lanes and
   asserts `data_write_strb`; the testbench applies only those lanes at the
   committing edge, preserving the others.
6. Writeback selects the ALU result, load data, U immediate, or `PC+4`. The
   next-PC path selects sequential, branch, JAL, or JALR behavior.
7. At the rising edge, enabled register writes and the PC update commit.

This is an event sequence through one single-cycle datapath, not pipeline stages.

## Branch path

The core computes equality, signed less-than, and unsigned less-than directly.
`branch_type` selects BEQ, BNE, BLT, BGE, BLTU, or BGEU, with inverse
selection for the greater-or-equal forms. Although the decoder selects ALU SUB
for branches, the branch decision does not consume an ALU zero flag. The target
adder uses the **current branch PC** plus the B immediate. No supported branch
enables register-file or external data-memory writes.

## Upper-immediate and jump path

LUI routes the U immediate directly to writeback. AUIPC selects current PC as
ALU operand A and the U immediate as operand B. JAL forms its target from the
current PC plus the signed J immediate; JALR forms an ALU sum from rs1 plus the
signed I immediate and clears target bit 0. Both jumps write `current_pc+4` to
rd. The directed jump program verifies that sequential instructions skipped by
JAL and JALR do not write their destination registers or memory.

The current external instruction-memory contract uses four-byte-aligned word
addresses. JALR bit 0 clearing is implemented, but no instruction-address-
misalignment exception exists if a target has bit 1 set.

## Subword memory path

`data_addr` is the full 32-bit ALU effective byte address. Its low two bits
select one of four byte lanes in the aligned external word. LB/LBU select one
byte and sign/zero-extend it; LH/LHU select lanes 0/1 or 2/3 and sign/zero-
extend them. SB emits one strobe and lane-aligned data; SH emits two adjacent
strobes; SW emits all four. The contract permits any byte address for byte
operations, even addresses for which a word access would be misaligned.

The core has no internal memory and no cross-word assembly/split path. A
halfword or word access that is misaligned under the documented limits is
unsupported and unverified, with no misalignment exception.
