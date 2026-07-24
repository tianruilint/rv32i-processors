import cocotb
from cocotb.triggers import Timer


def clear(dut):
    for name in ("reset", "in_valid", "in_alu_result", "in_store_data",
                 "in_rd_addr", "in_result_src", "in_reg_write", "in_mem_write",
                 "in_funct3", "in_imm", "in_pc_plus_4", "data_read_data"):
        getattr(dut, name).value = 0


@cocotb.test()
async def test_load_lanes(dut):
    clear(dut)
    dut.in_valid.value = 1
    dut.in_result_src.value = 1
    dut.in_reg_write.value = 1
    dut.data_read_data.value = 0x80FF7F01
    for offset, funct3, expected in (
        (0, 0, 0x01), (1, 0, 0x7F), (2, 0, 0xFFFFFFFF),
        (3, 4, 0x80), (0, 1, 0x7F01), (2, 1, 0xFFFF80FF),
        (2, 5, 0x80FF), (0, 2, 0x80FF7F01),
    ):
        dut.in_alu_result.value = 0x40 + offset
        dut.in_funct3.value = funct3
        await Timer(1, unit="ns")
        assert int(dut.out_load_data.value) == expected
        assert int(dut.data_write_en.value) == 0

    dut.in_alu_result.value = 0x41
    dut.in_funct3.value = 1
    await Timer(1, unit="ns")
    assert int(dut.out_load_data.value) == 0


@cocotb.test()
async def test_store_lanes_and_reset(dut):
    clear(dut)
    dut.in_valid.value = 1
    dut.in_mem_write.value = 1
    dut.in_store_data.value = 0xAABBCCDD
    for offset, funct3, expected_data, expected_strb in (
        (0, 0, 0x000000DD, 1), (3, 0, 0xDD000000, 8),
        (0, 1, 0x0000CCDD, 3), (2, 1, 0xCCDD0000, 12),
        (0, 2, 0xAABBCCDD, 15), (1, 1, 0, 0), (2, 2, 0, 0),
    ):
        dut.in_alu_result.value = 0x40 + offset
        dut.in_funct3.value = funct3
        await Timer(1, unit="ns")
        assert int(dut.data_addr.value) == 0x40 + offset
        assert int(dut.data_write_data.value) == expected_data
        assert int(dut.data_write_strb.value) == expected_strb
        assert int(dut.data_write_en.value) == int(expected_strb != 0)

    dut.reset.value = 1
    await Timer(1, unit="ns")
    assert int(dut.data_write_en.value) == 0
    assert int(dut.data_write_strb.value) == 0


@cocotb.test()
async def test_invalid_has_no_side_effect(dut):
    clear(dut)
    dut.in_mem_write.value = 1
    dut.in_reg_write.value = 1
    dut.in_funct3.value = 2
    await Timer(1, unit="ns")
    assert int(dut.data_write_en.value) == 0
    assert int(dut.out_reg_write.value) == 0
