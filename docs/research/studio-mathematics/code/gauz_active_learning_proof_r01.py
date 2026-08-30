"""GAUZ ACTIVE LEARNING PROOF R01.

Bounded synthetic proof for the mathematical learning controller described in
GAUZ_MATHEMATICAL_LEARNING_MACHINE_R01.md.

This proves only an exact synthetic linear-Gaussian acquisition result.
It does not prove general intelligence, model-weight self-modification,
or production effectiveness.
"""

from __future__ import annotations

import json
import math
import numpy as np

SEED = 222
D = 8
CANDIDATE_COUNT = 80
BUDGET = 20
NOISE_VAR = 0.04
RANDOM_TRIALS = 1000


def covariance_update(Sigma: np.ndarray, a: np.ndarray, sigma2: float) -> np.ndarray:
    """Linear-Gaussian posterior covariance update."""
    Sa = Sigma @ a
    return Sigma - np.outer(Sa, Sa) / (sigma2 + float(a @ Sa))


def expected_information_gain(Sigma: np.ndarray, a: np.ndarray, sigma2: float) -> float:
    """Expected scalar Gaussian information gain in nats."""
    return 0.5 * math.log1p(float(a @ Sigma @ a) / sigma2)


def make_candidate_pool(rng: np.random.Generator) -> np.ndarray:
    candidates: list[np.ndarray] = []

    # Deliberately redundant candidates around the first three dimensions.
    for _ in range(40):
        v = np.zeros(D)
        idx = int(rng.integers(0, 3))
        v[idx] = 1.0
        v += 0.08 * rng.normal(size=D)
        v /= np.linalg.norm(v)
        candidates.append(v)

    # Diverse candidates spanning the full latent space.
    for _ in range(40):
        v = rng.normal(size=D)
        v /= np.linalg.norm(v)
        candidates.append(v)

    return np.asarray(candidates)


def run_schedule(
    Sigma0: np.ndarray,
    A: np.ndarray,
    indices: list[int] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    Sigma = Sigma0.copy()
    traces = [float(np.trace(Sigma))]
    max_eigs = [float(np.linalg.eigvalsh(Sigma).max())]

    for i in indices:
        Sigma = covariance_update(Sigma, A[int(i)], NOISE_VAR)
        traces.append(float(np.trace(Sigma)))
        max_eigs.append(float(np.linalg.eigvalsh(Sigma).max()))

    return Sigma, np.asarray(traces), np.asarray(max_eigs)


def active_schedule(
    Sigma0: np.ndarray,
    A: np.ndarray,
) -> tuple[list[int], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    Sigma = Sigma0.copy()
    remaining = set(range(len(A)))
    selected: list[int] = []
    traces = [float(np.trace(Sigma))]
    max_eigs = [float(np.linalg.eigvalsh(Sigma).max())]
    gains: list[float] = []

    for _ in range(BUDGET):
        best: tuple[float, int] | None = None
        for i in remaining:
            score = expected_information_gain(Sigma, A[i], NOISE_VAR)
            if best is None or score > best[0]:
                best = (score, i)

        assert best is not None
        gain, i = best
        selected.append(i)
        gains.append(gain)
        remaining.remove(i)

        Sigma = covariance_update(Sigma, A[i], NOISE_VAR)
        traces.append(float(np.trace(Sigma)))
        max_eigs.append(float(np.linalg.eigvalsh(Sigma).max()))

    return selected, Sigma, np.asarray(traces), np.asarray(max_eigs), np.asarray(gains)


def proof() -> dict:
    rng = np.random.default_rng(SEED)
    A = make_candidate_pool(rng)
    Sigma0 = np.diag([1, 1, 1, 2, 2, 3, 4, 5]).astype(float)

    selected, Sigma_active, trace_active, maxeig_active, gains = active_schedule(Sigma0, A)

    random_final_trace: list[float] = []
    random_final_maxeig: list[float] = []

    for _ in range(RANDOM_TRIALS):
        ids = rng.choice(CANDIDATE_COUNT, size=BUDGET, replace=False)
        Sigma_r, _, _ = run_schedule(Sigma0, A, ids)
        random_final_trace.append(float(np.trace(Sigma_r)))
        random_final_maxeig.append(float(np.linalg.eigvalsh(Sigma_r).max()))

    random_final_trace_arr = np.asarray(random_final_trace)
    random_final_maxeig_arr = np.asarray(random_final_maxeig)

    active_trace = float(np.trace(Sigma_active))
    active_maxeig = float(np.linalg.eigvalsh(Sigma_active).max())
    random_trace_median = float(np.median(random_final_trace_arr))
    random_maxeig_median = float(np.median(random_final_maxeig_arr))

    gates = {
        "ACTIVE_POSTERIOR_TRACE_LT_RANDOM_MEDIAN": active_trace < random_trace_median,
        "ACTIVE_WORST_DIRECTION_LT_RANDOM_MEDIAN": active_maxeig < random_maxeig_median,
        "ACTIVE_BEATS_ALL_1000_RANDOM_TRACE_IN_THIS_SYNTHETIC_POOL": bool(
            np.all(random_final_trace_arr > active_trace)
        ),
        "ACTIVE_BEATS_ALL_1000_RANDOM_WORST_DIRECTION_IN_THIS_SYNTHETIC_POOL": bool(
            np.all(random_final_maxeig_arr > active_maxeig)
        ),
        "POSTERIOR_TRACE_MONOTONIC_NONINCREASING": bool(
            np.all(np.diff(trace_active) <= 1e-12)
        ),
        "WORST_EIGENVALUE_MONOTONIC_NONINCREASING": bool(
            np.all(np.diff(maxeig_active) <= 1e-12)
        ),
    }

    result = {
        "GAUZ_ACTIVE_LEARNING_PROOF_R01": "PASS" if all(gates.values()) else "FAIL",
        "scope": "synthetic linear-Gaussian active-learning proof only",
        "seed": SEED,
        "latent_dimensions": D,
        "candidate_experiments": CANDIDATE_COUNT,
        "budget_steps": BUDGET,
        "noise_variance": NOISE_VAR,
        "random_baseline_trials": RANDOM_TRIALS,
        "prior_trace": float(np.trace(Sigma0)),
        "active_final_trace": active_trace,
        "random_median_final_trace": random_trace_median,
        "trace_reduction_vs_random_median_fraction": 1.0 - active_trace / random_trace_median,
        "active_worst_direction_variance": active_maxeig,
        "random_median_worst_direction_variance": random_maxeig_median,
        "worst_direction_reduction_vs_random_median_fraction": 1.0 - active_maxeig / random_maxeig_median,
        "fraction_random_schedules_worse_on_trace": float(
            np.mean(random_final_trace_arr > active_trace)
        ),
        "fraction_random_schedules_worse_on_worst_direction": float(
            np.mean(random_final_maxeig_arr > active_maxeig)
        ),
        "total_expected_information_gain_nats": float(gains.sum()),
        "selected_experiment_ids": selected,
        "pass_gates": gates,
    }
    return result


if __name__ == "__main__":
    result = proof()
    print(json.dumps(result, indent=2))
    if result["GAUZ_ACTIVE_LEARNING_PROOF_R01"] != "PASS":
        raise SystemExit(1)
