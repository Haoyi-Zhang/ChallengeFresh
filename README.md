# Composable challenge freshness

This standalone repository accompanies **Noise-Aware Challenge-Freshness Certificates for Affine Identity Channels**. It evaluates conditional mathematical false-accept bounds for an explicitly declared finite affine identity model. It is not a device-authentication implementation, a hardware test, or evidence that a physical PUF satisfies the premises.

## Scientific contents

- `proofs/theorems.md` contains the complete written mathematical arguments. They are conventional proofs, not proof-assistant output.
- `src/` contains GF(2) linear algebra, exact multi-ball coverage, five certificate evaluators, a distinct full-posterior finite oracle, deterministic campaign generators, and an aggregate-results validator.
- `cases/` contains 15 exact JSON files: fourteen distinct named models used by the retained case table and one equivalent CLI alias for the running example. The separate fair-public-bit path-budget witness is generated from `src/families.py` and retained under `results/cases/`.
- `results/` retains all claim-linked CSV rows, exact sensitivity data, aggregate counts, and overwritten clean-reproduction receipts.
- `literature/` records the 12 TDSC + 5 influential + 5 adjacent full-text calibration and the precise closest-work boundary.
- `claim_evidence_ledger.csv` and `external_resources.csv` link claims and outside materials to the files that support or constrain them.

The central certificate maintains a proof-only affine shadow. Residual rank selects the exact worst-code fraction of an affine response space covered by a bounded union of Hamming balls. Fixed per-stage hazard bounds compose only when each one holds uniformly over every live history reaching that stage; history-dependent hazards use the pathwise admission theorem or the complete backward recurrence, without assuming independent attempts. One average conditional min-entropy deficit transfers the terminal event from a uniform reference law. For declared independent BSC observations, coherent signal coupling and affine-coset averaging retain part of the channel uncertainty while remaining sound.

In the exact local-coverage domain the coset risk is no greater than the coherent-signal, separate-flag, probability-preserving full-channel, and branch-oblivious full-revelation risks. Outside that domain the executable issues the minimum of independently sound complete bounds; it does not assert an unproved cross-regime domination.

## Run one declared model

Requirements are Python with `int.bit_count`, the standard library, and a Unix-like system for the bounded campaign runner. No package installation or network access is required. Run commands from this repository root:

```sh
python src/cli.py cases/noisy-observation.json --oracle
PYTHONPATH=src python -m unittest discover -s tests -v
```

The first command reports the required source parameters `d`, `k`, and `delta=d-k`; all five complete method bounds and their exact/fallback status; issued bound `17/32`; full-channel baseline `5/8`; and finite-oracle probability `17/32`. All are exact fractions. `--method` selects a diagnostic view but never replaces the issued minimum over complete sound bounds; `--trace` emits deterministic per-node certificate state, while the JSON root separately records the externally supplied source, map, channel, verifier, and stopping premises. Invalid or unsupported input produces an error and no certificate. The exact oracle has stricter dimensions and retry limits than the certificate; omit `--oracle` for larger declared models.

## Reproduce all retained evidence

```sh
python reproduce.py
python src/validate_results.py
```

The runner executes one child at a time, rejects optimized Python, imposes a 3.5 GiB address-space ceiling and 45-second CPU/command ceiling, and stops on any nonzero exit, timeout, or byte difference. To retain generated evidence and stdout/stderr, including failed commands, use fresh external directories with `--work-root /path/to/raw-work --receipt-root /path/to/receipts`. Existing group directories are not overwritten. Its bounded groups are:

```sh
python reproduce.py --group quick
python reproduce.py --group coverage
python reproduce.py --group noisy0
python reproduce.py --group noisy1
python reproduce.py --group noisy2
python reproduce.py --group noisy3
python reproduce.py --group noisy4
python reproduce.py --group sensitivity
python reproduce.py --group validate
```

Each generation group byte-compares newly generated scientific CSV/JSON evidence with the retained references. Timing receipts are written separately under `results/reproduction/` by default, or under `--receipt-root`; the validator regenerates coverage maxima and counting formulas, links direct and affine-code rows to that table, and recomputes equality, soundness, exactness, improvement, and exact-domain hierarchy indicators from raw numeric fields rather than trusting stored flags or `summary.json`. A failed inequality or equality is rejected even when its stored flag truthfully says zero. Tamper tests exercise both preserved and updated flags in isolated copies. The validator does not independently regenerate every code-specific or posterior-oracle computation; the generation groups and their byte comparisons provide that replay.

The fixed evidence includes:

- 1,020 exact coverage entries, 105 direct coverage equalities, all 465 subspaces through ambient dimension five, 7,989 affine-code inequalities, 273 log-concavity checks, 5,460 balanced-rank transfers, and 18,265 signal-coset partitions;
- 4,096 two-epoch models with `d=2`, two ordered rows per stage via `two_row_map(i)=(i&3,(i>>2)&3)`, of which 3,934 are certificate-exact and 162 conservative; `results/protocols/two_epoch_domain.json` records the exact Cartesian domain;
- 87,040 noisy-observation models, of which 86,842 are certificate-exact and 198 conservative; 31,428 improve the probability-preserving full-channel risk and 14,976 improve the minimum of the full-channel and separate-flag risks;
- 5,120 observation-after-rejection models, all exact in that fixed family;
- zero finite-model cases in which a retained certificate was below the full-posterior oracle;
- 45 unit tests (the original 39 plus six two-query conformance regressions; all 45 passed a separate Windows run), 14 retained named cases, one explicit path-budget witness, and 17 exact noise-sensitivity points.

These are exhaustive only under the inclusion rules implemented in `src/campaigns.py`. They are development-time finite checks, not a sample of deployments, a proof of the general theorems, or an independent replication.

The retained Linux/Python 3.12 reproduction passes all nine groups and 39 tests before the six conformance regressions were added. All 16 scientific CSVs and two JSON records match the retained reference bytes. The ten sequential commands use 149.954868 summed child CPU seconds and 150.071469 summed command elapsed seconds, including interpreter startup, tests, and validation. The largest recorded child RSS is 127,964 KiB; it is not aggregate process-tree memory. Current command receipts and raw console output are in `results/measurements/`, separate from the historical timing receipts in `results/reproduction/`.

## Declared model and interpretation

Read `model-language.md` before changing or adding a case. `dimension`, `min_entropy`, and `root` are mandatory. Integer fields must be actual integers (not booleans or floats), and a rational pair must contain two actual integers; the parser never substitutes `k=d` or truncates a float. Public affine offsets are absorbed into candidates in the theorem; the JSON language stores zero-offset maps. Observation nodes use independent rational BSC errors. An epoch fixes a response map, Hamming radius and bounded adaptive guess count; it reveals only accept/reject and reaches its continuation only after all guesses fail. A source deficit is charged once to the final event.

A certificate is an evaluated upper bound associated with explicit assumptions, not a signed attestation or succinct independently checkable proof object. No code path infers entropy, error independence, map correctness, verifier conformance, physical reliability, manufacturing uniqueness or unclonability.

## Maturity, literature and external use

The general results have complete written arguments and extensive finite checking but no proof-assistant mechanization or independent external review. The posterior oracle uses a different state representation, yet it was developed in the same research execution. Both exact and deliberately loose examples are retained.

The full-text calibration now covers twelve TDSC papers, five foundational/influential papers and five adjacent papers. The closest 2025 PUF-AKE work constructs and analyzes computational AKE with reusable robust fuzzy extraction and reports attacks on prior PUF protocols; this repository instead gives conditional information-theoretic bounds for declared finite affine raw-response channels. Neither result is presented as subsuming the other, and no priority claim is made.


The repository is standalone and does not depend on a parent paper folder, private path, omitted cache or network service. Original software is licensed under `LICENSE`. Scholarly papers are cited rather than redistributed; `external_resources.csv` records acquisition and licensing boundaries.
