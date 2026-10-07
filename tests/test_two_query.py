"""Portable, untimed, finite two-query conformance tests (standard library only).

Run python -B tests/test_two_query.py from this artifact, or use an absolute path.
No campaign, subprocess, clocks, private snapshots, or result writes are used.
"""
from fractions import Fraction
from math import comb
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ARTIFACT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARTIFACT / "src"))
import coverage
import validate_results
from certificate import evaluate_complete
from families import named_cases
from two_query_reference import antipodal_count, literal_union_max, witness_union

COUNTS = {}


def count(name, amount=1):
    COUNTS[name] = COUNTS.get(name, 0) + amount


def outcome(arguments):
    try:
        return ("return", coverage.max_coverage(*arguments))
    except (TypeError, ValueError) as error:
        return (type(error).__name__, str(error))


def protocol_record(protocol):
    result = evaluate_complete(protocol, collect_trace=True)
    return {
        "bounds": result["bounds"],
        "issued_risk": result["issued_risk"],
        "issued_methods": result["issued_methods"],
        "coverage_mode": result["coverage_mode"],
        "trace": {key: ev.trace_records() for key, ev in result["evaluators"].items()},
    }


class TwoQueryTests(unittest.TestCase):
    def test_exhaustive_profiles_and_counters_remain(self):
        for rank in range(25):
            values, witnesses, profiles, weights = coverage.exact_profile(rank, 2)
            self.assertEqual(profiles, rank + 1)
            self.assertEqual(weights, comb(rank + 3, 3))
            self.assertEqual(len(witnesses), rank + 1)
            for radius in range(rank + 1):
                expected = antipodal_count(rank, radius)
                self.assertEqual(coverage.max_coverage(rank, radius, 2), (expected, True))
                self.assertEqual(values[radius], expected)
                if rank <= 5:
                    self.assertEqual(witness_union(rank, radius, witnesses[radius]), expected)
                count("profile_radius_equalities")
            count("profile_visits", profiles)
            count("weight_vector_visits", weights)

    def test_independent_literal_center_reference(self):
        for rank in range(6):
            for radius in range(rank + 3):
                expected = literal_union_max(rank, radius, 2)
                self.assertEqual(coverage.max_coverage(rank, radius, 2), (expected, True))
                count("literal_two_query_equalities")
        for rank in range(5):
            for queries in (1, 3, 4):
                for radius in range(rank + 1):
                    self.assertEqual(coverage.max_coverage(rank, radius, queries)[0],
                                     literal_union_max(rank, radius, queries))
                    count("adjacent_query_equalities")

    def test_shortcut_and_large_admitted_ranks(self):
        coverage.max_coverage.cache_clear()
        with patch.object(coverage, "exact_profile", side_effect=AssertionError("profile queried")):
            for rank in (2, 3, 24, 25, 64, 256):
                for radius in sorted({0, (rank - 1) // 2, rank // 2, rank - 1, rank, rank + 1}):
                    self.assertEqual(coverage.max_coverage(rank, radius, 2),
                                     (antipodal_count(rank, radius), True))
                    count("shortcut_equalities")

    def test_admission_saturation_and_fallback_boundaries(self):
        invalid = ((-1, 0, 2), (3, -1, 2), (3, 0, 0), (3, 0, -2))
        for arguments in invalid:
            self.assertEqual(outcome(arguments),
                             ("ValueError", "invalid coverage parameters"))
            count("negative_argument_controls")
        # Direct API historical non-integer paths are deliberately not relaxed.
        for arguments in ((3, 0, 2.0), (3, 1.0, 2), (3, 0, Fraction(2)),
                          (3.0, 0, 2)):
            # The pre-existing typed=False caches can alias equal numeric
            # keys; this control deliberately tests a cold direct call.
            coverage.max_coverage.cache_clear()
            coverage.exact_profile.cache_clear()
            self.assertEqual(outcome(arguments)[0], "TypeError")
            count("non_integer_rejections")
        self.assertEqual(coverage.max_coverage(3, 3.0, 2.0), (8, True))
        self.assertEqual(coverage.max_coverage(3, True, 2), (8, True))
        self.assertEqual(coverage.max_coverage(1, 0, True), (1, True))
        for rank, queries, exact in ((24, 3, True), (25, 3, False),
                                     (8, 4, True), (9, 4, False)):
            self.assertEqual(coverage.exact_domain(rank, queries), exact)
            # Do not regenerate the unrelated large q=3/4 profile chunks.
            if not exact:
                self.assertEqual(coverage.max_coverage(rank, 0, queries), (queries, False))
            self.assertEqual(coverage.max_coverage(rank, rank, queries), (1 << rank, True))
            count("fallback_boundary_pairs")

    def test_validator_keeps_exhaustive_two_query_reference(self):
        row = dict(q="2", rank="3", radius="1", cube_size="8", coverage="8",
                   profiles_for_rank="4", weight_vectors_for_rank="20")
        sizes = {"profile.csv": 1020, "direct.csv": 105, "subspaces.csv": 7989,
                 "log_concavity.csv": 273, "balanced_transfers.csv": 5460, "cosets.csv": 18265}

        def fake_rows(path):
            return iter([row.copy()] * sizes[path.name])

        real_profile = coverage.exact_profile(3, 2)
        with patch.object(validate_results, "rows", side_effect=fake_rows):
            with patch.object(validate_results, "exact_profile", return_value=real_profile) as replay:
                with self.assertRaisesRegex(AssertionError, "duplicate profile tuple"):
                    validate_results.validate_coverage(ARTIFACT / "results")
                replay.assert_called_once_with(3, 2)
            with patch.object(validate_results, "exact_profile",
                              return_value=((1, 7, 8, 8), (), 4, 20)):
                with self.assertRaisesRegex(AssertionError, "formula differs from exhaustive profile"):
                    validate_results.validate_coverage(ARTIFACT / "results")
        count("exhaustive_validator_controls", 2)

    def test_query_reference_preserves_complete_named_outputs(self):
        # Differentially substitute the test-local literal reference only for
        # the small two-query cells encountered by these declared named cases.
        import certificate
        original = certificate.max_coverage

        def reference_query(rank, radius, queries):
            if queries == 2:
                return literal_union_max(rank, radius, queries), True
            return original(rank, radius, queries)

        for protocol in named_cases():
            current = protocol_record(protocol)
            with patch.object(certificate, "max_coverage", side_effect=reference_query):
                reference = protocol_record(protocol)
            self.assertEqual(current, reference)
            count("named_complete_output_equalities")
        # Existing negative findings remain inequalities, not forced equality.
        records = {p.name: protocol_record(p) for p in named_cases()}
        self.assertEqual(records["cross-flag-coupling"]["issued_risk"], Fraction(51, 64))
        self.assertEqual(records["flag-information-grant"]["issued_risk"], Fraction(7, 8))
        self.assertEqual(records["repeated-map"]["issued_risk"], Fraction(1))
        self.assertEqual(records["repetition-geometry"]["issued_risk"], Fraction(1))


if __name__ == "__main__":
    program = unittest.main(exit=False)
    print("finite checks:", dict(sorted(COUNTS.items())))
    raise SystemExit(0 if program.result.wasSuccessful() else 1)
