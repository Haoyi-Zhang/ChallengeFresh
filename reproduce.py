#!/usr/bin/env python3
"""Bounded, deterministic reproduction runner for all retained evidence."""
from __future__ import annotations

import argparse
import filecmp
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
GROUPS = ("quick", "coverage", "noisy0", "noisy1", "noisy2", "noisy3", "noisy4", "sensitivity", "validate")


def child_limits() -> None:
    limit = 7 * (1 << 29)  # 3.5 GiB
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))


def run(cmd: list[str], timeout: int = 45) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True,
                          timeout=timeout, preexec_fn=child_limits)
    elapsed = time.perf_counter() - start
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout}\n{proc.stderr}")
    return {
        "command": cmd,
        "wall_seconds": round(elapsed, 6),
        "child_user_seconds": round(after.ru_utime - before.ru_utime, 6),
        "child_system_seconds": round(after.ru_stime - before.ru_stime, 6),
        "max_rss_kib": after.ru_maxrss,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def compare_file(generated: Path, reference: Path) -> None:
    if not generated.is_file() or not reference.is_file():
        raise AssertionError(f"missing generated/reference file: {generated} / {reference}")
    if generated.read_bytes() != reference.read_bytes():
        raise AssertionError(f"scientific output differs: {reference.relative_to(ROOT)}")


def compare_subtree(generated_root: Path, reference_root: Path) -> None:
    generated = sorted(p.relative_to(generated_root) for p in generated_root.rglob("*") if p.is_file())
    reference = sorted(p.relative_to(reference_root) for p in reference_root.rglob("*") if p.is_file())
    # Reproduction receipts are deliberately not scientific reference data.
    reference = [p for p in reference if not str(p).startswith("reproduction/") and p.name != "summary.json"]
    if generated != reference:
        raise AssertionError(f"output file set differs\ngenerated={generated}\nreference={reference}")
    for rel in generated:
        compare_file(generated_root / rel, reference_root / rel)


def execute_group(group: str) -> dict[str, object]:
    commands: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix=f"freshness-{group}-") as tmp:
        out = Path(tmp) / "results"
        if group == "quick":
            commands.append(run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]))
            commands.append(run([sys.executable, "src/campaigns.py", "cases", "--output", str(out)]))
            compare_subtree(out / "cases", RESULTS / "cases")
        elif group == "coverage":
            commands.append(run([sys.executable, "src/campaigns.py", "coverage", "--output", str(out)]))
            compare_subtree(out / "coverage", RESULTS / "coverage")
        elif group.startswith("noisy") and group != "noisy4":
            obs = int(group[-1])
            commands.append(run([sys.executable, "src/campaigns.py", "adaptive", "--obs-row", str(obs),
                                 "--output", str(out)]))
            name = f"noisy_adaptive_obs{obs}.csv"
            compare_file(out / "protocols" / name, RESULTS / "protocols" / name)
        elif group == "noisy4":
            commands.append(run([sys.executable, "src/campaigns.py", "additional", "--output", str(out)]))
            for name in ("two_epoch.csv", "noisy_two_row.csv", "post_rejection.csv"):
                compare_file(out / "protocols" / name, RESULTS / "protocols" / name)
        elif group == "sensitivity":
            commands.append(run([sys.executable, "src/campaigns.py", "sensitivity", "--output", str(out)]))
            compare_subtree(out / "sensitivity", RESULTS / "sensitivity")
        elif group == "validate":
            commands.append(run([sys.executable, "src/validate_results.py"]))
        else:
            raise ValueError(group)
    return {"group": group, "status": "pass", "commands": commands}


def main() -> int:
    if sys.flags.optimize:
        raise SystemExit("optimized Python is not allowed for reproduction")
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=GROUPS)
    args = parser.parse_args()
    selected = (args.group,) if args.group else GROUPS
    for group in selected:
        receipt = execute_group(group)
        path = RESULTS / "reproduction" / f"{group}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{group}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
