import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.in_valid.value = 0
    dut.in_alu_result.value = 0
    dut.in_store_data.value = 0
    dut.in_rd_addr.value = 0
    dut.in_result_src.value = 0
    dut.in_reg_write.value = 0
    dut.in_mem_write.value = 0
    dut.in_funct3.value = 0
    dut.in_imm.value = 0
    dut.in_pc_plus_4.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.reset.value = 0


def assert_outputs_zero(dut):
    assert int(dut.out_valid.value) == 0
    assert int(dut.out_alu_result.value) == 0
    assert int(dut.out_store_data.value) == 0
    assert int(dut.out_rd_addr.value) == 0
    assert int(dut.out_result_src.value) == 0
    assert int(dut.out_reg_write.value) == 0
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_funct3.value) == 0
    assert int(dut.out_imm.value) == 0
    assert int(dut.out_pc_plus_4.value) == 0


@cocotb.test()
async def test_reset(dut):
    await setup(dut)

    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert_outputs_zero(dut)

    dut.reset.value = 0


@cocotb.test()
async def test_capture_valid(dut):
    await setup(dut)

    dut.in_valid.value = 1
    dut.in_alu_result.value = 0xDEADBEEF
    dut.in_store_data.value = 0x12345678
    dut.in_rd_addr.value = 5
    dut.in_result_src.value = 1
    dut.in_reg_write.value = 1
    dut.in_mem_write.value = 0
    dut.in_funct3.value = 2
    dut.in_imm.value = 0x00000010
    dut.in_pc_plus_4.value = 0x80000004

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_alu_result.value) == 0xDEADBEEF
    assert int(dut.out_store_data.value) == 0x12345678
    assert int(dut.out_rd_addr.value) == 5
    assert int(dut.out_result_src.value) == 1
    assert int(dut.out_reg_write.value) == 1
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_funct3.value) == 2
    assert int(dut.out_imm.value) == 0x10
    assert int(dut.out_pc_plus_4.value) == 0x80000004


@cocotb.test()
async def test_invalid_clears_output(dut):
    await setup(dut)

    dut.in_valid.value = 1
    dut.in_alu_result.value = 0xAAAAAAAA
    dut.in_store_data.value = 0xBBBBBBBB
    dut.in_rd_addr.value = 7
    dut.in_result_src.value = 2
    dut.in_reg_write.value = 1
    dut.in_mem_write.value = 1
    dut.in_funct3.value = 1
    dut.in_imm.value = 0xCCCCCCCC
    dut.in_pc_plus_4.value = 0xDDDDDDDD

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1

    dut.in_valid.value = 0
    dut.in_alu_result.value = 0xAAAAAAAA
    dut.in_store_data.value = 0xBBBBBBBB
    dut.in_rd_addr.value = 7
    dut.in_result_src.value = 2
    dut.in_reg_write.value = 1
    dut.in_mem_write.value = 1
    dut.in_funct3.value = 1
    dut.in_imm.value = 0xCCCCCCCC
    dut.in_pc_plus_4.value = 0xDDDDDDDD

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert_outputs_zero(dut)


@cocotb.test()
async def test_hold_when_valid(dut):
    await setup(dut)

    dut.in_valid.value = 1
    dut.in_alu_result.value = 0x11111111
    dut.in_store_data.value = 0x22222222
    dut.in_rd_addr.value = 3
    dut.in_result_src.value = 0
    dut.in_reg_write.value = 1
    dut.in_mem_write.value = 0
    dut.in_funct3.value = 0
    dut.in_imm.value = 0x33333333
    dut.in_pc_plus_4.value = 0x44444444

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.out_alu_result.value) == 0x11111111

    dut.in_alu_result.value = 0x55555555
    dut.in_store_data.value = 0x66666666
    dut.in_rd_addr.value = 9
    dut.in_result_src.value = 3
    dut.in_reg_write.value = 0
    dut.in_mem_write.value = 1
    dut.in_funct3.value = 4
    dut.in_imm.value = 0x77777777
    dut.in_pc_plus_4.value = 0x88888888

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_alu_result.value) == 0x55555555
    assert int(dut.out_store_data.value) == 0x66666666
    assert int(dut.out_rd_addr.value) == 9
    assert int(dut.out_result_src.value) == 3
    assert int(dut.out_reg_write.value) == 0
    assert int(dut.out_mem_write.value) == 1
    assert int(dut.out_funct3.value) == 4
    assert int(dut.out_imm.value) == 0x77777777
    assert int(dut.out_pc_plus_4.value) == 0x88888888


@cocotb.test()
async def test_reset_priority_over_valid(dut):
    await setup(dut)

    dut.in_valid.value = 1
    dut.in_alu_result.value = 0x00001000
    dut.in_store_data.value = 0xDEADBEEF
    dut.in_rd_addr.value = 0
    dut.in_result_src.value = 0
    dut.in_reg_write.value = 0
    dut.in_mem_write.value = 1
    dut.in_funct3.value = 2
    dut.in_imm.value = 0
    dut.in_pc_plus_4.value = 0x80000004

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_mem_write.value) == 1
    assert int(dut.out_store_data.value) == 0xDEADBEEF

    dut.reset.value = 1
    dut.in_valid.value = 1
    dut.in_mem_write.value = 1
    dut.in_store_data.value = 0xCAFEBABE
    dut.in_alu_result.value = 0x00002000

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 0
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_store_data.value) == 0
    assert int(dut.out_alu_result.value) == 0

    dut.reset.value = 0