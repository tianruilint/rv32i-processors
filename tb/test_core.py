import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_arithmetic_chain(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1;
    dut.instr.value = 0;
    dut.data_read_data.value = 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0;
    dut.instr.value = 0x00500093;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    assert actual_pc == 4;
    assert actual_x1 == 5;

    dut.instr.value = 0x00700113;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8;
    assert actual_x2 == 7;

    dut.instr.value = 0x002081B3;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x3 = int(dut.u_register_file.registers[3].value)
    assert actual_pc == 12;
    assert actual_x3 == 12;

    dut.instr.value = 0x40110233;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x4 = int(dut.u_register_file.registers[4].value)
    assert actual_pc == 16;
    assert actual_x4 == 2;

    dut.instr.value = 0x0020F2B3;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x5 = int(dut.u_register_file.registers[5].value)
    assert actual_pc == 20;
    assert actual_x5 == 5;

    dut.instr.value = 0x0020E333;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x6 = int(dut.u_register_file.registers[6].value)
    assert actual_pc == 24;
    assert actual_x6 == 7;

    dut.instr.value = 0x0020A3B3;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x7 = int(dut.u_register_file.registers[7].value)
    assert actual_pc == 28;
    assert actual_x7 == 1;

    dut.instr.value = 0xFFF00413;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x8 = int(dut.u_register_file.registers[8].value)
    assert actual_pc == 32;
    assert actual_x8 == 0xFFFFFFFF;

    dut.instr.value = 0x001424B3;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x9 = int(dut.u_register_file.registers[9].value)
    assert actual_pc == 36;
    assert actual_x9 == 1;

    dut.instr.value = 0x00617513;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x10 = int(dut.u_register_file.registers[10].value)
    assert actual_pc == 40;
    assert actual_x10 == 6;

    dut.instr.value = 0x0080E593;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x11 = int(dut.u_register_file.registers[11].value)
    assert actual_pc == 44;
    assert actual_x11 == 13;  

    dut.instr.value = 0x00042613;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x12 = int(dut.u_register_file.registers[12].value)
    assert actual_pc == 48;
    assert actual_x12 == 1;

    dut.instr.value = 0x06300013;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x0 = int(dut.rs1_data.value)
    assert actual_pc == 52;
    assert actual_x0 == 0;



@cocotb.test()
async def test_reset_blocks_register_write(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1;
    dut.instr.value = 0;
    dut.data_read_data.value = 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0;
    dut.instr.value = 0x00300693;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x13 = int(dut.u_register_file.registers[13].value)
    assert actual_pc == 4;
    assert actual_x13 == 3;

    dut.reset.value = 1;
    dut.instr.value = 0x00900693;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x13 = int(dut.u_register_file.registers[13].value)
    assert actual_pc == 0;
    assert actual_x13 == 3;
