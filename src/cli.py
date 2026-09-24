#!/usr/bin/env python3
"""Evaluate one declared protocol JSON file."""
from __future__ import annotations

import argparse
import json
import sys

from certificate import CertificateEvaluator, METHODS
from model import load_protocol
from oracle import PosteriorOracle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("--method", choices=METHODS, default="coset")
    parser.add_argument("--oracle", action="store_true")
    args = parser.parse_args()
    try:
        protocol = load_protocol(args.model)
        evaluator = CertificateEvaluator(protocol, args.method)
        output = {
            "name": protocol.name,
            "method": args.method,
            "reference_risk": str(evaluator.reference_risk()),
            "issued_risk": str(evaluator.transferred_risk()),
            "coverage_mode": "upper_bound" if evaluator.used_upper_bound else "exact",
            "states": evaluator.states,
            "transitions": evaluator.transitions,
        }
        if args.oracle:
            oracle = PosteriorOracle(protocol)
            output["oracle_risk"] = str(oracle.risk())
            output["oracle_states"] = oracle.states
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # fail closed for a command-line checker
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
