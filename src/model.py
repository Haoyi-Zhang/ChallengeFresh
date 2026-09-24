"""Validated finite protocol model and JSON parser."""
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


def _fraction(value: Any) -> Fraction:
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    if isinstance(value, list) and len(value) == 2:
        return Fraction(int(value[0]), int(value[1]))
    raise ValueError(f"invalid rational {value!r}")


def _parse_node(raw: Any, d: int, state: dict[str, int], depth: int) -> Node:
    if depth > 32:
        raise ValueError("protocol depth exceeds 32")
    if not isinstance(raw, dict):
        raise ValueError("node must be an object")
    state["nodes"] += 1
    if state["nodes"] > 256:
        raise ValueError("protocol has more than 256 nodes")
    kind = raw.get("type")
    if kind == "stop":
        if set(raw) != {"type"}:
            raise ValueError("unknown stop-node key")
        return Stop()
    if kind == "epoch":
        allowed = {"type", "rows", "radius", "guesses", "next"}
        if set(raw) - allowed:
            raise ValueError("unknown epoch-node key")
        rows = tuple(int(x) for x in raw.get("rows", ()))
        if len(rows) > 256:
            raise ValueError("epoch has too many rows")
        if any(x < 0 or x >= (1 << d) for x in rows):
            raise ValueError("epoch row outside latent dimension")
        radius = int(raw.get("radius", -1))
        guesses = int(raw.get("guesses", 0))
        if radius < 0 or radius > len(rows):
            raise ValueError("invalid epoch radius")
        if guesses < 1 or guesses > 64:
            raise ValueError("invalid epoch guess count")
        return Epoch(rows, radius, guesses, _parse_node(raw["next"], d, state, depth + 1))
    if kind == "observe":
        allowed = {"type", "rows", "eta", "children"}
        if set(raw) - allowed:
            raise ValueError("unknown observation-node key")
        rows = tuple(int(x) for x in raw.get("rows", ()))
        if len(rows) > 4:
            raise ValueError("observation width exceeds four")
        if any(x < 0 or x >= (1 << d) for x in rows):
            raise ValueError("observation row outside latent dimension")
        eta = _fraction(raw.get("eta"))
        if eta < 0 or eta > 1:
            raise ValueError("BSC crossover must lie in [0,1]")
        children_raw = raw.get("children")
        if not isinstance(children_raw, list) or len(children_raw) != (1 << len(rows)):
            raise ValueError("observation child count mismatch")
        children = tuple(_parse_node(x, d, state, depth + 1) for x in children_raw)
        return Observe(rows, eta, children)
    raise ValueError(f"unknown node type {kind!r}")


def parse_protocol(raw: dict[str, Any]) -> Protocol:
    allowed = {"name", "dimension", "min_entropy", "prior", "root"}
    if set(raw) - allowed:
        raise ValueError("unknown top-level key")
    d = int(raw.get("dimension", -1))
    if d < 0 or d > 256:
        raise ValueError("dimension must be in [0,256]")
    k = int(raw.get("min_entropy", d))
    if k < 0 or k > d:
        raise ValueError("min_entropy must be in [0,d]")
    prior_raw = raw.get("prior")
    prior = None
    if prior_raw is not None:
        if d > 12:
            raise ValueError("explicit prior dimension too large")
        if not isinstance(prior_raw, list) or len(prior_raw) != (1 << d):
            raise ValueError("prior length mismatch")
        prior = tuple(_fraction(x) for x in prior_raw)
        if any(x < 0 for x in prior) or sum(prior) != 1:
            raise ValueError("prior must be a probability distribution")
        if max(prior, default=Fraction(0)) > Fraction(1, 1 << k):
            raise ValueError("prior violates declared point-probability cap")
    root = _parse_node(raw["root"], d, {"nodes": 0}, 0)
    return Protocol(d, k, root, prior, str(raw.get("name", "unnamed")))


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
        return {"type": "epoch", "rows": list(node.rows), "radius": node.radius,
                "guesses": node.guesses, "next": to_jsonable(node.child)}
    return {"type": "observe", "rows": list(node.rows), "eta": str(node.eta),
            "children": [to_jsonable(x) for x in node.children]}
