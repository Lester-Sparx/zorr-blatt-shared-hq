from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any


INSPECT_REPOSITORY = "UKGovernmentBEIS/inspect_ai"
INSPECT_REF = "fbee5b35c656f1c7653af3adf682172033ee0590"
INSPECT_CORRECT_VALUE = "C"
TASK_REF = "issue:216/lester-oss-eval-r01"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class LesterOssEvalError(RuntimeError):
    pass


def _require_text(name: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise LesterOssEvalError(f"MISSING_{name}")
    return value


def build_sheriff_result_event(
    *,
    candidate_head: str,
    run_id: str,
    run_attempt: str,
    event_time: str,
    inspect_log: str,
    inspect_status: str,
    inspect_score: str,
) -> dict[str, Any]:
    if not _SHA40.fullmatch(candidate_head):
        raise LesterOssEvalError("INVALID_CANDIDATE_HEAD")
    run_id = _require_text("RUN_ID", run_id)
    run_attempt = _require_text("RUN_ATTEMPT", run_attempt)
    event_time = _require_text("EVENT_TIME", event_time)
    inspect_log = _require_text("INSPECT_LOG", inspect_log)
    inspect_status = _require_text("INSPECT_STATUS", inspect_status)
    inspect_score = _require_text("INSPECT_SCORE", inspect_score)

    verified_pass = (
        inspect_status == "success" and inspect_score == INSPECT_CORRECT_VALUE
    )
    execution_id = f"lester-oss-eval-r01:{candidate_head}:{run_id}:{run_attempt}"
    workflow_evidence = f"github-actions:run:{run_id}:attempt:{run_attempt}"
    upstream_evidence = f"inspect-upstream:{INSPECT_REPOSITORY}@{INSPECT_REF}"

    return {
        "specversion": "1.0",
        "id": execution_id,
        "source": "https://github.com/Lester-Sparx/zorr-blatt-shared-hq/actions",
        "type": "zb.agent.result",
        "subject": TASK_REF,
        "time": event_time,
        "datacontenttype": "application/json",
        "data": {
            "agentId": "LESTER",
            "taskRef": TASK_REF,
            "executionId": execution_id,
            "status": "PASS" if verified_pass else "FAIL",
            "evidence": [
                f"candidate-head:{candidate_head}",
                workflow_evidence,
                upstream_evidence,
                f"inspect-log:{inspect_log}",
            ],
            "verifiedPass": verified_pass,
            "incidentAttribution": "NONE",
            "processViolation": False,
            "safetyViolation": False,
            "evalFramework": "Inspect AI",
            "evalUpstreamRepository": INSPECT_REPOSITORY,
            "evalUpstreamRef": INSPECT_REF,
            "evalStatus": inspect_status,
            "evalScore": inspect_score,
            "skillStateAfter": "PARTIAL_ONLY",
            "transferRequired": True,
            "historicalBackfill": False,
            "disciplineAffectsCompetence": False,
        },
    }


def run_inspect_smoke(output_dir: Path) -> dict[str, Any]:
    try:
        from inspect_ai import Task, eval as inspect_eval
        from inspect_ai.dataset import Sample
        from inspect_ai.scorer import CORRECT, match
        from inspect_ai.solver import generate
    except ImportError as exc:
        raise LesterOssEvalError("INSPECT_AI_NOT_INSTALLED") from exc

    candidate_head = _require_text("GITHUB_SHA", os.environ.get("GITHUB_SHA", ""))
    run_id = _require_text("GITHUB_RUN_ID", os.environ.get("GITHUB_RUN_ID", ""))
    run_attempt = _require_text(
        "GITHUB_RUN_ATTEMPT", os.environ.get("GITHUB_RUN_ATTEMPT", "")
    )
    if not _SHA40.fullmatch(candidate_head):
        raise LesterOssEvalError("INVALID_CANDIDATE_HEAD")

    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = output_dir / "inspect-logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    task = Task(
        dataset=[
            Sample(
                id="lester-oss-eval-r01-smoke",
                input="Return the configured mock model response.",
                target="Default output from mockllm/model",
            )
        ],
        solver=[generate()],
        scorer=match(),
        metadata={
            "zorrTracker": "issue:216",
            "zorrExecutor": "LESTER",
            "candidateHead": candidate_head,
            "inspectUpstreamRef": INSPECT_REF,
        },
        name="lester_oss_eval_r01_smoke",
    )

    logs = inspect_eval(
        task,
        model="mockllm/model",
        log_dir=str(log_dir),
        log_format="json",
        fail_on_error=True,
    )
    if len(logs) != 1:
        raise LesterOssEvalError("INSPECT_LOG_COUNT_INVALID")
    log = logs[0]
    if not log.samples or len(log.samples) != 1:
        raise LesterOssEvalError("INSPECT_SAMPLE_COUNT_INVALID")
    scores = log.samples[0].scores
    if not scores or len(scores) != 1:
        raise LesterOssEvalError("INSPECT_SCORE_COUNT_INVALID")
    score = next(iter(scores.values()))
    score_text = score.text
    if score_text not in {CORRECT, INSPECT_CORRECT_VALUE}:
        raise LesterOssEvalError(f"INSPECT_SMOKE_SCORE_FAIL:{score_text}")

    event = build_sheriff_result_event(
        candidate_head=candidate_head,
        run_id=run_id,
        run_attempt=run_attempt,
        event_time=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        inspect_log=str(log.location),
        inspect_status=log.status,
        inspect_score=score_text,
    )
    event_path = output_dir / "sheriff-event.json"
    event_path.write_text(
        json.dumps(event, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(event, sort_keys=True))
    if not event["data"]["verifiedPass"]:
        raise LesterOssEvalError("INSPECT_SMOKE_NOT_VERIFIED_PASS")
    return event


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        run_inspect_smoke(args.output_dir)
    except LesterOssEvalError as exc:
        print(f"LESTER_OSS_EVAL_R01_FAIL={exc}")
        return 1
    print("LESTER_OSS_EVAL_R01_SMOKE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
