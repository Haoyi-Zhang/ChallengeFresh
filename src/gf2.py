"""Small exact GF(2) linear-algebra utilities using integer bit masks."""
from __future__ import annotations

from collections.abc import Iterable


def _require_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def mask_limit(d: int) -> int:
    d = _require_int(d, "dimension")
    if d < 0:
        raise ValueError("dimension must be nonnegative")
    return (1 << d) - 1


def canonical_basis(rows: Iterable[int], d: int) -> tuple[int, ...]:
    """Return the unique reduced row-echelon basis, high pivots first.

    Vectors are represented by ``d``-bit integers.  The implementation performs
    full Gauss--Jordan elimination, so the result is independent of input row
    order, duplicate rows, and redundant generators.
    """
    limit = mask_limit(d)
    work: list[int] = []
    for index, raw in enumerate(rows):
        row = _require_int(raw, f"row[{index}]")
        if row < 0 or row & ~limit:
            raise ValueError(f"row {row} does not fit dimension {d}")
        if row:
            work.append(row)

    # Sorting is not needed for mathematical uniqueness, but makes the pivot
    # search deterministic even before the final RREF is reached.
    work.sort(reverse=True)
    pivot_row = 0
    for pivot in range(d - 1, -1, -1):
        selected = next(
            (i for i in range(pivot_row, len(work)) if (work[i] >> pivot) & 1),
            None,
        )
        if selected is None:
            continue
        work[pivot_row], work[selected] = work[selected], work[pivot_row]
        pivot_vector = work[pivot_row]
        for i in range(len(work)):
            if i != pivot_row and ((work[i] >> pivot) & 1):
                work[i] ^= pivot_vector
        pivot_row += 1
        if pivot_row == len(work):
            break

    basis = [row for row in work[:pivot_row] if row]
    basis.sort(key=lambda row: row.bit_length(), reverse=True)
    return tuple(basis)


def rank(rows: Iterable[int], d: int) -> int:
    return len(canonical_basis(rows, d))


def extend_basis(basis: Iterable[int], rows: Iterable[int], d: int) -> tuple[int, ...]:
    return canonical_basis((*tuple(basis), *tuple(rows)), d)


def reduce_vector(v: int, basis: Iterable[int], d: int) -> int:
    v = _require_int(v, "vector")
    if v < 0 or v & ~mask_limit(d):
        raise ValueError("vector does not fit dimension")
    out = v
    for row in canonical_basis(basis, d):
        pivot = row.bit_length() - 1
        if (out >> pivot) & 1:
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
    """Basis of ``{x: row*x=0 for every row}``, as ``d``-bit masks."""
    b = canonical_basis(rows, d)
    pivot_to_row = {row.bit_length() - 1: row for row in b}
    pivots = set(pivot_to_row)
    free = [j for j in range(d) if j not in pivots]
    out: list[int] = []
    for free_column in free:
        x = 1 << free_column
        # In RREF every other pivot column is zero.  Setting a pivot bit to the
        # parity of the free entries in its row solves that equation directly.
        for pivot, row in pivot_to_row.items():
            if (row & x).bit_count() & 1:
                x |= 1 << pivot
        out.append(x)
    return canonical_basis(out, d)


def dot(row: int, x: int) -> int:
    row = _require_int(row, "row")
    x = _require_int(x, "vector")
    return (row & x).bit_count() & 1


def apply(rows: Iterable[int], x: int) -> int:
    x = _require_int(x, "vector")
    out = 0
    for j, row in enumerate(rows):
        out |= dot(row, x) << j
    return out


def image_basis(rows: Iterable[int], domain_basis: Iterable[int], d: int) -> tuple[int, ...]:
    rows_t = tuple(rows)
    m = len(rows_t)
    return canonical_basis((apply(rows_t, v) for v in domain_basis), m)


def image_points(rows: Iterable[int], d: int) -> tuple[int, ...]:
    rows_t = tuple(rows)
    return tuple(sorted({apply(rows_t, x) for x in range(1 << d)}))


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
    """Direct signal sets ``L{x:Sx=s}``, one per feasible shadow value."""
    srows = tuple(shadow)
    lrows = tuple(rows)
    groups: dict[int, set[int]] = {}
    for x in range(1 << d):
        groups.setdefault(apply(srows, x), set()).add(apply(lrows, x))
    unique = {tuple(sorted(v)) for v in groups.values()}
    return tuple(sorted(unique))
