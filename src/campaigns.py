#!/usr/bin/env python3
"""Deterministic finite campaigns used by the paper."""
from __future__ import annotations

import argparse
import csv
import json
from fractions import Fraction
from math import comb
from pathlib import Path
import time

from certificate import CertificateEvaluator
from coverage import (ball_volume, code_max_coverage, direct_max_coverage,
                      exact_profile, max_coverage)
from families import (named_cases, noisy_adaptive, noisy_two_row, post_rejection,
                      running_example, two_epoch)
from gf2 import (all_subspaces, canonical_basis, cosets, fiber_partition,
                 image_basis, nullspace_basis, span_points)
from oracle import PosteriorOracle

ETAS = (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1))


def fstr(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def write_csv(path: Path, fieldnames: list[str], rows) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def basis_text(basis: tuple[int, ...]) -> str:
    return ";".join(str(x) for x in basis)


def campaign_coverage(out: Path) -> dict:
    summary: dict[str, int | float] = {}

    def profile_rows():
        for q in (1, 2, 3):
            ranks = range(25)
            for r in ranks:
                vals, witnesses, profiles, weights = exact_profile(r, q)
                for t, value in enumerate(vals):
                    yield {"q": q, "rank": r, "radius": t, "coverage": value,
                           "cube_size": 1 << r, "witness_profile": basis_text(witnesses[t]),
                           "profiles_for_rank": profiles, "weight_vectors_for_rank": weights}
        q = 4
        for r in range(9):
            vals, witnesses, profiles, weights = exact_profile(r, q)
            for t, value in enumerate(vals):
                yield {"q": q, "rank": r, "radius": t, "coverage": value,
                       "cube_size": 1 << r, "witness_profile": basis_text(witnesses[t]),
                       "profiles_for_rank": profiles, "weight_vectors_for_rank": weights}

    profile_path = out / "coverage" / "profile.csv"
    summary["coverage_entries"] = write_csv(profile_path,
        ["q", "rank", "radius", "coverage", "cube_size", "witness_profile",
         "profiles_for_rank", "weight_vectors_for_rank"], profile_rows())
    # Work totals count a rank/retry chunk once, not once per radius.
    profile_total = weight_total = chunks = 0
    for q in (1, 2, 3):
        for r in range(25):
            _, _, p, w = exact_profile(r, q); profile_total += p; weight_total += w; chunks += 1
    for r in range(9):
        _, _, p, w = exact_profile(r, 4); profile_total += p; weight_total += w; chunks += 1
    summary.update(profile_chunks=chunks, profiles_visited=profile_total,
                   weight_vectors_visited=weight_total)

    direct_visited = 0
    def direct_rows():
        nonlocal direct_visited
        for q in (1, 2, 3):
            ranks = range(7)
            for r in ranks:
                for t in range(r + 1):
                    direct, visited = direct_max_coverage(r, t, q)
                    prof, exact = max_coverage(r, t, q)
                    direct_visited += visited
                    yield {"q": q, "rank": r, "radius": t, "direct": direct,
                           "profile": prof, "equal": int(direct == prof),
                           "center_sets_visited": visited, "exact": int(exact)}
        q = 4
        for r in range(6):
            for t in range(r + 1):
                direct, visited = direct_max_coverage(r, t, q)
                prof, exact = max_coverage(r, t, q)
                direct_visited += visited
                yield {"q": q, "rank": r, "radius": t, "direct": direct,
                       "profile": prof, "equal": int(direct == prof),
                       "center_sets_visited": visited, "exact": int(exact)}
    summary["direct_equalities"] = write_csv(out / "coverage" / "direct.csv",
        ["q", "rank", "radius", "direct", "profile", "equal", "center_sets_visited", "exact"],
        direct_rows())
    summary["direct_center_sets_visited"] = direct_visited

    subspace_counts: dict[int, int] = {}
    def subspace_rows():
        for n in range(6):
            spaces = all_subspaces(n)
            subspace_counts[n] = len(spaces)
            for sid, b in enumerate(spaces):
                points = span_points(b, n)
                r = len(b)
                for t in range(n + 1):
                    for q in (1, 2, 3):
                        value = code_max_coverage(points, n, t, q)
                        worst, _ = max_coverage(r, t, q)
                        yield {"ambient": n, "subspace_id": sid, "basis": basis_text(b),
                               "rank": r, "radius": t, "q": q, "code_coverage": value,
                               "worst_rank_coverage": worst, "holds": int(value <= worst)}
    summary["subspace_inequalities"] = write_csv(out / "coverage" / "subspaces.csv",
        ["ambient", "subspace_id", "basis", "rank", "radius", "q", "code_coverage",
         "worst_rank_coverage", "holds"], subspace_rows())
    summary["subspaces_total"] = sum(subspace_counts.values())
    summary["subspaces_by_ambient"] = subspace_counts

    def log_rows():
        for t in range(21):
            for r in range(t + 1, 24):
                fm = Fraction((1 << (r - 1)) - ball_volume(r - 1, t), 1 << (r - 1))
                f0 = Fraction((1 << r) - ball_volume(r, t), 1 << r)
                fp = Fraction((1 << (r + 1)) - ball_volume(r + 1, t), 1 << (r + 1))
                yield {"radius": t, "rank": r, "left": fstr(f0 * f0),
                       "right": fstr(fm * fp), "holds": int(f0 * f0 >= fm * fp)}
    summary["log_concavity_inequalities"] = write_csv(out / "coverage" / "log_concavity.csv",
        ["radius", "rank", "left", "right", "holds"], log_rows())

    def transfer_rows():
        emitted = 0
        for t in range(34):
            for a in range(t + 1, 34):
                for b in range(a + 2, 34):
                    fa = Fraction((1 << a) - ball_volume(a, t), 1 << a)
                    fb = Fraction((1 << b) - ball_volume(b, t), 1 << b)
                    fan = Fraction((1 << (a + 1)) - ball_volume(a + 1, t), 1 << (a + 1))
                    fbn = Fraction((1 << (b - 1)) - ball_volume(b - 1, t), 1 << (b - 1))
                    emitted += 1
                    yield {"radius": t, "small": a, "large": b,
                           "balanced": fstr(fan * fbn), "unbalanced": fstr(fa * fb),
                           "holds": int(fan * fbn >= fa * fb), "boundary": 0}
        # Four explicit zero-survival boundary cases.
        for t in range(4):
            a, b = t, t + 2
            yield {"radius": t, "small": a, "large": b, "balanced": "0",
                   "unbalanced": "0", "holds": 1, "boundary": 1}
    summary["balanced_transfer_inequalities"] = write_csv(out / "coverage" / "balanced_transfers.csv",
        ["radius", "small", "large", "balanced", "unbalanced", "holds", "boundary"],
        transfer_rows())

    def coset_rows():
        for d in range(5):
            for sid, s in enumerate(all_subspaces(d)):
                ker = nullspace_basis(s, d)
                for a in range(1 << d):
                    for b in range(1 << d):
                        rows = (a, b)
                        ds = image_basis(rows, ker, d)
                        im = image_basis(rows, tuple(1 << j for j in range(d)), d)
                        computed = tuple(sorted(cosets(ds, im, 2)))
                        direct = fiber_partition(s, rows, d)
                        yield {"dimension": d, "shadow_id": sid, "shadow_basis": basis_text(s),
                               "row0": a, "row1": b, "computed": "|".join(basis_text(c) for c in computed),
                               "direct": "|".join(basis_text(c) for c in direct),
                               "equal": int(computed == direct)}
    summary["signal_coset_partitions"] = write_csv(out / "coverage" / "cosets.csv",
        ["dimension", "shadow_id", "shadow_basis", "row0", "row1", "computed", "direct", "equal"],
        coset_rows())

    return summary


def protocol_metrics(protocol) -> dict[str, str | int]:
    evals = {}
    for method in ("branch", "full", "flag", "coherent", "coset"):
        ev = CertificateEvaluator(protocol, method)
        evals[method] = ev.transferred_risk()
    oracle = PosteriorOracle(protocol)
    exact = oracle.risk()
    return {**{m: fstr(v) for m, v in evals.items()}, "oracle": fstr(exact),
            "sound": int(evals["coset"] >= exact), "exact": int(evals["coset"] == exact),
            "improves_full": int(evals["coset"] < evals["full"]),
            "improves_simple_min": int(evals["coset"] < min(evals["full"], evals["flag"])),
            "oracle_states": oracle.states}


def campaign_adaptive(out: Path, obs_row: int) -> dict:
    path = out / "protocols" / f"noisy_adaptive_obs{obs_row}.csv"
    fields = ["obs_row", "eta", "left_config", "right_config", "branch", "full", "flag",
              "coherent", "coset", "oracle", "sound", "exact", "improves_full",
              "improves_simple_min", "oracle_states"]
    def rows():
        for eta in ETAS:
            for left in range(64):
                for right in range(64):
                    yield {"obs_row": obs_row, "eta": fstr(eta), "left_config": left,
                           "right_config": right, **protocol_metrics(noisy_adaptive(obs_row, eta, left, right))}
    return {"models": write_csv(path, fields, rows())}


def campaign_additional(out: Path) -> dict:
    summary: dict[str, int] = {}
    fields_two = ["map1", "radius1", "guesses1", "map2", "radius2", "guesses2",
                  "branch", "full", "flag", "coherent", "coset", "oracle", "sound", "exact",
                  "improves_full", "improves_simple_min", "oracle_states"]
    def two_rows():
        for a1 in range(16):
            for a2 in range(16):
                for t1 in (0, 1):
                    for q1 in (1, 2):
                        for t2 in (0, 1):
                            for q2 in (1, 2):
                                yield {"map1": a1, "radius1": t1, "guesses1": q1,
                                       "map2": a2, "radius2": t2, "guesses2": q2,
                                       **protocol_metrics(two_epoch(a1, t1, q1, a2, t2, q2))}
    summary["two_epoch_models"] = write_csv(out / "protocols" / "two_epoch.csv", fields_two, two_rows())

    fields_n = ["obs_map", "eta", "config", "branch", "full", "flag", "coherent", "coset",
                "oracle", "sound", "exact", "improves_full", "improves_simple_min", "oracle_states"]
    def noisy_rows():
        for obs_map in range(16):
            for eta in ETAS:
                for cfg in range(64):
                    yield {"obs_map": obs_map, "eta": fstr(eta), "config": cfg,
                           **protocol_metrics(noisy_two_row(obs_map, eta, cfg))}
    summary["two_row_models"] = write_csv(out / "protocols" / "noisy_two_row.csv", fields_n, noisy_rows())

    fields_p = ["first_row", "obs_row", "eta", "left_config", "right_config", "branch", "full",
                "flag", "coherent", "coset", "oracle", "sound", "exact", "improves_full",
                "improves_simple_min", "oracle_states"]
    def post_rows():
        for first in range(4):
            for obs in range(4):
                for eta in ETAS:
                    for left in range(8):
                        for right in range(8):
                            yield {"first_row": first, "obs_row": obs, "eta": fstr(eta),
                                   "left_config": left, "right_config": right,
                                   **protocol_metrics(post_rejection(first, obs, eta, left, right))}
    summary["post_rejection_models"] = write_csv(out / "protocols" / "post_rejection.csv", fields_p, post_rows())
    return summary


def campaign_cases(out: Path) -> dict:
    fields = ["case", "branch", "full", "flag", "coherent", "coset", "oracle", "sound", "exact",
              "improves_full", "improves_simple_min", "oracle_states"]
    def rows():
        for protocol in named_cases():
            yield {"case": protocol.name, **protocol_metrics(protocol)}
    return {"named_cases": write_csv(out / "cases" / "named_cases.csv", fields, rows())}


def campaign_sensitivity(out: Path) -> dict:
    fields = ["eta", "full", "coset", "oracle", "sound", "exact"]
    def rows():
        for i in range(17):
            eta = Fraction(i, 16)
            p = running_example(eta)
            full = CertificateEvaluator(p, "full").transferred_risk()
            coset = CertificateEvaluator(p, "coset").transferred_risk()
            oracle = PosteriorOracle(p).risk()
            yield {"eta": fstr(eta), "full": fstr(full), "coset": fstr(coset),
                   "oracle": fstr(oracle), "sound": int(coset >= oracle),
                   "exact": int(coset == oracle)}
    count = write_csv(out / "sensitivity" / "noise_sweep.csv", fields, rows())
    # Coverage slice used by Figure 1.
    def crows():
        for r in range(13):
            exact, _ = max_coverage(r, 1, 3)
            union = min(1 << r, 3 * ball_volume(r, 1))
            yield {"rank": r, "exact": fstr(Fraction(exact, 1 << r)),
                   "union": fstr(Fraction(union, 1 << r))}
    ccount = write_csv(out / "sensitivity" / "coverage_slice.csv",
                       ["rank", "exact", "union"], crows())
    return {"noise_points": count, "coverage_points": ccount}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", choices=("coverage", "adaptive", "additional", "cases", "sensitivity"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--obs-row", type=int)
    args = parser.parse_args()
    out = Path(args.output)
    start = time.process_time()
    wall = time.perf_counter()
    if args.campaign == "coverage": result = campaign_coverage(out)
    elif args.campaign == "adaptive":
        if args.obs_row not in range(4): raise SystemExit("--obs-row must be 0..3")
        result = campaign_adaptive(out, args.obs_row)
    elif args.campaign == "additional": result = campaign_additional(out)
    elif args.campaign == "cases": result = campaign_cases(out)
    else: result = campaign_sensitivity(out)
    result["cpu_seconds"] = round(time.process_time() - start, 6)
    result["wall_seconds"] = round(time.perf_counter() - wall, 6)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
