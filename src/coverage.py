"""Exact and conservative Hamming multi-ball coverage over binary cubes."""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from math import comb
from typing import Iterator


def ball_volume(r: int, t: int) -> int:
    if r < 0 or t < 0:
        return 0
    return sum(comb(r, i) for i in range(min(r, t) + 1))


def weak_compositions(total: int, parts: int) -> Iterator[tuple[int, ...]]:
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in weak_compositions(total - first, parts - 1):
            yield (first, *rest)


def _profile_histogram(profile: tuple[int, ...], q: int) -> tuple[int, ...]:
    r = sum(profile)
    hist = [0] * (r + 1)
    a = len(profile)

    def rec(p: int, d0: int, adjustments: list[int], mult: int) -> None:
        if p == a:
            mind = d0
            for adj in adjustments:
                cand = d0 + adj
                if cand < mind:
                    mind = cand
            hist[mind] += mult
            return
        c = profile[p]
        for w in range(c + 1):
            next_adj = adjustments.copy()
            delta = c - 2 * w
            for j in range(q - 1):
                if (p >> j) & 1:
                    next_adj[j] += delta
            rec(p + 1, d0 + w, next_adj, mult * comb(c, w))

    rec(0, 0, [0] * (q - 1), 1)
    if sum(hist) != 1 << r:
        raise AssertionError("profile histogram mass mismatch")
    return tuple(hist)


@lru_cache(maxsize=None)
def exact_profile(r: int, q: int) -> tuple[tuple[int, ...], tuple[tuple[int, ...], ...], int, int]:
    """Return all-radius maxima, one maximizing profile/radius, and work counts."""
    if r < 0 or q < 1:
        raise ValueError("invalid coverage parameters")
    q_eff = q
    if q_eff == 1:
        vals = tuple(ball_volume(r, t) for t in range(r + 1))
        return vals, tuple((r,) for _ in vals), 1, r + 1
    a = 1 << (q_eff - 1)
    best = [0] * (r + 1)
    witness: list[tuple[int, ...]] = [()] * (r + 1)
    profiles = 0
    weights = 0
    for profile in weak_compositions(r, a):
        profiles += 1
        local_weights = 1
        for c in profile:
            local_weights *= c + 1
        weights += local_weights
        hist = _profile_histogram(profile, q_eff)
        cumulative = 0
        for t, mass in enumerate(hist):
            cumulative += mass
            if cumulative > best[t]:
                best[t] = cumulative
                witness[t] = profile
    return tuple(best), tuple(witness), profiles, weights


def exact_domain(r: int, q: int) -> bool:
    return q <= 2 or (q == 3 and r <= 24) or (q == 4 and r <= 8)


@lru_cache(maxsize=None)
def max_coverage(r: int, t: int, q: int) -> tuple[int, bool]:
    """Coverage count and flag indicating exactness."""
    if r < 0 or t < 0 or q < 1:
        raise ValueError("invalid coverage parameters")
    if t >= r or q >= (1 << r):
        return 1 << r, True
    # Antipodal centers attain the two-ball volume bound. Keep non-int
    # direct-call behavior on the existing profile path (e.g. q=2.0).
    if type(r) is int and type(t) is int and type(q) is int and q == 2:
        return min(1 << r, 2 * ball_volume(r, t)), True
    if exact_domain(r, q):
        vals, _, _, _ = exact_profile(r, q)
        return vals[t], True
    return min(1 << r, q * ball_volume(r, t)), False


def direct_max_coverage(r: int, t: int, q: int) -> tuple[int, int]:
    """Brute-force unordered center sets. Returns maximum and sets visited."""
    n = 1 << r
    if q >= n:
        return n, 1
    best = 0
    visited = 0
    # Translation invariance allows center zero to be fixed.
    for rest in combinations(range(1, n), q - 1):
        centers = (0, *rest)
        visited += 1
        covered = 0
        for x in range(n):
            if min((x ^ c).bit_count() for c in centers) <= t:
                covered += 1
        best = max(best, covered)
    return best, visited


def code_max_coverage(points: tuple[int, ...], n: int, t: int, q: int) -> int:
    """Maximum number of code points covered by q ambient Hamming balls."""
    masks = set()
    for center in range(1 << n):
        mask = 0
        for i, x in enumerate(points):
            if (x ^ center).bit_count() <= t:
                mask |= 1 << i
        masks.add(mask)
    masks_t = tuple(sorted(masks))
    if q >= len(points):
        # This shortcut is safe only as an upper candidate; exact loop below is small.
        pass
    best = 0
    if q == 1:
        return max(m.bit_count() for m in masks_t)
    if q == 2:
        for i, a in enumerate(masks_t):
            for b in masks_t[i:]:
                best = max(best, (a | b).bit_count())
        return best
    if q == 3:
        for i, a in enumerate(masks_t):
            for j in range(i, len(masks_t)):
                ab = a | masks_t[j]
                for c in masks_t[j:]:
                    best = max(best, (ab | c).bit_count())
        return best
    raise ValueError("direct code solver supports q<=3")
