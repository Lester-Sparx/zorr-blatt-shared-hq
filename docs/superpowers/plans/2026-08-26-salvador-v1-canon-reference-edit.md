# SALVADOR v1 CANON REFERENCE EDIT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first real zero-budget SALVADOR production mode that takes one drawn local reference and produces one canon-preserving ComfyUI image-to-image result under `TASK_KIND = CANON_REFERENCE_EDIT` without activating production automatically.

**Architecture:** Keep the accepted controller state/evidence core unchanged and add a separate production backend beside the disposable smoke backend. The production backend owns immutable canon prompt composition, safe local reference staging into ComfyUI input, deterministic bounded preprocessing, production workflow materialization, model preflight, and provenance capture; the generic controller remains responsible for durable GitHub state, restart safety, result persistence, and duplicate suppression.

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
- Fixed local input root remains `D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\`; GitHub issue text never supplies a filesystem path.
- Production ComfyUI staging is deployment-owned and must remain under `D:\BLATT2\ComfyUI_windows_portable\ComfyUI\input`.
- Batch size = 1; output count = 1; first 4 GB target long side <= 768 px; no crop; deterministic aspect-preserving normalization.
- First compatibility baseline is a lightweight SD1.5-class local illustration/anime img2img path with conservative denoise in `0.25..0.45`; optional one structural ControlNet only if a separate local smoke proves it fits reliably.
- Exact production checkpoint/control model names remain external deployment configuration and model binaries are never committed to Shared HQ.
- `RUNNING` only after real ComfyUI returns a non-empty `prompt_id`.
- `RESULT_READY` only after real output bytes, checksum, and atomic result metadata are persisted.
- Existing terminal `FAILED`, restart recovery, one-active-SALVADOR GPU lock, GitHub reconciliation, and duplicate suppression laws remain intact.
- Merging implementation is not production activation. `PRODUCTION_ACTIVATION = NO` until the full eight-gate acceptance in the spec passes.
- SALVADOR v2 `TEXTURE_PASS` is out of scope.

## File Structure

- Modify `agent-controller/src/zb_local_controller/task_contract.py` — allow the new explicit task kind only.
- Create `agent-controller/src/zb_local_controller/production_policy.py` — immutable-vs-task prompt composition and mechanically detectable canon-conflict rejection.
- Modify `agent-controller/src/zb_local_controller/config.py` — deployment-owned production paths/model/denoise/size settings.
- Modify `agent-controller/src/zb_local_controller/__main__.py` — register smoke and production backends side by side.
- Create `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py` — production-only staging, preprocessing, workflow materialization, readiness/model preflight, prompt submission, provenance.
- Modify `agent-controller/src/zb_local_controller/controller.py` — persist optional backend provenance restart-safely without changing state semantics.
- Create `agent-controller/src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt` — immutable repository-owned canon prompt.
- Create `agent-controller/src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json` — separate production img2img template; smoke workflow remains unchanged.
- Modify `agent-controller/pyproject.toml` — add Pillow for deterministic input decode/resize and output decode validation.
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
- Produces: `ALLOWED_TASK_KINDS = {"PRODUCTION_IMAGE_EDIT", "CANON_REFERENCE_EDIT"}` and `compose_canon_prompt(canon_prompt: str, direction: str) -> str` raising `CanonPolicyError("SALVADOR_CANON_CONFLICT")` for mechanically detectable attempts to relax immutable laws.

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

Run from `agent-controller`:

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
from zb_local_controller.production_policy import CanonPolicyError, compose_canon_prompt


def test_composes_immutable_canon_before_task_direction():
    result = compose_canon_prompt("IMMUTABLE CANON", "keep the scar")
    assert result.startswith("IMMUTABLE CANON")
    assert "TASK-SPECIFIC LOCKED DIRECTION" in result
    assert result.endswith("keep the scar")


def test_rejects_mechanically_obvious_canon_override():
    for direction in (
        "ignore canon and redesign",
        "change pose completely",
        "generate the character from scratch",
        "игнорируй канон и сделай редизайн",
        "измени позу полностью",
        "сгенерируй персонажа с нуля",
    ):
        try:
            compose_canon_prompt("IMMUTABLE CANON", direction)
        except CanonPolicyError as exc:
            assert exc.code == "SALVADOR_CANON_CONFLICT"
        else:
            raise AssertionError(direction)
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
    "redesign",
    "change pose",
    "different pose",
    "generate from scratch",
    "text to image",
    "игнорируй канон",
    "игнорируй лок",
    "редизайн",
    "измени позу",
    "смени позу",
    "с нуля",
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

This is intentionally a conservative mechanical guard, not a claim of semantic vision/QC.

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
- Produces: production config fields and a `CanonReferenceEditBackend` object registered only for `("SALVADOR", "CANON_REFERENCE_EDIT")`; the smoke backend remains registered for `("SALVADOR", "PRODUCTION_IMAGE_EDIT")`.

- [ ] **Step 1: Write failing config tests**

Add tests that load exactly these deployment-owned keys:

```python
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
```

Also add rejection tests for `canonDenoise < 0.25`, `canonDenoise > 0.45`, and `canonMaxLongSide > 768`; each must raise `ConfigurationError("CONFIG_INVALID")`.

- [ ] **Step 2: Run config tests and verify RED**

```powershell
python -m pytest -q tests/test_config.py
```

Expected: missing config fields / unknown keys.

- [ ] **Step 3: Extend `ControllerConfig` and `load_config`**

Add fields with safe non-activated defaults:

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

Validate after parsing:

```python
if not 0.25 <= config.canon_denoise <= 0.45:
    raise ConfigurationError("CONFIG_INVALID")
if not 64 <= config.canon_max_long_side <= 768:
    raise ConfigurationError("CONFIG_INVALID")
```

An empty `canonModelName` is valid configuration but means production model preflight must fail closed when a production task is actually attempted.

- [ ] **Step 4: Create a minimal production backend skeleton and failing CLI registry test**

Initial class:

```python
from .comfyui import ComfyUIBackend


class CanonReferenceEditBackend(ComfyUIBackend):
    WORKFLOW_VERSION = "salvador-canon-reference-edit-v1"
    CANON_PROMPT_VERSION = "salvador-canon-v1"
```

Add a CLI test using injected factories to assert the controller registry receives two mappings and that the two task kinds do not share the same backend object.

- [ ] **Step 5: Update `_default_backend_factory` into a registry factory**

Use one smoke backend plus one production backend:

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

Keep dependency injection in `main()` testable; do not instantiate or call a production model during CLI construction.

- [ ] **Step 6: Run focused tests, then commit**

```powershell
python -m pytest -q tests/test_config.py tests/test_cli.py
git add src/zb_local_controller/config.py src/zb_local_controller/__main__.py src/zb_local_controller/backends/canon_reference_edit.py tests/test_config.py tests/test_cli.py
git commit -m "feat: register canon reference edit backend"
```

Expected: focused tests PASS; smoke CLI behavior remains unchanged.

---

### Task 3: Add deterministic safe reference staging and bounded preprocessing

**Files:**
- Modify: `agent-controller/pyproject.toml`
- Modify: `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py`
- Create: `agent-controller/tests/test_canon_reference_edit.py`

**Interfaces:**
- Consumes: validated `ReferenceFile.path`, strict `task.task_id`, deployment-owned `comfyui_input_root`.
- Produces: `_stage_reference(task, reference) -> StagedReference` where `StagedReference` records staged filename/path, source SHA-256, working width, and working height.

- [ ] **Step 1: Add Pillow dependency and write failing staging tests**

In `pyproject.toml` set:

```toml
dependencies = ["Pillow>=11"]
```

Test with a generated `1600x900` RGB PNG and assert:

```python
staged = backend._stage_reference(TASK, REF)
assert staged.path.parent == comfyui_input_root / "ZB_CANON_REFERENCE_EDIT"
assert staged.path.name.startswith("ZB-SALVADOR-CANON-001-")
assert staged.path.suffix == ".png"
assert max(staged.working_width, staged.working_height) == 768
assert abs((staged.working_width / staged.working_height) - (1600 / 900)) < 0.01
assert staged.source_sha256 == hashlib.sha256(source_bytes).hexdigest()
```

Add a second test with `512x700` input to assert it is not upscaled: `max(...) == 700`.

Add a corrupt-image test that must raise `BackendError("SALVADOR_UNSUPPORTED_INPUT")`.

- [ ] **Step 2: Run the new backend tests and verify RED**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py
```

Expected: missing `StagedReference` / `_stage_reference`.

- [ ] **Step 3: Implement deterministic staging**

Use:

```python
from dataclasses import dataclass
from hashlib import sha256
from PIL import Image
import os


@dataclass(frozen=True)
class StagedReference:
    path: Path
    source_sha256: str
    working_width: int
    working_height: int
```

Algorithm:

1. Read source bytes and hash them.
2. Decode with Pillow and force full `image.load()`.
3. Convert to RGB.
4. If long side > `max_long_side`, call `thumbnail((max_long_side, max_long_side), Image.Resampling.LANCZOS)`; otherwise keep native dimensions.
5. Never crop and never upscale.
6. Write PNG atomically under `<comfyui_input_root>/ZB_CANON_REFERENCE_EDIT/`.
7. Filename is `<task_id>-<source_sha256[:12]>.png`.
8. Use a `.tmp` sibling and `os.replace`.

Do not stage outside the deployment-owned ComfyUI input root.

- [ ] **Step 4: Add idempotence test**

Call `_stage_reference` twice for the same task/source and assert the exact same staged path and exact same bytes. This prevents unnecessary staging churn during retries.

- [ ] **Step 5: Run focused tests, then commit**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py
git add pyproject.toml src/zb_local_controller/backends/canon_reference_edit.py tests/test_canon_reference_edit.py
git commit -m "feat: stage canon references safely"
```

Expected: all staging tests PASS.

---

### Task 4: Add immutable canon prompt asset and a separate SD1.5 img2img workflow template

**Files:**
- Create: `agent-controller/src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt`
- Create: `agent-controller/src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json`
- Modify: `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py`
- Modify: `agent-controller/tests/test_canon_reference_edit.py`

**Interfaces:**
- Consumes: staged reference filename, external model name, immutable canon prompt file, task direction, negative prompt, configured denoise.
- Produces: `_workflow_for(task, reference) -> dict[str, Any]` containing no unresolved `__ZB_*__` tokens and exactly one output branch.

- [ ] **Step 1: Write the immutable prompt asset exactly as a production law**

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

- [ ] **Step 2: Write a failing template-materialization test**

The test template contract must require these tokens exactly once where applicable:

```text
__ZB_REFERENCE__
__ZB_MODEL__
__ZB_POSITIVE_PROMPT__
__ZB_NEGATIVE_PROMPT__
__ZB_DENOISE__
__ZB_SEED__
```

After `_workflow_for`, recursively assert no string starts with `__ZB_`.

- [ ] **Step 3: Create the production workflow JSON with only core img2img nodes**

Use this node flow:

```text
CheckpointLoaderSimple
  -> CLIPTextEncode positive
  -> CLIPTextEncode negative
LoadImage
CheckpointLoaderSimple.VAE + LoadImage.IMAGE -> VAEEncode
CheckpointLoaderSimple.MODEL + positive + negative + VAEEncode.LATENT -> KSampler
KSampler.LATENT + CheckpointLoaderSimple.VAE -> VAEDecode
VAEDecode.IMAGE -> SaveImage
```

The committed workflow template must use:

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

Do not add ControlNet in the baseline workflow. Structural ControlNet is a later compatibility enhancement only if the baseline already works on 4 GB and a separate smoke proves the additional model fits.

- [ ] **Step 4: Implement exact token replacement and deterministic seed**

Compose positive prompt with `compose_canon_prompt()`.

Derive seed from task/source identity:

```python
seed_bytes = hashlib.sha256(f"{task.task_id}:{staged.source_sha256}".encode("utf-8")).digest()[:8]
seed = int.from_bytes(seed_bytes, "big") & ((1 << 63) - 1)
```

Materialize exact typed values: strings for model/reference/prompts, float for denoise, integer for seed.

If token counts differ from the exact template contract or any unresolved `__ZB_` remains, raise `BackendError("SALVADOR_RESULT_INVALID")` before any HTTP submit.

- [ ] **Step 5: Assert immutable prompt precedence and canon conflict**

Tests must prove the submitted positive prompt begins with the repository prompt, contains the task direction only under `TASK-SPECIFIC LOCKED DIRECTION`, and rejects `ignore canon and redesign` with `SALVADOR_CANON_CONFLICT` before POST `/prompt`.

- [ ] **Step 6: Run focused tests, then commit**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py tests/test_production_policy.py
git add src/zb_local_controller/prompts/salvador-canon-reference-edit-v1.txt src/zb_local_controller/workflows/salvador-canon-reference-edit-v1.json src/zb_local_controller/backends/canon_reference_edit.py tests/test_canon_reference_edit.py
git commit -m "feat: add canon img2img workflow"
```

Expected: focused tests PASS and the disposable smoke workflow file is untouched.

---

### Task 5: Add production ComfyUI readiness/model preflight and stable backend failures

**Files:**
- Modify: `agent-controller/src/zb_local_controller/backends/canon_reference_edit.py`
- Modify: `agent-controller/tests/test_canon_reference_edit.py`

**Interfaces:**
- Consumes: ComfyUI `/system_stats`, `/object_info`, external `canon_model_name`.
- Produces: `ensure_ready()` that fails closed with stable SALVADOR codes and `execution_metadata(execution_id: str) -> dict[str, Any]` after successful submit.

- [ ] **Step 1: Write failing readiness tests**

Tests:

```python
def test_missing_model_name_fails_closed(...):
    with pytest.raises(BackendError) as exc:
        backend(model_name="").ensure_ready()
    assert exc.value.code == "SALVADOR_MODEL_UNAVAILABLE"


def test_unreachable_comfyui_maps_to_stable_salvador_error(...):
    with pytest.raises(BackendError) as exc:
        backend(...).ensure_ready()
    assert exc.value.code == "SALVADOR_BACKEND_UNAVAILABLE"
```

Add a response fixture for `/object_info/CheckpointLoaderSimple` whose `ckpt_name` list excludes the configured model and assert `SALVADOR_MODEL_UNAVAILABLE`.

Add a node preflight fixture missing `KSampler` and assert `SALVADOR_BACKEND_UNAVAILABLE` because the deployment cannot execute the approved workflow.

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
python -m pytest -q tests/test_canon_reference_edit.py -k "ready or model or preflight"
```

- [ ] **Step 3: Implement readiness preflight**

Required node classes:

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

`ensure_ready()` order:

1. model name non-empty else `SALVADOR_MODEL_UNAVAILABLE`;
2. `GET /system_stats` else `SALVADOR_BACKEND_UNAVAILABLE`;
3. `GET /object_info` and ensure all required classes exist else `SALVADOR_BACKEND_UNAVAILABLE`;
4. inspect `CheckpointLoaderSimple.input.required.ckpt_name[0]` and require exact configured model name else `SALVADOR_MODEL_UNAVAILABLE`.

Never infer a model by fuzzy filename matching.

- [ ] **Step 4: Override submit only enough to stage/materialize and record metadata**

On successful `POST /prompt`, require a real non-empty string `prompt_id`, then store:

```python
self._execution_metadata[prompt_id] = {
    "taskKind": "CANON_REFERENCE_EDIT",
    "workflowVersion": self.WORKFLOW_VERSION,
    "canonPromptVersion": self.CANON_PROMPT_VERSION,
    "modelId": self.model_name,
    "workingWidth": staged.working_width,
    "workingHeight": staged.working_height,
    "sourceSha256": staged.source_sha256,
    "seed": seed,
    "denoise": self.denoise,
}
```

Expose a defensive copy from:

```python
def execution_metadata(self, execution_id: str) -> dict[str, Any]:
    return dict(self._execution_metadata.get(execution_id, {}))
```

- [ ] **Step 5: Add failure mapping for poll/collect**

For the production backend only:

- transport failure -> `SALVADOR_BACKEND_UNAVAILABLE`;
- completed execution without one image -> `SALVADOR_RESULT_INVALID`;
- collected non-PNG/empty bytes -> `SALVADOR_RESULT_INVALID`.

Keep generic smoke backend error codes unchanged.

- [ ] **Step 6: Run focused tests, then commit**

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
- Produces: execution journal field `backendMetadata` and final `result.json` production provenance without changing old smoke metadata validity or state transitions.

- [ ] **Step 1: Write a failing provenance persistence test**

Use a fake backend that returns prompt id `canon-prompt-1` and:

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

After submit, assert `execution.json` contains that exact object under `backendMetadata`.

After result completion, assert `result.json` contains:

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

Create controller A, submit once, persist journal, destroy it; create controller B with the same result root and issue comments not yet containing RUNNING. Assert B reconstructs the same execution id and does not call `submit()` again. The final result must retain the original `backendMetadata` from the journal.

- [ ] **Step 3: Run focused controller tests and verify RED**

```powershell
python -m pytest -q tests/test_controller.py -k "metadata or provenance or restart"
```

- [ ] **Step 4: Implement generic optional metadata capture**

After backend submit:

```python
metadata_fn = getattr(backend, "execution_metadata", None)
backend_metadata = metadata_fn(execution_id) if callable(metadata_fn) else {}
self._persist_execution_journal(task, execution_id, backend_metadata)
```

Change journal payload to:

```python
{
    "taskId": task.task_id,
    "executionId": execution_id,
    "startedAt": self._clock(),
    "backendMetadata": dict(backend_metadata or {}),
}
```

When an existing journal is loaded, preserve that metadata verbatim. Do not regenerate model provenance from current config after a restart.

- [ ] **Step 5: Extend `_persist_result` without breaking smoke**

Load `backendMetadata` from the execution journal and merge only allowlisted keys:

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

Always add aliases required by the spec:

```python
metadata["promptId"] = execution_id
metadata["resultSha256"] = digest
```

Do not allow backend metadata to overwrite `taskId`, `agent`, `backend`, `state`, `executionId`, `sha256`, `bytes`, or `createdAt`.

- [ ] **Step 6: Preserve old result reconciliation**

Update `_existing_result_metadata()` only if necessary so old smoke results and new production results both validate by canonical `sha256`. Do not make provenance mandatory for old `PRODUCTION_IMAGE_EDIT` results.

- [ ] **Step 7: Run full controller tests, then commit**

```powershell
python -m pytest -q tests/test_controller.py
git add src/zb_local_controller/controller.py tests/test_controller.py
git commit -m "feat: persist canon execution provenance"
```

Expected: controller tests PASS including restart and duplicate regression.

---

### Task 7: Complete mocked end-to-end production regression and deployment docs

**Files:**
- Modify: `agent-controller/config.example.json`
- Modify: `agent-controller/README.md`
- Modify: `agent-controller/tests/test_cli.py`
- Modify: `agent-controller/tests/test_controller.py`
- Modify: `agent-controller/tests/test_canon_reference_edit.py`

**Interfaces:**
- Consumes: all Tasks 1–6.
- Produces: one fully mocked `CANON_REFERENCE_EDIT` lifecycle proof plus clear deployment instructions; no live model call yet.

- [ ] **Step 1: Add a full mocked lifecycle test**

Test one candidate issue with `CANON_REFERENCE_EDIT` and a valid temp reference. Assert:

```text
cycle 1: one submit with non-empty prompt id
RUNNING durable event uses that exact id
completed backend result writes result.png + result.json
RESULT_READY uses the exact result SHA256
cycle 2: submitted == 0
no third durable event
```

The fake production backend must expose production provenance and the final JSON must contain it.

- [ ] **Step 2: Add explicit smoke-path regression**

Run the existing disposable `PRODUCTION_IMAGE_EDIT` test fixture and assert it still selects the original `ComfyUIBackend` workflow and does not require `canonModelName`.

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

The empty model name is intentional: the repository never chooses or activates a production binary automatically.

- [ ] **Step 4: Update README with exact operator flow**

Document:

```text
1. Put exactly one drawn reference in D:\BLATT2\ZB_AGENT_INBOX\<TASK_ID>\
2. Configure exact installed SD1.5-class checkpoint filename in local config as canonModelName.
3. Create GitHub task with TASK_KIND = CANON_REFERENCE_EDIT.
4. Run controller from agent-controller working directory.
5. RUNNING requires real prompt_id; RESULT_READY requires local result files/checksum.
6. Implementation merge != production activation.
```

State explicitly that chat attachment -> Windows inbox transport is not part of v1.

- [ ] **Step 5: Run the entire suite and compile**

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

### Task 8: Independent source/QC gate before any live production-model call

**Files:**
- No production source change is allowed in this task unless a finding sends work back to an earlier task.

**Interfaces:**
- Consumes: exact implementation head after Task 7.
- Produces: DUNCAN verdict `PASS` or `CHANGES_REQUIRED` for source identity, tests, safety boundaries, workflow scope, and production non-activation.

- [ ] **Step 1: Record exact implementation head and file delta**

Commands:

```powershell
git rev-parse HEAD
git diff --stat cf68c4882f84d8d0cce07f05ccc15345b913ddca..HEAD
```

Reviewer must verify the disposable smoke workflow remains byte-identical unless a separately justified regression fix was required.

- [ ] **Step 2: Independently rerun tests and compile from exact blobs**

```powershell
python -m pytest -q
python -m compileall -q src
```

No author-supplied test result counts as independent QC.

- [ ] **Step 3: Verify security/evidence laws**

Reviewer must verify:

```text
issue text cannot choose a filesystem path
issue text cannot choose a model filename
canon model is deployment config only
no shell execution from direction text
no paid API key/dependency
RUNNING still requires real prompt_id
RESULT_READY still requires persisted bytes/checksum
terminal FAILED remains terminal
duplicate/restart tests remain green
production activation remains NO
```

- [ ] **Step 4: Verify workflow scope**

Baseline production workflow may contain only the core img2img classes from Task 4. No text-to-image empty latent node, no multi-image batch, no ControlNet yet, no upscale stage, no texture/material nodes.

- [ ] **Step 5: Post durable verdict**

Exact durable header:

```text
DUNCAN_SALVADOR_V1_IMPLEMENTATION_QC_COMPLETE
VERDICT = PASS|CHANGES_REQUIRED
EXACT_HEAD = <actual exact head>
PRODUCTION_ACTIVATION = NO
```

If `CHANGES_REQUIRED`, stop. Do not begin Task 9.

---

### Task 9: Run the first 4 GB local model compatibility and preservation smoke

**Files:**
- Local deployment config only; never commit model binaries or local machine config.
- Disposable local reference/result directories only.

**Interfaces:**
- Consumes: DUNCAN-PASS implementation head, local ComfyUI, one free/local SD1.5-class illustration/anime checkpoint, one non-sensitive drawn single-character test reference.
- Produces: real ComfyUI prompt id, local result/checksum/provenance, duplicate proof, and a go/no-go visual preservation verdict. This is still not production activation.

- [ ] **Step 1: Install the exact approved implementation on owner Windows and rerun tests**

From `D:\BLATT2\zb-local-agent-controller\agent-controller`:

```powershell
python -m pip install -e ".[test]"
python -m pytest -q
```

Stop on any failure.

- [ ] **Step 2: Fresh ComfyUI preflight**

```powershell
(Invoke-WebRequest 'http://127.0.0.1:8188/system_stats' -UseBasicParsing).StatusCode
```

Expected: `200`.

- [ ] **Step 3: Resolve an exact local checkpoint without guessing**

Inspect:

```text
D:\BLATT2\ComfyUI_windows_portable\ComfyUI\models\checkpoints\
```

Select one exact free/local SD1.5-class illustration/anime `.safetensors` checkpoint whose provenance/license is acceptable and whose architecture is known to be SD1.5-compatible. Record the exact filename and file SHA-256 in the deployment/QC handoff. If no suitable checkpoint exists, stop with `OWNER_ACTION_REQUIRED = MODEL_ACQUISITION`; do not silently download a random checkpoint and do not switch to a paid backend.

- [ ] **Step 4: Create a local production config outside GitHub history**

Use a local JSON file whose `canonModelName` is the exact installed filename, `canonDenoise = 0.35`, and `canonMaxLongSide = 768`. Do not commit this file if it contains machine-specific model selection.

- [ ] **Step 5: Prepare one disposable preservation reference**

Create task directory:

```text
D:\BLATT2\ZB_AGENT_INBOX\ZB-SALVADOR-CANON-SMOKE-001\
```

Put exactly one non-sensitive drawn single-character reference there. Do not use locked production face/body art for this first model-compatibility smoke.

- [ ] **Step 6: Create the disposable GitHub task**

Body exactly:

```text
ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-CANON-SMOKE-001
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

Preserve the same subject, geometry, pose, framing, composition, silhouette, major costume shapes, and asymmetries. Apply the approved ZORR BLATT production drawing treatment. No redesign.
```

- [ ] **Step 7: Run exactly one real controller cycle**

From the `agent-controller` working directory with the local production config:

```powershell
python -m zb_local_controller --once --config <local-config-path>
```

Required evidence before calling it RUNNING:

```text
submitted = 1
real non-empty ComfyUI prompt_id
SALVADOR_RUNNING durable event contains the same id
```

- [ ] **Step 8: Finish the execution if the first cycle did not already finish**

Run one additional `--once` only after checking the first durable event. Required final evidence:

```text
SALVADOR_RESULT_READY
result.png exists
result.json exists
result SHA-256 matches durable event
result.json records taskKind/workflowVersion/canonPromptVersion/modelId/working dimensions/promptId
```

- [ ] **Step 9: Prove duplicate suppression**

Run one further unchanged `--once` and require `submitted = 0`. Confirm the task has exactly one RUNNING and one RESULT_READY event for the same execution id.

- [ ] **Step 10: Perform visual preservation gate**

JINGO/OWNER compares input and output. PASS requires all of:

```text
same subject is clearly retained
pose/composition materially unchanged
major geometry preserved
no unsolicited redesign
one character only
output moves visibly toward approved production drawing treatment
no locked canon used or violated in this disposable smoke
```

If geometry preservation is weak at `denoise = 0.35`, repeat only as a new disposable task id with one documented lower denoise value inside the approved range, starting at `0.30`, then `0.25`; never mutate a completed task back to ASSIGNED. If even `0.25` fails preservation, the baseline model is rejected.

- [ ] **Step 11: Optional structural-conditioning spike only after baseline result**

Only if the baseline runs reliably but visual preservation is insufficient may a separate spike test one line-art/canny ControlNet compatible with the selected SD1.5 checkpoint. It must be a separate branch/task, separate VRAM smoke, and separate QC delta. It is not part of the baseline implementation merge.

- [ ] **Step 12: Record smoke handoff**

Durable evidence must include exact implementation head, exact model filename + SHA-256, prompt id, result SHA-256, denoise, working dimensions, duplicate submission = NO, and visual preservation verdict. Keep `PRODUCTION_ACTIVATION = NO`.

---

### Task 10: Final production activation gate

**Files:**
- No source changes.

**Interfaces:**
- Consumes: Tasks 1–9 PASS plus one owner-selected non-sensitive drawn production acceptance reference.
- Produces: explicit owner decision only; no implicit activation.

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

Until the owner explicitly writes a production activation approval, durable state remains:

```text
PRODUCTION_ACTIVATION = NO
```

- [ ] **Step 3: After explicit owner approval only, record activation metadata**

Record the exact implementation commit, exact approved model filename/SHA-256, workflow version, canon prompt version, accepted denoise/working-size profile, and acceptance evidence issue/comment IDs. Activation metadata may point to local model identity but must not publish the model binary or private local files.

## Plan Self-Review

- Spec coverage: all v1 requirements map to Tasks 1–10; `TEXTURE_PASS`, chat-to-local bridge, photo input, multi-character generation, pose changes, upscale, and ControlNet baseline expansion remain excluded.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain. Runtime-selected production checkpoint identity is intentionally discovered in Task 9 because the approved spec requires external deployment configuration; the plan gives an exact selection/stop rule rather than a placeholder.
- Type consistency: `CanonReferenceEditBackend.execution_metadata(execution_id) -> dict[str, Any]`, journal `backendMetadata`, and result provenance keys are named consistently across Tasks 5–7.
- Evidence consistency: existing `executionId` remains the canonical ComfyUI prompt id; `promptId` is an explicit result-metadata alias only. Existing `sha256` remains canonical checksum; `resultSha256` is an explicit production alias only.
- Safety: production issue text cannot choose paths/models or bypass canon policy; live activation remains owner-gated.
