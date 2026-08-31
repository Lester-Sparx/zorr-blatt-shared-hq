from __future__ import annotations

import unittest

from scripts.zb_execution_contract import (
    ExecutionContractError,
    parse_execution_request,
    parse_execution_result,
)


ASSIGN_MESSAGE = """ZB_AGENT_MESSAGE_V1
MESSAGE_ID = assign-only-msg
EVENT_ID = assign-only-event
CORRELATION_ID = assign-only-correlation
CAUSATION_MESSAGE_ID = NONE
TASK_ID = ASSIGN_ONLY_TASK
FROM_ROLE = JINGO
TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
BASE_SHA = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
TASK_REVISION = 1
DESIGN_HEAD = bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
NO_AUTO_MERGE = TRUE
"""

ASSIGN_RECEIPT_PASS = """ZB_AGENT_RECEIPT_V1
MESSAGE_ID = assign-only-msg
CORRELATION_ID = assign-only-correlation
SOURCE_COMMENT_ID = 123
TASK_ID = ASSIGN_ONLY_TASK
TASK_REVISION = 1
BASE_SHA = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
DESIGN_HEAD = bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
LOGICAL_FROM_ROLE = JINGO
LOGICAL_TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
STATE = RESULT
RESULT_CODE = PASS
EXECUTION_ID = github-actions:123:1
PRODUCTION_ACTIVE = NO
"""


class AssignVsExecutionBoundaryTests(unittest.TestCase):
    def test_assign_message_cannot_parse_as_execution_result(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_MARKER"):
            parse_execution_result(ASSIGN_MESSAGE)

    def test_assign_receipt_pass_cannot_parse_as_execution_request_or_result(self) -> None:
        for parser in (parse_execution_request, parse_execution_result):
            with self.subTest(parser=parser.__name__), self.assertRaisesRegex(
                ExecutionContractError,
                "INVALID_MARKER",
            ):
                parser(ASSIGN_RECEIPT_PASS)


if __name__ == "__main__":
    unittest.main()
