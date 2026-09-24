"""Independent exact posterior oracle for small declared models."""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache

from certificate import channel_prob
from gf2 import apply
from model import Epoch, Node, Observe, Protocol, Stop


class OracleLimitError(RuntimeError):
    pass


class PosteriorOracle:
    def __init__(self, protocol: Protocol, max_states: int = 200_000):
        if protocol.dimension > 6:
            raise OracleLimitError("oracle dimension exceeds six")
        self.protocol = protocol
        self.max_states = max_states
        self.states = 0
        self._node_ids: dict[int, int] = {}
        self._next_id = 0
        self._cache: dict[tuple[int, tuple[Fraction, ...]], Fraction] = {}

    def _id(self, node: Node) -> int:
        key = id(node)
        if key not in self._node_ids:
            self._node_ids[key] = self._next_id
            self._next_id += 1
        return self._node_ids[key]

    def _solve(self, node: Node, masses: tuple[Fraction, ...]) -> Fraction:
        key = (self._id(node), masses)
        if key in self._cache:
            return self._cache[key]
        self.states += 1
        if self.states > self.max_states:
            raise OracleLimitError("oracle state limit exceeded")
        if isinstance(node, Stop):
            result = Fraction(0)
        elif isinstance(node, Observe):
            m = len(node.rows)
            result = Fraction(0)
            for o, child in enumerate(node.children):
                branch = tuple(mass * channel_prob(o, apply(node.rows, x), m, node.eta)
                               for x, mass in enumerate(masses))
                result += self._solve(child, branch)
        elif isinstance(node, Epoch):
            n = len(node.rows)
            if n > 4 or node.guesses > 4:
                raise OracleLimitError("oracle epoch width/retry limit exceeded")
            accept_masks: set[int] = set()
            for y in range(1 << n):
                mask = 0
                for x in range(1 << self.protocol.dimension):
                    if (apply(node.rows, x) ^ y).bit_count() <= node.radius:
                        mask |= 1 << x
                accept_masks.add(mask)

            @lru_cache(maxsize=None)
            def attempts(left: int, current: tuple[Fraction, ...]) -> Fraction:
                if left == 0 or not any(current):
                    return self._solve(node.child, current)
                best = Fraction(-1)
                for mask in accept_masks:
                    won = sum((mass for x, mass in enumerate(current) if (mask >> x) & 1), Fraction(0))
                    remain = tuple(Fraction(0) if (mask >> x) & 1 else mass
                                   for x, mass in enumerate(current))
                    val = won + attempts(left - 1, remain)
                    if val > best:
                        best = val
                return best

            result = attempts(node.guesses, masses)
        else:
            raise TypeError(node)
        self._cache[key] = result
        return result

    def risk(self) -> Fraction:
        n = 1 << self.protocol.dimension
        if self.protocol.prior is None:
            masses = tuple(Fraction(1, n) for _ in range(n))
        else:
            masses = self.protocol.prior
        return self._solve(self.protocol.root, masses)
