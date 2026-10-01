"""Declared finite protocol families and named examples."""
from __future__ import annotations

from fractions import Fraction

from model import Epoch, Observe, Protocol, Stop

STOP = Stop()


def two_row_map(index: int) -> tuple[int, int]:
    if index < 0 or index >= 16:
        raise ValueError(index)
    return index & 3, (index >> 2) & 3


def config(index: int, child=STOP) -> Epoch:
    if index < 0 or index >= 64:
        raise ValueError(index)
    map_index = index // 4
    rem = index % 4
    radius = rem // 2
    guesses = rem % 2 + 1
    return Epoch(two_row_map(map_index), radius, guesses, child)


def small_config(index: int, child=STOP) -> Epoch:
    if index < 0 or index >= 8:
        raise ValueError(index)
    rows = (1, 2) if index // 4 == 0 else (1, 1)
    rem = index % 4
    return Epoch(rows, rem // 2, rem % 2 + 1, child)


def two_epoch(a1: int, t1: int, q1: int, a2: int, t2: int, q2: int) -> Protocol:
    root = Epoch(two_row_map(a1), t1, q1,
                 Epoch(two_row_map(a2), t2, q2, STOP))
    return Protocol(2, 2, root, name="two-epoch")


def noisy_adaptive(obs_row: int, eta: Fraction, left: int, right: int) -> Protocol:
    return Protocol(2, 2, Observe((obs_row,), eta, (config(left), config(right))),
                    name="noisy-adaptive")


def noisy_two_row(obs_map: int, eta: Fraction, continuation: int) -> Protocol:
    child = config(continuation)
    return Protocol(2, 2, Observe(two_row_map(obs_map), eta, (child, child, child, child)),
                    name="noisy-two-row")


def post_rejection(first_row: int, obs_row: int, eta: Fraction,
                   left: int, right: int) -> Protocol:
    observation = Observe((obs_row,), eta, (small_config(left), small_config(right)))
    root = Epoch((first_row,), 0, 1, observation)
    return Protocol(2, 2, root, name="post-rejection")


def running_example(eta: Fraction = Fraction(1, 4)) -> Protocol:
    branch0 = Epoch((1, 2), 0, 1, Epoch((4, 8), 0, 1, STOP))
    branch1 = Epoch((1, 4), 0, 1, Epoch((2, 8), 0, 1, STOP))
    return Protocol(4, 4, Observe((1,), eta, (branch0, branch1)),
                    name="noisy-running-example")


def deterministic_branching() -> Protocol:
    # Observe X1 exactly; branch 0 tests X1, branch 1 tests X2.
    return Protocol(2, 2, Observe((1,), Fraction(0),
                                  (Epoch((1,), 0, 1, STOP),
                                   Epoch((2,), 0, 1, STOP))),
                    name="deterministic-branching")



def fair_public_bit_path_budget() -> Protocol:
    """Fair public bit selects conditional risks 1/4 and 1/2; total is 3/8."""
    low = Epoch((1, 2), 0, 1, STOP)   # one exact guess of two fair bits
    high = Epoch((1,), 0, 1, STOP)     # one exact guess of one fair bit
    # A zero row through BSC(1/2) is a public fair bit independent of X.
    return Protocol(2, 2, Observe((0,), Fraction(1, 2), (low, high)),
                    name="fair-public-bit-path-budget")

def flag_information() -> Protocol:
    # Observe both bits through eta=1/4, then make two exact guesses of the pair.
    child = Epoch((1, 2), 0, 2, STOP)
    return Protocol(2, 2, Observe((1, 2), Fraction(1, 4),
                                  (child, child, child, child)),
                    name="flag-information-grant")


def flag_coupling() -> Protocol:
    # Old exact observation of both bits, then noisy repetition chooses 4/1/3/3 guesses
    # on two fresh bits. This is the paper's cross-flag coupling witness.
    continuations = tuple(Epoch((4, 8), 0, q, STOP) for q in (4, 1, 3, 3))
    noisy = Observe((1, 2), Fraction(1, 4), continuations)
    exact = Observe((1, 2), Fraction(0), (noisy, noisy, noisy, noisy))
    return Protocol(4, 4, exact, name="cross-flag-coupling")


def independent_blocks() -> Protocol:
    root = Epoch((1, 2, 4), 0, 1,
                 Epoch((8, 16, 32), 0, 1, STOP))
    return Protocol(6, 6, root, name="independent-blocks")


def tolerant_three() -> Protocol:
    return Protocol(4, 4, Epoch((1, 2, 4, 8), 1, 3, STOP),
                    name="three-tolerant-guesses")


def repeated_map() -> Protocol:
    return Protocol(2, 2, Epoch((1, 2), 0, 1,
                                Epoch((1, 2), 0, 1, STOP)),
                    name="repeated-map")


def overlapping_blocks() -> Protocol:
    return Protocol(3, 3, Epoch((1, 2), 0, 1,
                                Epoch((2, 4), 0, 1, STOP)),
                    name="overlapping-blocks")


def repetition_geometry() -> Protocol:
    return Protocol(1, 1, Epoch((1, 1, 1), 1, 1, STOP),
                    name="repetition-geometry")


def helper_reveals_response() -> Protocol:
    # Exact public observation, followed by the same one-bit response.
    child = Epoch((1,), 0, 1, STOP)
    return Protocol(1, 1, Observe((1,), Fraction(0), (child, child)),
                    name="helper-reveals-response")


def adaptive_exact_observation() -> Protocol:
    return noisy_adaptive(1, Fraction(0), 0, 63)


def rejection_posterior() -> Protocol:
    return Protocol(2, 2, Epoch((1, 2), 0, 1,
                                Epoch((1, 2), 0, 1, STOP)),
                    name="rejection-posterior")


def coordinate_geometry() -> Protocol:
    return Protocol(1, 1, Epoch((1,), 1, 1, STOP), name="coordinate-geometry")


def biased_capped_source() -> Protocol:
    # Uniform-reference risk 5/16 and deficit one gives 5/8 exactly.
    # Event is a five-point winning set in F_2^4, each assigned mass 1/8.
    # Remaining mass is spread over three non-winning points at 1/8 each.
    root = Epoch((1, 2, 4, 8), 1, 1, STOP)  # one radius-one ball has five points
    prior = [Fraction(0) for _ in range(16)]
    winning = [0, 1, 2, 4, 8]
    other = [3, 5, 6]
    for x in winning + other:
        prior[x] = Fraction(1, 8)
    return Protocol(4, 3, root, tuple(prior), name="biased-capped-source")


def named_cases() -> tuple[Protocol, ...]:
    return (
        adaptive_exact_observation(),
        biased_capped_source(),
        coordinate_geometry(),
        deterministic_branching(),
        flag_information(),
        helper_reveals_response(),
        independent_blocks(),
        running_example(),
        overlapping_blocks(),
        flag_coupling(),
        rejection_posterior(),
        repeated_map(),
        repetition_geometry(),
        tolerant_three(),
    )
