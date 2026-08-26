# SALVADOR v1 CANON REFERENCE EDIT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first real zero-budget SALVADOR production mode that takes one drawn local reference and produces one canon-preserving ComfyUI image-to-image result under `TASK_KIND = CANON_REFERENCE_EDIT` without activating production automatically.

**Architecture:** Keep the accepted controller state/evidence core intact and add a separate production backend beside the disposable smoke backend. The production backend owns immutable canon prompt composition, safe local reference staging into ComfyUI input, deterministic bounded preprocessing, production workflow materialization, model preflight, and provenance capture; the generic controller remains responsible for durable GitHub state, restart safety, result persistence, and duplicate suppression.

**Tech Stack:** Python 3.12+, pytest, Pillow, GitHub CLI, local ComfyUI HTTP API, core ComfyUI SD1.5-class img2img nodes, Windows local filesystem.

**Spec:** `docs/superpowers/specs/2026-08-26-salvador-v1-canon-reference-edit-design.md`

## Global Constraints

- `REFERENCE -> CANON EDIT`; never text-to-image from scratch.
- Preserve identity, geometry, pose, composition, silhouette, major costume/weapon read; no redesign.
- `CANON > prettier output`.
- One drawn single-character reference -> one output image.
- `TASK_KIND = CANON_REFERENCE_EDIT`, `AGENT = SALVADOR`, `REFERENCE = LOCAL_INBOX`, `BACKEND = COMFYUI_LOCAL`.
- Local inference only; zero paid inference APIs and no `OPENAI_API_KEY`.
- Keep the disposable `PRODUCTION_IMAGE_EDIT` / `ImageInvert` smoke path intact for regression proof; never silently repurpose it as production.
- Fixed local input root remains `D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\`; `<TASK_ID>` is the strict parsed task identifier, never issue-controlled path text.
- Production ComfyUI staging is deployment-owned and remains under `D:\BLATT2\ComfyUI_windows_portable\ComfyUI\input`.
- Batch size = 1; output count = 1; first 4 GB target long side <= 768 px; no crop; deterministic aspect-preserving normalization.
- First compatibility baseline is a lightweight SD1.5-class local illustration/anime img2img path with conservative denoise in `0.25..0.45`; optional one structural ControlNet only if a separate local smoke proves it fits reliably.
- Exact production checkpoint/control model names remain external deployment configuration and model binaries are never committed to Shared HQ.
- `RUNNING` only after real ComfyUI returns a non-empty `prompt_id`.
- `RESULT_READY` only after real output bytes, checksum, production provenance, and atomic result metadata are persisted.
- Existing terminal `FAILED`, restart recovery, one-active-SALVADOR GPU lock, GitHub reconciliation, and duplicate suppression laws remain intact.
- Merging implementation is not production activation. `PRODUCTION_ACTIVATION = NO` until the full eight-gate acceptance in the spec passes.
- SALVADOR v2 `TEXTURE_PASS` is out of scope.

## File Structure

- Modify `agent-controller/src/zb_local_controller/task_contract.py` — allow the new explicit task kind only.
- Create `agent-controller/src/zb_local_controller/production_policy.py` — immutable-vs-task prompt composition and mechanically detectable canon-conflict rejection.
- Modify `agent-controller/src/zb_local_controller/config.py` — deployment-owned production paths/model/denoise/size settings.
- Modify `agent-controller/src/zb_local_controller/__main__.py` — register smoke and production backends side by side.
- Create `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py` — production-only staging, preprocessing, workflow materialization, readiness/model preflight, prompt submission, output validation, provenance.
- Modify `agent-controller/src/zb_local_controller/controller.py` — persist optional backend provenance restart-safely without changing state semantics.
- Create `agent-controller/src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt` — immutable repository-owned canon prompt.
- Create `agent-controller/src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json` — separate production img2img template; smoke workflow remains unchanged.
- Modify `agent-controller/pyproject.toml` — add Pillow for deterministic input/output decode and bounded resize.
- Modify `agent-controller/config.example.json` — document production deployment fields with an intentionally empty model name.
- Modify `agent-controller/README.md` — document v1 task contract, local model setup boundary, and non-activation law.
- Modify/add tests under `agent-controller/tests/` for contract, policy, config, production backend, controller provenance, CLI registry, and full regression.

---

### Task 1: Extend the strict task contract and add production canon-policy composition

**Files:**
- Modify: `agent-controller/src/zb_local_controller/task_contract.py`
- Create: `agent-controller/src/zb_local_controller/production_policy.py`
- Modify: `agent-controller/tests/test_task_contract.py`
- Create: `agent-controller/tests/test_production_policy.py`

**Interfaces:**
- Consumes: existing `AgentTask` and strict `ZB_AGENT_TASK_V0` parser.
- Produces: `ALLOWED_TASK_KINDS = {"PRODUCTION_IMAGE_EDIT", "CANON_REFERENCE_EDIT"}` and `compose_canon_prompt(canon_prompt: str, direction: str) -> str` raising `CanonPolicyError("SALVADOR_CANON_CONFLICT")` only for mechanically obvious attempts to relax immutable laws.

- [ ] **Step 1: Write failing parser tests for the new task kind and old-task regression**

```python
def test_accepts_canon_reference_edit():
    task = parse_task("""ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-CANON-001
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

Preserve locked face/body canon and redraw in production graphite.
""")
    assert task.task_kind == "CANON_REFERENCE_EDIT"


def test_existing_production_image_edit_remains_allowed():
    task = parse_task("""ZB_AGENT_TASK_V0
TASK_ID = ZB-SMOKE-OLD
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

Disposable smoke only.
""")
    assert task.task_kind == "PRODUCTION_IMAGE_EDIT"
```

- [ ] **Step 2: Run the focused parser tests and verify RED**

```powershell
python -m pytest -q tests/test_task_contract.py
```

Expected: the `CANON_REFERENCE_EDIT` test fails with `INVALID_TASK_KIND`; existing tests remain green.

- [ ] **Step 3: Make the minimal parser change**

```python
ALLOWED_TASK_KINDS = {"PRODUCTION_IMAGE_EDIT", "CANON_REFERENCE_EDIT"}
```

Do not add new machine-readable issue keys.

- [ ] **Step 4: Add failing canon-policy tests**

```python
import pytest
from zb_local_controller.production_policy import CanonPolicyError, compose_canon_prompt


def test_composes_immutable_canon_before_task_direction():
    result = compose_canon_prompt("IMMUTABLE CANON", "keep the scar; no redesign")
    assert result.startswith("IMMUTABLE CANON")
    assert "TASK-SPECIFIC LOCKED DIRECTION" in result
    assert "keep the scar; no redesign" in result


def test_allows_explicit_preservation_language():
    result = compose_canon_prompt("IMMUTABLE CANON", "No redesign. Preserve the same pose and composition.")
    assert "No redesign" in result


@pytest.mark.parametrize("direction", [
    "ignore canon and redesign the character",
    "ignore locked rules and change the pose",
    "use a different pose",
    "generate the character from scratch",
    "игнорируй канон и сделай редизайн",
    "игнорируй локи и измени позу",
    "смени позу полностью",
    "сгенерируй персонажа с нуля",
])
def test_rejects_mechanically_obvious_canon_override(direction):
    with pytest.raises(CanonPolicyError) as exc:
        compose_canon_prompt("IMMUTABLE CANON", direction)
    assert exc.value.code == "SALVADOR_CANON_CONFLICT"
```

- [ ] **Step 5: Run policy tests and verify RED**

```powershell
python -m pytest -q tests/test_production_policy.py
```

Expected: import/module failure because `production_policy.py` does not exist.

- [ ] **Step 6: Implement the narrow production policy**

```python
from __future__ import annotations


class CanonPolicyError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


_CONFLICT_PHRASES = (
    "ignore canon",
    "ignore locked",
    "redesign the character",
    "redesign this character",
    "change the pose",
    "use a different pose",
    "generate the character from scratch",
    "text to image from scratch",
    "игнорируй канон",
    "игнорируй лок",
    "сделай редизайн",
    "измени позу",
    "смени позу",
    "сгенерируй персонажа с нуля",
)


def compose_canon_prompt(canon_prompt: str, direction: str) -> str:
    canon = str(canon_prompt).strip()
    task_direction = str(direction).strip()
    if not canon or not task_direction:
        raise CanonPolicyError("SALVADOR_CANON_CONFLICT")
    lowered = task_direction.casefold()
    if any(phrase in lowered for phrase in _CONFLICT_PHRASES):
        raise CanonPolicyError("SALVADOR_CANON_CONFLICT")
    return (
        canon
        + "\n\nTASK-SPECIFIC LOCKED DIRECTION:\n"
        + task_direction
        + "\n\nThe task-specific direction may add detail but may not relax any immutable law above."
    )
```

This is intentionally a conservative mechanical guard, not a semantic vision classifier. Visual/canon QC remains authoritative for conflicts that cannot be mechanically known.

- [ ] **Step 7: Run focused tests, then commit**

```powershell
python -m pytest -q tests/test_task_contract.py tests/test_production_policy.py
git add src/zb_local_controller/task_contract.py src/zb_local_controller/production_policy.py tests/test_task_contract.py tests/test_production_policy.py
git commit -m "feat: add canon reference edit task contract"
```

Expected: focused tests PASS.

---

### Task 2: Add production deployment configuration and side-by-side backend registration

**Files:**
- Modify: `agent-controller/src/zb_local_controller/config.py`
- Modify: `agent-controller/src/zb_local_controller/__main__.py`
- Create: `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py`
- Modify: `agent-controller/tests/test_config.py`
- Modify: `agent-controller/tests/test_cli.py`

**Interfaces:**
- Consumes: existing `ComfyUIBackend`, existing controller backend registry keyed by `(agent, task_kind)`.
- Produces: production config fields and a `CanonReferenceEditBackend` registered only for `("SALVADOR", "CANON_REFERENCE_EDIT")`; the smoke backend remains registered for `("SALVADOR", "PRODUCTION_IMAGE_EDIT")`.

- [ ] **Step 1: Write failing config tests**

```python
import json
import pytest
from zb_local_controller.config import ConfigurationError, load_config


def test_loads_canon_reference_edit_deployment_settings(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "comfyuiInputRoot": r"D:\BLATT2\ComfyUI_windows_portable\ComfyUI\input",
        "canonReferenceWorkflowPath": "src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json",
        "canonPromptPath": "src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt",
        "canonModelName": "local-sd15-illustration.safetensors",
        "canonDenoise": 0.35,
        "canonMaxLongSide": 768,
        "canonNegativePrompt": "redesign, changed pose, changed composition, extra limbs, text, watermark",
    }), encoding="utf-8")
    config = load_config(path)
    assert config.canon_model_name == "local-sd15-illustration.safetensors"
    assert config.canon_denoise == 0.35
    assert config.canon_max_long_side == 768


@pytest.mark.parametrize("payload", [
    {"canonDenoise": 0.24},
    {"canonDenoise": 0.46},
    {"canonMaxLongSide": 769},
])
def test_rejects_out_of_policy_canon_settings(tmp_path, payload):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ConfigurationError) as exc:
        load_config(path)
    assert exc.value.code == "CONFIG_INVALID"
```

- [ ] **Step 2: Run config tests and verify RED**

```powershell
python -m pytest -q tests/test_config.py
```

Expected: unknown deployment keys or missing attributes.

- [ ] **Step 3: Extend `ControllerConfig` and `load_config`**

Add safe non-activated defaults:

```python
comfyui_input_root: Path = Path(r"D:\BLATT2\ComfyUI_windows_portable\ComfyUI\input")
canon_reference_workflow_path: Path = Path("src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json")
canon_prompt_path: Path = Path("src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt")
canon_model_name: str = ""
canon_denoise: float = 0.35
canon_max_long_side: int = 768
canon_negative_prompt: str = "redesign, changed pose, changed composition, extra limbs, text, watermark"
```

Allow JSON keys:

```text
comfyuiInputRoot
canonReferenceWorkflowPath
canonPromptPath
canonModelName
canonDenoise
canonMaxLongSide
canonNegativePrompt
```

Construct the dataclass first, then validate:

```python
if not 0.25 <= config.canon_denoise <= 0.45:
    raise ConfigurationError("CONFIG_INVALID")
if not 64 <= config.canon_max_long_side <= 768:
    raise ConfigurationError("CONFIG_INVALID")
```

An empty `canonModelName` is valid static configuration but production model preflight must fail closed when a production task is attempted.

- [ ] **Step 4: Create the backend constructor skeleton**

```python
from __future__ import annotations
from pathlib import Path
from typing import Any
from .comfyui import ComfyUIBackend


class CanonReferenceEditBackend(ComfyUIBackend):
    WORKFLOW_VERSION = "salvador-canon-reference-edit-v1"
    CANON_PROMPT_VERSION = "salvador-canon-v1"

    def __init__(
        self,
        base_url: str,
        workflow_path: Path,
        canon_prompt_path: Path,
        comfyui_input_root: Path,
        model_name: str,
        denoise: float,
        max_long_side: int,
        negative_prompt: str,
        transport: Any | None = None,
    ):
        super().__init__(base_url, workflow_path, transport=transport)
        self.canon_prompt_path = Path(canon_prompt_path)
        self.comfyui_input_root = Path(comfyui_input_root)
        self.model_name = str(model_name)
        self.denoise = float(denoise)
        self.max_long_side = int(max_long_side)
        self.negative_prompt = str(negative_prompt)
        self._execution_metadata: dict[str, dict[str, Any]] = {}
```

- [ ] **Step 5: Write a failing CLI registry test and switch CLI injection to a registry factory**

Change `main()` injection from a single `backend_factory` to:

```python
backend_registry_factory: Callable[[ControllerConfig], dict[tuple[str, str], Any]] = _default_backend_registry
```

Build registry exactly:

```python
def _default_backend_registry(config: ControllerConfig):
    smoke = ComfyUIBackend(config.comfyui_url, config.workflow_path)
    canon = CanonReferenceEditBackend(
        base_url=config.comfyui_url,
        workflow_path=config.canon_reference_workflow_path,
        canon_prompt_path=config.canon_prompt_path,
        comfyui_input_root=config.comfyui_input_root,
        model_name=config.canon_model_name,
        denoise=config.canon_denoise,
        max_long_side=config.canon_max_long_side,
        negative_prompt=config.canon_negative_prompt,
    )
    return {
        ("SALVADOR", "PRODUCTION_IMAGE_EDIT"): smoke,
        ("SALVADOR", "CANON_REFERENCE_EDIT"): canon,
    }
```

The CLI test must inject a registry factory returning two sentinel backend objects and assert `Controller.backend_registry` receives both exact keys. No backend method is called merely by constructing the CLI.

- [ ] **Step 6: Run focused tests, then commit**

```powershell
python -m pytest -q tests/test_config.py tests/test_cli.py
git add src/zb_local_controller/config.py src/zb_local_controller/__main__.py src/zb_local_controller/backends/canon_reference_edit.py tests/test_config.py tests/test_cli.py
git commit -m "feat: register canon reference edit backend"
```

Expected: focused tests PASS; smoke CLI behavior remains available.

---

### Task 3: Add deterministic safe reference staging and bounded preprocessing

**Files:**
- Modify: `agent-controller/pyproject.toml`
- Modify: `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py`
- Create: `agent-controller/tests/test_canon_reference_edit.py`

**Interfaces:**
- Consumes: validated `ReferenceFile.path`, strict `task.task_id`, deployment-owned `comfyui_input_root`.
- Produces: `_stage_reference(task, reference) -> StagedReference` with filesystem path, ComfyUI-relative input name, source SHA-256, working width, and working height.

- [ ] **Step 1: Add Pillow and create an exact test scaffold**

In `pyproject.toml`:

```toml
dependencies = ["Pillow>=11"]
```

Start `tests/test_canon_reference_edit.py` with:

```python
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from PIL import Image

from zb_local_controller.backends.base import BackendError
from zb_local_controller.backends.canon_reference_edit import CanonReferenceEditBackend
from zb_local_controller.task_contract import AgentTask

TASK = AgentTask(
    "ZB-SALVADOR-CANON-001",
    "SALVADOR",
    "CANON_REFERENCE_EDIT",
    "ASSIGNED",
    "LOCAL_INBOX",
    "No redesign. Preserve the same pose and composition.",
)


class FakeTransport:
    def __init__(self, json_responses=None, byte_responses=None, errors=None):
        self.json_responses = list(json_responses or [])
        self.byte_responses = list(byte_responses or [])
        self.errors = list(errors or [])
        self.calls = []

    def request_json(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if self.errors:
            error = self.errors.pop(0)
            if error is not None:
                raise error
        return self.json_responses.pop(0) if self.json_responses else {}

    def request_bytes(self, path):
        self.calls.append(("GET_BYTES", path, None))
        return self.byte_responses.pop(0) if self.byte_responses else b""


def make_backend(tmp_path, transport=None, model_name="local-model.safetensors"):
    workflow = tmp_path / "workflow.json"
    workflow.write_text("{}", encoding="utf-8")
    prompt = tmp_path / "canon.txt"
    prompt.write_text("IMMUTABLE CANON", encoding="utf-8")
    return CanonReferenceEditBackend(
        base_url="http://127.0.0.1:8188",
        workflow_path=workflow,
        canon_prompt_path=prompt,
        comfyui_input_root=tmp_path / "comfy-input",
        model_name=model_name,
        denoise=0.35,
        max_long_side=768,
        negative_prompt="redesign, changed pose, extra limbs",
        transport=transport or FakeTransport(),
    )
```

- [ ] **Step 2: Write failing staging tests**

```python
def test_stages_large_reference_as_bounded_png_without_crop(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (1600, 900), "white").save(source)
    source_bytes = source.read_bytes()
    staged = make_backend(tmp_path)._stage_reference(TASK, SimpleNamespace(path=source))
    assert staged.path.parent == tmp_path / "comfy-input" / "ZB_CANON_REFERENCE_EDIT"
    assert staged.comfyui_name == f"ZB_CANON_REFERENCE_EDIT/{staged.path.name}"
    assert staged.path.name.startswith("ZB-SALVADOR-CANON-001-")
    assert staged.path.suffix == ".png"
    assert max(staged.working_width, staged.working_height) == 768
    assert abs((staged.working_width / staged.working_height) - (1600 / 900)) < 0.01
    assert staged.source_sha256 == hashlib.sha256(source_bytes).hexdigest()


def test_does_not_upscale_reference(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (512, 700), "white").save(source)
    staged = make_backend(tmp_path)._stage_reference(TASK, SimpleNamespace(path=source))
    assert (staged.working_width, staged.working_height) == (512, 700)


def test_corrupt_reference_is_stable_unsupported_input(tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"not an image")
    with pytest.raises(BackendError) as exc:
        make_backend(tmp_path)._stage_reference(TASK, SimpleNamespace(path=source))
    assert exc.value.code == "SALVADOR_UNSUPPORTED_INPUT"
```

- [ ] **Step 3: Run staging tests and verify RED**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py
```

Expected: missing `StagedReference` / `_stage_reference`.

- [ ] **Step 4: Implement deterministic staging**

```python
from dataclasses import dataclass
from hashlib import sha256
import os
from PIL import Image


@dataclass(frozen=True)
class StagedReference:
    path: Path
    comfyui_name: str
    source_sha256: str
    working_width: int
    working_height: int
```

Algorithm:

1. Read source bytes and SHA-256 them.
2. Decode with Pillow and force `image.load()`; decode failure -> `BackendError("SALVADOR_UNSUPPORTED_INPUT")`.
3. Convert to RGB.
4. If long side > `max_long_side`, call `thumbnail((max_long_side, max_long_side), Image.Resampling.LANCZOS)`; otherwise do not resize.
5. Never crop and never upscale.
6. Create `<comfyui_input_root>/ZB_CANON_REFERENCE_EDIT`.
7. Filename is `<task.task_id>-<source_sha256[:12]>.png`.
8. Save a PNG to a `.tmp` sibling and atomically `os.replace` it.
9. Return `comfyui_name = "ZB_CANON_REFERENCE_EDIT/" + filename` so ComfyUI `LoadImage` can resolve the subdirectory safely.

- [ ] **Step 5: Add idempotence test**

Call `_stage_reference` twice for the same task/source and assert exact same path, `comfyui_name`, SHA-256, dimensions, and staged bytes.

- [ ] **Step 6: Run focused tests, then commit**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py
git add pyproject.toml src/zb_local_controller/backends/canon_reference_edit.py tests/test_canon_reference_edit.py
git commit -m "feat: stage canon references safely"
```

Expected: all staging tests PASS.

---

### Task 4: Add immutable canon prompt asset and separate SD1.5 img2img workflow materialization

**Files:**
- Create: `agent-controller/src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt`
- Create: `agent-controller/src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json`
- Modify: `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py`
- Modify: `agent-controller/tests/test_canon_reference_edit.py`

**Interfaces:**
- Consumes: `StagedReference`, external model name, immutable canon prompt file, task direction, negative prompt, configured denoise.
- Produces: `_materialize_workflow(task, staged) -> tuple[dict[str, Any], int]`, returning a fully typed ComfyUI prompt and deterministic seed with no unresolved `__ZB_*__` tokens.

- [ ] **Step 1: Write the immutable prompt asset exactly**

```text
ZORR BLATT SALVADOR CANON REFERENCE EDIT V1.
Redraw the supplied existing drawn character reference into the approved ZORR BLATT production drawing canon.
Preserve the same character identity/read, head-body relationship, body proportions, pose, framing, composition, silhouette, limb placement, major costume shapes, weapon placement, major asymmetries, and major value/color zones that matter to the character.
Do not redesign the character. Do not invent a new pose. Do not change the composition. Do not convert this task into text-to-image from scratch. Do not add a second character. Do not beautify at the expense of locked canon.
Simplify micro-detail and visual noise only when that simplification follows approved production drawing rules.
Locked project canon outranks locked character canon; locked character canon outranks task-specific direction; task-specific direction outranks source micro-detail; all canon outranks model aesthetic preference.
CANON > prettier output.
One input character. One output image.
```

- [ ] **Step 2: Create the baseline production workflow JSON**

Use only these core img2img nodes:

```json
{
  "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "__ZB_MODEL__"}},
  "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "__ZB_POSITIVE_PROMPT__", "clip": ["1", 1]}},
  "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "__ZB_NEGATIVE_PROMPT__", "clip": ["1", 1]}},
  "4": {"class_type": "LoadImage", "inputs": {"image": "__ZB_REFERENCE__"}},
  "5": {"class_type": "VAEEncode", "inputs": {"pixels": ["4", 0], "vae": ["1", 2]}},
  "6": {"class_type": "KSampler", "inputs": {"seed": "__ZB_SEED__", "steps": 20, "cfg": 6.0, "sampler_name": "euler", "scheduler": "normal", "denoise": "__ZB_DENOISE__", "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["5", 0]}},
  "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
  "8": {"class_type": "SaveImage", "inputs": {"filename_prefix": "ZB_CANON_REFERENCE_EDIT", "images": ["7", 0]}}
}
```

Do not add `EmptyLatentImage`, ControlNet, multi-image batch, upscale, or texture/material nodes.

- [ ] **Step 3: Write failing materialization tests**

Tests must assert the template contains exact counts:

```text
__ZB_REFERENCE__ = 1
__ZB_MODEL__ = 1
__ZB_POSITIVE_PROMPT__ = 1
__ZB_NEGATIVE_PROMPT__ = 1
__ZB_DENOISE__ = 1
__ZB_SEED__ = 1
```

After materialization, recursively assert no string begins with `__ZB_`; `KSampler.inputs.seed` is `int`; `denoise` is `float`; LoadImage uses `staged.comfyui_name`.

- [ ] **Step 4: Implement `_materialize_workflow`**

Read the workflow JSON and immutable prompt. Compose positive prompt with `compose_canon_prompt`; catch `CanonPolicyError` and re-raise `BackendError(exc.code)` so controller error handling stays intact.

Derive seed:

```python
seed_bytes = hashlib.sha256(f"{task.task_id}:{staged.source_sha256}".encode("utf-8")).digest()[:8]
seed = int.from_bytes(seed_bytes, "big") & ((1 << 63) - 1)
```

Replace exact tokens recursively with typed values. Any token-count mismatch, malformed JSON, missing prompt asset, or unresolved `__ZB_` token -> `BackendError("SALVADOR_RESULT_INVALID")` before HTTP submit.

- [ ] **Step 5: Assert immutable precedence and benign preservation language**

A materialized positive prompt must begin with the repository prompt and contain task direction only after `TASK-SPECIFIC LOCKED DIRECTION`. `No redesign. Preserve the same pose.` must be accepted; `ignore canon and redesign the character` must fail before POST `/prompt`.

- [ ] **Step 6: Run focused tests, then commit**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py tests/test_production_policy.py
git add src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json src/zb_local_controller/backends/canon_reference_edit.py tests/test_canon_reference_edit.py
git commit -m "feat: add canon img2img workflow"
```

Expected: focused tests PASS and disposable smoke workflow remains untouched.

---

### Task 5: Add production ComfyUI readiness/model preflight, submit, and output validation

**Files:**
- Modify: `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py`
- Modify: `agent-controller/tests/test_canon_reference_edit.py`

**Interfaces:**
- Consumes: ComfyUI `/system_stats`, `/object_info`, `/prompt`, `/history/<prompt_id>`, `/view`, external `canon_model_name`.
- Produces: fail-closed `ensure_ready()`, real production `submit() -> str`, inherited-compatible `poll()`, validated `collect() -> bytes`, and `execution_metadata(execution_id) -> dict[str, Any]`.

- [ ] **Step 1: Write exact failing readiness tests**

```python
def test_missing_model_name_fails_closed(tmp_path):
    b = make_backend(tmp_path, model_name="")
    with pytest.raises(BackendError) as exc:
        b.ensure_ready()
    assert exc.value.code == "SALVADOR_MODEL_UNAVAILABLE"


def test_unreachable_comfyui_maps_to_stable_salvador_error(tmp_path):
    transport = FakeTransport(errors=[OSError("down")])
    b = make_backend(tmp_path, transport=transport)
    with pytest.raises(BackendError) as exc:
        b.ensure_ready()
    assert exc.value.code == "SALVADOR_BACKEND_UNAVAILABLE"
```

Add a ready fixture where `/system_stats` succeeds and `/object_info` contains all required classes but `CheckpointLoaderSimple.input.required.ckpt_name[0]` excludes `local-model.safetensors`; assert `SALVADOR_MODEL_UNAVAILABLE`.

Add a fixture missing `KSampler`; assert `SALVADOR_BACKEND_UNAVAILABLE`.

- [ ] **Step 2: Run focused readiness tests and verify RED**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py -k "model_name or unreachable or preflight"
```

- [ ] **Step 3: Implement readiness preflight**

```python
_REQUIRED_NODES = {
    "CheckpointLoaderSimple",
    "CLIPTextEncode",
    "LoadImage",
    "VAEEncode",
    "KSampler",
    "VAEDecode",
    "SaveImage",
}
```

Order:

1. empty model -> `SALVADOR_MODEL_UNAVAILABLE`;
2. `GET /system_stats` transport failure -> `SALVADOR_BACKEND_UNAVAILABLE`;
3. `GET /object_info`; missing required class -> `SALVADOR_BACKEND_UNAVAILABLE`;
4. require exact configured model filename in checkpoint choices -> `SALVADOR_MODEL_UNAVAILABLE` otherwise.

Never fuzzy-match or auto-select a checkpoint.

- [ ] **Step 4: Write failing real-submit metadata test**

Create a 512x512 test reference and `FakeTransport(json_responses=[{"prompt_id": "canon-prompt-1"}])`. Call `submit(TASK, REF)` and assert exact return `canon-prompt-1`, one POST `/prompt`, and metadata:

```python
meta = b.execution_metadata("canon-prompt-1")
assert meta["taskKind"] == "CANON_REFERENCE_EDIT"
assert meta["workflowVersion"] == "salvador-canon-reference-edit-v1"
assert meta["canonPromptVersion"] == "salvador-canon-v1"
assert meta["modelId"] == "local-model.safetensors"
assert meta["workingWidth"] == 512
assert meta["workingHeight"] == 512
assert meta["sourceSha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
assert meta["denoise"] == 0.35
assert isinstance(meta["seed"], int)
```

- [ ] **Step 5: Implement submit and provenance capture**

`submit()` must:

1. `_stage_reference(task, reference)`;
2. `_materialize_workflow(task, staged)`;
3. POST `{"prompt": workflow}` to `/prompt`;
4. transport failure or missing/blank `prompt_id` -> `BackendError("SALVADOR_BACKEND_UNAVAILABLE")`;
5. record metadata keyed by the real prompt id;
6. return the real prompt id.

`execution_metadata()` returns a defensive copy.

- [ ] **Step 6: Add production poll/collect validation tests**

Test transport failure maps to `SALVADOR_BACKEND_UNAVAILABLE`; completed history without exactly one image maps to `SALVADOR_RESULT_INVALID`; collected empty/non-PNG bytes maps to `SALVADOR_RESULT_INVALID`.

For a valid PNG, `collect()` must decode with Pillow via `Image.open(BytesIO(content)); image.load()` and require positive dimensions. Decode/format failure -> `SALVADOR_RESULT_INVALID`.

- [ ] **Step 7: Run focused tests, then commit**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py
git add src/zb_local_controller/backends/canon_reference_edit.py tests/test_canon_reference_edit.py
git commit -m "feat: preflight canon ComfyUI deployment"
```

Expected: production backend tests PASS.

---

### Task 6: Persist production provenance restart-safely in `execution.json` and `result.json`

**Files:**
- Modify: `agent-controller/src/zb_local_controller/controller.py`
- Modify: `agent-controller/tests/test_controller.py`

**Interfaces:**
- Consumes: optional backend method `execution_metadata(execution_id) -> dict[str, Any]`.
- Produces: execution journal field `backendMetadata` and final production provenance without changing old smoke result validity or state transitions.

- [ ] **Step 1: Write failing provenance persistence test**

Use a fake backend returning `canon-prompt-1` and:

```python
def execution_metadata(self, execution_id):
    return {
        "taskKind": "CANON_REFERENCE_EDIT",
        "workflowVersion": "salvador-canon-reference-edit-v1",
        "canonPromptVersion": "salvador-canon-v1",
        "modelId": "local-model.safetensors",
        "workingWidth": 512,
        "workingHeight": 768,
        "sourceSha256": "a" * 64,
        "seed": 123,
        "denoise": 0.35,
    }
```

After submit, `execution.json` must contain that exact object under `backendMetadata`. After completion:

```python
assert meta["taskKind"] == "CANON_REFERENCE_EDIT"
assert meta["workflowVersion"] == "salvador-canon-reference-edit-v1"
assert meta["canonPromptVersion"] == "salvador-canon-v1"
assert meta["modelId"] == "local-model.safetensors"
assert meta["workingWidth"] == 512
assert meta["workingHeight"] == 768
assert meta["promptId"] == "canon-prompt-1"
assert meta["resultSha256"] == meta["sha256"]
```

- [ ] **Step 2: Add restart test before implementation**

Controller A submits once and persists journal. Controller B starts from the same result root before RESULT_READY. Assert B reconstructs the same execution id and never calls `submit()` a second time. Final result retains original `backendMetadata` from the journal.

- [ ] **Step 3: Run focused tests and verify RED**

```powershell
python -m pytest -q tests/test_controller.py -k "metadata or provenance or restart"
```

- [ ] **Step 4: Implement optional metadata capture at submit**

```python
metadata_fn = getattr(backend, "execution_metadata", None)
backend_metadata = metadata_fn(execution_id) if callable(metadata_fn) else {}
self._persist_execution_journal(task, execution_id, backend_metadata)
```

Journal payload:

```python
{
    "taskId": task.task_id,
    "executionId": execution_id,
    "startedAt": self._clock(),
    "backendMetadata": dict(backend_metadata or {}),
}
```

Give `_persist_execution_journal(..., backend_metadata=None)` a default so existing recovery call sites remain valid.

- [ ] **Step 5: Persist allowlisted production provenance**

In `_finish_execution`, load the current journal before `_persist_result`. For `CANON_REFERENCE_EDIT`, missing/empty `backendMetadata` at result time must fail closed with `BackendError("SALVADOR_RESULT_INVALID")`; a production result must not be declared ready without provenance.

Allow only:

```python
_PROVENANCE_KEYS = {
    "taskKind",
    "workflowVersion",
    "canonPromptVersion",
    "modelId",
    "workingWidth",
    "workingHeight",
    "sourceSha256",
    "seed",
    "denoise",
}
```

Add:

```python
metadata["promptId"] = execution_id
metadata["resultSha256"] = digest
```

Backend metadata cannot overwrite `taskId`, `agent`, `backend`, `state`, `executionId`, `sha256`, `bytes`, or `createdAt`.

- [ ] **Step 6: Preserve smoke compatibility**

Old `PRODUCTION_IMAGE_EDIT` results remain valid with only canonical `sha256`; production provenance is mandatory only for `CANON_REFERENCE_EDIT`.

- [ ] **Step 7: Run controller tests, then commit**

```powershell
python -m pytest -q tests/test_controller.py
git add src/zb_local_controller/controller.py tests/test_controller.py
git commit -m "feat: persist canon execution provenance"
```

Expected: controller tests PASS including restart and duplicate regression.

---

### Task 7: Complete mocked end-to-end regression and deployment documentation

**Files:**
- Modify: `agent-controller/config.example.json`
- Modify: `agent-controller/README.md`
- Modify: `agent-controller/tests/test_cli.py`
- Modify: `agent-controller/tests/test_controller.py`
- Modify: `agent-controller/tests/test_canon_reference_edit.py`

**Interfaces:**
- Consumes: Tasks 1–6.
- Produces: fully mocked `CANON_REFERENCE_EDIT` lifecycle proof plus exact deployment instructions; no live model call.

- [ ] **Step 1: Add a full mocked production lifecycle test**

One candidate issue, one valid reference, one production backend. Assert:

```text
cycle 1: exactly one submit with non-empty prompt id
RUNNING durable event uses exact prompt id
completion writes result.png + result.json
RESULT_READY uses exact result SHA256
result.json contains production provenance
cycle 2: submitted == 0
no third durable event
```

- [ ] **Step 2: Add disposable smoke regression**

Existing `PRODUCTION_IMAGE_EDIT` must still use the original smoke backend/workflow and must not require `canonModelName`.

- [ ] **Step 3: Update `config.example.json`**

Add:

```json
"comfyuiInputRoot": "D:\\BLATT2\\ComfyUI_windows_portable\\ComfyUI\\input",
"canonReferenceWorkflowPath": "src\\zb_local_controller\\workflows\\salvador-canon-reference-edit-v1.json",
"canonPromptPath": "src\\zb_local_controller\\prompts\\salvador-canon-reference-edit-v1.txt",
"canonModelName": "",
"canonDenoise": 0.35,
"canonMaxLongSide": 768,
"canonNegativePrompt": "redesign, changed pose, changed composition, extra limbs, text, watermark"
```

Empty model name is intentional and keeps production deactivated by default.

- [ ] **Step 4: Update README operator flow**

Document exactly:

```text
1. Put exactly one drawn reference in D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\ where <TASK_ID> is the task's strict machine ID.
2. Configure the exact already-installed SD1.5-class checkpoint filename as canonModelName in local deployment config.
3. Create a GitHub task with TASK_KIND = CANON_REFERENCE_EDIT.
4. Run controller from the agent-controller working directory with that local config.
5. RUNNING requires a real prompt_id; RESULT_READY requires local result files/checksum/provenance.
6. Implementation merge is not production activation.
```

Also state: chat attachment -> Windows inbox transport is not part of v1.

- [ ] **Step 5: Run full suite and compile**

```powershell
python -m pytest -q
python -m compileall -q src
```

Expected: all tests PASS; compile exit `0`.

- [ ] **Step 6: Commit**

```powershell
git add config.example.json README.md tests
git commit -m "test: cover canon reference edit lifecycle"
```

---

### Task 8: Independent DUNCAN source/QC gate before any live model call

**Files:**
- No source change unless QC returns findings to an earlier task.

**Interfaces:**
- Consumes: exact implementation head after Task 7.
- Produces: independent `PASS` or `CHANGES_REQUIRED` on source identity, tests, safety, workflow scope, and non-activation.

- [ ] **Step 1: Capture exact head and delta**

```powershell
$head = git rev-parse HEAD
$head
git diff --stat cf68c4882f84d8d0cce07f05ccc15345b913ddca..HEAD
```

Reviewer verifies disposable smoke workflow remains byte-identical unless a separately justified regression fix exists.

- [ ] **Step 2: Independently rerun tests and compile**

```powershell
python -m pytest -q
python -m compileall -q src
```

Author-supplied results do not count as independent QC.

- [ ] **Step 3: Verify security/evidence laws**

```text
issue text cannot choose filesystem path
issue text cannot choose model filename
canon model is deployment config only
no shell execution from task direction
no paid API key/dependency
RUNNING still requires real prompt_id
RESULT_READY still requires bytes/checksum/provenance
terminal FAILED remains terminal
duplicate/restart tests remain green
PRODUCTION_ACTIVATION = NO
```

- [ ] **Step 4: Verify baseline workflow scope**

Allowed classes are exactly `CheckpointLoaderSimple`, `CLIPTextEncode`, `LoadImage`, `VAEEncode`, `KSampler`, `VAEDecode`, `SaveImage`. No `EmptyLatentImage`, ControlNet, multi-image batch, upscale, or texture/material nodes.

- [ ] **Step 5: Post durable verdict with exact head output**

```text
DUNCAN_SALVADOR_V1_IMPLEMENTATION_QC_COMPLETE
VERDICT = PASS|CHANGES_REQUIRED
EXACT_HEAD = value printed by `git rev-parse HEAD` in Step 1
PRODUCTION_ACTIVATION = NO
```

If `CHANGES_REQUIRED`, stop. Do not begin Task 9.

---

### Task 9: Run the first 4 GB local model compatibility and preservation smoke

**Files:**
- Local deployment config only; never commit model binaries or machine-specific model selection.
- Disposable local reference/result directories only.

**Interfaces:**
- Consumes: DUNCAN-PASS implementation head, local ComfyUI, one verified free/local SD1.5-class illustration/anime checkpoint, one non-sensitive drawn single-character test reference.
- Produces: real prompt id, local result/checksum/provenance, duplicate proof, and visual preservation verdict. Still no production activation.

- [ ] **Step 1: Install exact implementation and rerun tests on owner Windows**

From `D:\BLATT2\zb-local-agent-controller\agent-controller`:

```powershell
python -m pip install -e ".[test]"
python -m pytest -q
```

Stop on failure.

- [ ] **Step 2: Fresh ComfyUI preflight**

```powershell
(Invoke-WebRequest 'http://127.0.0.1:8188/system_stats' -UseBasicParsing).StatusCode
```

Expected: `200`.

- [ ] **Step 3: Resolve exact local checkpoint without guessing**

List candidates:

```powershell
Get-ChildItem 'D:\BLATT2\ComfyUI_windows_portable\ComfyUI\models\checkpoints' -File -Filter '*.safetensors' | Select-Object FullName,Length
```

After provenance/license/architecture review identifies one acceptable SD1.5-class illustration/anime checkpoint, capture it interactively and hash it:

```powershell
$modelPath = Read-Host 'Paste the exact full path of the verified SD1.5 checkpoint'; if (-not (Test-Path -LiteralPath $modelPath -PathType Leaf)) { throw 'MODEL FILE NOT FOUND' }; $modelName = [System.IO.Path]::GetFileName($modelPath); $modelSha256 = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLower(); $modelName; $modelSha256
```

If no acceptable candidate exists, stop with `OWNER_ACTION_REQUIRED = MODEL_ACQUISITION`. Do not silently download a random checkpoint and do not switch to paid inference.

- [ ] **Step 4: Create exact local production config path**

Create `D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json` from the selected runtime model variable:

```powershell
$configDir='D:\BLATT2\ZB_AGENT_CONFIG'; New-Item -ItemType Directory -Force -Path $configDir | Out-Null; @{ comfyuiUrl='http://127.0.0.1:8188'; comfyuiInputRoot='D:\BLATT2\ComfyUI_windows_portable\ComfyUI\input'; canonReferenceWorkflowPath='src\zb_local_controller\workflows\salvador-canon-reference-edit-v1.json'; canonPromptPath='src\zb_local_controller\prompts\salvador-canon-reference-edit-v1.txt'; canonModelName=$modelName; canonDenoise=0.35; canonMaxLongSide=768; canonNegativePrompt='redesign, changed pose, changed composition, extra limbs, text, watermark' } | ConvertTo-Json | Set-Content -Encoding UTF8 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json'
```

This local file is not committed.

- [ ] **Step 5: Prepare one disposable preservation reference**

Create:

```text
D:\BLATT2\ZB_AGENT_INBOX\ZB-SALVADOR-CANON-SMOKE-001\
```

Put exactly one non-sensitive drawn single-character reference in that directory. Do not use locked production face/body art for the first model-compatibility smoke.

- [ ] **Step 6: Create disposable GitHub task**

Body exactly:

```text
ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-CANON-SMOKE-001
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

No redesign. Preserve the same subject, geometry, pose, framing, composition, silhouette, major costume shapes, and asymmetries. Apply the approved ZORR BLATT production drawing treatment.
```

- [ ] **Step 7: Run exactly one real controller cycle**

From `D:\BLATT2\zb-local-agent-controller\agent-controller`:

```powershell
python -m zb_local_controller --once --config 'D:\BLATT2\ZB_AGENT_CONFIG\salvador-canon-reference-edit.json'
```

Required before calling it RUNNING:

```text
submitted = 1
real non-empty ComfyUI prompt_id
SALVADOR_RUNNING durable event contains the same id
```

- [ ] **Step 8: Finish if the first cycle did not already finish**

Run the exact same command one additional time only after inspecting the first durable state. Required final evidence:

```text
SALVADOR_RESULT_READY
result.png exists
result.json exists
result SHA-256 matches durable event
result.json records taskKind/workflowVersion/canonPromptVersion/modelId/working dimensions/promptId
```

- [ ] **Step 9: Prove duplicate suppression**

After RESULT_READY, run the same command once more and require `submitted = 0`. Confirm exactly one RUNNING and one RESULT_READY event exist for the same execution id.

- [ ] **Step 10: Visual preservation gate**

JINGO/OWNER PASS requires:

```text
same subject clearly retained
pose/composition materially unchanged
major geometry preserved
no unsolicited redesign
one character only
output visibly moves toward approved production drawing treatment
no locked production canon used or violated in this disposable smoke
```

If preservation is weak at `0.35`, use a new disposable task id with `canonDenoise = 0.30`; if still weak, another new task id with `0.25`. Never mutate a completed task back to ASSIGNED. If `0.25` still fails, reject the baseline model.

- [ ] **Step 11: Structural-conditioning spike remains separate**

Only if baseline runs reliably but visual preservation remains insufficient may a new design/spike test one compatible line-art/canny ControlNet. It must be a separate branch/task, VRAM smoke, and QC delta; it is not smuggled into the baseline implementation.

- [ ] **Step 12: Record durable smoke handoff**

Record implementation head, exact model filename, model SHA-256, prompt id, result SHA-256, denoise, working dimensions, `DUPLICATE_SUBMISSION = NO`, visual preservation verdict, and `PRODUCTION_ACTIVATION = NO`.

---

### Task 10: Final production activation gate

**Files:**
- No source changes.

**Interfaces:**
- Consumes: Tasks 1–9 PASS plus one owner-selected non-sensitive drawn production acceptance reference.
- Produces: explicit owner decision only; never implicit activation.

- [ ] **Step 1: Reconfirm all eight spec gates**

```text
1. implementation tests PASS
2. independent DUNCAN QC PASS
3. disposable local production-model preservation smoke PASS
4. real ComfyUI prompt_id evidence
5. real persisted output + SHA256
6. duplicate submission proof
7. JINGO visual/canon QC PASS on a non-sensitive production test reference
8. explicit OWNER production activation approval
```

- [ ] **Step 2: Do not infer approval from merge, PASS comments, or successful model output**

Until explicit owner production activation approval:

```text
PRODUCTION_ACTIVATION = NO
```

- [ ] **Step 3: After explicit owner approval only, record activation metadata**

Record exact implementation commit, approved model filename/SHA-256, workflow version, canon prompt version, accepted denoise/working-size profile, and acceptance evidence issue/comment IDs. Never publish the model binary or private local files.

## Plan Self-Review

- Spec coverage: Tasks 1–10 cover contract, immutable canon prompt, separate production workflow, local staging, 4 GB limits, external model identity, state/evidence law, provenance, independent QC, live preservation smoke, visual QC, duplicate proof, and explicit owner activation.
- Excluded scope remains excluded: `TEXTURE_PASS`, chat-to-local bridge, photo input, multi-character generation, pose changes, upscale, and baseline ControlNet.
- Placeholder scan: no implementation code uses `...`, `TBD`, or `TODO`. Symbolic `<TASK_ID>` appears only where it denotes the runtime strict task identifier defined by the task contract; runtime model identity is deliberately selected and captured by exact commands in Task 9.
- Type consistency: `StagedReference.comfyui_name`, `_materialize_workflow(task, staged) -> tuple[dict[str, Any], int]`, `execution_metadata(execution_id) -> dict[str, Any]`, journal `backendMetadata`, and result provenance keys are consistent across tasks.
- Evidence consistency: existing `executionId` remains canonical ComfyUI prompt id; `promptId` is a result-metadata alias. Existing `sha256` remains canonical checksum; `resultSha256` is a production alias.
- Policy consistency: benign `No redesign` language is accepted; only mechanically explicit attempts to relax immutable laws fail as `SALVADOR_CANON_CONFLICT`.
- Safety: production issue text cannot choose paths/models or shell commands; live activation remains owner-gated.
