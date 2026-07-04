import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer



@cocotb.test()
async def test_lw_sw(dut):

    memory = {}

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1;
    dut.instr.value = 0;
    dut.data_read_data.value = 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0;
    dut.instr.value = 0x04000093;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    assert actual_pc == 4;
    assert actual_x1 == 64;

    dut.instr.value = 0x02A00113;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8;
    assert actual_x2 == 42;





    dut.instr.value = 0x0020A423;

    await Timer(1, unit="ns")

    actual_data_addr = int(dut.data_addr.value)
    actual_data_write_data = int(dut.data_write_data.value)
    actual_data_write_en = int(dut.data_write_en.value)
    assert actual_data_addr == 72;
    assert actual_data_write_data == 42;
    assert actual_data_write_en == 1;

    await RisingEdge(dut.clk)

    if actual_data_write_en:
        memory[actual_data_addr] = actual_data_write_data;

    actual_memory = memory[72];
    assert actual_memory == 42;


    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    assert actual_pc == 12

    dut.instr.value = 0x0080A183;

    await Timer(1, unit="ns")

    actual_data_addr = int(dut.data_addr.value)
    actual_data_write_en = int(dut.data_write_en.value)
    dut.data_read_data.value = memory[actual_data_addr];

    await Timer(1, unit="ns")
    assert actual_data_write_en == 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_x3 = int(dut.u_register_file.registers[3].value)
    actual_pc = int(dut.current_pc.value)
    actual_data_write_en = int(dut.data_write_en.value)
    assert actual_x3 == 42;
    assert actual_pc == 16;