from __future__ import annotations

from fractions import Fraction
from itertools import permutations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from certificate import CertificateEvaluator, evaluate_complete, source_premises
from coverage import ball_volume, direct_max_coverage, max_coverage
from families import (biased_capped_source, deterministic_branching,
                      fair_public_bit_path_budget, flag_coupling,
                      flag_information, running_example)
from gf2 import (all_subspaces, apply, canonical_basis, cosets, dot, image_basis,
                 nullspace_basis, rank, span_points)
from model import Epoch, Protocol, Stop, parse_protocol
from oracle import PosteriorOracle


ROOT = Path(__file__).resolve().parents[1]


class LinearAlgebraTests(unittest.TestCase):
    def test_01_canonical_basis_equivalence(self):
        self.assertEqual(canonical_basis((3, 5, 6), 3), canonical_basis((3, 5), 3))

    def test_02_regression_all_permutations(self):
        expected = (9, 5, 3)
        for ordering in permutations((3, 6, 12)):
            self.assertEqual(canonical_basis(ordering, 4), expected, ordering)

    def test_03_canonical_basis_idempotent_and_redundancy_invariant(self):
        basis = canonical_basis((3, 6, 12, 3, 0, 10), 4)
        self.assertEqual(basis, canonical_basis(basis, 4))
        self.assertEqual(basis, canonical_basis(reversed((3, 6, 12, 3, 0, 10)), 4))

    def test_04_direct_nullspace_regression(self):
        ns = nullspace_basis((3, 6, 12), 4)
        self.assertEqual(ns, (15,))
        self.assertEqual(set(span_points(ns, 4)), {0, 15})
        self.assertTrue(all(dot(row, x) == 0 for row in (3, 6, 12) for x in span_points(ns, 4)))

    def test_05_rank_nullity_and_orthogonality_all_small_subspaces(self):
        for d in range(5):
            for basis in all_subspaces(d):
                ns = nullspace_basis(basis, d)
                self.assertEqual(rank(basis, d) + rank(ns, d), d)
                self.assertTrue(all(dot(row, x) == 0
                                    for row in basis for x in span_points(ns, d)))

    def test_06_coset_partition(self):
        ambient = canonical_basis((1, 2), 2)
        sub = canonical_basis((3,), 2)
        self.assertEqual(cosets(sub, ambient, 2), ((0, 3), (1, 2)))

    def test_07_all_subspace_counts(self):
        self.assertEqual([len(all_subspaces(d)) for d in range(6)], [1, 2, 5, 16, 67, 374])

    def test_08_high_bit_ordering(self):
        row = 1 << 255
        self.assertEqual(apply((row,), row), 1)
        self.assertEqual(len(nullspace_basis((row,), 256)), 255)


class CoverageTests(unittest.TestCase):
    def test_09_one_ball_volume(self):
        value, exact = max_coverage(8, 2, 1)
        self.assertTrue(exact)
        self.assertEqual(value, ball_volume(8, 2))

    def test_10_two_ball_closed_behavior(self):
        self.assertEqual(max_coverage(5, 2, 2)[0], 32)

    def test_11_three_ball_negative_control(self):
        self.assertEqual(max_coverage(4, 1, 3)[0], 13)
        self.assertEqual(3 * ball_volume(4, 1), 15)

    def test_12_profile_matches_direct(self):
        for r in range(5):
            for q in range(1, 5):
                for t in range(r + 1):
                    self.assertEqual(max_coverage(r, t, q)[0], direct_max_coverage(r, t, q)[0])


class ValidationTests(unittest.TestCase):
    def test_13_unknown_key_rejected(self):
        with self.assertRaises(ValueError):
            parse_protocol({"dimension": 1, "min_entropy": 1,
                            "root": {"type": "stop"}, "extra": 1})

    def test_14_missing_min_entropy_rejected(self):
        with self.assertRaisesRegex(ValueError, "min_entropy"):
            parse_protocol({"dimension": 1, "root": {"type": "stop"}})

    def test_15_bool_and_float_integer_coercions_rejected(self):
        bad = [
            {"dimension": True, "min_entropy": 1, "root": {"type": "stop"}},
            {"dimension": 1.0, "min_entropy": 1, "root": {"type": "stop"}},
            {"dimension": 1, "min_entropy": False, "root": {"type": "stop"}},
            {"dimension": 1, "min_entropy": 1,
             "root": {"type": "epoch", "rows": [1.0], "radius": 0,
                      "guesses": 1, "next": {"type": "stop"}}},
            {"dimension": 1, "min_entropy": 1,
             "root": {"type": "epoch", "rows": [1], "radius": False,
                      "guesses": 1, "next": {"type": "stop"}}},
        ]
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_protocol(raw)

    def test_16_bad_rational_pair_rejected_without_truncation(self):
        raw = {
            "dimension": 1,
            "min_entropy": 1,
            "root": {
                "type": "observe",
                "rows": [1],
                "eta": [1.5, 2],
                "children": [{"type": "stop"}, {"type": "stop"}],
            },
        }
        with self.assertRaisesRegex(ValueError, r"eta\[0\]"):
            parse_protocol(raw)

    def test_17_bad_child_count_rejected(self):
        with self.assertRaises(ValueError):
            parse_protocol({"dimension": 1, "min_entropy": 1,
                            "root": {"type": "observe", "rows": [1],
                                     "eta": "1/4", "children": []}})

    def test_18_prior_cap_rejected(self):
        with self.assertRaises(ValueError):
            parse_protocol({"dimension": 2, "min_entropy": 2,
                            "prior": ["1", "0", "0", "0"],
                            "root": {"type": "stop"}})

    def test_19_legal_pair_and_string_rationals_preserve_result(self):
        raw = {
            "name": "legal-input",
            "dimension": 1,
            "min_entropy": 1,
            "root": {
                "type": "observe",
                "rows": [0],
                "eta": [1, 2],
                "children": [
                    {"type": "epoch", "rows": [1], "radius": 0, "guesses": 1,
                     "next": {"type": "stop"}},
                    {"type": "epoch", "rows": [1], "radius": 0, "guesses": 1,
                     "next": {"type": "stop"}},
                ],
            },
        }
        protocol = parse_protocol(raw)
        self.assertEqual(evaluate_complete(protocol)["issued_risk"], Fraction(1, 2))


class CertificateOracleTests(unittest.TestCase):
    def test_20_running_example(self):
        p = running_example()
        self.assertEqual(CertificateEvaluator(p, "full").transferred_risk(), Fraction(5, 8))
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(17, 32))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(17, 32))

    def test_21_issued_minimum_and_baselines(self):
        complete = evaluate_complete(running_example())
        self.assertEqual(complete["issued_risk"], Fraction(17, 32))
        self.assertIn("coset", complete["issued_methods"])
        self.assertEqual(complete["bounds"]["full"]["transferred_risk"], Fraction(5, 8))
        self.assertEqual(complete["coverage_mode"], "exact")

    def test_22_deterministic_fiber_average(self):
        p = deterministic_branching()
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(3, 4))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(3, 4))

    def test_23_flag_coupling(self):
        p = flag_coupling()
        self.assertEqual(CertificateEvaluator(p, "full").transferred_risk(), Fraction(51, 64))
        self.assertEqual(CertificateEvaluator(p, "flag").transferred_risk(), Fraction(53, 64))
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(51, 64))

    def test_24_flag_information_loss(self):
        p = flag_information()
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(7, 8))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(3, 4))

    def test_25_noise_complement_relabeling(self):
        p1 = running_example(Fraction(1, 4))
        root = p1.root
        p2 = type(p1)(p1.dimension, p1.min_entropy,
                      type(root)(root.rows, Fraction(3, 4), tuple(reversed(root.children))),
                      p1.prior, "complemented")
        self.assertEqual(PosteriorOracle(p1).risk(), PosteriorOracle(p2).risk())
        self.assertEqual(CertificateEvaluator(p1, "coset").transferred_risk(),
                         CertificateEvaluator(p2, "coset").transferred_risk())

    def test_26_entropy_transfer_equality(self):
        p = biased_capped_source()
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(5, 8))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(5, 8))

    def test_27_fair_public_bit_path_witness(self):
        p = fair_public_bit_path_budget()
        self.assertEqual(CertificateEvaluator(p, "branch").transferred_risk(), Fraction(1, 2))
        self.assertEqual(CertificateEvaluator(p, "full").transferred_risk(), Fraction(3, 8))
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(3, 8))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(3, 8))

    def test_28_trace_is_deterministic_and_contains_source_steps(self):
        first = evaluate_complete(running_example(), collect_trace=True)
        second = evaluate_complete(running_example(), collect_trace=True)
        for method in ("branch", "full", "flag", "coherent", "coset"):
            trace1 = first["evaluators"][method].trace_records()
            trace2 = second["evaluators"][method].trace_records()
            self.assertEqual(trace1, trace2)
            self.assertTrue(trace1)
            self.assertTrue(any(row["node_type"] == "epoch" and "coverage_source" in row
                                for row in trace1))

    def test_29_fallback_status_is_explicit(self):
        rows = tuple(1 << i for i in range(25))
        p = Protocol(25, 25, Epoch(rows, 1, 3, Stop()), name="fallback")
        complete = evaluate_complete(p)
        self.assertEqual(complete["coverage_mode"], "fallback")
        self.assertTrue(all(item["coverage_mode"] == "fallback"
                            for item in complete["bounds"].values()))

    def test_30_source_premises_report_d_k_delta(self):
        premises = source_premises(Protocol(4, 3, Stop(), name="premises"))
        self.assertEqual((premises["d"], premises["k"], premises["delta"]), (4, 3, 1))

    def test_31_cli_root_output_and_diagnostic_method(self):
        model = {
            "name": "cli-minimal",
            "dimension": 1,
            "min_entropy": 1,
            "root": {"type": "epoch", "rows": [1], "radius": 0, "guesses": 1,
                     "next": {"type": "stop"}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.json"
            path.write_text(json.dumps(model), encoding="utf-8")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "src")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "src" / "cli.py"), str(path),
                 "--method", "full", "--trace", "--oracle"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = json.loads(proc.stdout)
        self.assertEqual((output["d"], output["k"], output["delta"]), (1, 1, 0))
        self.assertEqual(output["issued_risk"], "1/2")
        self.assertEqual(output["diagnostic"]["method"], "full")
        self.assertIn("full", output["bounds"])
        self.assertIn("coset", output["trace"])


if __name__ == "__main__":
    unittest.main()
