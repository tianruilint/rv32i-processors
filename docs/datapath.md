# P1 Datapaths: single-cycle and five-stage pipeline

Source tops: `rtl/rv32i_core.sv` and `rtl/rv32i_pipeline_core.sv`.
Both use the shared decoder, register file, immediate generator, and ALU.
Instruction and data memories are external cocotb/Python components.

## v2.0 stage map

```mermaid
flowchart LR
    IF["IF: PC + external instruction word"] --> IFID["IF/ID"]
    IFID --> ID["ID: decoder + immediate + register-file reads"]
    ID --> IDEX["ID/EX"]
    IDEX --> EX["EX: forwarding + ALU + branch/jump target"]
    EX --> EXMEM["EX/MEM"]
    EXMEM --> MEM["MEM: external word + lane selection/store strobe"]
    MEM --> MEMWB["MEM/WB"]
    MEMWB --> WB["WB: result selection + register-file write"]
    EXMEM -. "ALU / LUI / PC+4 forward" .-> EX
    MEMWB -. "all WB results forward" .-> EX
    MEMWB -. "same-edge bypass" .-> ID
    IDEX -. "load-use detector" .-> IFID
    EX -. "taken redirect: PC update and two-slot flush" .-> IFID
```

Only MEM may write external data memory; only WB may write the register file.
An invalid slot cannot perform either write. The EX/MEM forwarding path is
disabled for loads because load data is captured at MEM/WB. If ID uses the rd
of a load in EX, the frontend and IF/ID hold while ID/EX becomes a bubble.
During the held cycle the load advances through MEM while EX contains the
bubble. At the following edge the load enters MEM/WB and the consumer enters
EX, where MEM/WB forwarding supplies the data. A taken EX branch or jump
invalidates both younger slots, then fetch resumes from the target PC.
Counters count non-reset cycles and valid WB retirements, not test cases or
static instruction kinds.

## RTL modules and stored state

| File/module | Role |
| --- | --- |
| `pipeline_frontend.sv` | PC and IF/ID registers; normal fetch, hold, and redirect |
| `pipeline_id.sv` | Combinational decode/read/bypass; contains the shared register-file instance |
| `pipeline_id_ex.sv` | ID/EX state, cleared for reset, bubble, or flush |
| `pipeline_ex.sv` | Combinational forwarding, ALU, branch comparison, and redirect |
| `pipeline_ex_mem.sv` | EX/MEM state; carries the raw forwarded store operand |
| `pipeline_hazard.sv` | Combinational load-use detection and stall/bubble/flush controls |
| `pipeline_mem.sv` | Combinational load extension and lane-aligned store interface |
| `pipeline_mem_wb.sv` | MEM/WB state, including retirement PC |
| `rv32i_pipeline_core.sv` | Wiring, WB selection, EX/MEM PC observation register, and counters |

The register-file instance sits inside the ID module, but its write port is
driven exclusively by WB. Physical module placement does not change the stage
that authorizes the write. EX/MEM and MEM/WB continue advancing during a
load-use stall; only PC/IF-ID hold, and ID/EX receives a bubble.

## v1.0 single-cycle map

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

## Why an array becomes flip-flops and MUXes

`register_file.sv` declares 32 words of 32 bits. The single-cycle hierarchical generic synthesis
reported 1024 enabled single-bit flip-flops and 1984 MUXes in this module.
Two independent read addresses require two data-selection networks. A binary
32-to-1 selection tree has 31 two-input MUXes per bit; `31 * 32 * 2 = 1984`
matches this run. This is an explanation of the observed structure, not a
guarantee that every synthesis configuration will produce identical cells.

No memory objects remained after mapping; storage did not disappear. No SRAM
macro was selected. Architectural x0 behavior is implemented by the RTL's
read bypass/write protection; do not infer that synthesis must remove exactly
32 storage cells for x0.

## Timing and performance boundary

Register-file reads are combinational; writes occur on clock edges. A complete
single-cycle load path includes register read, address calculation, external
memory, and writeback. Core-only STA omits the memory delay and therefore
cannot measure that complete path.

Pipelining separates combinational work with registers and adds forwarding
and control logic. It can shorten a required clock period, while stalls,
flushes, and fill increase finite-program cycle counts. Actual execution time
depends on both quantities. The measured cycles/CPI are in
[verification.md](verification.md); the pre-layout STA results and unresolved
electrical constraints are in [synthesis.md](synthesis.md).
