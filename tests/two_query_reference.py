"""Test-only literal cube reference; no production imports or private paths."""
from itertools import combinations_with_replacement
from math import comb


def literal_union_max(rank: int, radius: int, queries: int) -> int:
    """Enumerate center multisets and cube points, including repeated centers."""
    if not 0 <= rank <= 5 or not 1 <= queries <= 4:
        raise ValueError("literal reference limited to rank <=5 and queries <=4")
    points = range(1 << rank)
    balls = [
        sum(1 << x for x in points if (x ^ center).bit_count() <= radius)
        for center in points
    ]
    best = 0
    for centers in combinations_with_replacement(points, queries):
        union = 0
        for center in centers:
            union |= balls[center]
        best = max(best, union.bit_count())
    return best


def antipodal_count(rank: int, radius: int) -> int:
    """Count weights missed by both antipodal centers, rather than cap volumes."""
    return (1 << rank) - sum(
        comb(rank, weight) for weight in range(radius + 1, rank - radius)
    )


def witness_union(rank: int, radius: int, profile: tuple[int, int]) -> int:
    """A two-pattern profile induces centers zero and a suffix of ones."""
    assert sum(profile) == rank
    second = (1 << profile[1]) - 1
    return sum(
        min(x.bit_count(), (x ^ second).bit_count()) <= radius
        for x in range(1 << rank)
    )

