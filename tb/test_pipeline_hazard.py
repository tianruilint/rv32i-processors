import cocotb
from cocotb.triggers import Timer


def clear(dut):
    for name in ("id_valid", "id_rs1_addr", "id_rs2_addr", "id_uses_rs1",
                 "id_uses_rs2", "ex_valid", "ex_reg_write", "ex_result_src",
                 "ex_rd_addr", "redirect"):
        getattr(dut, name).value = 0


@cocotb.test()
async def test_load_use_and_false_matches(dut):
    clear(dut)
    dut.id_valid.value = 1
    dut.ex_valid.value = 1
    dut.ex_reg_write.value = 1
    dut.ex_result_src.value = 1
    dut.ex_rd_addr.value = 3
    dut.id_rs1_addr.value = 3
    dut.id_uses_rs1.value = 1
    await Timer(1, unit="ns")
    assert (int(dut.stall.value), int(dut.bubble.value), int(dut.flush.value)) == (1, 1, 0)

    dut.id_uses_rs1.value = 0
    await Timer(1, unit="ns")
    assert int(dut.stall.value) == 0

    dut.id_rs2_addr.value = 3
    dut.id_uses_rs2.value = 1
    await Timer(1, unit="ns")
    assert int(dut.stall.value) == 1

    dut.ex_rd_addr.value = 0
    dut.id_rs2_addr.value = 0
    await Timer(1, unit="ns")
    assert int(dut.stall.value) == 0

    dut.ex_rd_addr.value = 3
    dut.ex_result_src.value = 0
    await Timer(1, unit="ns")
    assert int(dut.stall.value) == 0


@cocotb.test()
async def test_redirect_wins(dut):
    clear(dut)
    dut.id_valid.value = 1
    dut.id_uses_rs1.value = 1
    dut.id_rs1_addr.value = 5
    dut.ex_valid.value = 1
    dut.ex_reg_write.value = 1
    dut.ex_result_src.value = 1
    dut.ex_rd_addr.value = 5
    dut.redirect.value = 1
    await Timer(1, unit="ns")
    assert (int(dut.stall.value), int(dut.bubble.value), int(dut.flush.value)) == (0, 0, 1)
