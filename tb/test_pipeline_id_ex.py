import cocotb
from cocotb.triggers import Timer


INPUTS = (
    "valid", "pc", "pc_plus_4", "rs1_addr", "rs2_addr", "rd_addr",
    "rs1_data", "rs2_data", "imm", "funct3", "alu_op", "alu_src",
    "alu_a_pc", "result_src", "reg_write", "mem_write", "branch",
    "branch_type", "jump_type", "uses_rs1", "uses_rs2",
)


async def edge(dut):
    dut.clk.value = 0
    await Timer(1, unit="ns")
    dut.clk.value = 1
    await Timer(1, unit="ns")


@cocotb.test()
async def test_capture_flush_bubble_reset(dut):
    dut.clk.value = 0
    dut.reset.value = 1
    dut.flush.value = 0
    dut.bubble.value = 0
    for name in INPUTS:
        getattr(dut, "in_" + name).value = 0
    await edge(dut)
    assert int(dut.out_valid.value) == 0

    dut.reset.value = 0
    dut.in_valid.value = 1
    dut.in_pc.value = 0x10
    dut.in_pc_plus_4.value = 0x14
    dut.in_rs1_addr.value = 2
    dut.in_rd_addr.value = 3
    dut.in_imm.value = 0xFFFFF000
    dut.in_reg_write.value = 1
    dut.in_result_src.value = 2
    await edge(dut)
    for name in INPUTS:
        assert int(getattr(dut, "out_" + name).value) == int(getattr(dut, "in_" + name).value)

    dut.flush.value = 1
    await edge(dut)
    assert int(dut.out_valid.value) == 0
    assert int(dut.out_reg_write.value) == 0
    dut.flush.value = 0

    await edge(dut)
    dut.bubble.value = 1
    await edge(dut)
    assert int(dut.out_valid.value) == 0
    assert int(dut.out_reg_write.value) == 0
    dut.bubble.value = 0

    await edge(dut)
    dut.reset.value = 1
    await edge(dut)
    assert int(dut.out_valid.value) == 0
    assert int(dut.out_reg_write.value) == 0
