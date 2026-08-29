from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "config" / "sheriff" / "OPEN_SOURCE_COMPONENTS.json"
COMPOSE = ROOT / "config" / "sheriff" / "docker-compose.yml"
REQUIREMENTS = ROOT / "requirements-sheriff.txt"
REQUIRED_FILES = [
    ROOT / "schemas" / "SHERIFF_AGENT_EVENT_V1.schema.json",
    ROOT / "schemas" / "SHERIFF_VERDICT_V1.schema.json",
    ROOT / "config" / "sheriff" / "opa" / "sheriff.rego",
    ROOT / "config" / "sheriff" / "opa" / "sheriff_test.rego",
    ROOT / "config" / "sheriff" / "postgres" / "001_sheriff.sql",
    ROOT / "config" / "sheriff" / "nats.conf",
    ROOT / "config" / "sheriff" / "Dockerfile.worker",
    ROOT / "scripts" / "sheriff_core.py",
    ROOT / "scripts" / "sheriff_worker.py",
]

ALLOWED_LICENSES = {
    "GPL-3.0-or-later", "Apache-2.0", "PostgreSQL", "AGPL-3.0-only",
    "MIT", "LGPL-3.0-only", "PSF-2.0",
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
        "glicko2-py", "nats-py", "psycopg", "jsonschema",
    }
    missing = sorted(required_ids - ids)
    if missing:
        fail(f"missing required components: {', '.join(missing)}")

    compose = COMPOSE.read_text(encoding="utf-8")
    compose_images = set(re.findall(r"^\s*image:\s*([^\s#]+)", compose, flags=re.MULTILINE))
    declared_images = {
        runtime_ref for runtime_ref in runtime_refs
        if not runtime_ref.startswith("local:") and "==" not in runtime_ref
    }
    if compose_images != declared_images:
        fail(
            "compose/manifest image mismatch: "
            f"undeclared={sorted(compose_images - declared_images)} "
            f"unused={sorted(declared_images - compose_images)}"
        )

    lower_compose = compose.lower()
    for forbidden_shape in ("cron:", "schedule:", "sleep "):
        if forbidden_shape in lower_compose:
            fail(f"polling/scheduling shape rejected: {forbidden_shape}")

    requirements = REQUIREMENTS.read_text(encoding="utf-8")
    requirements_upper = requirements.upper()
    for required_pin in ("glicko2-py==0.1.0", "nats-py==2.15.0", "psycopg[binary]==3.3.4", "jsonschema==4.25.1"):
        if required_pin.lower() not in requirements.lower():
            fail(f"required OSS dependency must be pinned: {required_pin}")
    for word in FORBIDDEN:
        if word in requirements_upper:
            fail(f"forbidden dependency/provider in requirements: {word}")

    print("SHERIFF OSS CONTROL PLANE V1 VALIDATION PASS")


if __name__ == "__main__":
    main()
