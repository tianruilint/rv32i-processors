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



@cocotb.test()
async def test_xor_sltu_instrs(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0
    dut.instr.value = 0x00100093

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    assert actual_pc == 4
    assert actual_x1 == 1

    dut.instr.value = 0xFFF00113

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8
    assert actual_x2 == 0xFFFFFFFF

    dut.instr.value = 0x00114233

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x4 = int(dut.u_register_file.registers[4].value)
    assert actual_pc == 12
    assert actual_x4 == 0xFFFFFFFE

    dut.instr.value = 0xFFF0C293

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x5 = int(dut.u_register_file.registers[5].value)
    assert actual_pc == 16
    assert actual_x5 == 0xFFFFFFFE

    dut.instr.value = 0x00113333

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x6 = int(dut.u_register_file.registers[6].value)
    assert actual_pc == 20
    assert actual_x6 == 0

    dut.instr.value = 0x0020B3B3

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x7 = int(dut.u_register_file.registers[7].value)
    assert actual_pc == 24
    assert actual_x7 == 1

    dut.instr.value = 0xFFF0B413

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x8 = int(dut.u_register_file.registers[8].value)
    assert actual_pc == 28
    assert actual_x8 == 1

    dut.instr.value = 0xFFF13493

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x9 = int(dut.u_register_file.registers[9].value)
    actual_data_write_en = int(dut.data_write_en.value)
    assert actual_pc == 32
    assert actual_x9 == 0
    assert actual_data_write_en == 0


@cocotb.test()
async def test_shift_instrs(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0
    dut.instr.value = 0x00100093

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    assert actual_pc == 4
    assert actual_x1 == 1

    dut.instr.value = 0x01F09113

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8
    assert actual_x2 == 0x80000000

    dut.instr.value = 0x01F00193

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x3 = int(dut.u_register_file.registers[3].value)
    assert actual_pc == 12
    assert actual_x3 == 31

    dut.instr.value = 0x02000213

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x4 = int(dut.u_register_file.registers[4].value)
    assert actual_pc == 16
    assert actual_x4 == 32

    dut.instr.value = 0x003092B3

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x5 = int(dut.u_register_file.registers[5].value)
    assert actual_pc == 20
    assert actual_x5 == 0x80000000

    dut.instr.value = 0x01F09313

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x6 = int(dut.u_register_file.registers[6].value)
    assert actual_pc == 24
    assert actual_x6 == 0x80000000

    dut.instr.value = 0x003153B3

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x7 = int(dut.u_register_file.registers[7].value)
    assert actual_pc == 28
    assert actual_x7 == 1

    dut.instr.value = 0x01F15413

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x8 = int(dut.u_register_file.registers[8].value)
    assert actual_pc == 32
    assert actual_x8 == 1

    dut.instr.value = 0x403154B3

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x9 = int(dut.u_register_file.registers[9].value)
    assert actual_pc == 36
    assert actual_x9 == 0xFFFFFFFF

    dut.instr.value = 0x41F15513

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x10 = int(dut.u_register_file.registers[10].value)
    assert actual_pc == 40
    assert actual_x10 == 0xFFFFFFFF

    dut.instr.value = 0x004095B3

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x11 = int(dut.u_register_file.registers[11].value)
    assert actual_pc == 44
    assert actual_x11 == 1

    dut.instr.value = 0x00415633

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x12 = int(dut.u_register_file.registers[12].value)
    assert actual_pc == 48
    assert actual_x12 == 0x80000000

    dut.instr.value = 0x404156B3

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x13 = int(dut.u_register_file.registers[13].value)
    actual_data_write_en = int(dut.data_write_en.value)
    assert actual_pc == 52
    assert actual_x13 == 0x80000000
    assert actual_data_write_en == 0




@cocotb.test()
async def test_upper_immediate_instrs(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0
    dut.instr.value = 0xABCDE0B7

    await Timer(1, unit="ns")
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    assert actual_data_write_en == 0
    assert actual_data_write_strb == 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    assert actual_pc == 4
    assert actual_x1 == 0xABCDE000

    dut.instr.value = 0x12345117

    await Timer(1, unit="ns")
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    assert actual_data_write_en == 0
    assert actual_data_write_strb == 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8
    assert actual_x2 == 0x12345004


@cocotb.test()
async def test_jal_jalr_control_flow(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    imem = {
        0:  0x00000293,
        4:  0x00000313,
        8:  0x008000EF,
        12: 0x06300293,
        16: 0x02500113,
        20: 0x004101E7,
        24: 0x04200313,
        40: 0x12345237,
    }

    visited = []

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0

    for _ in range(16):
        actual_pc = int(dut.current_pc.value)

        if actual_pc == 44:
            break

        visited.append(actual_pc)

        dut.instr.value = imem[actual_pc]

        await Timer(1, unit="ns")
        actual_data_write_en = int(dut.data_write_en.value)
        assert actual_data_write_en == 0

        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    actual_x3 = int(dut.u_register_file.registers[3].value)
    actual_x4 = int(dut.u_register_file.registers[4].value)
    actual_x5 = int(dut.u_register_file.registers[5].value)
    actual_x6 = int(dut.u_register_file.registers[6].value)

    assert visited == [0, 4, 8, 16, 20, 40]
    assert actual_pc == 44
    assert actual_x1 == 12
    assert actual_x2 == 37
    assert actual_x3 == 24
    assert actual_x4 == 0x12345000
    assert actual_x5 == 0
    assert actual_x6 == 0

@cocotb.test()
async def test_jal_negative_offset(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0
    dut.instr.value = 0x00100093

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    assert actual_pc == 4
    assert actual_x1 == 1

    dut.instr.value = 0x00200113

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8
    assert actual_x2 == 2

    dut.instr.value = 0xFFDFF1EF

    await Timer(1, unit="ns")

    actual_rf_we = int(dut.rf_we.value)
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    assert actual_rf_we == 1
    assert actual_data_write_en == 0
    assert actual_data_write_strb == 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    actual_x3 = int(dut.u_register_file.registers[3].value)
    assert actual_pc == 4
    assert actual_x1 == 1
    assert actual_x2 == 2
    assert actual_x3 == 12
