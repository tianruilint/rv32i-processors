import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_immediate_formats(dut):
    vectors = [
        (0, 0x12300000, 0x00000123),
        (0, 0xFF800000, 0xFFFFFFF8),
        (1, 0x00000A00, 0x00000014),
        (1, 0xFE000800, 0xFFFFFFF0),
        (2, 0x00000800, 0x00000010),
        (2, 0xFE000E80, 0xFFFFFFFC),
        (3, 0x12345000, 0x12345000),
        (3, 0xFFF00000, 0xFFF00000),
        (4, 0x008000EF, 0x00000008),
        (4, 0x001000EF, 0x00000800),
        (4, 0x000010EF, 0x00001000),
        (4, 0xFFDFF06F, 0xFFFFFFFC),
        (7, 0xFFFFFFFF, 0x00000000),
    ]

    for imm_type, instr, expected in vectors:
        dut.imm_type.value = imm_type;
        dut.instr.value = instr;

        await Timer(1, unit="ns")

        actual = int(dut.imm.value)
        assert actual == expected, (
           f"imm_type={imm_type}: "
           f"expected=0x{expected:08X}, actual=0x{actual:08X}"
        )
