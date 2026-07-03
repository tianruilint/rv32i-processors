"""Exhaustive cocotb smoke test for the educational full adder."""

from itertools import product

import cocotb
from cocotb.triggers import Timer


def _read_logic(signal):
    """Return an integer for a resolved bit, or text for an unresolved value."""
    try:
        return int(signal.value)
    except (TypeError, ValueError):
        return str(signal.value)


@cocotb.test()
async def test_all_input_combinations(dut):
    """Exercise every three-bit input value and report all mismatches."""
    failures = []

    for a_i, b_i, cin_i in product((0, 1), repeat=3):
        dut.a_i.value = a_i
        dut.b_i.value = b_i
        dut.cin_i.value = cin_i
        await Timer(1, unit="ns")

        input_total = a_i + b_i + cin_i
        expected_sum = input_total % 2
        expected_carry = input_total // 2
        actual_sum = _read_logic(dut.sum_o)
        actual_carry = _read_logic(dut.cout_o)

        if (actual_sum, actual_carry) != (expected_sum, expected_carry):
            failures.append(
                "inputs: "
                f"a_i={a_i}, b_i={b_i}, cin_i={cin_i}; "
                f"expected sum={expected_sum}, actual sum={actual_sum}; "
                f"expected carry={expected_carry}, actual carry={actual_carry}"
            )

    assert not failures, "Full-adder mismatch(es):\n" + "\n".join(failures)
