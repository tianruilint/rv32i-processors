import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_reset_and_sequential_increment(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.take_target.value = 0
    dut.target_pc.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual = int(dut.current_pc.value)
    assert actual == 0

    dut.reset.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual = int(dut.current_pc.value)
    assert actual == 4

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    actual = int(dut.current_pc.value)
    assert actual == 8

@cocotb.test()
async def test_target_selection_and_reset_priority(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.take_target.value = 1
    dut.target_pc.value =  0x00000040

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual = int(dut.current_pc.value)
    assert actual == 0

    dut.reset.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual = int(dut.current_pc.value)
    assert actual == 0x00000040

    dut.take_target.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    expected = 0x00000044
    actual = int(dut.current_pc.value)
    assert actual == expected, (
    f"PC mismatch: expected=0x{expected:08X}, "
    f"actual=0x{actual:08X}"
    )

@cocotb.test()
async def test_pc_wraparound(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.take_target.value = 0
    dut.target_pc.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    dut.reset.value = 0
    dut.take_target.value = 1
    dut.target_pc.value =  0xFFFFFFFC

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual = int(dut.current_pc.value)
    assert actual == 0xFFFFFFFC

    dut.take_target.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    actual = int(dut.current_pc.value)
    assert actual == 0x00000000