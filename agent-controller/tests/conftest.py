from __future__ import annotations
import hashlib
from dataclasses import replace
import pytest
from zb_communication_orchestrator.contracts import parse_message

VALID_MESSAGE = '''ZB_AGENT_MESSAGE_V1
MESSAGE_ID = msg-001
EVENT_ID = evt-001
CORRELATION_ID = corr-001
CAUSATION_MESSAGE_ID = NONE
TASK_ID = ZB-COMM-001
FROM_ROLE = JINGO
TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
TARGET_REPO = Lester-Sparx/zorr-blatt-shared-hq
TARGET_ISSUE = 106
TARGET_PR = 109
BASE_SHA = 0b9b77a9d82f45e7e1821dd6c9c26861a90cf688
TARGET_HEAD_SHA = a1ad3e3a86d043544fb2900aa5f2d9faecefa7ad
TASK_REVISION = 1
EVIDENCE_REF = issue:106#comment:5448764648
EVIDENCE_SHA256 = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
EXPECTED_GATE = LESTER_RESULT
NO_AUTO_MERGE = TRUE

Implement deterministic core.
'''

@pytest.fixture
def message():
    return parse_message(VALID_MESSAGE)

@pytest.fixture
def evidence_bytes():
    return b'evidence'
