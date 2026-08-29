from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "config" / "sheriff" / "OPEN_SOURCE_COMPONENTS.json"
COMPOSE = ROOT / "config" / "sheriff" / "docker-compose.yml"
REQUIREMENTS = ROOT / "requirements-sheriff.txt"
REQUIRED_FILES = [
    ROOT / "schemas" / "SHERIFF_AGENT_EVENT_V1.schema.json",
    ROOT / "config" / "sheriff" / "opa" / "sheriff.rego",
    ROOT / "config" / "sheriff" / "opa" / "sheriff_test.rego",
    ROOT / "config" / "sheriff" / "postgres" / "001_sheriff.sql",
    ROOT / "config" / "sheriff" / "nats.conf",
    ROOT / "config" / "sheriff" / "Dockerfile.worker",
    ROOT / "scripts" / "sheriff_core.py",
    ROOT / "scripts" / "sheriff_worker.py",
]

ALLOWED_LICENSES = {
    "GPL-3.0-or-later",
    "Apache-2.0",
    "PostgreSQL",
    "AGPL-3.0-only",
    "MIT",
    "LGPL-3.0-only",
    "PSF-2.0",
}
FORBIDDEN = {"PROPRIETARY", "OPENAI", "ANTHROPIC"}


def fail(message: str) -> None:
    raise SystemExit(f"SHERIFF_OSS_VALIDATION_FAIL: {message}")


def main() -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"missing required file: {path.relative_to(ROOT)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schemaVersion") != "SHERIFF_OSS_COMPONENTS_V1":
        fail("wrong manifest schemaVersion")
    if manifest.get("policy") != "OPEN_CODE_ONLY":
        fail("manifest policy must be OPEN_CODE_ONLY")

    components = manifest.get("components")
    if not isinstance(components, list) or not components:
        fail("components must be a non-empty list")

    ids: set[str] = set()
    runtime_refs: set[str] = set()
    for item in components:
        component_id = str(item.get("id", "")).strip()
        if not component_id or component_id in ids:
            fail(f"missing/duplicate component id: {component_id!r}")
        ids.add(component_id)

        source = str(item.get("source", ""))
        license_id = str(item.get("license", ""))
        runtime_ref = str(item.get("runtimeRef", ""))
        purpose = str(item.get("purpose", ""))
        if not source.startswith("https://"):
            fail(f"component {component_id} has non-HTTPS source")
        if license_id not in ALLOWED_LICENSES:
            fail(f"component {component_id} license rejected: {license_id or 'UNKNOWN'}")
        if not runtime_ref or not purpose:
            fail(f"component {component_id} missing runtimeRef/purpose")
        if any(word in f"{component_id} {source} {runtime_ref}".upper() for word in FORBIDDEN):
            fail(f"component {component_id} contains forbidden proprietary provider")
        runtime_refs.add(runtime_ref)

    required_ids = {
        "forgejo", "nats", "opa", "postgresql", "opentelemetry-collector",
        "prometheus", "loki", "grafana-oss", "sheriff-worker",
        "glicko2-py", "nats-py", "psycopg",
    }
    missing = sorted(required_ids - ids)
    if missing:
        fail(f"missing required components: {', '.join(missing)}")

    compose = COMPOSE.read_text(encoding="utf-8")
    for runtime_ref in runtime_refs:
        if runtime_ref.startswith("local:") or "==" in runtime_ref:
            continue
        if runtime_ref not in compose:
            fail(f"declared runtime image not used by compose: {runtime_ref}")

    lower_compose = compose.lower()
    for forbidden_shape in ("cron:", "schedule:", "sleep "):
        if forbidden_shape in lower_compose:
            fail(f"polling/scheduling shape rejected: {forbidden_shape}")

    requirements = REQUIREMENTS.read_text(encoding="utf-8").upper()
    if "GLICKO2-PY==0.1.0" not in requirements:
        fail("Glicko-2 OSS dependency must be pinned")
    for word in FORBIDDEN:
        if word in requirements:
            fail(f"forbidden dependency/provider in requirements: {word}")

    print("SHERIFF OSS CONTROL PLANE V1 VALIDATION PASS")


if __name__ == "__main__":
    main()
