import cocotb
from cocotb.triggers import Timer

ALU_ADD  = 0x0
ALU_SUB  = 0x1
ALU_AND  = 0x2
ALU_OR   = 0x3
ALU_SLT  = 0x8

IMM_I = 0X0
IMM_S = 0X1
IMM_B = 0X2


@cocotb.test()
async def test_decoder(dut):
    vectors = [
        (0x33, 0b000, 0b0000000,
        (1, 0, 0, 0, 0, IMM_I, ALU_ADD)),

        (0x33, 0b000, 0b0100000,
        (1, 0, 0, 0, 0, IMM_I, ALU_SUB)),

        (0x33, 0b111, 0b0000000,
        (1, 0, 0, 0, 0, IMM_I, ALU_AND)),

        (0x13, 0b000, 0b0000000,
        (1, 1, 0, 0, 0, IMM_I, ALU_ADD)),

        (0x13, 0b100, 0b0000000,
        (0, 0, 0, 0, 0, IMM_I, ALU_ADD)),

        (0x03, 0b010, 0b0000000,
        (1, 1, 0, 1, 0, IMM_I, ALU_ADD)),

        (0x23, 0b010, 0b0000000,
        (0, 1, 1, 0, 0, IMM_S, ALU_ADD)),

        (0x63, 0b000, 0b0000000,
        (0, 0, 0, 0, 1, IMM_B, ALU_SUB)),

        (0x7f, 0b000, 0b0000000,
        (0, 0, 0, 0, 0, IMM_I, ALU_ADD)),
    ]

    for opcode, funct3, funct7, expected in vectors:
        dut.opcode.value = opcode;
        dut.funct3.value = funct3;
        dut.funct7.value = funct7;

        await Timer(1, unit="ns")

        actual = (
            int(dut.reg_write.value),
            int(dut.alu_src.value),
            int(dut.mem_write.value),
            int(dut.result_src.value),
            int(dut.branch.value),
            int(dut.imm_type.value),
            int(dut.alu_op.value),
        )

        assert actual == expected, (
            f"opcode=0x{opcode:02X}, "
            f"funct3={funct3:03b}, funct7={funct7:07b}: "
            f"expected={expected}, actual={actual}"
        )