import hashlib
import json
import os
from pathlib import Path

import cocotb
from cocotb.triggers import Timer


def i(rd, rs1, imm, funct3=0, opcode=0x13):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def r(rd, rs1, rs2):
    return (rs2 << 20) | (rs1 << 15) | (rd << 7) | 0x33


def b(rs1, rs2, offset):
    value = offset & 0x1FFF
    return (((value >> 12) & 1) << 31) | (((value >> 5) & 63) << 25) | (rs2 << 20) | (rs1 << 15) | (1 << 12) | (((value >> 1) & 15) << 8) | (((value >> 11) & 1) << 7) | 0x63


def read_word(memory, address):
    base = address & ~3
    return sum(memory.get(base + lane, 0) << (8 * lane) for lane in range(4))


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


async def check_program(dut, name, words, trace, registers, memory=None, expected_stalls=0, expected_redirects=0):
    pipeline = hasattr(dut, "retire_valid")
    memory = dict(memory or {})
    original_memory = dict(memory)
    dut.clk.value = 0
    dut.reset.value = 1
    dut.instr.value = 0
    dut.data_read_data.value = 0
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")
    dut.clk.value = 0
    dut.reset.value = 0
    await Timer(1, unit="ns")

    retired = []
    stalls = 0
    redirects = 0
    cycles = 0
    terminal = trace[-1]
    for _ in range(len(trace) * 4 + 20):
        pc = int(dut.current_pc.value)
        if not pipeline:
            assert pc in words, f"unexpected fetch PC {pc:#x}"
        dut.instr.value = words.get(pc, i(0, 0, 0))
        await Timer(1, unit="ns")
        address = int(dut.data_addr.value)
        dut.data_read_data.value = read_word(memory, address)
        await Timer(1, unit="ns")
        assert int(dut.data_write_en.value) == 0, "benchmark has no store instructions"
        was_valid = int(dut.retire_valid.value) if pipeline else 1
        retired_pc = int(dut.retire_pc.value) if pipeline else pc
        if pipeline:
            stalls += int(dut.stall.value)
            redirects += int(dut.redirect.value)
        dut.clk.value = 1
        await Timer(1, unit="ns")
        cycles += 1
        if was_valid:
            retired.append(retired_pc)
        if was_valid and retired_pc == terminal:
            break
        dut.clk.value = 0
        await Timer(1, unit="ns")
    else:
        assert False, f"terminal PC {terminal:#x} did not retire"

    assert retired == trace
    assert memory == original_memory
    rf = dut.u_id.u_register_file if pipeline else dut.u_register_file
    for index, expected in registers.items():
        actual = 0 if index == 0 else int(rf.registers[index].value)
        assert actual == expected, f"x{index}: {actual:#x} != {expected:#x}"
    if pipeline:
        assert (stalls, redirects) == (expected_stalls, expected_redirects)
        assert int(dut.cycle_count.value) == cycles
        assert int(dut.retired_count.value) == len(trace)
        assert cycles == len(trace) + 4 + expected_stalls + 2 * expected_redirects
    else:
        assert cycles == len(trace)

    record = {
        "workload": name, "core": "pipeline" if pipeline else "single_cycle",
        "cycles": cycles, "retired": len(retired), "cpi": cycles / len(retired),
        "ipc": len(retired) / cycles, "stalls": stalls, "redirects": redirects,
        "program_sha256": sha(words), "retirement_trace_sha256": sha(retired),
        "checked_registers": registers, "no_store_checked_each_cycle": True,
        "memory_contract": "zero-wait aligned-word input",
        "measurement_window": "first active edge through terminal instruction commit; reset excluded",
    }
    destination = Path(os.environ["BENCHMARK_RESULTS_DIR"])
    destination.mkdir(parents=True, exist_ok=True)
    (destination / f"{record['core']}_{name}.json").write_text(json.dumps(record, indent=2))
    dut._log.info("BENCHMARK %s", json.dumps(record))


@cocotb.test()
async def test_long_independent(dut):
    words = {}
    expected = {0: 0}
    for index in range(511):
        rd = index % 30 + 1
        value = (index * 37) % 2000
        words[4 * index] = i(rd, 0, value)
        expected[rd] = value
    words[2044] = i(31, 0, 1)
    expected[31] = 1
    await check_program(dut, "independent_512", words, list(range(0, 2048, 4)), expected)


@cocotb.test()
async def test_long_dependent(dut):
    words = {0: i(1, 0, 0)}
    for index in range(1, 511):
        words[4 * index] = i(1, 1, 1)
    words[2044] = i(31, 0, 1)
    await check_program(dut, "dependent_512", words, list(range(0, 2048, 4)), {0: 0, 1: 510, 31: 1})


@cocotb.test()
async def test_long_branch_loop(dut):
    words = {0: i(1, 0, 256), 4: i(2, 0, 0), 8: r(2, 2, 1),
             12: i(1, 1, -1), 16: b(1, 0, -8), 20: i(31, 0, 1)}
    trace = [0, 4] + [8, 12, 16] * 256 + [20]
    await check_program(dut, "branch_loop_256", words, trace,
                        {0: 0, 1: 0, 2: 32896, 31: 1}, expected_redirects=255)


@cocotb.test()
async def test_repeated_load_use(dut):
    words = {0: i(3, 0, 0x100), 4: i(2, 0, 0)}
    for index in range(128):
        words[8 + 8 * index] = i(1, 3, 0, 2, 0x03)
        words[12 + 8 * index] = r(2, 2, 1)
    terminal = 8 + 8 * 128
    words[terminal] = i(31, 0, 1)
    await check_program(dut, "load_use_128", words, list(range(0, terminal + 4, 4)),
                        {0: 0, 1: 7, 2: 896, 3: 0x100, 31: 1},
                        memory={0x100: 7}, expected_stalls=128)
