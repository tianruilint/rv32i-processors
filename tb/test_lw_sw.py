import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


def read_word(memory, address):
    base = address & ~0x3
    byte0 = memory[base + 0]
    byte1 = memory[base + 1]
    byte2 = memory[base + 2]
    byte3 = memory[base + 3]
    word = byte0 | (byte1 << 8) | (byte2 << 16) | (byte3 << 24)
    return word


def apply_write(memory, address, write_data, write_strb):
    base = address & ~0x3
    for lane in range(4):
        if write_strb & (1 << lane):
            byte = (write_data >> (8 * lane)) & 0xFF
            memory[base + lane] = byte

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



@cocotb.test()
async def test_subword_load_store(dut):

    memory = {
        0x40: 0x11,
        0x41: 0x22,
        0x42: 0x33,
        0x43: 0x44,
    }

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0

    dut.instr.value = 0x04000093
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    assert actual_pc == 4
    assert actual_x1 == 0x40

    dut.instr.value = 0xF8000113
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8
    assert actual_x2 == 0xFFFFFF80

    dut.instr.value = 0x002080A3
    await Timer(1, unit="ns")
    actual_data_addr = int(dut.data_addr.value)
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    actual_data_write_data = int(dut.data_write_data.value)
    assert actual_data_addr == 0x41
    assert actual_data_write_en == 1
    assert actual_data_write_strb == 0b0010
    assert actual_data_write_data == 0x00008000

    await RisingEdge(dut.clk)
    if actual_data_write_en:
        apply_write(memory, actual_data_addr, actual_data_write_data, actual_data_write_strb)
    await Timer(1, unit="ns")

    assert memory[0x40] == 0x11
    assert memory[0x41] == 0x80
    assert memory[0x42] == 0x33
    assert memory[0x43] == 0x44

    actual_pc = int(dut.current_pc.value)
    assert actual_pc == 12

    dut.instr.value = 0x00108183
    await Timer(1, unit="ns")
    actual_data_addr = int(dut.data_addr.value)
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    assert actual_data_write_en == 0
    assert actual_data_write_strb == 0b0000
    dut.data_read_data.value = read_word(memory, actual_data_addr)
    await Timer(1, unit="ns")
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    actual_x3 = int(dut.u_register_file.registers[3].value)
    assert actual_pc == 16
    assert actual_x3 == 0xFFFFFF80

    dut.instr.value = 0x0010C203
    await Timer(1, unit="ns")
    actual_data_addr = int(dut.data_addr.value)
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    assert actual_data_write_en == 0
    assert actual_data_write_strb == 0b0000
    dut.data_read_data.value = read_word(memory, actual_data_addr)
    await Timer(1, unit="ns")
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    actual_x4 = int(dut.u_register_file.registers[4].value)
    assert actual_pc == 20
    assert actual_x4 == 0x00000080

    dut.instr.value = 0x00209123
    await Timer(1, unit="ns")
    actual_data_addr = int(dut.data_addr.value)
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    actual_data_write_data = int(dut.data_write_data.value)
    assert actual_data_addr == 0x42
    assert actual_data_write_en == 1
    assert actual_data_write_strb == 0b1100
    assert actual_data_write_data == 0xFF800000

    await RisingEdge(dut.clk)
    if actual_data_write_en:
        apply_write(memory, actual_data_addr, actual_data_write_data, actual_data_write_strb)
    await Timer(1, unit="ns")

    assert memory[0x40] == 0x11
    assert memory[0x41] == 0x80
    assert memory[0x42] == 0x80
    assert memory[0x43] == 0xFF

    actual_pc = int(dut.current_pc.value)
    assert actual_pc == 24

    dut.instr.value = 0x00209283
    await Timer(1, unit="ns")
    actual_data_addr = int(dut.data_addr.value)
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    assert actual_data_write_en == 0
    assert actual_data_write_strb == 0b0000
    dut.data_read_data.value = read_word(memory, actual_data_addr)
    await Timer(1, unit="ns")
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    actual_x5 = int(dut.u_register_file.registers[5].value)
    assert actual_pc == 28
    assert actual_x5 == 0xFFFFFF80

    dut.instr.value = 0x0020D303
    await Timer(1, unit="ns")
    actual_data_addr = int(dut.data_addr.value)
    actual_data_write_en = int(dut.data_write_en.value)
    actual_data_write_strb = int(dut.data_write_strb.value)
    assert actual_data_write_en == 0
    assert actual_data_write_strb == 0b0000
    dut.data_read_data.value = read_word(memory, actual_data_addr)
    await Timer(1, unit="ns")
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    actual_x6 = int(dut.u_register_file.registers[6].value)
    assert actual_pc == 32
    assert actual_x6 == 0x0000FF80


@cocotb.test()
async def test_subword_lane_boundaries(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0

    dut.instr.value = 0x04000093
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    actual_x1 = int(dut.u_register_file.registers[1].value)
    assert actual_pc == 4
    assert actual_x1 == 0x40

    dut.instr.value = 0xF8000113
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual_pc = int(dut.current_pc.value)
    actual_x2 = int(dut.u_register_file.registers[2].value)
    assert actual_pc == 8
    assert actual_x2 == 0xFFFFFF80

    store_cases = [
        (0x00208023, 0x40, 0x00000080, 0b0001),
        (0x00208123, 0x42, 0x00800000, 0b0100),
        (0x002081A3, 0x43, 0x80000000, 0b1000),
        (0x00209023, 0x40, 0x0000FF80, 0b0011),
    ]

    for instr, exp_addr, exp_data, exp_strb in store_cases:
        dut.instr.value = instr
        await Timer(1, unit="ns")
        actual_data_addr = int(dut.data_addr.value)
        actual_data_write_en = int(dut.data_write_en.value)
        actual_data_write_data = int(dut.data_write_data.value)
        actual_data_write_strb = int(dut.data_write_strb.value)
        assert actual_data_write_en == 1
        assert actual_data_addr == exp_addr
        assert actual_data_write_data == exp_data
        assert actual_data_write_strb == exp_strb
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

    actual_pc = int(dut.current_pc.value)
    assert actual_pc == 24

    memory = {
        0x40: 0x11,
        0x41: 0x80,
        0x42: 0x33,
        0x43: 0xFF,
    }

    load_cases = [
        (0x0000C383, 0x11, 7),
        (0x0020C383, 0x33, 7),
        (0x0030C383, 0xFF, 7),
        (0x00009403, 0xFFFF8011, 8),
        (0x0000D483, 0x00008011, 9),
    ]

    for instr, exp_value, rd in load_cases:
        dut.instr.value = instr
        await Timer(1, unit="ns")
        actual_data_addr = int(dut.data_addr.value)
        actual_data_write_en = int(dut.data_write_en.value)
        actual_data_write_strb = int(dut.data_write_strb.value)
        assert actual_data_write_en == 0
        assert actual_data_write_strb == 0b0000
        dut.data_read_data.value = read_word(memory, actual_data_addr)
        await Timer(1, unit="ns")
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        actual_value = int(dut.u_register_file.registers[rd].value)
        assert actual_value == exp_value

    actual_pc = int(dut.current_pc.value)
    assert actual_pc == 44