"""Exact-rational affine-shadow certificate evaluators."""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import combinations

from coverage import max_coverage
from gf2 import (apply, canonical_basis, cosets, extend_basis, image_basis,
                 image_points_fast, nullspace_basis, rank, span_points)
from model import Epoch, Node, Observe, Protocol, Stop


METHODS = ("branch", "full", "flag", "coherent", "coset")


class ResourceLimitError(RuntimeError):
    pass


def _insert_bits(flagged_value: int, fair_value: int, flagged: tuple[int, ...], m: int,
                 complement_mask: int = 0) -> int:
    out = 0
    fi = ui = 0
    flagged_set = set(flagged)
    for j in range(m):
        if j in flagged_set:
            bit = ((flagged_value >> fi) & 1) ^ ((complement_mask >> j) & 1)
            fi += 1
        else:
            bit = (fair_value >> ui) & 1
            ui += 1
        out |= bit << j
    return out


def channel_prob(output: int, signal: int, m: int, eta: Fraction) -> Fraction:
    errors = (output ^ signal).bit_count()
    return eta ** errors * (1 - eta) ** (m - errors)


class CertificateEvaluator:
    def __init__(self, protocol: Protocol, method: str = "coset", max_states: int = 20_000,
                 max_transitions: int = 200_000):
        if method not in METHODS:
            raise ValueError(f"unknown method {method}")
        self.protocol = protocol
        self.method = method
        self.max_states = max_states
        self.max_transitions = max_transitions
        self.states = 0
        self.transitions = 0
        self.used_upper_bound = False
        self._node_ids: dict[int, int] = {}
        self._next_id = 0
        self._cache: dict[tuple[int, tuple[int, ...]], Fraction] = {}

    def _id(self, node: Node) -> int:
        key = id(node)
        if key not in self._node_ids:
            self._node_ids[key] = self._next_id
            self._next_id += 1
        return self._node_ids[key]

    def survival(self, node: Node, shadow: tuple[int, ...]) -> Fraction:
        shadow = canonical_basis(shadow, self.protocol.dimension)
        key = (self._id(node), shadow)
        if key in self._cache:
            return self._cache[key]
        self.states += 1
        if self.states > self.max_states:
            raise ResourceLimitError("certificate state limit exceeded")
        if isinstance(node, Stop):
            result = Fraction(1)
        elif isinstance(node, Epoch):
            new_shadow = extend_basis(shadow, node.rows, self.protocol.dimension)
            r = len(new_shadow) - len(shadow)
            covered, exact = max_coverage(r, node.radius, node.guesses)
            self.used_upper_bound |= not exact
            hazard = Fraction(covered, 1 << r)
            self.transitions += 1
            result = (1 - hazard) * self.survival(node.child, new_shadow)
        elif isinstance(node, Observe):
            result = self._observe(node, shadow)
        else:
            raise TypeError(node)
        if self.transitions > self.max_transitions:
            raise ResourceLimitError("certificate transition limit exceeded")
        self._cache[key] = result
        return result

    def _observe(self, node: Observe, shadow: tuple[int, ...]) -> Fraction:
        d = self.protocol.dimension
        m = len(node.rows)
        if self.method == "branch":
            charged = extend_basis(shadow, node.rows, d)
            return min(self.survival(child, charged) for child in node.children)
        if self.method == "full":
            charged = extend_basis(shadow, node.rows, d)
            values = [self.survival(child, charged) for child in node.children]
            best = None
            for w in image_points_fast(node.rows, d):
                val = sum((channel_prob(o, w, m, node.eta) * values[o]
                           for o in range(1 << m)), Fraction(0))
                best = val if best is None or val < best else best
            return best if best is not None else Fraction(1)

        rho = abs(1 - 2 * node.eta)
        complement_all = (1 << m) - 1 if node.eta > Fraction(1, 2) else 0
        signal_values = image_points_fast(node.rows, d)
        g = {w: Fraction(0) for w in signal_values}
        separate_total = Fraction(0)

        for mask in range(1 << m):
            flagged = tuple(j for j in range(m) if (mask >> j) & 1)
            unflagged_count = m - len(flagged)
            p_flag = rho ** len(flagged) * (1 - rho) ** unflagged_count
            if p_flag == 0:
                continue
            selected_rows = tuple(node.rows[j] for j in flagged)
            s_i = extend_basis(shadow, selected_rows, d)
            child_values = [self.survival(child, s_i) for child in node.children]
            self.transitions += len(child_values)
            feasible_v = image_points_fast(selected_rows, d)
            costs: dict[int, Fraction] = {}
            projected_complement = 0
            for idx, j in enumerate(flagged):
                if (complement_all >> j) & 1:
                    projected_complement |= 1 << idx
            for v in feasible_v:
                cost = Fraction(0)
                for u in range(1 << unflagged_count):
                    o = _insert_bits(v, u, flagged, m, complement_all)
                    cost += child_values[o]
                costs[v] = cost / (1 << unflagged_count)
            if self.method == "flag":
                separate_total += p_flag * min(costs.values())
            else:
                for w in signal_values:
                    projected = 0
                    for idx, j in enumerate(flagged):
                        projected |= ((w >> j) & 1) << idx
                    # _insert_bits applies complements; costs are keyed by the pre-complement signal.
                    g[w] += p_flag * costs[projected]

        if self.method == "flag":
            return separate_total
        if self.method == "coherent":
            return min(g.values())
        # Affine-fiber coset averaging.
        ker_s = nullspace_basis(shadow, d)
        ds_basis = image_basis(node.rows, ker_s, d)
        im_basis = image_basis(node.rows, tuple(1 << j for j in range(d)), d)
        partition = cosets(ds_basis, im_basis, m)
        return min(sum((g[w] for w in c), Fraction(0)) / len(c) for c in partition)

    def reference_risk(self) -> Fraction:
        return 1 - self.survival(self.protocol.root, ())

    def transferred_risk(self) -> Fraction:
        reference = self.reference_risk()
        factor = 1 << (self.protocol.dimension - self.protocol.min_entropy)
        return min(Fraction(1), factor * reference)


def evaluate_all(protocol: Protocol) -> dict[str, Fraction]:
    return {method: CertificateEvaluator(protocol, method).transferred_risk() for method in METHODS}
