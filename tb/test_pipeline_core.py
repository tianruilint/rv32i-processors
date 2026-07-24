import cocotb
from cocotb.triggers import Timer


def r(rd, rs1, rs2, funct3, funct7=0):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | 0x33


def i(rd, rs1, imm, funct3=0, opcode=0x13):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def s(rs2, rs1, imm, funct3):
    value = imm & 0xFFF
    return ((value >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | ((value & 31) << 7) | 0x23


def b(rs1, rs2, offset, funct3):
    value = offset & 0x1FFF
    return (((value >> 12) & 1) << 31) | (((value >> 5) & 63) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (((value >> 1) & 15) << 8) | (((value >> 11) & 1) << 7) | 0x63


def u(rd, value, opcode=0x37):
    return (value & 0xFFFFF000) | (rd << 7) | opcode


def j(rd, offset):
    value = offset & 0x1FFFFF
    return (((value >> 20) & 1) << 31) | (((value >> 1) & 0x3FF) << 21) | (((value >> 11) & 1) << 20) | (((value >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F


def read_word(memory, address):
    base = address & ~3
    return sum(memory.get(base + lane, 0) << (8 * lane) for lane in range(4))


def apply_write(memory, address, data, strb):
    base = address & ~3
    for lane in range(4):
        if strb & (1 << lane):
            memory[base + lane] = (data >> (8 * lane)) & 0xFF


def reg(dut, index):
    if index == 0:
        return 0
    return int(dut.u_id.u_register_file.registers[index].value)


async def run_program(dut, words, end_pc, memory=None, max_cycles=120):
    if memory is None:
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

    retired = []
    stalls = 0
    redirects = 0
    for _ in range(max_cycles):
        pc = int(dut.current_pc.value)
        dut.instr.value = words.get(pc, i(0, 0, 0))
        await Timer(1, unit="ns")
        address = int(dut.data_addr.value)
        dut.data_read_data.value = read_word(memory, address)
        await Timer(1, unit="ns")

        write_en = int(dut.data_write_en.value)
        write_data = int(dut.data_write_data.value)
        write_strb = int(dut.data_write_strb.value)
        was_valid = int(dut.retire_valid.value)
        retired_pc = int(dut.retire_pc.value)
        stalls += int(dut.stall.value)
        redirects += int(dut.redirect.value)
        dut.clk.value = 1
        await Timer(1, unit="ns")
        if write_en:
            apply_write(memory, address, write_data, write_strb)
        if was_valid:
            retired.append(retired_pc)
        if was_valid and retired_pc == end_pc:
            assert int(dut.retired_count.value) == len(retired)
            return memory, retired, int(dut.cycle_count.value), stalls, redirects
        dut.clk.value = 0
        await Timer(1, unit="ns")
    assert False, f"terminal PC {end_pc} did not retire; trace={retired}"


@cocotb.test()
async def test_forwarding_and_pc4(dut):
    words = {
        0: i(1, 0, 5),
        4: i(2, 0, 7),
        8: r(3, 1, 2, 0),
        12: r(4, 3, 1, 0, 0x20),
        16: i(5, 4, 3, 7),
        20: u(6, 0x12345000),
        24: r(7, 6, 1, 0),
        28: i(31, 0, 1),
    }
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, 28)
    assert retired == list(range(0, 32, 4))
    assert [reg(dut, n) for n in (1, 2, 3, 4, 5)] == [5, 7, 12, 7, 3]
    assert reg(dut, 6) == 0x12345000
    assert reg(dut, 7) == 0x12345005
    assert (cycles, stalls, redirects) == (12, 0, 0)
    assert memory == {}
    dut._log.info("BENCHMARK pipeline alu_forwarding cycles=%d retired=%d cpi=%.4f", cycles, len(retired), cycles / len(retired))


@cocotb.test()
async def test_load_store_and_subword_hazards(dut):
    words = {
        0: i(1, 0, 0x40),
        4: i(2, 0, 0x7F),
        8: s(2, 1, 0, 2),
        12: i(3, 1, 0, 2, 0x03),
        16: r(4, 3, 2, 0),
        20: s(4, 1, 1, 0),
        24: i(5, 1, 1, 4, 0x03),
        28: s(5, 1, 2, 0),
        32: i(6, 1, 0, 1, 0x03),
        36: i(31, 0, 1),
    }
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, 36)
    assert retired == list(range(0, 40, 4))
    assert read_word(memory, 0x40) == 0x00FEFE7F
    assert [reg(dut, n) for n in (3, 4, 5, 6)] == [0x7F, 0xFE, 0xFE, 0xFFFFFE7F]
    assert (cycles, stalls, redirects) == (16, 2, 0)
    dut._log.info("BENCHMARK pipeline memory_hazards cycles=%d retired=%d cpi=%.4f", cycles, len(retired), cycles / len(retired))


@cocotb.test()
async def test_taken_branch_flushes_store_and_register_write(dut):
    words = {
        0: i(3, 0, 0),
        4: i(1, 0, 0x40),
        8: i(2, 0, 1),
        12: b(2, 2, 12, 0),
        16: s(2, 1, 0, 2),
        20: i(3, 0, 9),
        24: i(4, 0, 7),
        28: i(31, 0, 1),
    }
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, 28)
    assert retired == [0, 4, 8, 12, 24, 28]
    assert reg(dut, 3) == 0 and reg(dut, 4) == 7
    assert read_word(memory, 0x40) == 0
    assert (cycles, stalls, redirects) == (12, 0, 1)


@cocotb.test()
async def test_jal_jalr_links_and_flush(dut):
    words = {
        0: i(1, 0, 25),
        4: j(2, 8),
        8: s(1, 0, 0x40, 2),
        12: i(3, 1, 0, 0, 0x67),
        16: s(1, 0, 0x44, 2),
        20: i(4, 0, 99),
        24: r(4, 2, 3, 0),
        28: i(31, 0, 1),
    }
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, 28)
    assert retired == [0, 4, 12, 24, 28]
    assert [reg(dut, n) for n in (2, 3, 4)] == [8, 16, 24]
    assert read_word(memory, 0x40) == 0
    assert read_word(memory, 0x44) == 0
    assert (cycles, stalls, redirects) == (13, 0, 2)


@cocotb.test()
async def test_loop_program_and_cpi(dut):
    words = {
        0: i(1, 0, 5),
        4: i(2, 0, 0),
        8: r(2, 2, 1, 0),
        12: i(1, 1, -1),
        16: b(1, 0, -8, 1),
        20: i(3, 0, 0x40),
        24: s(2, 3, 0, 2),
        28: i(4, 3, 0, 2, 0x03),
        32: r(5, 4, 2, 0),
        36: i(31, 0, 1),
    }
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, 36)
    assert [reg(dut, n) for n in (1, 2, 4, 5)] == [0, 15, 15, 30]
    assert read_word(memory, 0x40) == 15
    assert len(retired) == 22
    assert (cycles, stalls, redirects) == (35, 1, 4)
    assert retired.count(8) == 5 and retired.count(16) == 5
    dut._log.info("BENCHMARK pipeline loop_sum5 cycles=%d retired=%d cpi=%.4f", cycles, len(retired), cycles / len(retired))


@cocotb.test()
async def test_signed_unsigned_and_shifts(dut):
    words = {
        0: i(7, 0, 0),
        4: i(1, 0, -1),
        8: i(2, 0, 1),
        12: r(3, 1, 2, 2),
        16: r(4, 1, 2, 3),
        20: i(5, 1, 0x41F, 5),
        24: i(6, 1, 31, 5),
        28: b(1, 2, 8, 4),
        32: i(7, 0, 99),
        36: b(1, 2, 8, 7),
        40: i(7, 0, 88),
        44: i(8, 0, 9),
        48: i(31, 0, 1),
    }
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, 48)
    assert [reg(dut, n) for n in (3, 4, 5, 6, 7, 8)] == [1, 0, 0xFFFFFFFF, 1, 0, 9]
    assert 32 not in retired and 40 not in retired
    assert (stalls, redirects) == (0, 2)


@cocotb.test()
async def test_load_to_branch_stall_and_wrong_path_store(dut):
    words = {
        0: i(1, 0, 0x40),
        4: i(2, 0, 1),
        8: s(2, 1, 0, 2),
        12: i(3, 1, 0, 2, 0x03),
        16: b(3, 2, 12, 0),
        20: s(2, 1, 4, 2),
        24: i(4, 0, 99),
        28: i(5, 0, 8),
        32: i(31, 0, 1),
    }
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, 32)
    assert retired == [0, 4, 8, 12, 16, 28, 32]
    assert read_word(memory, 0x40) == 1
    assert read_word(memory, 0x44) == 0
    assert reg(dut, 5) == 8
    assert (cycles, stalls, redirects) == (14, 1, 1)


@cocotb.test()
async def test_reset_clears_inflight_store(dut):
    dut.clk.value = 0
    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0xDEADBEEF
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")
    dut.clk.value = 0
    dut.reset.value = 0

    for _ in range(3):
        dut.instr.value = s(0, 0, 0, 2) if int(dut.current_pc.value) == 0 else i(0, 0, 0)
        await Timer(1, unit="ns")
        dut.clk.value = 1
        await Timer(1, unit="ns")
        dut.clk.value = 0

    assert int(dut.data_write_en.value) == 1
    dut.reset.value = 1
    await Timer(1, unit="ns")
    assert int(dut.data_write_en.value) == 0
    dut.clk.value = 1
    await Timer(1, unit="ns")
    assert int(dut.current_pc.value) == 0
    assert int(dut.retire_valid.value) == 0
    assert int(dut.cycle_count.value) == 0
    assert int(dut.retired_count.value) == 0


@cocotb.test()
async def test_subword_sign_extension_and_half_store(dut):
    words = {
        0: i(1, 0, 0x40),
        4: u(2, 0x8000),
        8: i(2, 2, 1),
        12: s(2, 1, 2, 1),
        16: i(3, 1, 2, 1, 0x03),
        20: i(4, 1, 2, 5, 0x03),
        24: i(5, 1, 3, 0, 0x03),
        28: i(6, 1, 3, 4, 0x03),
        32: s(2, 1, 0, 0),
        36: i(7, 1, 0, 2, 0x03),
        40: i(0, 0, 99),
        44: i(8, 0, 1),
        48: i(31, 0, 1),
    }
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, 48)
    assert read_word(memory, 0x40) == 0x80010001
    assert [reg(dut, n) for n in (3, 4, 5, 6, 7, 8)] == [0xFFFF8001, 0x8001, 0xFFFFFF80, 0x80, 0x80010001, 1]
    assert retired == list(range(0, 52, 4))
    assert (cycles, stalls, redirects) == (17, 0, 0)


@cocotb.test()
async def test_remaining_alu_and_branch_types(dut):
    program = [
        i(19, 0, 0),
        i(1, 0, -1),
        i(2, 0, 1),
        i(3, 0, 31),
        r(4, 1, 2, 7),
        r(5, 1, 2, 6),
        r(6, 1, 2, 4),
        r(7, 2, 3, 1),
        r(8, 1, 3, 5),
        r(9, 1, 3, 5, 0x20),
        r(10, 2, 1, 0, 0x20),
        i(11, 1, 0xF, 7),
        i(12, 2, 0x10, 6),
        i(13, 2, 0xF, 4),
        i(14, 1, 0, 2),
        i(15, 1, 1, 3),
        i(16, 2, 31, 1),
        i(17, 1, 31, 5),
        i(18, 1, 0x41F, 5),
        b(2, 1, 8, 5),
        i(19, 0, 9),
        b(2, 1, 8, 6),
        i(19, 0, 8),
        u(20, 0x1000, 0x17),
        i(31, 0, 1),
    ]
    words = {4 * index: word for index, word in enumerate(program)}
    end_pc = 4 * (len(program) - 1)
    memory, retired, cycles, stalls, redirects = await run_program(dut, words, end_pc)
    expected = {
        4: 1, 5: 0xFFFFFFFF, 6: 0xFFFFFFFE, 7: 0x80000000,
        8: 1, 9: 0xFFFFFFFF, 10: 2, 11: 15, 12: 17,
        13: 14, 14: 1, 15: 0, 16: 0x80000000, 17: 1,
        18: 0xFFFFFFFF, 19: 0, 20: 0x1000 + 4 * (len(program) - 2),
    }
    for index, value in expected.items():
        assert reg(dut, index) == value, f"x{index}: {reg(dut, index):08x} != {value:08x}"
    assert 80 not in retired and 88 not in retired
    assert (cycles, stalls, redirects) == (len(retired) + 8, 0, 2)
