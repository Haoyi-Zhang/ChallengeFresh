from __future__ import annotations

import csv
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_results import validate_results


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


if __name__ == "__main__":
    unittest.main()
