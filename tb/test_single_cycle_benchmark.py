import cocotb
from cocotb.triggers import Timer


def read_word(memory, address):
    base = address & ~3
    return sum(memory.get(base + lane, 0) << (8 * lane) for lane in range(4))


def apply_write(memory, address, data, strb):
    base = address & ~3
    for lane in range(4):
        if strb & (1 << lane):
            memory[base + lane] = (data >> (8 * lane)) & 0xFF


def encode_r(rd, rs1, rs2, funct3=0, funct7=0):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | 0x33


def encode_i(rd, rs1, imm, funct3=0, opcode=0x13):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def encode_s(rs2, rs1, imm, funct3):
    value = imm & 0xFFF
    return ((value >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | ((value & 31) << 7) | 0x23


def encode_u(rd, value):
    return (value & 0xFFFFF000) | (rd << 7) | 0x37


async def run_case(dut, words, end_pc):
    memory = {}
    dut.clk.value = 0
    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")
    dut.clk.value = 0
    dut.reset.value = 0

    cycles = 0
    for _ in range(100):
        pc = int(dut.current_pc.value)
        if pc == end_pc + 4:
            return memory, cycles
        assert pc in words
        dut.instr.value = words[pc]
        await Timer(1, unit="ns")
        address = int(dut.data_addr.value)
        dut.data_read_data.value = read_word(memory, address)
        await Timer(1, unit="ns")
        write_en = int(dut.data_write_en.value)
        write_data = int(dut.data_write_data.value)
        write_strb = int(dut.data_write_strb.value)
        dut.clk.value = 1
        await Timer(1, unit="ns")
        if write_en:
            apply_write(memory, address, write_data, write_strb)
        cycles += 1
        dut.clk.value = 0
        await Timer(1, unit="ns")
    assert False, "program did not reach terminal PC"


@cocotb.test()
async def test_alu_forwarding_benchmark(dut):
    words = {
        0: encode_i(1, 0, 5),
        4: encode_i(2, 0, 7),
        8: encode_r(3, 1, 2),
        12: encode_r(4, 3, 1, 0, 0x20),
        16: encode_i(5, 4, 3, 7),
        20: encode_u(6, 0x12345000),
        24: encode_r(7, 6, 1),
        28: encode_i(31, 0, 1),
    }
    memory, cycles = await run_case(dut, words, 28)
    assert [int(dut.u_register_file.registers[n].value) for n in (3, 4, 5, 6, 7)] == [12, 7, 3, 0x12345000, 0x12345005]
    assert cycles == 8 and memory == {}
    dut._log.info("BENCHMARK single_cycle alu_forwarding cycles=%d retired=%d cpi=%.4f", cycles, cycles, 1.0)


@cocotb.test()
async def test_memory_hazards_benchmark(dut):
    words = {
        0: encode_i(1, 0, 0x40),
        4: encode_i(2, 0, 0x7F),
        8: encode_s(2, 1, 0, 2),
        12: encode_i(3, 1, 0, 2, 0x03),
        16: encode_r(4, 3, 2),
        20: encode_s(4, 1, 1, 0),
        24: encode_i(5, 1, 1, 4, 0x03),
        28: encode_s(5, 1, 2, 0),
        32: encode_i(6, 1, 0, 1, 0x03),
        36: encode_i(31, 0, 1),
    }
    memory, cycles = await run_case(dut, words, 36)
    assert read_word(memory, 0x40) == 0x00FEFE7F
    assert [int(dut.u_register_file.registers[n].value) for n in (3, 4, 5, 6)] == [0x7F, 0xFE, 0xFE, 0xFFFFFE7F]
    assert cycles == 10
    dut._log.info("BENCHMARK single_cycle memory_hazards cycles=%d retired=%d cpi=%.4f", cycles, cycles, 1.0)


@cocotb.test()
async def test_loop_sum5_benchmark(dut):
    def r(rd, rs1, rs2):
        return (rs2 << 20) | (rs1 << 15) | (rd << 7) | 0x33

    def i(rd, rs1, imm, opcode=0x13, funct3=0):
        return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

    def s(rs2, rs1, imm):
        value = imm & 0xFFF
        return ((value >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (2 << 12) | ((value & 31) << 7) | 0x23

    def b(rs1, rs2, offset):
        value = offset & 0x1FFF
        return (((value >> 12) & 1) << 31) | (((value >> 5) & 63) << 25) | (rs2 << 20) | (rs1 << 15) | (1 << 12) | (((value >> 1) & 15) << 8) | (((value >> 11) & 1) << 7) | 0x63

    words = {
        0: i(1, 0, 5),
        4: i(2, 0, 0),
        8: r(2, 2, 1),
        12: i(1, 1, -1),
        16: b(1, 0, -8),
        20: i(3, 0, 0x40),
        24: s(2, 3, 0),
        28: i(4, 3, 0, 0x03, 2),
        32: r(5, 4, 2),
        36: i(31, 0, 1),
    }
    memory = {}
    dut.clk.value = 0
    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")
    dut.clk.value = 0
    dut.reset.value = 0

    cycles = 0
    for _ in range(60):
        pc = int(dut.current_pc.value)
        if pc == 40:
            break
        assert pc in words
        dut.instr.value = words[pc]
        await Timer(1, unit="ns")
        address = int(dut.data_addr.value)
        dut.data_read_data.value = read_word(memory, address)
        await Timer(1, unit="ns")
        write_en = int(dut.data_write_en.value)
        write_data = int(dut.data_write_data.value)
        write_strb = int(dut.data_write_strb.value)
        dut.clk.value = 1
        await Timer(1, unit="ns")
        if write_en:
            apply_write(memory, address, write_data, write_strb)
        cycles += 1
        dut.clk.value = 0
        await Timer(1, unit="ns")
    else:
        assert False, "program did not reach PC 40"

    rf = dut.u_register_file.registers
    assert [int(rf[n].value) for n in (1, 2, 4, 5)] == [0, 15, 15, 30]
    assert read_word(memory, 0x40) == 15
    assert cycles == 22
    dut._log.info("BENCHMARK single_cycle loop_sum5 cycles=%d retired=%d cpi=%.4f", cycles, cycles, 1.0)
