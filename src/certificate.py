"""Exact-rational affine-shadow certificate evaluators."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from coverage import max_coverage
from gf2 import (canonical_basis, cosets, extend_basis, image_basis,
                 image_points_fast, nullspace_basis)
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


def source_premises(protocol: Protocol) -> dict[str, Any]:
    """Machine-readable statement of premises supplied rather than verified."""
    return {
        "d": protocol.dimension,
        "k": protocol.min_entropy,
        "delta": protocol.entropy_deficit,
        "source_premise": (
            "explicit prior satisfying the declared point-probability cap"
            if protocol.prior is not None
            else "declared average conditional min-entropy lower bound"
        ),
        "response_model": "finite zero-offset affine maps over GF(2)",
        "verifier_model": "ideal trusted response; Hamming acceptance; accept/reject feedback only",
        "observation_model": "independent homogeneous BSC per observation node",
        "policy_model": "finite acyclic public-history tree with bounded retries",
        "externally_supplied": [
            "entropy premise",
            "affine-map conformance",
            "BSC independence and crossover",
            "trusted ideal response",
            "epoch discipline and finite stopping rule",
        ],
    }


class CertificateEvaluator:
    def __init__(self, protocol: Protocol, method: str = "coset", max_states: int = 20_000,
                 max_transitions: int = 200_000, collect_trace: bool = False):
        if method not in METHODS:
            raise ValueError(f"unknown method {method}")
        self.protocol = protocol
        self.method = method
        self.max_states = max_states
        self.max_transitions = max_transitions
        self.collect_trace = collect_trace
        self.states = 0
        self.transitions = 0
        self.used_upper_bound = False
        self._node_ids: dict[int, int] = {}
        self._next_id = 0
        self._cache: dict[tuple[int, tuple[int, ...]], Fraction] = {}
        self._paths_by_object: dict[int, set[str]] = {}
        self._trace: dict[tuple[int, tuple[int, ...]], dict[str, Any]] = {}
        self._index_paths(protocol.root, "root")

    def _index_paths(self, node: Node, path: str) -> None:
        self._paths_by_object.setdefault(id(node), set()).add(path)
        if isinstance(node, Epoch):
            self._index_paths(node.child, f"{path}.next")
        elif isinstance(node, Observe):
            for output, child in enumerate(node.children):
                self._index_paths(child, f"{path}.out[{output}]")

    def _id(self, node: Node) -> int:
        key = id(node)
        if key not in self._node_ids:
            self._node_ids[key] = self._next_id
            self._next_id += 1
        return self._node_ids[key]

    @property
    def coverage_mode(self) -> str:
        return "fallback" if self.used_upper_bound else "exact"

    def _record(self, node: Node, shadow: tuple[int, ...], result: Fraction,
                details: dict[str, Any] | None = None) -> None:
        if not self.collect_trace:
            return
        node_id = self._id(node)
        record: dict[str, Any] = {
            "method": self.method,
            "paths": sorted(self._paths_by_object.get(id(node), {f"node[{node_id}]"})),
            "node_type": node.kind,
            "shadow_basis": list(shadow),
            "survival": str(result),
            "risk": str(1 - result),
        }
        if details:
            record.update(details)
        self._trace[(node_id, shadow)] = record

    def trace_records(self) -> list[dict[str, Any]]:
        """Return deterministic evaluated node-state records for this method."""
        return sorted(
            self._trace.values(),
            key=lambda r: (r["paths"][0], tuple(r["shadow_basis"]), r["node_type"]),
        )

    def survival(self, node: Node, shadow: tuple[int, ...]) -> Fraction:
        shadow = canonical_basis(shadow, self.protocol.dimension)
        key = (self._id(node), shadow)
        if key in self._cache:
            return self._cache[key]
        self.states += 1
        if self.states > self.max_states:
            raise ResourceLimitError("certificate state limit exceeded")

        details: dict[str, Any] = {}
        if isinstance(node, Stop):
            result = Fraction(1)
        elif isinstance(node, Epoch):
            new_shadow = extend_basis(shadow, node.rows, self.protocol.dimension)
            residual_rank = len(new_shadow) - len(shadow)
            covered, exact = max_coverage(residual_rank, node.radius, node.guesses)
            self.used_upper_bound |= not exact
            hazard = Fraction(covered, 1 << residual_rank)
            self.transitions += 1
            result = (1 - hazard) * self.survival(node.child, new_shadow)
            details = {
                "rows": list(node.rows),
                "residual_rank": residual_rank,
                "radius": node.radius,
                "guesses": node.guesses,
                "coverage_count": covered,
                "cube_size": 1 << residual_rank,
                "local_hazard": str(hazard),
                "coverage_source": "exact-on-demand" if exact else "sound-union-fallback",
                "next_shadow_basis": list(new_shadow),
            }
        elif isinstance(node, Observe):
            result = self._observe(node, shadow)
            details = {
                "rows": list(node.rows),
                "eta": str(node.eta),
                "outputs": 1 << len(node.rows),
            }
        else:
            raise TypeError(node)

        if self.transitions > self.max_transitions:
            raise ResourceLimitError("certificate transition limit exceeded")
        self._cache[key] = result
        self._record(node, shadow, result, details)
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
                val = sum(
                    (channel_prob(o, w, m, node.eta) * values[o]
                     for o in range(1 << m)),
                    Fraction(0),
                )
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
        return min(sum((g[w] for w in coset), Fraction(0)) / len(coset)
                   for coset in partition)

    def reference_risk(self) -> Fraction:
        return 1 - self.survival(self.protocol.root, ())

    def transferred_risk(self) -> Fraction:
        reference = self.reference_risk()
        factor = 1 << self.protocol.entropy_deficit
        return min(Fraction(1), factor * reference)


def evaluate_all(protocol: Protocol) -> dict[str, Fraction]:
    """Backward-compatible exact risks for every complete method."""
    return {method: CertificateEvaluator(protocol, method).transferred_risk()
            for method in METHODS}


def evaluate_complete(protocol: Protocol, collect_trace: bool = False) -> dict[str, Any]:
    """Evaluate all complete sound methods and issue their minimum risk."""
    evaluators: dict[str, CertificateEvaluator] = {}
    bounds: dict[str, dict[str, Any]] = {}
    for method in METHODS:
        evaluator = CertificateEvaluator(protocol, method, collect_trace=collect_trace)
        transferred = evaluator.transferred_risk()
        evaluators[method] = evaluator
        bounds[method] = {
            "reference_risk": evaluator.reference_risk(),
            "transferred_risk": transferred,
            "coverage_mode": evaluator.coverage_mode,
            "states": evaluator.states,
            "transitions": evaluator.transitions,
        }
    issued_risk = min(item["transferred_risk"] for item in bounds.values())
    issued_methods = tuple(
        method for method in METHODS
        if bounds[method]["transferred_risk"] == issued_risk
    )
    issued_mode = (
        "exact"
        if all(bounds[method]["coverage_mode"] == "exact" for method in issued_methods)
        else "fallback"
    )
    return {
        "bounds": bounds,
        "issued_risk": issued_risk,
        "issued_methods": issued_methods,
        "coverage_mode": issued_mode,
        "evaluators": evaluators,
    }
