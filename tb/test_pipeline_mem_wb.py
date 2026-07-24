import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_capture_and_bubble(dut):
    dut.clk.value = 0
    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.in_pc.value = 0
    dut.in_alu_result.value = 0
    dut.in_load_data.value = 0
    dut.in_rd_addr.value = 0
    dut.in_result_src.value = 0
    dut.in_reg_write.value = 0
    dut.in_imm.value = 0
    dut.in_pc_plus_4.value = 0
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")
    assert int(dut.out_valid.value) == 0

    dut.clk.value = 0
    dut.reset.value = 0
    dut.in_valid.value = 1
    dut.in_pc.value = 0x20
    dut.in_alu_result.value = 0x40
    dut.in_load_data.value = 0xABCD
    dut.in_rd_addr.value = 7
    dut.in_result_src.value = 1
    dut.in_reg_write.value = 1
    dut.in_imm.value = 0x1000
    dut.in_pc_plus_4.value = 0x24
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")
    assert int(dut.out_valid.value) == 1
    assert int(dut.out_pc.value) == 0x20
    assert int(dut.out_load_data.value) == 0xABCD
    assert int(dut.out_rd_addr.value) == 7
    assert int(dut.out_reg_write.value) == 1

    dut.clk.value = 0
    dut.in_valid.value = 0
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")
    assert int(dut.out_valid.value) == 0
    assert int(dut.out_reg_write.value) == 0
