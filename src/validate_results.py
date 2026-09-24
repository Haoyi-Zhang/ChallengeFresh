#!/usr/bin/env python3
"""Independent aggregation and invariant checks over retained CSV results."""
from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    summary: dict[str, object] = {}
    expected_coverage = {
        "profile.csv": 1020, "direct.csv": 105, "subspaces.csv": 7989,
        "log_concavity.csv": 273, "balanced_transfers.csv": 5460, "cosets.csv": 18265,
    }
    for name, expected in expected_coverage.items():
        data = list(rows(RESULTS / "coverage" / name))
        require(len(data) == expected, f"{name}: expected {expected}, got {len(data)}")
        key = "equal" if name in {"direct.csv", "cosets.csv"} else "holds"
        if name == "profile.csv":
            continue
        require(all(int(r[key]) == 1 for r in data), f"{name}: failed inequality/equality")
    direct = list(rows(RESULTS / "coverage" / "direct.csv"))
    require(sum(int(r["center_sets_visited"]) for r in direct) == 47243,
            "direct center-set count mismatch")
    profile = list(rows(RESULTS / "coverage" / "profile.csv"))
    # Count rank/retry chunks once.
    unique_chunks = {}
    for r in profile:
        unique_chunks[(r["q"], r["rank"])] = (int(r["profiles_for_rank"]),
                                                int(r["weight_vectors_for_rank"]))
    require(len(unique_chunks) == 84, "profile chunk count mismatch")
    require(sum(v[0] for v in unique_chunks.values()) == 33695, "profile visit count mismatch")
    require(sum(v[1] for v in unique_chunks.values()) == 11274571, "weight-vector count mismatch")

    adaptive_paths = [RESULTS / "protocols" / f"noisy_adaptive_obs{i}.csv" for i in range(4)]
    adaptive = [r for p in adaptive_paths for r in rows(p)]
    two_row = list(rows(RESULTS / "protocols" / "noisy_two_row.csv"))
    noisy = adaptive + two_row
    require(len(adaptive) == 81920, "adaptive family size mismatch")
    require(len(two_row) == 5120, "two-row family size mismatch")
    require(len(noisy) == 87040, "noisy family size mismatch")
    require(all(int(r["sound"]) == 1 for r in noisy), "noisy soundness violation")
    require(sum(int(r["exact"]) for r in noisy) == 86842, "noisy exact count mismatch")
    require(sum(int(r["improves_full"]) for r in noisy) == 31428,
            "noisy full-baseline improvement count mismatch")
    require(sum(int(r["improves_simple_min"]) for r in noisy) == 14976,
            "noisy simple-min improvement count mismatch")

    two_epoch = list(rows(RESULTS / "protocols" / "two_epoch.csv"))
    require(len(two_epoch) == 4096, "two-epoch family size mismatch")
    require(all(int(r["sound"]) == 1 for r in two_epoch), "two-epoch soundness violation")
    require(sum(int(r["exact"]) for r in two_epoch) == 3934, "two-epoch exact count mismatch")
    max_gap = max(Fraction(r["coset"]) - Fraction(r["oracle"]) for r in two_epoch)
    require(max_gap == Fraction(1, 2), "two-epoch maximum gap mismatch")

    post = list(rows(RESULTS / "protocols" / "post_rejection.csv"))
    require(len(post) == 5120, "post-rejection family size mismatch")
    require(all(int(r["sound"]) == 1 and int(r["exact"]) == 1 for r in post),
            "post-rejection mismatch")

    noise_sweep = list(rows(RESULTS / "sensitivity" / "noise_sweep.csv"))
    require(len(noise_sweep) == 17, "noise sweep size mismatch")
    require(all(int(r["sound"]) == 1 and int(r["exact"]) == 1 for r in noise_sweep),
            "noise sweep mismatch")
    cases = list(rows(RESULTS / "cases" / "named_cases.csv"))
    require(len(cases) == 14 and all(int(r["sound"]) == 1 for r in cases),
            "named-case mismatch")

    summary.update({
        "coverage_entries": 1020,
        "profile_chunks": 84,
        "profiles_visited": 33695,
        "weight_vectors_visited": 11274571,
        "direct_equalities": 105,
        "direct_center_sets_visited": 47243,
        "subspaces": 465,
        "subspace_inequalities": 7989,
        "log_concavity_inequalities": 273,
        "balanced_transfer_inequalities": 5460,
        "signal_coset_partitions": 18265,
        "two_epoch_models": 4096,
        "two_epoch_exact": 3934,
        "two_epoch_conservative": 162,
        "two_epoch_max_gap": "1/2",
        "noisy_models": 87040,
        "noisy_exact": 86842,
        "noisy_conservative": 198,
        "noisy_improves_full": 31428,
        "noisy_improves_simple_min": 14976,
        "post_rejection_models": 5120,
        "post_rejection_exact": 5120,
        "named_cases": 14,
        "noise_sweep_points": 17,
        "violations": 0,
        "oracle_states_noisy": sum(int(r["oracle_states"]) for r in noisy),
        "oracle_states_two_epoch": sum(int(r["oracle_states"]) for r in two_epoch),
        "oracle_states_post_rejection": sum(int(r["oracle_states"]) for r in post),
    })
    path = RESULTS / "summary.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
