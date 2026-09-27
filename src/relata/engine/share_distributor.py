"""Deterministic Share Distribution with Exact Integer Conservation (Largest Remainder Method).

Guarantees the fundamental invariant: sum(allocated_shares) == total_shares with zero rounding drift.
"""

from __future__ import annotations

from decimal import Decimal


def distribute_integer_shares(total_shares: int, weights: list[Decimal]) -> list[int]:
    """Distributes total_shares across arbitrary fractional weights using the Largest Remainder Method (Hamilton-Hare).

    Invariant:
        sum(distribute_integer_shares(T, weights)) == T for all T >= 0.

    Args:
        total_shares: Exact non-negative integer of shares/options to distribute.
        weights: List of fractional decimal weights (should sum approximately to 1.0).

    Returns:
        List of exact integer share allocations per tranche.
    """
    if total_shares <= 0 or not weights:
        return [0] * len(weights)

    # Normalize weights if necessary
    weight_sum = sum(weights)
    if weight_sum <= 0:
        return [0] * len(weights)

    normalized_weights = [w / weight_sum for w in weights]
    num_tranches = len(normalized_weights)

    allocated: list[int] = []
    remainders: list[tuple[Decimal, int]] = []
    total_allocated = 0

    for idx, weight in enumerate(normalized_weights):
        ideal_decimal = Decimal(total_shares) * weight
        floor_val = int(ideal_decimal)
        rem = ideal_decimal - Decimal(floor_val)

        allocated.append(floor_val)
        remainders.append((rem, idx))
        total_allocated += floor_val

    unallocated = total_shares - total_allocated
    # Sort remainders descending by remainder size, then by index for deterministic stability
    remainders.sort(key=lambda x: (-x[0], x[1]))

    for i in range(unallocated):
        target_idx = remainders[i % num_tranches][1]
        allocated[target_idx] += 1

    return allocated
