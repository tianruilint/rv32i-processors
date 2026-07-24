import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_pipeline_frontend(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.stall.value = 0
    dut.redirect.value = 0
    dut.redirect_pc.value = 0
    dut.instr.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 0
    assert int(dut.if_id_valid.value) == 0

    dut.reset.value = 0
    dut.instr.value = 0xAAAAAAAA

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 4
    assert int(dut.if_id_valid.value) == 1
    assert int(dut.if_id_pc.value) == 0
    assert int(dut.if_id_instr.value) == 0xAAAAAAAA
    assert int(dut.if_id_pc_plus_4.value) == 4

    dut.stall.value = 1
    dut.instr.value = 0xBBBBBBBB

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 4
    assert int(dut.if_id_valid.value) == 1
    assert int(dut.if_id_pc.value) == 0
    assert int(dut.if_id_instr.value) == 0xAAAAAAAA
    assert int(dut.if_id_pc_plus_4.value) == 4

    dut.stall.value = 1
    dut.redirect.value = 1
    dut.redirect_pc.value = 0x20
    dut.instr.value = 0xBBBBBBBB

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 0x20
    assert int(dut.if_id_valid.value) == 0

    dut.stall.value = 0
    dut.redirect.value = 0
    dut.instr.value = 0xCCCCCCCC

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 0x24
    assert int(dut.if_id_valid.value) == 1
    assert int(dut.if_id_pc.value) == 0x20
    assert int(dut.if_id_instr.value) == 0xCCCCCCCC
    assert int(dut.if_id_pc_plus_4.value) == 0x24

    dut.reset.value = 1
    dut.redirect.value = 1
    dut.redirect_pc.value = 0x40
    dut.instr.value = 0xDDDDDDDD

    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.current_pc.value) == 0
    assert int(dut.if_id_valid.value) == 0