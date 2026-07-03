import random

import cocotb
from cocotb.triggers import Timer

MASK32 = 0xFFFFFFFF

ALU_ADD  = 0x0
ALU_SUB  = 0x1
ALU_AND  = 0x2
ALU_OR   = 0x3
ALU_XOR  = 0x4
ALU_SLL  = 0x5
ALU_SRL  = 0x6
ALU_SRA  = 0x7
ALU_SLT  = 0x8
ALU_SLTU = 0x9

def u32(value):
    return value & MASK32

def s32(value):
    value &= MASK32

    if value & 0x80000000:
        return value - 0x100000000

    return value

def alu_reference(op,a,b):
    a = u32(a)
    b = u32(b)
    shamt = b & 0x1F

    if op == ALU_ADD:
        return u32(a+b)
    if op == ALU_SUB:
        return u32(a-b)
    if op == ALU_AND:
        return a & b
    if op == ALU_OR:
        return a | b
    if op == ALU_XOR:
        return a ^ b
    if op == ALU_SLL:
        return u32(a << shamt)
    if op == ALU_SRL:
        return u32(a >> shamt)
    if op == ALU_SRA:
        return u32(s32(a) >> shamt)
    if op == ALU_SLT:
        return int(s32(a) < s32(b))
    if op == ALU_SLTU:
        return int(a < b)
    
    return 0

async def check_alu(dut, op ,a ,b):
    dut.alu_op.value = op
    dut.a.value = u32(a)
    dut.b.value = u32(b)

    await Timer(1, unit="ns")

    expected = alu_reference(op, a, b)
    actual = int(dut.result.value)

    assert actual == expected, (
        f"ALU mismatch: op=0x{op:X}, a=0x{u32(a):08X}, b=0x{u32(b):08X}, "
        f"expected=0x{expected:08X}, actual=0x{actual:08X}"
    )

@cocotb.test()
async def test_cases1(dut):

    cases = [
        (ALU_ADD,   5,          7),
        (ALU_ADD,   0xFFFFFFFF, 1),
        (ALU_SUB,   7,          5),
        (ALU_SUB,   0,          1),

        (ALU_AND,   0xF0F0,     0x0FF0),
        (ALU_OR,    0xF000,     0x0F00),
        (ALU_XOR,   0xAAAA5555, 0xFFFF0000),

        (ALU_SLT,   0xFFFFFFFF, 1),

        (ALU_SLTU,  0xFFFFFFFF, 1),

        (ALU_SLL,   1,          31),
        (ALU_SLL,   1,          32),

        (ALU_SRL,   0x80000000, 1),
        (ALU_SRA,   0x80000000, 1),
        
        (ALU_ADD,   0,          0),
        (ALU_ADD,   0x7FFFFFFF, 1),
        (ALU_SLT,   5,          5),
        (ALU_SLT,   0xFFFFFFFF, 0xFFFFFFFF),
        (ALU_SLL,   0x55555555, 0), 
        (ALU_SLL,   0x55555555, 31),
    ]

    for op, a, b in cases:
        await check_alu(dut, op, a, b)

@cocotb.test()
async def test_cases2(dut):

    rng = random.Random(20260906)

    operations = [
        ALU_ADD,
        ALU_SUB,
        ALU_AND,
        ALU_OR,
        ALU_XOR,
        ALU_SLL,
        ALU_SRL,
        ALU_SRA,
        ALU_SLT,
        ALU_SLTU,
    ]

    for op in operations:
        for _ in range(200):
            a = rng.getrandbits(32)
            b = rng.getrandbits(32)

            await check_alu(dut, op, a, b)
