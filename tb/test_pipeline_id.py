import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


ALU_ADD = 0
ALU_SUB = 1
ALU_AND = 2
ALU_OR  = 3
ALU_SLT = 8
ALU_XOR = 4
ALU_SLTU = 9
ALU_SLL = 5
ALU_SRL = 6
ALU_SRA = 7

IMM_I = 0
IMM_S = 1
IMM_B = 2
IMM_U = 3
IMM_J = 4

NONE = 0
BEQ  = 1
BNE  = 2
BLT  = 3
BGE  = 4
BLTU = 5
BGEU = 6


async def setup(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.if_id_valid.value = 0
    dut.if_id_pc.value = 0
    dut.if_id_instr.value = 0
    dut.if_id_pc_plus_4.value = 0
    dut.wb_valid.value = 0
    dut.wb_reg_write.value = 0
    dut.wb_rd_addr.value = 0
    dut.wb_data.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0


@cocotb.test()
async def test_basic_alu_decode(dut):
    await setup(dut)

    dut.if_id_instr.value = 0x00500293
    dut.if_id_valid.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_rs1_addr.value) == 0
    assert int(dut.out_rd_addr.value) == 5
    assert int(dut.out_rs1_data.value) == 0
    assert int(dut.out_imm.value) == 5
    assert int(dut.out_alu_op.value) == ALU_ADD
    assert int(dut.out_alu_src.value) == 1
    assert int(dut.out_reg_write.value) == 1
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_uses_rs1.value) == 1
    assert int(dut.out_uses_rs2.value) == 0


@cocotb.test()
async def test_load_store_decode(dut):
    await setup(dut)

    dut.if_id_instr.value = 0x00532223
    dut.if_id_valid.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_rs1_addr.value) == 6
    assert int(dut.out_rs2_addr.value) == 5
    assert int(dut.out_imm.value) == 4
    assert int(dut.out_mem_write.value) == 1
    assert int(dut.out_reg_write.value) == 0
    assert int(dut.out_uses_rs1.value) == 1
    assert int(dut.out_uses_rs2.value) == 1

    dut.if_id_instr.value = 0x00432283
    dut.if_id_valid.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_rs1_addr.value) == 6
    assert int(dut.out_rd_addr.value) == 5
    assert int(dut.out_imm.value) == 4
    assert int(dut.out_result_src.value) == 1
    assert int(dut.out_alu_src.value) == 1
    assert int(dut.out_reg_write.value) == 1
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_uses_rs1.value) == 1
    assert int(dut.out_uses_rs2.value) == 0


@cocotb.test()
async def test_branch_lui_jal_decode(dut):
    await setup(dut)

    dut.if_id_instr.value = 0x00208463
    dut.if_id_valid.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_branch.value) == 1
    assert int(dut.out_branch_type.value) == BEQ
    assert int(dut.out_reg_write.value) == 0
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_uses_rs1.value) == 1
    assert int(dut.out_uses_rs2.value) == 1

    dut.if_id_instr.value = 0x123453B7
    dut.if_id_valid.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_imm.value) == 0x12345000
    assert int(dut.out_result_src.value) == 2
    assert int(dut.out_reg_write.value) == 1
    assert int(dut.out_uses_rs1.value) == 0
    assert int(dut.out_uses_rs2.value) == 0

    dut.if_id_instr.value = 0x008000EF
    dut.if_id_valid.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_result_src.value) == 3
    assert int(dut.out_jump_type.value) == 1
    assert int(dut.out_reg_write.value) == 1
    assert int(dut.out_uses_rs1.value) == 0
    assert int(dut.out_uses_rs2.value) == 0


@cocotb.test()
async def test_invalid_slot_safety(dut):
    await setup(dut)

    dut.if_id_instr.value = 0x00532223
    dut.if_id_valid.value = 0

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 0
    assert int(dut.out_reg_write.value) == 0
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_branch.value) == 0
    assert int(dut.out_jump_type.value) == 0
    assert int(dut.out_uses_rs1.value) == 0
    assert int(dut.out_uses_rs2.value) == 0
    assert int(dut.out_rs1_addr.value) == 0
    assert int(dut.out_rs2_addr.value) == 0
    assert int(dut.out_rd_addr.value) == 0
    assert int(dut.out_rs1_data.value) == 0
    assert int(dut.out_rs2_data.value) == 0
    assert int(dut.out_imm.value) == 0


@cocotb.test()
async def test_wb_to_id_bypass(dut):
    await setup(dut)

    dut.if_id_instr.value = 0x005281B3
    dut.if_id_valid.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_rs1_data.value) == 0
    assert int(dut.out_rs2_data.value) == 0

    dut.wb_valid.value = 1
    dut.wb_reg_write.value = 1
    dut.wb_rd_addr.value = 5
    dut.wb_data.value = 0x12345678

    await Timer(1, unit="ns")

    assert int(dut.out_rs1_data.value) == 0x12345678
    assert int(dut.out_rs2_data.value) == 0x12345678

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.wb_valid.value = 0
    dut.wb_reg_write.value = 0
    dut.wb_rd_addr.value = 0
    dut.wb_data.value = 0

    await Timer(1, unit="ns")

    assert int(dut.out_rs1_data.value) == 0x12345678
    assert int(dut.out_rs2_data.value) == 0x12345678