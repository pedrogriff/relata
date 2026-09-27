"""Tests for deterministic share distribution and integer conservation."""

from __future__ import annotations

from decimal import Decimal

from relata.engine.share_distributor import distribute_integer_shares


def test_distribute_shares_conservation_invariant() -> None:
    """Verifies that sum of allocated integer shares strictly equals total_shares across awkward weights."""
    test_cases = [
        (100, [Decimal("0.33"), Decimal("0.33"), Decimal("0.22"), Decimal("0.12")]),
        (1, [Decimal("0.25"), Decimal("0.25"), Decimal("0.25"), Decimal("0.25")]),
        (10, [Decimal("0.3333333333"), Decimal("0.3333333333"), Decimal("0.3333333333")]),
        (120_000, [Decimal("1.0") / Decimal("36")] * 36),
        (7, [Decimal("0.1")] * 10),
        (0, [Decimal("0.5"), Decimal("0.5")]),
    ]

    for total_shares, weights in test_cases:
        allocated = distribute_integer_shares(total_shares, weights)
        assert sum(allocated) == total_shares, f"Failed conservation for total={total_shares}, sum={sum(allocated)}"
        assert len(allocated) == len(weights)
        assert all(s >= 0 for s in allocated)


def test_distribute_shares_empty_or_zero() -> None:
    assert distribute_integer_shares(0, [Decimal("0.5"), Decimal("0.5")]) == [0, 0]
    assert distribute_integer_shares(100, []) == []
    assert distribute_integer_shares(-50, [Decimal("1.0")]) == [0]
