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
