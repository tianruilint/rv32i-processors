import cocotb
from cocotb.triggers import Timer


ALU_ADD  = 0
ALU_SUB  = 1
ALU_AND  = 2
ALU_OR   = 3
ALU_XOR  = 4
ALU_SLL  = 5
ALU_SRL  = 6
ALU_SRA  = 7
ALU_SLT  = 8
ALU_SLTU = 9

BR_NONE = 0
BR_BEQ  = 1
BR_BNE  = 2
BR_BLT  = 3
BR_BGE  = 4
BR_BLTU = 5
BR_BGEU = 6

JMP_NONE = 0
JMP_JAL  = 1
JMP_JALR = 2

RES_ALU  = 0
RES_LOAD = 1
RES_LUI  = 2
RES_PC4  = 3


def clear_inputs(dut):
    dut.in_valid.value = 0
    dut.in_pc.value = 0
    dut.in_pc_plus_4.value = 0
    dut.in_rs1_addr.value = 0
    dut.in_rs2_addr.value = 0
    dut.in_rd_addr.value = 0
    dut.in_rs1_data.value = 0
    dut.in_rs2_data.value = 0
    dut.in_imm.value = 0
    dut.in_funct3.value = 0
    dut.in_alu_op.value = 0
    dut.in_alu_src.value = 0
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = 0
    dut.in_reg_write.value = 0
    dut.in_mem_write.value = 0
    dut.in_branch.value = 0
    dut.in_branch_type.value = 0
    dut.in_jump_type.value = 0
    dut.in_uses_rs1.value = 0
    dut.in_uses_rs2.value = 0
    dut.fwd_ex_mem_valid.value = 0
    dut.fwd_ex_mem_reg_write.value = 0
    dut.fwd_ex_mem_rd_addr.value = 0
    dut.fwd_ex_mem_result_src.value = 0
    dut.fwd_ex_mem_data.value = 0
    dut.fwd_mem_wb_valid.value = 0
    dut.fwd_mem_wb_reg_write.value = 0
    dut.fwd_mem_wb_rd_addr.value = 0
    dut.fwd_mem_wb_data.value = 0


@cocotb.test()
async def test_addi(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_rs1_addr.value = 0
    dut.in_rs2_addr.value = 0
    dut.in_rd_addr.value = 1
    dut.in_rs1_data.value = 0
    dut.in_rs2_data.value = 0
    dut.in_imm.value = 5
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 1
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 1
    dut.in_mem_write.value = 0
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 0

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 1
    assert int(dut.out_alu_result.value) == 5
    assert int(dut.out_rd_addr.value) == 1
    assert int(dut.out_result_src.value) == RES_ALU
    assert int(dut.out_reg_write.value) == 1
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_store_data.value) == 0
    assert int(dut.out_redirect.value) == 0


@cocotb.test()
async def test_add_reg(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_rs1_addr.value = 1
    dut.in_rs2_addr.value = 2
    dut.in_rd_addr.value = 3
    dut.in_rs1_data.value = 0x11111111
    dut.in_rs2_data.value = 0x22222222
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 0
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 1
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_alu_result.value) == 0x33333333
    assert int(dut.out_reg_write.value) == 1


@cocotb.test()
async def test_auipc(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_pc.value = 0x20
    dut.in_pc_plus_4.value = 0x24
    dut.in_rs1_addr.value = 0
    dut.in_rd_addr.value = 5
    dut.in_rs1_data.value = 0xDEADBEEF
    dut.in_imm.value = 0x1000
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 1
    dut.in_alu_a_pc.value = 1
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 1
    dut.in_uses_rs1.value = 0

    await Timer(1, unit="ns")

    assert int(dut.out_alu_result.value) == 0x1020
    assert int(dut.out_rd_addr.value) == 5
    assert int(dut.out_reg_write.value) == 1


@cocotb.test()
async def test_ex_mem_priority_over_mem_wb(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_rs1_addr.value = 5
    dut.in_rs2_addr.value = 5
    dut.in_rd_addr.value = 10
    dut.in_rs1_data.value = 0xAAAA0000
    dut.in_rs2_data.value = 0xBBBB0000
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 0
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 1
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 1

    dut.fwd_ex_mem_valid.value = 1
    dut.fwd_ex_mem_reg_write.value = 1
    dut.fwd_ex_mem_rd_addr.value = 5
    dut.fwd_ex_mem_result_src.value = RES_ALU
    dut.fwd_ex_mem_data.value = 0x11111111

    dut.fwd_mem_wb_valid.value = 1
    dut.fwd_mem_wb_reg_write.value = 1
    dut.fwd_mem_wb_rd_addr.value = 5
    dut.fwd_mem_wb_data.value = 0x22222222

    await Timer(1, unit="ns")

    assert int(dut.out_alu_result.value) == 0x22222222


@cocotb.test()
async def test_mem_wb_when_ex_mem_not_match(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_rs1_addr.value = 5
    dut.in_rs2_addr.value = 6
    dut.in_rd_addr.value = 10
    dut.in_rs1_data.value = 0x100
    dut.in_rs2_data.value = 0x200
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 0
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 1
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 1

    dut.fwd_ex_mem_valid.value = 1
    dut.fwd_ex_mem_reg_write.value = 1
    dut.fwd_ex_mem_rd_addr.value = 7
    dut.fwd_ex_mem_result_src.value = RES_ALU
    dut.fwd_ex_mem_data.value = 0xDEAD

    dut.fwd_mem_wb_valid.value = 1
    dut.fwd_mem_wb_reg_write.value = 1
    dut.fwd_mem_wb_rd_addr.value = 5
    dut.fwd_mem_wb_data.value = 0x12345678

    await Timer(1, unit="ns")

    assert int(dut.out_alu_result.value) == 0x12345878


@cocotb.test()
async def test_load_address_not_forwarded_from_ex_mem(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_rs1_addr.value = 5
    dut.in_rd_addr.value = 10
    dut.in_rs1_data.value = 0x100
    dut.in_imm.value = 7
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 1
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 1
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 0

    dut.fwd_ex_mem_valid.value = 1
    dut.fwd_ex_mem_reg_write.value = 1
    dut.fwd_ex_mem_rd_addr.value = 5
    dut.fwd_ex_mem_result_src.value = RES_LOAD
    dut.fwd_ex_mem_data.value = 0xBADBAD

    dut.fwd_mem_wb_valid.value = 0
    dut.fwd_mem_wb_reg_write.value = 0
    dut.fwd_mem_wb_rd_addr.value = 0
    dut.fwd_mem_wb_data.value = 0

    await Timer(1, unit="ns")

    assert int(dut.out_alu_result.value) == 0x107
    assert int(dut.out_alu_result.value) != 0x100 + 0xBADBAD


@cocotb.test()
async def test_store_data_uses_forwarded_rs2(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_rs1_addr.value = 6
    dut.in_rs2_addr.value = 5
    dut.in_rd_addr.value = 0
    dut.in_rs1_data.value = 0x100
    dut.in_rs2_data.value = 0xAABBCCDD
    dut.in_imm.value = 4
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 1
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 0
    dut.in_mem_write.value = 1
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_alu_result.value) == 0x104
    assert int(dut.out_store_data.value) == 0xAABBCCDD
    assert int(dut.out_mem_write.value) == 1


@cocotb.test()
async def test_store_data_uses_forwarded_rs2_from_ex_mem(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_rs1_addr.value = 6
    dut.in_rs2_addr.value = 5
    dut.in_rd_addr.value = 0
    dut.in_rs1_data.value = 0x100
    dut.in_rs2_data.value = 0x00000000
    dut.in_imm.value = 4
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 1
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 0
    dut.in_mem_write.value = 1
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 1

    dut.fwd_ex_mem_valid.value = 1
    dut.fwd_ex_mem_reg_write.value = 1
    dut.fwd_ex_mem_rd_addr.value = 5
    dut.fwd_ex_mem_result_src.value = RES_ALU
    dut.fwd_ex_mem_data.value = 0x11223344

    await Timer(1, unit="ns")

    assert int(dut.out_alu_result.value) == 0x104
    assert int(dut.out_store_data.value) == 0x11223344
    assert int(dut.out_mem_write.value) == 1


@cocotb.test()
async def test_invalid_clears_write_enables_and_redirect(dut):
    clear_inputs(dut)
    dut.in_valid.value = 0
    dut.in_rs1_addr.value = 1
    dut.in_rs2_addr.value = 2
    dut.in_rd_addr.value = 5
    dut.in_rs1_data.value = 0x100
    dut.in_rs2_data.value = 0x200
    dut.in_imm.value = 0x10
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 0
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 1
    dut.in_mem_write.value = 1
    dut.in_branch.value = 1
    dut.in_branch_type.value = BR_BEQ
    dut.in_jump_type.value = JMP_JAL

    await Timer(1, unit="ns")

    assert int(dut.out_valid.value) == 0
    assert int(dut.out_reg_write.value) == 0
    assert int(dut.out_mem_write.value) == 0
    assert int(dut.out_redirect.value) == 0
    assert int(dut.out_redirect_pc.value) == 0


@cocotb.test()
async def test_jal_redirect(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_pc.value = 0x80000000
    dut.in_pc_plus_4.value = 0x80000004
    dut.in_rd_addr.value = 1
    dut.in_imm.value = 0x100
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 1
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_PC4
    dut.in_reg_write.value = 1
    dut.in_jump_type.value = JMP_JAL

    await Timer(1, unit="ns")

    assert int(dut.out_redirect.value) == 1
    assert int(dut.out_redirect_pc.value) == 0x80000100
    assert int(dut.out_reg_write.value) == 1
    assert int(dut.out_result_src.value) == RES_PC4


@cocotb.test()
async def test_jalr_redirect_clears_lsb(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_pc.value = 0x80000000
    dut.in_pc_plus_4.value = 0x80000004
    dut.in_rs1_addr.value = 5
    dut.in_rd_addr.value = 1
    dut.in_rs1_data.value = 0x80000101
    dut.in_imm.value = 0
    dut.in_alu_op.value = ALU_ADD
    dut.in_alu_src.value = 1
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_PC4
    dut.in_reg_write.value = 1
    dut.in_jump_type.value = JMP_JALR
    dut.in_uses_rs1.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_redirect.value) == 1
    assert int(dut.out_redirect_pc.value) == 0x80000100
    assert int(dut.out_result_src.value) == RES_PC4


@cocotb.test()
async def test_branch_beq_taken(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_pc.value = 0x80000000
    dut.in_rs1_addr.value = 5
    dut.in_rs2_addr.value = 6
    dut.in_rs1_data.value = 0x1234
    dut.in_rs2_data.value = 0x1234
    dut.in_imm.value = 0x20
    dut.in_alu_op.value = ALU_SUB
    dut.in_alu_src.value = 0
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 0
    dut.in_branch.value = 1
    dut.in_branch_type.value = BR_BEQ
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_redirect.value) == 1
    assert int(dut.out_redirect_pc.value) == 0x80000020


@cocotb.test()
async def test_branch_bltu_not_taken_when_rs1_larger(dut):
    clear_inputs(dut)
    dut.in_valid.value = 1
    dut.in_pc.value = 0x80000000
    dut.in_rs1_addr.value = 5
    dut.in_rs2_addr.value = 6
    dut.in_rs1_data.value = 0xFFFFFFFF
    dut.in_rs2_data.value = 0x00000001
    dut.in_imm.value = 0x20
    dut.in_alu_op.value = ALU_SUB
    dut.in_alu_src.value = 0
    dut.in_alu_a_pc.value = 0
    dut.in_result_src.value = RES_ALU
    dut.in_reg_write.value = 0
    dut.in_branch.value = 1
    dut.in_branch_type.value = BR_BLTU
    dut.in_uses_rs1.value = 1
    dut.in_uses_rs2.value = 1

    await Timer(1, unit="ns")

    assert int(dut.out_redirect.value) == 0