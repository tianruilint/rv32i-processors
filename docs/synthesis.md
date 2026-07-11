# Single-cycle Synthesis Record

Top: `rv32i_core`. The six source files below are the hand-written core and its
five child modules; the full-adder exercise and Python memory models are not
part of this synthesized hierarchy.

## Tool and reproduction

Yosys: `0.33 (git sha1 2584903a060)`.
From the repository root in WSL:

```sh
mkdir -p reports/synthesis build/synthesis
yosys -Q -T -l reports/synthesis/day13-core.log -p '
  read_verilog -sv rtl/rv32i_core.sv rtl/pc.sv rtl/decoder.sv rtl/register_file.sv rtl/immediate_generator.sv rtl/alu.sv;
  synth -top rv32i_core;
  check -assert;
  stat;
  write_verilog -noattr build/synthesis/rv32i_core.v
'
```

There is currently no `make synth-core` target.

Flow: parse synthesizable SystemVerilog, elaborate hierarchy, lower processes,
optimize and map memory/logic, map to generic gates, check the resulting design,
print statistics, then emit a generated Verilog netlist.

The flow preserves the module hierarchy; it does not use `synth -flatten`.
