# Run from the repository root after generating the Nangate45-mapped netlist.
read_liberty build/timing/NangateOpenCellLibrary_typical.lib
read_verilog build/timing/rv32i_core_nangate45.v
link_design rv32i_core
read_sdc timing/constraints.sdc

report_units
if {![check_setup -verbose]} {
    puts stderr "ERROR: incomplete timing constraints"
    exit 2
}
puts "Constraint setup checks passed."

puts "=== WORST SETUP SLACK ==="
report_worst_slack -max -digits 3
puts "=== SETUP WNS AND TNS ==="
report_wns
report_tns
puts "=== FIVE WORST SETUP PATHS ==="
report_checks -path_delay max -group_count 5 -format summary -digits 3
puts "=== WORST PATH DETAIL ==="
report_checks -path_delay max -group_count 1 -fields {slew capacitance input_pin} -digits 3
puts "=== PATHS ENDING AT CORE REGISTERS ==="
report_checks -path_delay max -to [all_registers -data_pins] -group_count 5 -format summary -digits 3
puts "=== REGISTER TO REGISTER ==="
report_checks -path_delay max -from [all_registers -clock_pins] -to [all_registers -data_pins] -group_count 3 -format summary -digits 3
puts "=== LOAD INPUT TO CORE REGISTERS ==="
report_checks -path_delay max -from [get_ports {data_read_data*}] -to [all_registers -data_pins] -group_count 3 -format summary -digits 3
puts "=== DESIGN RULE VIOLATORS (MAX SLEW/CAPACITANCE/FANOUT) ==="
report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3
