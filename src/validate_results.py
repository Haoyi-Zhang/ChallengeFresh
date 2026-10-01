#!/usr/bin/env python3
"""Recompute retained-result invariants from raw numeric fields.

The validator never accepts a stored success flag on trust: every ``holds``,
``equal``, protocol soundness/exactness/improvement flag, and exact-domain
hierarchy flag is recomputed from the accompanying raw values.
"""
from __future__ import annotations

import argparse
import csv
import json
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Iterable

from certificate import METHODS
from coverage import ball_volume
from certificate import evaluate_complete
from model import Observe, Protocol
from oracle import PosteriorOracle
from families import fair_public_bit_path_budget, two_row_map

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "results"


def rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fraction(value: str, context: str) -> Fraction:
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise AssertionError(f"{context}: invalid rational {value!r}") from exc


def integer(value: str, context: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise AssertionError(f"{context}: invalid integer {value!r}") from exc
    require(str(parsed) == value or (value.startswith("-") and str(parsed) == value),
            f"{context}: noncanonical integer {value!r}")
    return parsed


def flag(row: dict[str, str], name: str, expected: bool, context: str) -> None:
    require(name in row, f"{context}: missing flag {name}")
    require(row[name] in {"0", "1"}, f"{context}: malformed flag {name}={row[name]!r}")
    require(int(row[name]) == int(expected),
            f"{context}: stored {name}={row[name]} disagrees with recomputed {int(expected)}")


def validate_coverage(results: Path) -> dict[str, int]:
    coverage = results / "coverage"
    expected_counts = {
        "profile.csv": 1020,
        "direct.csv": 105,
        "subspaces.csv": 7989,
        "log_concavity.csv": 273,
        "balanced_transfers.csv": 5460,
        "cosets.csv": 18265,
    }
    loaded: dict[str, list[dict[str, str]]] = {}
    for name, expected in expected_counts.items():
        data = list(rows(coverage / name))
        require(len(data) == expected, f"{name}: expected {expected}, got {len(data)}")
        loaded[name] = data

    direct = loaded["direct.csv"]
    for index, row in enumerate(direct, 2):
        context = f"direct.csv:{index}"
        direct_value = integer(row["direct"], context)
        profile_value = integer(row["profile"], context)
        flag(row, "equal", direct_value == profile_value, context)
        flag(row, "exact", True, context)
    require(sum(integer(row["center_sets_visited"], "direct.csv") for row in direct) == 47243,
            "direct center-set count mismatch")

    subspaces = loaded["subspaces.csv"]
    for index, row in enumerate(subspaces, 2):
        context = f"subspaces.csv:{index}"
        actual = integer(row["code_coverage"], context)
        worst = integer(row["worst_rank_coverage"], context)
        flag(row, "holds", actual <= worst, context)
    distinct_subspaces = {(row["ambient"], row["subspace_id"]) for row in subspaces}
    require(len(distinct_subspaces) == 465, "subspace count mismatch")

    log_rows = loaded["log_concavity.csv"]
    for index, row in enumerate(log_rows, 2):
        context = f"log_concavity.csv:{index}"
        left = fraction(row["left"], context)
        right = fraction(row["right"], context)
        flag(row, "holds", left >= right, context)

    transfers = loaded["balanced_transfers.csv"]
    boundary_seen: dict[int, Fraction] = {}
    for index, row in enumerate(transfers, 2):
        context = f"balanced_transfers.csv:{index}"
        t = integer(row["radius"], context)
        a = integer(row["small"], context)
        b = integer(row["large"], context)
        balanced = fraction(row["balanced"], context)
        unbalanced = fraction(row["unbalanced"], context)
        is_boundary = row["boundary"] == "1"
        require(row["boundary"] in {"0", "1"}, f"{context}: malformed boundary flag")
        if is_boundary:
            require((a, b) == (t, t + 2), f"{context}: wrong boundary indices")
            expected_balanced = Fraction(1, 1 << (2 * (t + 1)))
            require(balanced == expected_balanced,
                    f"{context}: balanced boundary {balanced} != {expected_balanced}")
            require(unbalanced == 0, f"{context}: unbalanced boundary must be zero")
            boundary_seen[t] = balanced
        else:
            require(a >= t + 1 and b >= a + 2, f"{context}: outside stated transfer domain")
            fa = Fraction((1 << a) - ball_volume(a, t), 1 << a)
            fb = Fraction((1 << b) - ball_volume(b, t), 1 << b)
            fan = Fraction((1 << (a + 1)) - ball_volume(a + 1, t), 1 << (a + 1))
            fbn = Fraction((1 << (b - 1)) - ball_volume(b - 1, t), 1 << (b - 1))
            require(balanced == fan * fbn, f"{context}: balanced value not regenerated by formula")
            require(unbalanced == fa * fb, f"{context}: unbalanced value not regenerated by formula")
        flag(row, "holds", balanced >= unbalanced, context)
    require(boundary_seen == {
        0: Fraction(1, 4),
        1: Fraction(1, 16),
        2: Fraction(1, 64),
        3: Fraction(1, 256),
    }, "balanced boundary rows mismatch")

    coset_rows = loaded["cosets.csv"]
    for index, row in enumerate(coset_rows, 2):
        context = f"cosets.csv:{index}"
        flag(row, "equal", row["computed"] == row["direct"], context)

    profile = loaded["profile.csv"]
    unique_chunks: dict[tuple[str, str], tuple[int, int]] = {}
    for row in profile:
        unique_chunks[(row["q"], row["rank"])] = (
            integer(row["profiles_for_rank"], "profile.csv"),
            integer(row["weight_vectors_for_rank"], "profile.csv"),
        )
    require(len(unique_chunks) == 84, "profile chunk count mismatch")
    require(sum(value[0] for value in unique_chunks.values()) == 33695,
            "profile visit count mismatch")
    require(sum(value[1] for value in unique_chunks.values()) == 11274571,
            "weight-vector count mismatch")

    return {
        "coverage_entries": len(profile),
        "profile_chunks": len(unique_chunks),
        "profiles_visited": sum(value[0] for value in unique_chunks.values()),
        "weight_vectors_visited": sum(value[1] for value in unique_chunks.values()),
        "direct_equalities": len(direct),
        "direct_center_sets_visited": 47243,
        "subspaces": len(distinct_subspaces),
        "subspace_inequalities": len(subspaces),
        "log_concavity_inequalities": len(log_rows),
        "balanced_transfer_inequalities": len(transfers),
        "signal_coset_partitions": len(coset_rows),
    }


def validate_protocol_row(row: dict[str, str], context: str, *, exact_domain: bool) -> dict[str, Fraction | bool]:
    values = {method: fraction(row[method], context) for method in METHODS}
    oracle = fraction(row["oracle"], context)
    issued = fraction(row["issued"], context)
    for name, value in (*values.items(), ("oracle", oracle), ("issued", issued)):
        require(Fraction(0) <= value <= Fraction(1),
                f"{context}: {name} probability outside [0,1]: {value}")
    expected_issued = min(values.values())
    require(issued == expected_issued,
            f"{context}: issued={issued} is not min complete bound {expected_issued}")
    expected_methods = ";".join(method for method in METHODS if values[method] == expected_issued)
    require(row["issued_methods"] == expected_methods,
            f"{context}: issued method set mismatch")

    expected_mode = "exact" if exact_domain else "fallback"
    require(row["coverage_mode"] == expected_mode,
            f"{context}: stored coverage mode {row['coverage_mode']!r} disagrees with declared family domain {expected_mode!r}")
    applicability = exact_domain
    flag(row, "hierarchy_applicable", applicability, context)
    hierarchy = (
        values["coset"] <= values["coherent"]
        <= min(values["flag"], values["full"])
        <= values["branch"]
    )
    flag(row, "hierarchy_holds", hierarchy, context)
    if applicability:
        require(hierarchy, f"{context}: exact-domain hierarchy violation")

    sound = issued >= oracle
    exact = issued == oracle
    improves_full = issued < values["full"]
    improves_simple = issued < min(values["full"], values["flag"])
    flag(row, "sound", sound, context)
    flag(row, "exact", exact, context)
    flag(row, "improves_full", improves_full, context)
    flag(row, "improves_simple_min", improves_simple, context)
    require(sound, f"{context}: issued certificate below exact oracle")
    return {
        "issued": issued,
        "oracle": oracle,
        "exact": exact,
        "improves_full": improves_full,
        "improves_simple_min": improves_simple,
    }


def validate_two_epoch_domain(results: Path, data: list[dict[str, str]]) -> None:
    path = results / "protocols" / "two_epoch_domain.json"
    domain = json.loads(path.read_text(encoding="utf-8"))
    require(domain["family"] == "two_epoch", "two-epoch metadata family mismatch")
    require(domain["latent_dimension"] == 2, "two-epoch metadata must state d=2")
    require(domain["stages"] == 2, "two-epoch metadata stage count mismatch")
    require(domain["map_definition"] == "two_row_map(i)=(i & 3, (i >> 2) & 3)",
            "two-epoch map definition mismatch")
    expected_maps = [{"index": i, "rows": list(two_row_map(i))} for i in range(16)]
    require(domain["maps"] == expected_maps, "two-epoch map table mismatch")
    require(domain["radii"] == [0, 1] and domain["guess_counts"] == [1, 2],
            "two-epoch radius/guess domain mismatch")
    require(domain["expected_models"] == 4096 and domain["count_formula"] == "16^2 * 2^4",
            "two-epoch count metadata mismatch")

    actual = {
        (
            integer(row["map1"], "two_epoch.csv"),
            integer(row["radius1"], "two_epoch.csv"),
            integer(row["guesses1"], "two_epoch.csv"),
            integer(row["map2"], "two_epoch.csv"),
            integer(row["radius2"], "two_epoch.csv"),
            integer(row["guesses2"], "two_epoch.csv"),
        )
        for row in data
    }
    expected = set(product(range(16), (0, 1), (1, 2), range(16), (0, 1), (1, 2)))
    require(actual == expected, "two-epoch CSV is not the complete declared d=2 two-row domain")


def validate_path_budget_witness(results: Path) -> None:
    record = json.loads((results / "cases" / "path_budget_witness.json").read_text(encoding="utf-8"))
    witness = fair_public_bit_path_budget()
    require(record["case"] == witness.name, "path witness name mismatch")
    require(isinstance(witness.root, Observe), "path witness root must be an observation")

    exact_branch_risks: list[Fraction] = []
    issued_branch_risks: list[Fraction] = []
    for branch_index, child in enumerate(witness.root.children):
        branch = Protocol(
            witness.dimension, witness.min_entropy, child, witness.prior,
            f"{witness.name}-branch-{branch_index}",
        )
        exact_branch_risks.append(PosteriorOracle(branch).risk())
        issued_branch_risks.append(evaluate_complete(branch)["issued_risk"])

    stored_exact = [fraction(value, "path_budget_witness.json")
                    for value in record["conditional_path_risks"]]
    stored_issued = [fraction(value, "path_budget_witness.json")
                     for value in record["conditional_path_issued"]]
    require(stored_exact == exact_branch_risks == [Fraction(1, 4), Fraction(1, 2)],
            "path witness exact branch risks mismatch")
    require(stored_issued == issued_branch_risks == exact_branch_risks,
            "path witness branch certificates mismatch")

    exact_recursive = PosteriorOracle(witness).risk()
    issued_recursive = evaluate_complete(witness)["issued_risk"]
    require(fraction(record["exact_recursive_risk"], "path_budget_witness.json")
            == exact_recursive == Fraction(3, 8),
            "path witness recursion must be 3/8")
    require(fraction(record["issued_risk"], "path_budget_witness.json")
            == issued_recursive == Fraction(3, 8),
            "path witness issued risk must be 3/8")
    require(fraction(record["uniform_fixed_stage_bound"], "path_budget_witness.json")
            == max(exact_branch_risks) == Fraction(1, 2),
            "path witness uniform bound mismatch")
    require(fraction(record["pathwise_admission_alpha"], "path_budget_witness.json")
            == Fraction(1, 2), "path witness admission budget mismatch")


def validate_protocols(results: Path) -> dict[str, int | str]:
    protocols = results / "protocols"
    adaptive_paths = [protocols / f"noisy_adaptive_obs{i}.csv" for i in range(4)]
    adaptive = [row for path in adaptive_paths for row in rows(path)]
    two_row = list(rows(protocols / "noisy_two_row.csv"))
    noisy = adaptive + two_row
    require(len(adaptive) == 81920, "adaptive family size mismatch")
    require(len(two_row) == 5120, "two-row family size mismatch")
    require(len(noisy) == 87040, "noisy family size mismatch")
    noisy_metrics = [validate_protocol_row(row, f"noisy:{index}", exact_domain=True)
                     for index, row in enumerate(noisy, 2)]

    two_epoch = list(rows(protocols / "two_epoch.csv"))
    require(len(two_epoch) == 4096, "two-epoch family size mismatch")
    validate_two_epoch_domain(results, two_epoch)
    two_metrics = [validate_protocol_row(row, f"two_epoch.csv:{index}", exact_domain=True)
                   for index, row in enumerate(two_epoch, 2)]
    max_gap = max(metric["issued"] - metric["oracle"] for metric in two_metrics)
    require(max_gap == Fraction(1, 2), "two-epoch maximum gap mismatch")

    post = list(rows(protocols / "post_rejection.csv"))
    require(len(post) == 5120, "post-rejection family size mismatch")
    post_metrics = [validate_protocol_row(row, f"post_rejection.csv:{index}", exact_domain=True)
                    for index, row in enumerate(post, 2)]
    require(all(metric["exact"] for metric in post_metrics), "post-rejection mismatch")

    cases = list(rows(results / "cases" / "named_cases.csv"))
    require(len(cases) == 14, "named-case count mismatch")
    for index, row in enumerate(cases, 2):
        validate_protocol_row(row, f"named_cases.csv:{index}", exact_domain=True)
    validate_path_budget_witness(results)

    noise_sweep = list(rows(results / "sensitivity" / "noise_sweep.csv"))
    require(len(noise_sweep) == 17, "noise sweep size mismatch")
    for index, row in enumerate(noise_sweep, 2):
        context = f"noise_sweep.csv:{index}"
        coset = fraction(row["coset"], context)
        oracle = fraction(row["oracle"], context)
        flag(row, "sound", coset >= oracle, context)
        flag(row, "exact", coset == oracle, context)
        require(coset >= oracle, f"{context}: coset below oracle")

    return {
        "two_epoch_models": len(two_epoch),
        "two_epoch_exact": sum(int(metric["exact"]) for metric in two_metrics),
        "two_epoch_conservative": sum(not bool(metric["exact"]) for metric in two_metrics),
        "two_epoch_max_gap": "1/2",
        "noisy_models": len(noisy),
        "noisy_exact": sum(int(metric["exact"]) for metric in noisy_metrics),
        "noisy_conservative": sum(not bool(metric["exact"]) for metric in noisy_metrics),
        "noisy_improves_full": sum(int(metric["improves_full"]) for metric in noisy_metrics),
        "noisy_improves_simple_min": sum(int(metric["improves_simple_min"]) for metric in noisy_metrics),
        "post_rejection_models": len(post),
        "post_rejection_exact": sum(int(metric["exact"]) for metric in post_metrics),
        "named_cases": len(cases),
        "path_budget_witnesses": 1,
        "noise_sweep_points": len(noise_sweep),
        "oracle_states_noisy": sum(integer(row["oracle_states"], "noisy") for row in noisy),
        "oracle_states_two_epoch": sum(integer(row["oracle_states"], "two_epoch") for row in two_epoch),
        "oracle_states_post_rejection": sum(integer(row["oracle_states"], "post") for row in post),
    }


def validate_results(results: Path = DEFAULT_RESULTS, write_summary: bool = True) -> dict[str, object]:
    results = Path(results)
    require(results.is_dir(), f"results directory not found: {results}")
    summary: dict[str, object] = {}
    summary.update(validate_coverage(results))
    summary.update(validate_protocols(results))
    summary["violations"] = 0
    if write_summary:
        (results / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--no-write-summary", action="store_true")
    args = parser.parse_args()
    summary = validate_results(args.results, write_summary=not args.no_write_summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
