import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


MASK32 = 0xFFFFFFFF

    
@cocotb.test()
async def test_write_and_read_x5(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reg_write.value = 0
    dut.rd_addr.value = 0
    dut.rs1_addr.value = 0
    dut.rs2_addr.value = 0
    dut.rd_data.value = 0

    await Timer(1, unit="ns")

    dut.reg_write.value = 1
    dut.rd_addr.value = 5
    dut.rd_data.value = 0x12345678

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reg_write.value = 0

    dut.rs1_addr.value = 5
    await Timer(1, unit="ns")

    actual = int(dut.rs1_data.value)

    assert actual == 0x12345678, (
        f"write/read x5 failed: "
        f"expected=0x12345678, actual=0x{actual:08X}"
    )

@cocotb.test()
async def test_x0_read_is_zero(dut):

    dut.reg_write.value = 0
    dut.rd_addr.value = 0
    dut.rs1_addr.value = 0
    dut.rs2_addr.value = 0
    dut.rd_data.value = 0


    await Timer(1, unit="ns")

    actual = int(dut.rs1_data.value)

    assert actual == 0, (
        f"write/read x0 failed: "
        f"expected=0, actual=0x{actual:08X}"
    )

@cocotb.test()
async def test_write_to_x0_is_ignored(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reg_write.value = 0
    dut.rd_addr.value = 0
    dut.rs1_addr.value = 0
    dut.rs2_addr.value = 0
    dut.rd_data.value = 0

    await Timer(1, unit="ns")

    dut.reg_write.value = 1
    dut.rd_addr.value = 0
    dut.rd_data.value = 0x12345678

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reg_write.value = 0

    dut.rs1_addr.value = 0
    await Timer(1, unit="ns")

    actual = int(dut.rs1_data.value)

    assert actual == 0, (
        f"write/read x0 failed: "
        f"expected=0, actual=0x{actual:08X}"
    )

@cocotb.test()
async def test_two_read_ports(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reg_write.value = 1
    dut.rd_addr.value = 5
    dut.rd_data.value = 0x11111111

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.rd_addr.value = 6
    dut.rd_data.value = 0x22222222

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reg_write.value = 0

    dut.rs1_addr.value = 5
    dut.rs2_addr.value = 6

    await Timer(1, unit="ns")

    actual_rs1 = int(dut.rs1_data.value)
    actual_rs2 = int(dut.rs2_data.value)

    assert actual_rs1 == 0x11111111
    assert actual_rs2 == 0x22222222

@cocotb.test()
async def test_write_disabled_keeps_old_value(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reg_write.value = 1
    dut.rd_addr.value = 5
    dut.rd_data.value = 0xAAAAAAAA

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reg_write.value = 0
    dut.rd_addr.value = 5
    dut.rd_data.value = 0xBBBBBBBB

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.rs1_addr.value = 5
    await Timer(1, unit="ns")

    actual_rs1 = int(dut.rs1_data.value)

    assert actual_rs1 == 0xAAAAAAAA
