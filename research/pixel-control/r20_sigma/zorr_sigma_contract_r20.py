from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch

import zorr_timestep_contract_r16 as r16

SCHEMA = "ZORR_SIGMA_CONTRACT_R20"
PINNED_DIFFUSERS_REF = r16.PINNED_DIFFUSERS_REF
FRESH_DIFFUSERS_MAIN = "2e618cb6027037597cf80905fc3e356a71923087"
PIPELINE_BLOB = "3f18cbe21d0fe12f89859d188dba2a487f3d87c5"
EULER_SCHEDULER_BLOB = "eac6efe18aaf775b846e7536fd972686d3ec9683"
EULER_TEST_BLOB = "ee99465abfc39e7a7ce7a6734b22dbeb42df5efd"
DIFFUSERS_LICENSE_BLOB = "038e32f6445e8f265bde482613cf0d2f43d86dbc"

# Exact durable predecessor identities from /ZORR/PixelControl.
R04_MANIFEST_SHA256 = "c7c334cebe94dbad833f89b436771a18a7f46983842bf0d114054a0a573b1c95"
R16_CODE_SHA256 = "cfaf3773628f19a7353425f92826fdfebb2f95a6971dc8e7a9c34c8fec1a4f62"
R16_MANIFEST_SHA256 = "48e2bef311c5d12de3c4472b5925bf07ced8322c579e9968792b0ddac34e11e5"
R16_TEST_SHA256 = "a3ec95bb4c9fd106e75cabc787e2097966c0f4905d3d8a5251b5f15fc0257a7d"

# Defaults in pinned EulerDiscreteScheduler.__init__ that materially control
# the selected non-custom sigma path but were not all explicit in R16's
# model scheduler_config. We bind them explicitly here rather than relying on
# future library defaults.
EXPECTED_SIGMA_DEFAULTS = {
    "trained_betas": None,
    "rescale_betas_zero_snr": False,
    "use_exponential_sigmas": False,
    "use_beta_sigmas": False,
    "final_sigmas_type": "zero",
    "timestep_type": "discrete",
}


@dataclass(frozen=True)
class SigmaContractR20:
    requested_timesteps: List[int]
    full_sigma_count: int
    begin_index: int
    denoise_sigma_count: int
    successor_sigma_count: int
    full_sigmas_sha256_le_f32: str
    denoise_sigmas_sha256_le_f32: str
    successor_sigmas_sha256_le_f32: str
    initial_add_noise_sigma_f32: float
    first_step_sigma_f32: float
    terminal_successor_sigma_f32: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_predecessor_identity(root: Path) -> Dict[str, str]:
    expected = {
        "zorr_backend_manifest_r04.json": R04_MANIFEST_SHA256,
        "zorr_timestep_contract_r16.py": R16_CODE_SHA256,
        "zorr_timestep_contract_r16_manifest.json": R16_MANIFEST_SHA256,
        "test_zorr_timestep_contract_r16.py": R16_TEST_SHA256,
    }
    got: Dict[str, str] = {}
    for name, want in expected.items():
        path = root / name
        if not path.is_file():
            raise ValueError(f"missing predecessor artifact: {name}")
        digest = sha256_file(path)
        if digest != want:
            raise ValueError(f"predecessor identity drift: {name}")
        got[name] = digest
    return got


def validate_effective_scheduler_contract(
    scheduler_config: Dict[str, Any],
    effective_defaults: Dict[str, Any],
) -> None:
    r16.validate_scheduler_config(scheduler_config)
    for key, value in EXPECTED_SIGMA_DEFAULTS.items():
        if effective_defaults.get(key) != value:
            raise ValueError(f"sigma-affecting/default scheduler drift: {key}")

    # Selected R20 path must remain the ordinary model-config schedule. Custom
    # timesteps/sigmas would be a different execution contract.
    if scheduler_config["use_karras_sigmas"] is not False:
        raise ValueError("R20 selected path requires use_karras_sigmas=False")


def _float32_bytes(arr: np.ndarray) -> bytes:
    a = np.asarray(arr, dtype=np.float32)
    # Stable content identity is explicitly little-endian IEEE-754 binary32.
    return a.astype("<f4", copy=False).tobytes(order="C")


def float32_sha256(arr: np.ndarray) -> str:
    return hashlib.sha256(_float32_bytes(arr)).hexdigest()


def derive_full_sigmas_source_equivalent(
    scheduler_config: Dict[str, Any],
    effective_defaults: Dict[str, Any],
    num_inference_steps: int,
) -> np.ndarray:
    """Mirror the pinned EulerDiscreteScheduler selected sigma path.

    This function intentionally reproduces only scheduler scalar construction.
    It does not instantiate a Diffusers pipeline, load model weights, generate
    latents, or claim target-CUDA numerical identity.
    """
    validate_effective_scheduler_contract(scheduler_config, effective_defaults)
    if num_inference_steps <= 0:
        raise ValueError("num_inference_steps must be positive")

    train_steps = int(scheduler_config["num_train_timesteps"])
    beta_start = float(scheduler_config["beta_start"])
    beta_end = float(scheduler_config["beta_end"])

    # Pinned source: scaled_linear beta schedule is built in torch.float32.
    betas = torch.linspace(
        beta_start**0.5,
        beta_end**0.5,
        train_steps,
        dtype=torch.float32,
        device="cpu",
    ) ** 2
    alphas = 1.0 - betas
    alphas_cumprod = torch.cumprod(alphas, dim=0)

    # Pinned source converts the training sigma tensor to NumPy and uses
    # np.interp for interpolation_type='linear'.
    training_sigmas = (((1 - alphas_cumprod) / alphas_cumprod) ** 0.5).cpu().numpy()
    timesteps = np.asarray(
        r16.euler_leading_timesteps(num_inference_steps, scheduler_config),
        dtype=np.float32,
    )
    sigmas = np.interp(
        timesteps,
        np.arange(0, len(training_sigmas)),
        training_sigmas,
    )

    # Pinned constructor default final_sigmas_type='zero', explicitly bound by
    # EXPECTED_SIGMA_DEFAULTS above.
    sigmas = np.concatenate([sigmas, [0.0]]).astype(np.float32)
    return sigmas


def derive_selected_contract(
    r04_manifest: Dict[str, Any],
    r16_manifest: Dict[str, Any],
    effective_defaults: Dict[str, Any],
) -> tuple[SigmaContractR20, np.ndarray, np.ndarray, np.ndarray]:
    r16.validate_r04_manifest(r04_manifest)
    scheduler_config = r16_manifest["selected_scheduler_config"]
    validate_effective_scheduler_contract(scheduler_config, effective_defaults)
    timestep_contract = r16.derive_selected_r04_contract(r04_manifest, scheduler_config)

    sigmas = derive_full_sigmas_source_equivalent(
        scheduler_config,
        effective_defaults,
        timestep_contract.requested_num_inference_steps,
    )
    if len(sigmas) != timestep_contract.requested_num_inference_steps + 1:
        raise AssertionError("full sigma count must equal requested steps + terminal sigma")

    begin_index = timestep_contract.t_start * timestep_contract.scheduler_order
    # Pipeline set_begin_index(begin_index) is called before prepare_latents.
    # Scheduler.add_noise() with begin_index set and step_index still None uses
    # sigmas[begin_index]. Scheduler.step() also initializes to begin_index.
    denoise_sigmas = sigmas[begin_index:-1]
    successor_sigmas = sigmas[begin_index + 1 :]

    if len(denoise_sigmas) != timestep_contract.effective_denoising_steps:
        raise AssertionError("effective denoise sigma count mismatch")
    if len(successor_sigmas) != timestep_contract.effective_denoising_steps:
        raise AssertionError("successor sigma count mismatch")
    if float(sigmas[-1]) != 0.0:
        raise AssertionError("selected terminal sigma must be exactly zero")

    c = SigmaContractR20(
        requested_timesteps=timestep_contract.requested_timesteps,
        full_sigma_count=len(sigmas),
        begin_index=begin_index,
        denoise_sigma_count=len(denoise_sigmas),
        successor_sigma_count=len(successor_sigmas),
        full_sigmas_sha256_le_f32=float32_sha256(sigmas),
        denoise_sigmas_sha256_le_f32=float32_sha256(denoise_sigmas),
        successor_sigmas_sha256_le_f32=float32_sha256(successor_sigmas),
        initial_add_noise_sigma_f32=float(sigmas[begin_index]),
        first_step_sigma_f32=float(sigmas[begin_index]),
        terminal_successor_sigma_f32=float(successor_sigmas[-1]),
    )
    return c, sigmas, denoise_sigmas, successor_sigmas


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
