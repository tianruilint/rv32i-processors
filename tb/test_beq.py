import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_beq(dut):

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

    dut.instr.value = 0x00500113;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8;
    assert actual_x2 == 5;

    dut.instr.value = 0x00208463;
    await Timer(1, unit="ns")

    assert int(dut.rf_we.value) == 0;
    assert int(dut.data_write_en.value) == 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    assert actual_pc == 16;

    dut.instr.value = 0x00400193;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x3 = int(dut.u_register_file.registers[3].value)
    assert actual_pc == 20;
    assert actual_x3 == 4;

    dut.instr.value = 0x00308463;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    assert actual_pc == 24;

    dut.instr.value = 0xFE208AE3;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    assert actual_pc == 12;


@cocotb.test()
async def test_bne(dut):

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

    assert int(dut.current_pc.value) == 4;
    assert int(dut.u_register_file.registers[1].value) == 5;

    dut.instr.value = 0x00500113;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 8;
    assert int(dut.u_register_file.registers[2].value) == 5;

    dut.instr.value = 0x00209463;
    await Timer(1, unit="ns")

    assert int(dut.rf_we.value) == 0;
    assert int(dut.data_write_en.value) == 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 12;

    dut.instr.value = 0x00400193;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 16;
    assert int(dut.u_register_file.registers[3].value) == 4;

    dut.instr.value = 0x00309463;
    await Timer(1, unit="ns")

    assert int(dut.rf_we.value) == 0;
    assert int(dut.data_write_en.value) == 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 24;


@cocotb.test()
async def test_blt_bge(dut):

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1;
    dut.instr.value = 0;
    dut.data_read_data.value = 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0;

    dut.instr.value = 0xFFF00093;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.u_register_file.registers[1].value) == 0xFFFFFFFF;

    dut.instr.value = 0x00100113;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.u_register_file.registers[2].value) == 1;

    dut.instr.value = 0x0020C463;
    await Timer(1, unit="ns")
    assert int(dut.rf_we.value) == 0;
    assert int(dut.data_write_en.value) == 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.current_pc.value) == 16;

    dut.instr.value = 0x0020D463;
    await Timer(1, unit="ns")
    assert int(dut.rf_we.value) == 0;
    assert int(dut.data_write_en.value) == 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.current_pc.value) == 20;


@cocotb.test()
async def test_bltu_bgeu(dut):

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1;
    dut.instr.value = 0;
    dut.data_read_data.value = 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0;

    dut.instr.value = 0xFFF00093;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.u_register_file.registers[1].value) == 0xFFFFFFFF;

    dut.instr.value = 0x00100113;
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.u_register_file.registers[2].value) == 1;

    dut.instr.value = 0x0020E463;
    await Timer(1, unit="ns")
    assert int(dut.rf_we.value) == 0;
    assert int(dut.data_write_en.value) == 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.current_pc.value) == 12;

    dut.instr.value = 0x0020F463;
    await Timer(1, unit="ns")
    assert int(dut.rf_we.value) == 0;
    assert int(dut.data_write_en.value) == 0;

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.current_pc.value) == 20;
