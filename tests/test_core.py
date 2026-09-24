from __future__ import annotations

from fractions import Fraction
import json
import tempfile
import unittest

from certificate import CertificateEvaluator
from coverage import ball_volume, direct_max_coverage, max_coverage
from families import (biased_capped_source, deterministic_branching, flag_coupling,
                      flag_information, running_example)
from gf2 import (all_subspaces, apply, canonical_basis, cosets, image_basis,
                 nullspace_basis, span_points)
from model import parse_protocol
from oracle import PosteriorOracle


class LinearAlgebraTests(unittest.TestCase):
    def test_01_canonical_basis_equivalence(self):
        self.assertEqual(canonical_basis((3, 5, 6), 3), canonical_basis((3, 5), 3))

    def test_02_nullspace_orthogonality(self):
        basis = canonical_basis((0b1011, 0b0110), 4)
        ns = nullspace_basis(basis, 4)
        self.assertEqual(len(ns), 2)
        self.assertTrue(all(((r & x).bit_count() & 1) == 0 for r in basis for x in span_points(ns, 4)))

    def test_03_coset_partition(self):
        ambient = canonical_basis((1, 2), 2)
        sub = canonical_basis((3,), 2)
        self.assertEqual(cosets(sub, ambient, 2), ((0, 3), (1, 2)))

    def test_04_all_subspace_counts(self):
        self.assertEqual([len(all_subspaces(d)) for d in range(6)], [1, 2, 5, 16, 67, 374])

    def test_05_high_bit_ordering(self):
        row = 1 << 255
        self.assertEqual(apply((row,), row), 1)
        self.assertEqual(len(nullspace_basis((row,), 256)), 255)


class CoverageTests(unittest.TestCase):
    def test_06_one_ball_volume(self):
        value, exact = max_coverage(8, 2, 1)
        self.assertTrue(exact)
        self.assertEqual(value, ball_volume(8, 2))

    def test_07_two_ball_closed_behavior(self):
        self.assertEqual(max_coverage(5, 2, 2)[0], 32)

    def test_08_three_ball_negative_control(self):
        self.assertEqual(max_coverage(4, 1, 3)[0], 13)
        self.assertEqual(3 * ball_volume(4, 1), 15)

    def test_09_profile_matches_direct(self):
        for r in range(5):
            for q in range(1, 5):
                for t in range(r + 1):
                    self.assertEqual(max_coverage(r, t, q)[0], direct_max_coverage(r, t, q)[0])


class ValidationTests(unittest.TestCase):
    def test_10_unknown_key_rejected(self):
        with self.assertRaises(ValueError):
            parse_protocol({"dimension": 1, "min_entropy": 1, "root": {"type": "stop"}, "extra": 1})

    def test_11_bad_child_count_rejected(self):
        with self.assertRaises(ValueError):
            parse_protocol({"dimension": 1, "min_entropy": 1,
                            "root": {"type": "observe", "rows": [1], "eta": "1/4", "children": []}})

    def test_12_prior_cap_rejected(self):
        with self.assertRaises(ValueError):
            parse_protocol({"dimension": 2, "min_entropy": 2, "prior": ["1", "0", "0", "0"],
                            "root": {"type": "stop"}})


class CertificateOracleTests(unittest.TestCase):
    def test_13_running_example(self):
        p = running_example()
        self.assertEqual(CertificateEvaluator(p, "full").transferred_risk(), Fraction(5, 8))
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(17, 32))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(17, 32))

    def test_14_deterministic_fiber_average(self):
        p = deterministic_branching()
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(3, 4))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(3, 4))

    def test_15_flag_coupling(self):
        p = flag_coupling()
        self.assertEqual(CertificateEvaluator(p, "full").transferred_risk(), Fraction(51, 64))
        self.assertEqual(CertificateEvaluator(p, "flag").transferred_risk(), Fraction(53, 64))
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(51, 64))

    def test_16_flag_information_loss(self):
        p = flag_information()
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(7, 8))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(3, 4))

    def test_17_noise_complement_relabeling(self):
        p1 = running_example(Fraction(1, 4))
        # Complementing output swaps the two public continuations.
        root = p1.root
        p2 = type(p1)(p1.dimension, p1.min_entropy,
                      type(root)(root.rows, Fraction(3, 4), tuple(reversed(root.children))),
                      p1.prior, "complemented")
        self.assertEqual(PosteriorOracle(p1).risk(), PosteriorOracle(p2).risk())
        self.assertEqual(CertificateEvaluator(p1, "coset").transferred_risk(),
                         CertificateEvaluator(p2, "coset").transferred_risk())

    def test_18_entropy_transfer_equality(self):
        p = biased_capped_source()
        self.assertEqual(CertificateEvaluator(p, "coset").transferred_risk(), Fraction(5, 8))
        self.assertEqual(PosteriorOracle(p).risk(), Fraction(5, 8))


if __name__ == "__main__":
    unittest.main()
