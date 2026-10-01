"""Validated finite protocol model and strict JSON parser."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Stop:
    kind: str = "stop"


@dataclass(frozen=True)
class Epoch:
    rows: tuple[int, ...]
    radius: int
    guesses: int
    child: "Node"
    kind: str = "epoch"


@dataclass(frozen=True)
class Observe:
    rows: tuple[int, ...]
    eta: Fraction
    children: tuple["Node", ...]
    kind: str = "observe"


Node = Stop | Epoch | Observe


@dataclass(frozen=True)
class Protocol:
    dimension: int
    min_entropy: int
    root: Node
    prior: tuple[Fraction, ...] | None = None
    name: str = "unnamed"

    @property
    def entropy_deficit(self) -> int:
        return self.dimension - self.min_entropy


def _require_int(value: Any, field: str) -> int:
    """Accept an actual JSON integer, never bool or a coercible float/string."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _require_rows(value: Any, field: str, d: int, max_rows: int) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array of integers")
    if len(value) > max_rows:
        raise ValueError(f"{field} has too many rows")
    rows = tuple(_require_int(x, f"{field}[{i}]") for i, x in enumerate(value))
    if any(x < 0 or x >= (1 << d) for x in rows):
        raise ValueError(f"{field} contains a row outside latent dimension")
    return rows


def _fraction(value: Any, field: str = "rational") -> Fraction:
    """Parse exact rational JSON forms without lossy numeric coercion.

    Accepted forms are an integer, a Fraction-compatible string such as
    ``"1/4"``, or a two-integer JSON array ``[numerator, denominator]``.
    Booleans and floats are rejected even though Python can coerce them.
    """
    if isinstance(value, bool):
        raise ValueError(f"{field} must not be boolean")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"invalid {field} {value!r}") from exc
    if isinstance(value, list):
        if len(value) != 2:
            raise ValueError(f"{field} pair must contain exactly two integers")
        numerator = _require_int(value[0], f"{field}[0]")
        denominator = _require_int(value[1], f"{field}[1]")
        if denominator == 0:
            raise ValueError(f"{field} denominator must be nonzero")
        return Fraction(numerator, denominator)
    raise ValueError(f"invalid {field} {value!r}")


def _parse_node(raw: Any, d: int, state: dict[str, int], depth: int, path: str) -> Node:
    if depth > 32:
        raise ValueError("protocol depth exceeds 32")
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be an object")
    state["nodes"] += 1
    if state["nodes"] > 256:
        raise ValueError("protocol has more than 256 nodes")
    kind = raw.get("type")
    if kind == "stop":
        if set(raw) != {"type"}:
            raise ValueError(f"{path}: unknown stop-node key")
        return Stop()
    if kind == "epoch":
        required = {"type", "rows", "radius", "guesses", "next"}
        if set(raw) != required:
            missing = sorted(required - set(raw))
            extra = sorted(set(raw) - required)
            raise ValueError(f"{path}: epoch keys mismatch; missing={missing}, extra={extra}")
        rows = _require_rows(raw["rows"], f"{path}.rows", d, 256)
        radius = _require_int(raw["radius"], f"{path}.radius")
        guesses = _require_int(raw["guesses"], f"{path}.guesses")
        if radius < 0 or radius > len(rows):
            raise ValueError(f"{path}: invalid epoch radius")
        if guesses < 1 or guesses > 64:
            raise ValueError(f"{path}: invalid epoch guess count")
        return Epoch(
            rows,
            radius,
            guesses,
            _parse_node(raw["next"], d, state, depth + 1, f"{path}.next"),
        )
    if kind == "observe":
        required = {"type", "rows", "eta", "children"}
        if set(raw) != required:
            missing = sorted(required - set(raw))
            extra = sorted(set(raw) - required)
            raise ValueError(f"{path}: observation keys mismatch; missing={missing}, extra={extra}")
        rows = _require_rows(raw["rows"], f"{path}.rows", d, 4)
        eta = _fraction(raw["eta"], f"{path}.eta")
        if eta < 0 or eta > 1:
            raise ValueError(f"{path}: BSC crossover must lie in [0,1]")
        children_raw = raw["children"]
        if not isinstance(children_raw, list) or len(children_raw) != (1 << len(rows)):
            raise ValueError(f"{path}: observation child count mismatch")
        children = tuple(
            _parse_node(x, d, state, depth + 1, f"{path}.children[{i}]")
            for i, x in enumerate(children_raw)
        )
        return Observe(rows, eta, children)
    raise ValueError(f"{path}: unknown node type {kind!r}")


def parse_protocol(raw: dict[str, Any]) -> Protocol:
    if not isinstance(raw, dict):
        raise ValueError("protocol must be an object")
    allowed = {"name", "dimension", "min_entropy", "prior", "root"}
    if set(raw) - allowed:
        raise ValueError(f"unknown top-level key(s): {sorted(set(raw) - allowed)}")
    for required in ("dimension", "min_entropy", "root"):
        if required not in raw:
            raise ValueError(f"missing required top-level field {required!r}")

    d = _require_int(raw["dimension"], "dimension")
    if d < 0 or d > 256:
        raise ValueError("dimension must be in [0,256]")
    k = _require_int(raw["min_entropy"], "min_entropy")
    if k < 0 or k > d:
        raise ValueError("min_entropy must be in [0,d]")

    name_raw = raw.get("name", "unnamed")
    if not isinstance(name_raw, str):
        raise ValueError("name must be a string")

    prior_raw = raw.get("prior")
    prior = None
    if prior_raw is not None:
        if d > 12:
            raise ValueError("explicit prior dimension too large")
        if not isinstance(prior_raw, list) or len(prior_raw) != (1 << d):
            raise ValueError("prior length mismatch")
        prior = tuple(_fraction(x, f"prior[{i}]") for i, x in enumerate(prior_raw))
        if any(x < 0 for x in prior) or sum(prior) != 1:
            raise ValueError("prior must be a probability distribution")
        if max(prior, default=Fraction(0)) > Fraction(1, 1 << k):
            raise ValueError("prior violates declared point-probability cap")

    root = _parse_node(raw["root"], d, {"nodes": 0}, 0, "root")
    return Protocol(d, k, root, prior, name_raw)


def load_protocol(path: str | Path) -> Protocol:
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise ValueError("protocol file must contain an object")
    return parse_protocol(raw)


def to_jsonable(node: Node) -> dict[str, Any]:
    if isinstance(node, Stop):
        return {"type": "stop"}
    if isinstance(node, Epoch):
        return {
            "type": "epoch",
            "rows": list(node.rows),
            "radius": node.radius,
            "guesses": node.guesses,
            "next": to_jsonable(node.child),
        }
    return {
        "type": "observe",
        "rows": list(node.rows),
        "eta": str(node.eta),
        "children": [to_jsonable(x) for x in node.children],
    }
