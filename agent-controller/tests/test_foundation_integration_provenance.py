from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "foundation-integration-provenance.json"


def test_foundation_integration_provenance_is_exact_and_non_activating() -> None:
    data = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    assert data == {
        "schema": "ZB_FOUNDATION_INTEGRATION_PROVENANCE_V1",
        "daemonSourceHead": "9e2ccfbaca88a95eac2e119e5eac720f9074dd35",
        "referenceBridgeSourceHead": "cea94c518e6f5f3e58b084d58a28be9e8d2fa205",
        "referenceBridgeBaseHead": "9e2ccfbaca88a95eac2e119e5eac720f9074dd35",
        "approvedCommunicationSpecHead": "9c9f0ebbf2bd5d5dc5b21578718f1ef356e278f9",
        "executionBaseMainSha": "0b9b77a9d82f45e7e1821dd6c9c26861a90cf688",
        "pr103Mutation": False,
        "issue102ProofCopied": False,
        "productionActivation": False,
        "canonChange": False,
        "ownerLock": False,
    }
