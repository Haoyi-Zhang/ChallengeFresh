"""Small exact GF(2) linear-algebra utilities using integer bit masks."""
from __future__ import annotations

from collections.abc import Iterable


def mask_limit(d: int) -> int:
    if d < 0:
        raise ValueError("dimension must be nonnegative")
    return (1 << d) - 1


def canonical_basis(rows: Iterable[int], d: int) -> tuple[int, ...]:
    """Return a unique reduced basis, ordered by decreasing pivot bit."""
    limit = mask_limit(d)
    pivots: dict[int, int] = {}
    for raw in rows:
        row = int(raw)
        if row < 0 or row & ~limit:
            raise ValueError(f"row {row} does not fit dimension {d}")
        while row:
            p = row.bit_length() - 1
            if p in pivots:
                row ^= pivots[p]
            else:
                # Clear this pivot from every existing row, then install it.
                for q in tuple(pivots):
                    if (pivots[q] >> p) & 1:
                        pivots[q] ^= row
                pivots[p] = row
                break
    # Re-reduce from high to low to make the representation canonical.
    for p in sorted(pivots, reverse=True):
        row = pivots[p]
        for q in sorted(pivots):
            if q < p and ((row >> q) & 1):
                row ^= pivots[q]
        pivots[p] = row
    return tuple(pivots[p] for p in sorted(pivots, reverse=True))


def rank(rows: Iterable[int], d: int) -> int:
    return len(canonical_basis(rows, d))


def extend_basis(basis: Iterable[int], rows: Iterable[int], d: int) -> tuple[int, ...]:
    return canonical_basis((*tuple(basis), *tuple(rows)), d)


def reduce_vector(v: int, basis: Iterable[int], d: int) -> int:
    if v < 0 or v & ~mask_limit(d):
        raise ValueError("vector does not fit dimension")
    out = v
    for row in canonical_basis(basis, d):
        p = row.bit_length() - 1
        if (out >> p) & 1:
            out ^= row
    return out


def in_span(v: int, basis: Iterable[int], d: int) -> bool:
    return reduce_vector(v, basis, d) == 0


def span_points(basis: Iterable[int], d: int) -> tuple[int, ...]:
    b = canonical_basis(basis, d)
    points = [0]
    for row in b:
        points += [x ^ row for x in points]
    return tuple(sorted(points))


def nullspace_basis(rows: Iterable[int], d: int) -> tuple[int, ...]:
    """Basis of {x: row·x=0 for every row}, represented as d-bit masks."""
    b = canonical_basis(rows, d)
    pivot_to_row = {row.bit_length() - 1: row for row in b}
    pivots = set(pivot_to_row)
    free = [j for j in range(d) if j not in pivots]
    out: list[int] = []
    for f in free:
        x = 1 << f
        # Each reduced row has its pivot plus free-coordinate coefficients.
        for p, row in pivot_to_row.items():
            if ((row & x).bit_count() & 1):
                x |= 1 << p
        out.append(x)
    return canonical_basis(out, d)


def dot(row: int, x: int) -> int:
    return (row & x).bit_count() & 1


def apply(rows: Iterable[int], x: int) -> int:
    out = 0
    for j, row in enumerate(rows):
        out |= dot(int(row), x) << j
    return out


def image_basis(rows: Iterable[int], domain_basis: Iterable[int], d: int) -> tuple[int, ...]:
    rows_t = tuple(rows)
    m = len(rows_t)
    return canonical_basis((apply(rows_t, v) for v in domain_basis), m)


def image_points(rows: Iterable[int], d: int) -> tuple[int, ...]:
    rows_t = tuple(rows)
    return span_points(canonical_basis(rows_t, d), d) if False else tuple(
        sorted({apply(rows_t, x) for x in range(1 << d)})
    )


def image_points_fast(rows: Iterable[int], d: int) -> tuple[int, ...]:
    rows_t = tuple(rows)
    m = len(rows_t)
    standard = tuple(1 << j for j in range(d))
    ib = image_basis(rows_t, standard, d)
    return span_points(ib, m)


def cosets(subspace_basis: Iterable[int], ambient_basis: Iterable[int], m: int) -> tuple[tuple[int, ...], ...]:
    sub = set(span_points(subspace_basis, m))
    ambient = set(span_points(ambient_basis, m))
    if not sub <= ambient:
        raise ValueError("subspace is not contained in ambient space")
    remaining = set(ambient)
    out: list[tuple[int, ...]] = []
    while remaining:
        rep = min(remaining)
        coset = tuple(sorted(rep ^ v for v in sub))
        out.append(coset)
        remaining.difference_update(coset)
    return tuple(out)


def all_subspaces(d: int) -> tuple[tuple[int, ...], ...]:
    """Enumerate every linear subspace of F_2^d as a canonical basis."""
    seen: set[tuple[int, ...]] = {()}
    frontier = [()]
    all_vectors = range(1, 1 << d)
    while frontier:
        b = frontier.pop()
        for v in all_vectors:
            if not in_span(v, b, d):
                nb = canonical_basis((*b, v), d)
                if nb not in seen:
                    seen.add(nb)
                    frontier.append(nb)
    return tuple(sorted(seen, key=lambda b: (len(b), b)))


def fiber_partition(shadow: Iterable[int], rows: Iterable[int], d: int) -> tuple[tuple[int, ...], ...]:
    """Direct signal sets L{x:Sx=s}, one per feasible shadow value."""
    srows = tuple(shadow)
    lrows = tuple(rows)
    groups: dict[int, set[int]] = {}
    for x in range(1 << d):
        groups.setdefault(apply(srows, x), set()).add(apply(lrows, x))
    unique = {tuple(sorted(v)) for v in groups.values()}
    return tuple(sorted(unique))
