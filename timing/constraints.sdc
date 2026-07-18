# Educational core-only setup model, not a physical timing signoff.
# Nangate45 typical Liberty reports nanoseconds and femtofarads.
# This 10 ns target is an explicit analysis constraint, not a measured Fmax.
create_clock -name core_clk -period 10.0 [get_ports clk]
set_clock_uncertainty -setup 0.10 [get_clocks core_clk]

# The instruction and data memories are outside this RTL. These input delays
# are illustrative arrival budgets at the core pins, not measured memory delays.
set_input_delay -clock core_clk -max 0.50 [get_ports {instr* data_read_data* reset}]
set_input_delay -clock core_clk -min 0.00 [get_ports {instr* data_read_data* reset}]
set_input_transition 0.05 [get_ports {instr* data_read_data* reset}]

# Output requirements and loads are also illustrative external assumptions.
set_output_delay -clock core_clk -max 0.50 [get_ports {current_pc* data_addr* data_write_data* data_write_en data_write_strb*}]
set_output_delay -clock core_clk -min 0.00 [get_ports {current_pc* data_addr* data_write_data* data_write_en data_write_strb*}]
set_load 5.0 [get_ports {current_pc* data_addr* data_write_data* data_write_en data_write_strb*}]
