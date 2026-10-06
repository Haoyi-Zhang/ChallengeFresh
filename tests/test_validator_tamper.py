from __future__ import annotations

import csv
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_results import validate_coverage, validate_results


ROOT = Path(__file__).resolve().parents[1]


def rewrite_first_row(path: Path, mutate) -> None:
    with path.open(newline="", encoding="utf-8") as fh:
        data = list(csv.DictReader(fh))
        fieldnames = list(data[0])
    mutate(data[0])
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)


class ValidatorTamperTests(unittest.TestCase):
    def copy_results(self, tmp: str) -> Path:
        target = Path(tmp) / "results"
        shutil.copytree(ROOT / "results", target)
        return target

    def test_32_rejects_changed_coverage_value_with_success_flag_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self.copy_results(tmp)
            path = target / "coverage" / "balanced_transfers.csv"
            rewrite_first_row(path, lambda row: row.__setitem__("balanced", "0"))
            with self.assertRaises(AssertionError):
                validate_results(target, write_summary=False)

    def test_33_rejects_changed_protocol_value_with_flags_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self.copy_results(tmp)
            path = target / "protocols" / "noisy_adaptive_obs0.csv"
            def mutate(row):
                row["issued"] = "0"
                # Stored sound/exact/improvement flags are intentionally untouched.
            rewrite_first_row(path, mutate)
            with self.assertRaises(AssertionError):
                validate_results(target, write_summary=False)

    def test_34_rejects_failed_direct_equality_with_truthful_zero_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self.copy_results(tmp)
            def mutate(row):
                row['direct'] = str(int(row['profile']) + 1)
                row['equal'] = '0'
            rewrite_first_row(target / 'coverage' / 'direct.csv', mutate)
            with self.assertRaisesRegex(AssertionError, 'equality failed'):
                validate_coverage(target)

    def test_35_rejects_failed_lifting_with_truthful_zero_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self.copy_results(tmp)
            def mutate(row):
                row['code_coverage'] = str(int(row['worst_rank_coverage']) + 1)
                row['holds'] = '0'
            rewrite_first_row(target / 'coverage' / 'subspaces.csv', mutate)
            with self.assertRaisesRegex(AssertionError, 'lifting inequality failed'):
                validate_coverage(target)

    def test_36_rejects_failed_log_concavity_with_truthful_zero_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self.copy_results(tmp)
            def mutate(row):
                row['left'], row['right'], row['holds'] = '0', '1', '0'
            rewrite_first_row(target / 'coverage' / 'log_concavity.csv', mutate)
            with self.assertRaisesRegex(AssertionError, 'log-concavity inequality failed'):
                validate_coverage(target)

    def test_37_rejects_failed_coset_equality_with_truthful_zero_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self.copy_results(tmp)
            def mutate(row):
                row['computed'], row['equal'] = 'different-owned-symbol', '0'
            rewrite_first_row(target / 'coverage' / 'cosets.csv', mutate)
            with self.assertRaisesRegex(AssertionError, 'coset equality failed'):
                validate_coverage(target)

    def test_38_rejects_unchecked_negative_profile_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self.copy_results(tmp)
            rewrite_first_row(target / 'coverage' / 'profile.csv',
                              lambda row: row.__setitem__('coverage', '-1'))
            with self.assertRaisesRegex(AssertionError, 'regenerated maximum'):
                validate_coverage(target)

    def test_39_rejects_agreeing_direct_values_disconnected_from_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self.copy_results(tmp)
            def mutate(row):
                row['direct'], row['profile'] = '0', '0'
            rewrite_first_row(target / 'coverage' / 'direct.csv', mutate)
            with self.assertRaisesRegex(AssertionError, 'regenerated profile table'):
                validate_coverage(target)


if __name__ == "__main__":
    unittest.main()
