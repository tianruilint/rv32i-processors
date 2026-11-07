# Debugging Notes

## Simulator address used as a dictionary key

- **Symptom:** `test_program2` raised
  `TypeError: unhashable type: 'LogicArray'` during memory access.
- **Root cause:** a simulator value was used directly as a Python dictionary
  key; it had not been converted to an integer byte address.
- **Fix:** use `int(dut.data_addr.value)`, drive load data before the clock
  edge, and apply stores using captured address/data/enable signals.
- **Verification:** the program tests check final register values and the
  stored/read word; subword tests additionally check byte-strobe preservation.

## Shift-immediate encoding qualification

- **Symptom:** the decoder activated an unsupported SLLI-shaped encoding.
- **Root cause:** instruction bits [31:25] were treated as ordinary I-type
  immediate data, including for shift-immediate instructions.
- **Fix:** require `0000000` for SLLI/SRLI and `0100000` for SRAI, while
  retaining all twelve immediate bits for ordinary I-type arithmetic.
- **Verification:** `tb/test_decoder.py::test_decoder` contains legal and
  illegal shift-immediate vectors and checks the safe inactive defaults.

## Independent test initialization

- **Symptom:** selecting `test_subword_lane_boundaries` led to premature
  simulation termination and zero-time follow-on failures.
- **Root cause:** the case depended on another test to initialize its clock,
  reset, and address registers.
- **Fix:** establish clock, reset, inputs, and register preconditions within
  the case itself.
- **Verification:** `tb/test_lw_sw.py::test_subword_lane_boundaries` checks
  all four byte lanes, both aligned halfword lanes, and load selection.

## Jump decode and datapath integration

- **Symptom:** intermediate jump integration selected the wrong immediate
  for JALR, omitted its funct3 qualification, and had ambiguous writeback cases.
- **Root cause:** decoder fields and the expanded operand/writeback choices
  were not consistently connected across the datapath.
- **Fix:** use I-type immediates and `funct3=000` for JALR; select ALU,
  load, U immediate, and PC+4 in distinct writeback cases; select PC for AUIPC
  through `alu_a_pc`; provide combinational defaults.
- **Verification:** immediate-generator and decoder vectors check encodings;
  `test_upper_immediate_instrs`, `test_jal_jalr_control_flow`, and
  `test_jal_negative_offset` check results, link values, targets, and
  skipped-write suppression.

## Terminal PC included in an execution trace

- **Symptom:** the recorded PC trace included a terminal sentinel that had
  never executed.
- **Root cause:** the test appended the current PC before checking completion.
- **Fix:** check the sentinel before appending it. Pipeline programs instead
  stop when the designated terminal instruction retires.
- **Verification:** `test_jal_jalr_control_flow` checks the exact executed-PC
  sequence, and pipeline program tests compare retirement traces and counters.

## Flush fanout limiting the clock

- **Symptom:** the OpenROAD clock sweep closed at 1.6 ns but failed at 1.4 ns
  by 6 ps; the worst endpoints were ID/EX fields such as `alu_op` and `imm`
  that have no logical link to the branch decision driving the path.
- **Root cause:** an EX redirect, used as `flush`, synchronously cleared every
  ID/EX field (~200 flops), so the forwarding → branch-compare path fanned out
  to all of them. Separately, reset-gating the store data in `pipeline_mem.sv`
  made a combinational `reset` input → `data_write_data` output path.
- **Fix:** flush/bubble clear only valid, `reg_write`, `mem_write`, `branch`
  and `jump_type`; the payload is cleared only on reset. A redirect only
  invalidates IF/ID. Reset gates `data_write_en`, not the data or strobe.
- **Verification:** `test_pipeline_id_ex` checks all five controls on flush,
  bubble and reset; the 74 default and 6 reference cases pass; the full sweep
  was rerun with LEC equivalent at every clock, and 1.4 ns now closes
  (see [pnr/README.md](../pnr/README.md#first-sweep-and-rtl-fix)).

## Upper PC bits never exercised

- **Symptom:** toggle coverage showed the upper ~21 bits of every PC, PC+4
  and redirect signal never changed.
- **Root cause:** all test programs, including the generated ones, live below
  address 0x800, so a fault in the upper PC+4 carry chain could not be seen.
- **Fix:** add `high_address_pc` to `tb/test_isa_reference.py`, which crosses
  the 0x7FFFFFFC → 0x80000000 carry, branches at 0xFFFFFFF4 and wraps a JAL
  link value at 0xFFFFFFFC to zero.
- **Verification:** both cores match the reference model on every retirement;
  merged toggle coverage rose from 82.4% to 97.5%.
