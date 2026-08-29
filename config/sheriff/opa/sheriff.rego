package zorr.sheriff

# Policy contract markers: FALSE_PASS, SELF_JUDGEMENT, PASS_WITHOUT_EVIDENCE.

known_event_types := {
    "zb.agent.task.started",
    "zb.agent.result",
    "zb.agent.qc",
    "zb.sheriff.verdict",
    "zb.league.match",
}

default decision := {
    "admit": false,
    "incidentClass": null,
    "disciplineDelta": 0,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "UNKNOWN_EVENT_TYPE",
}

has_evidence if {
    is_array(input.data.evidence)
    count(input.data.evidence) > 0
}

is_self_judgement if {
    input.type == "zb.sheriff.verdict"
    input.data.sheriffId == input.data.agentId
}

is_safety_violation if {
    input.type == "zb.agent.result"
    input.data.safetyViolation == true
}

is_false_pass if {
    input.type == "zb.agent.result"
    input.data.status == "PASS"
    has_evidence
    input.data.verifiedPass == false
}

is_pass_without_evidence if {
    input.type in {"zb.agent.result", "zb.agent.qc"}
    input.data.status == "PASS"
    not has_evidence
}

is_process_violation if {
    input.type == "zb.agent.result"
    input.data.processViolation == true
}

is_self_caught if {
    input.type == "zb.agent.result"
    input.data.selfCaught == true
    has_evidence
    input.data.status in {"FAIL", "BLOCKED"}
}

is_correctness_incident if {
    input.type == "zb.agent.result"
    input.data.incidentAttribution == "AGENT_CORRECTNESS"
    has_evidence
    input.data.status in {"FAIL", "BLOCKED"}
}

is_honest_fail if {
    input.type == "zb.agent.result"
    input.data.status in {"FAIL", "BLOCKED"}
    has_evidence
    not is_safety_violation
    not is_process_violation
    not is_self_caught
    not is_correctness_incident
}

is_clean_pass if {
    input.type in {"zb.agent.result", "zb.agent.qc"}
    input.data.status == "PASS"
    has_evidence
    not is_false_pass
}

decision := {
    "admit": false,
    "incidentClass": null,
    "disciplineDelta": 0,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "SELF_JUDGEMENT",
} if {
    is_self_judgement
}

decision := {
    "admit": false,
    "incidentClass": null,
    "disciplineDelta": 0,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "PASS_WITHOUT_EVIDENCE",
} if {
    is_pass_without_evidence
}

decision := {
    "admit": true,
    "incidentClass": "I4_SAFETY_SECURITY",
    "disciplineDelta": -25,
    "meritDelta": 0,
    "hardHold": true,
    "reason": "SAFETY_SECURITY_VIOLATION",
} if {
    is_safety_violation
}

decision := {
    "admit": true,
    "incidentClass": "I3_CRITICAL_INTEGRITY",
    "disciplineDelta": -20,
    "meritDelta": 0,
    "hardHold": true,
    "reason": "FALSE_PASS",
} if {
    is_false_pass
    not is_safety_violation
}

decision := {
    "admit": true,
    "incidentClass": "I2_PROCESS",
    "disciplineDelta": -5,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "PROCESS_VIOLATION",
} if {
    is_process_violation
    not is_safety_violation
    not is_false_pass
}

decision := {
    "admit": true,
    "incidentClass": "I0_SELF_CAUGHT",
    "disciplineDelta": 0,
    "meritDelta": 1,
    "hardHold": false,
    "reason": "SELF_CAUGHT_BEFORE_HANDOFF",
} if {
    is_self_caught
    not is_safety_violation
    not is_process_violation
}

decision := {
    "admit": true,
    "incidentClass": "I1_CORRECTNESS",
    "disciplineDelta": -2,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "AGENT_CORRECTNESS_INCIDENT",
} if {
    is_correctness_incident
    not is_safety_violation
    not is_process_violation
    not is_self_caught
}

decision := {
    "admit": true,
    "incidentClass": null,
    "disciplineDelta": 0,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "HONEST_FAIL",
} if {
    is_honest_fail
}

decision := {
    "admit": true,
    "incidentClass": null,
    "disciplineDelta": 0,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "VERIFIED_RESULT",
} if {
    is_clean_pass
}

decision := {
    "admit": true,
    "incidentClass": null,
    "disciplineDelta": 0,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "KNOWN_EVENT",
} if {
    input.type in {"zb.agent.task.started", "zb.league.match"}
}

decision := {
    "admit": true,
    "incidentClass": null,
    "disciplineDelta": 0,
    "meritDelta": 0,
    "hardHold": false,
    "reason": "INDEPENDENT_VERDICT",
} if {
    input.type == "zb.sheriff.verdict"
    input.type in known_event_types
    not is_self_judgement
}
