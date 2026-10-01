#!/usr/bin/env python3
"""Evaluate one declared protocol JSON file."""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from typing import Any

from certificate import METHODS, evaluate_complete, source_premises
from model import load_protocol
from oracle import PosteriorOracle


def _json_fraction_tree(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_fraction_tree(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_fraction_tree(item) for item in value]
    # Fractions are deliberately rendered exactly; ordinary ints/strings pass.
    if isinstance(value, Fraction):
        return str(value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Issue the minimum of all implemented complete sound bounds. "
            "--method adds one diagnostic view without changing the issued bound."
        )
    )
    parser.add_argument("model")
    parser.add_argument("--method", choices=METHODS,
                        help="show one method as a diagnostic; issuance still uses all complete bounds")
    parser.add_argument("--trace", action="store_true",
                        help="include deterministic evaluated node-state traces for all methods")
    parser.add_argument("--oracle", action="store_true",
                        help="also run the bounded exact posterior oracle when supported")
    args = parser.parse_args()
    try:
        protocol = load_protocol(args.model)
        complete = evaluate_complete(protocol, collect_trace=args.trace)
        output: dict[str, Any] = {
            "name": protocol.name,
            # Keep the mathematical symbols explicit at the JSON root.
            "d": protocol.dimension,
            "k": protocol.min_entropy,
            "delta": protocol.entropy_deficit,
            "source_premises": source_premises(protocol),
            "issued_risk": complete["issued_risk"],
            "issued_methods": complete["issued_methods"],
            "issued_coverage_mode": complete["coverage_mode"],
            "bounds": complete["bounds"],
        }
        if args.method:
            output["diagnostic"] = {
                "method": args.method,
                **complete["bounds"][args.method],
                "note": "diagnostic selection does not replace the issued minimum",
            }
        if args.trace:
            output["trace"] = {
                method: complete["evaluators"][method].trace_records()
                for method in METHODS
            }
        if args.oracle:
            oracle = PosteriorOracle(protocol)
            output["oracle_risk"] = oracle.risk()
            output["oracle_states"] = oracle.states
        print(json.dumps(_json_fraction_tree(output), indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # fail closed for a command-line checker
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
