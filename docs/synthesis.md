# Synthesis and Timing

## Tools and inputs

| Input | Version or identity |
| --- | --- |
| RTL tops | `rv32i_core`, `rv32i_pipeline_core` |
| Lint | Verilator 5.050 |
| Synthesis | Yosys 0.33, revision `2584903a060` |
| STA | OpenSTA 2.6.0 |

The instruction and data memories are external to both synthesized cores.
No SRAM macro, placement, routing, or extracted wire parasitics are included.
EDA tools and the Nangate45 library are obtained from their upstream
distributions and retain their respective licenses. They are not bundled
with the project source.

## Lint and generic synthesis

```sh
make lint-core lint-pipeline
```

From the repository root:

```sh
mkdir -p build/synthesis
core_sources="rtl/rv32i_core.sv rtl/pc.sv rtl/decoder.sv rtl/register_file.sv rtl/immediate_generator.sv rtl/alu.sv"
pipeline_sources="rtl/rv32i_pipeline_core.sv rtl/pipeline_frontend.sv rtl/pipeline_id.sv rtl/pipeline_id_ex.sv rtl/pipeline_ex.sv rtl/pipeline_ex_mem.sv rtl/pipeline_hazard.sv rtl/pipeline_mem.sv rtl/pipeline_mem_wb.sv rtl/decoder.sv rtl/immediate_generator.sv rtl/register_file.sv rtl/alu.sv"
yosys -Q -T -l build/synthesis/core_generic.log -p "read_verilog -sv $core_sources; synth -top rv32i_core; check -assert; stat; write_verilog -noattr build/synthesis/rv32i_core.v"
yosys -Q -T -l build/synthesis/pipeline_generic.log -p "read_verilog -sv $pipeline_sources; synth -top rv32i_pipeline_core -flatten; check -assert; stat; write_verilog -noattr build/synthesis/rv32i_pipeline_core.v"
```

## Technology mapping

- Local input: `build/timing/NangateOpenCellLibrary_typical.lib`

After saving the library, run the following in the same shell as the source
lists above:

```sh
mkdir -p build/timing
liberty=build/timing/NangateOpenCellLibrary_typical.lib
sha256sum "$liberty"
yosys -Q -T -q -l build/timing/yosys_map.log -p "read_liberty -lib -ignore_miss_func $liberty; read_verilog -sv $core_sources; hierarchy -check -top rv32i_core; synth -top rv32i_core -flatten; dfflibmap -liberty $liberty; abc -liberty $liberty; clean; check -assert; stat -liberty $liberty; write_verilog -noattr -noexpr -nodec build/timing/rv32i_core_nangate45.v"
yosys -Q -T -q -l build/timing/pipeline_yosys_map.log -p "read_liberty -lib -ignore_miss_func $liberty; read_verilog -sv $pipeline_sources; hierarchy -check -top rv32i_pipeline_core; synth -top rv32i_pipeline_core -flatten; dfflibmap -liberty $liberty; abc -liberty $liberty; clean; check -assert; stat -liberty $liberty; write_verilog -noattr -noexpr -nodec build/timing/rv32i_pipeline_core_nangate45.v"
```

## STA constraints and reproduction

Both SDC files use the following assumptions:

| Constraint | Value |
| --- | --- |
| Clock period | 10.00 ns |
| Setup uncertainty | 0.10 ns |
| External input/output delay, max | 0.50 ns |
| External input/output delay, min | 0.00 ns |
| Input transition | 0.05 ns |
| Output load | 5 fF |
| Clock network | Ideal |
| Library corner | Nangate45 typical |

The pipeline SDC additionally constrains its retirement and counter output
ports. The input/output budgets are illustrative pin constraints; they are
not measured instruction- or data-memory access times.

For an OpenSTA installation available as `sta`:

```sh
sta -no_init -no_splash -exit timing/run_sta.tcl > build/timing/single_cycle_sta_10ns.txt 2>&1
sta -no_init -no_splash -exit timing/run_pipeline_sta.tcl > build/timing/pipeline_sta_10ns.txt 2>&1
```
