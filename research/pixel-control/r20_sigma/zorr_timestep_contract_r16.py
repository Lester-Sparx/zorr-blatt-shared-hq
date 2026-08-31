from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

PINNED_DIFFUSERS_REF = "c1bf18c92c6285334adcaac7e75ef8946a227f49"
FRESH_DIFFUSERS_MAIN = "2e618cb6027037597cf80905fc3e356a71923087"
PIPELINE_BLOB = "3f18cbe21d0fe12f89859d188dba2a487f3d87c5"
EULER_SCHEDULER_BLOB = "eac6efe18aaf775b846e7536fd972686d3ec9683"
EULER_TEST_BLOB = "ee99465abfc39e7a7ce7a6734b22dbeb42df5efd"

EXPECTED_MODEL_ID = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
EXPECTED_MODEL_REVISION = "212ee7d92278cfec477f0ccd1e369cd9d6e9c7e3"
EXPECTED_PIPELINE = "StableDiffusionXLInpaintPipeline"
EXPECTED_STEPS = 20
EXPECTED_STRENGTH = 0.99
EXPECTED_GUIDANCE = 8.0
EXPECTED_SEED = 0

EXPECTED_SCHEDULER = {
    "_class_name": "EulerDiscreteScheduler",
    "num_train_timesteps": 1000,
    "timestep_spacing": "leading",
    "steps_offset": 1,
    "beta_schedule": "scaled_linear",
    "beta_start": 0.00085,
    "beta_end": 0.012,
    "interpolation_type": "linear",
    "prediction_type": "epsilon",
    "use_karras_sigmas": False,
}


@dataclass(frozen=True)
class TimestepContractR16:
    requested_num_inference_steps: int
    strength: float
    scheduler_order: int
    init_timestep: int
    t_start: int
    effective_denoising_steps: int
    requested_timesteps: List[int]
    effective_timesteps: List[int]
    initial_noise_timestep: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_r04_manifest(r04: Dict[str, Any]) -> None:
    selected = r04.get("selected_model", {})
    baseline = r04.get("source_derived_baseline", {})
    framework = r04.get("framework", {})
    expected = {
        "model_id": EXPECTED_MODEL_ID,
        "immutable_revision": EXPECTED_MODEL_REVISION,
        "pipeline_class": EXPECTED_PIPELINE,
        "variant": "fp16",
        "format": "safetensors",
    }
    for key, value in expected.items():
        if selected.get(key) != value:
            raise ValueError(f"R04 selected_model drift: {key}")
    if framework.get("revision") != PINNED_DIFFUSERS_REF:
        raise ValueError("R04 Diffusers pin drift")
    baseline_expected = {
        "num_inference_steps": EXPECTED_STEPS,
        "guidance_scale": EXPECTED_GUIDANCE,
        "strength": EXPECTED_STRENGTH,
        "seed": EXPECTED_SEED,
    }
    for key, value in baseline_expected.items():
        if baseline.get(key) != value:
            raise ValueError(f"R04 source-derived baseline drift: {key}")


def validate_scheduler_config(config: Dict[str, Any]) -> None:
    for key, value in EXPECTED_SCHEDULER.items():
        if config.get(key) != value:
            raise ValueError(f"scheduler config drift: {key}")


def euler_leading_timesteps(num_inference_steps: int, scheduler_config: Dict[str, Any]) -> List[int]:
    """Mirror the pinned EulerDiscreteScheduler leading timestep-index rule.

    This intentionally derives integer timestep indices only. It does not attempt
    to reproduce the sigma vector or model inference.
    """
    validate_scheduler_config(scheduler_config)
    if not isinstance(num_inference_steps, int) or num_inference_steps <= 0:
        raise ValueError("num_inference_steps must be a positive integer")
    train_steps = int(scheduler_config["num_train_timesteps"])
    step_ratio = train_steps // num_inference_steps
    offset = int(scheduler_config["steps_offset"])
    # Pinned source: arange(0,N) * floor(train/N), round, reverse, + offset.
    return [int(i * step_ratio + offset) for i in range(num_inference_steps - 1, -1, -1)]


def derive_contract(
    num_inference_steps: int,
    strength: float,
    scheduler_config: Dict[str, Any],
    scheduler_order: int = 1,
) -> TimestepContractR16:
    if not (0.0 < strength <= 1.0):
        raise ValueError("strength must be in (0,1]")
    if scheduler_order != 1:
        raise ValueError("R16 selected Euler scheduler contract expects order=1")

    requested = euler_leading_timesteps(num_inference_steps, scheduler_config)
    # Pinned SDXL inpaint get_timesteps(): Python int truncates toward zero.
    init_timestep = min(int(num_inference_steps * strength), num_inference_steps)
    t_start = max(num_inference_steps - init_timestep, 0)
    effective = requested[t_start * scheduler_order :]
    effective_steps = num_inference_steps - t_start
    if len(effective) != effective_steps:
        raise AssertionError("source-derived timestep length invariant failed")
    if not effective:
        raise ValueError("effective denoising schedule is empty")

    return TimestepContractR16(
        requested_num_inference_steps=num_inference_steps,
        strength=strength,
        scheduler_order=scheduler_order,
        init_timestep=init_timestep,
        t_start=t_start,
        effective_denoising_steps=effective_steps,
        requested_timesteps=requested,
        effective_timesteps=effective,
        initial_noise_timestep=effective[0],
    )


def derive_selected_r04_contract(r04: Dict[str, Any], scheduler_config: Dict[str, Any]) -> TimestepContractR16:
    validate_r04_manifest(r04)
    baseline = r04["source_derived_baseline"]
    return derive_contract(
        int(baseline["num_inference_steps"]),
        float(baseline["strength"]),
        scheduler_config,
        scheduler_order=1,
    )
