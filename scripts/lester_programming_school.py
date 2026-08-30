from __future__ import annotations

SKILL_STATES = ("UNTESTED", "FAILED", "PARTIAL", "PROVEN")
MODES = {"STUDY", "EXECUTION", "TRANSFER"}
RESULTS = {"PASS", "FAIL"}
DOMAINS = (
    "python",
    "typescript_javascript",
    "git_github",
    "testing_tdd",
    "debugging_root_cause",
    "software_architecture",
    "oss_reuse",
    "ci_cd_automation",
    "security_supply_chain",
    "data_storage_search",
    "graphics_realtime",
    "computer_vision",
    "ai_agent_integration",
    "performance_reliability",
    "windows_linux_runtime",
    "math_scientific_computing",
)


class LesterProgrammingSchoolError(RuntimeError):
    pass
