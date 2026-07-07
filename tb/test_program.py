import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer



@cocotb.test()
async def test_program(dut):

    imem = {
        0: 0x00500093,
        4: 0x00700113,
        8: 0x002081B3,
    }

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0

    for _ in range(3):
        pc = int(dut.current_pc.value)

        instr = imem[pc]

        dut.instr.value = instr

        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

    actual_x3 = int(dut.u_register_file.registers[3].value)
    actual_pc = int(dut.current_pc.value)
    assert actual_x3 == 12
    assert actual_pc == 12


@cocotb.test()
async def test_program2(dut):

    imem = {
        0: 0x00000093,
        4: 0x00000113,
        8: 0x00008863,
        12:0x00110133,
        16:0xFFF08093,
        20:0xFE000AE3,
        24:0x04202023,
        28:0x04002183,
    }

    memory = {}

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0

    for _ in range(40):

        pc = int(dut.current_pc.value)

        if pc == 32:
            break

        instr = imem[pc]

        dut.instr.value = instr
        await Timer(1, unit="ns")
        actual_data_addr = int(dut.data_addr.value)

        is_lw = (instr & 0x7F) == 0x03

        if (is_lw):
            dut.data_read_data.value = memory[actual_data_addr]
        else:
            dut.data_read_data.value = 0

        actual_data_write_en = int(dut.data_write_en.value)
        actual_data_write_data = int(dut.data_write_data.value)

        await Timer(1, unit="ns")
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns") 

        if actual_data_write_en:
            memory[actual_data_addr] = actual_data_write_data
            
    
    actual_x1 = int(dut.u_register_file.registers[1].value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    actual_x3 = int(dut.u_register_file.registers[3].value)
    actual_pc = int(dut.current_pc.value)

    assert actual_x1 == 0
    assert actual_x2 == 0
    assert actual_x3 == 0
    assert memory[64] == 0
    assert actual_pc == 32