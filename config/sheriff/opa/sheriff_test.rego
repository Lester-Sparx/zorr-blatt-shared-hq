package zorr.sheriff

base_event(event_type, data) := {
    "specversion": "1.0",
    "id": "evt-1",
    "source": "zb://test",
    "type": event_type,
    "subject": "task/test",
    "time": "2026-08-29T08:00:00Z",
    "datacontenttype": "application/json",
    "data": data,
}

test_honest_fail_is_admitted_without_penalty if {
    d := decision with input as base_event("zb.agent.result", {
        "agentId": "LESTER",
        "taskRef": "T1",
        "executionId": "E1",
        "status": "FAIL",
        "evidence": ["run:1"],
        "incidentAttribution": "SYSTEM_UPSTREAM",
    })
    d.admit == true
    d.incidentClass == null
    d.disciplineDelta == 0
    d.reason == "HONEST_FAIL"
}

test_false_pass_is_critical if {
    d := decision with input as base_event("zb.agent.result", {
        "agentId": "LESTER",
        "taskRef": "T1",
        "executionId": "E1",
        "status": "PASS",
        "evidence": ["run:1"],
        "verifiedPass": false,
    })
    d.admit == true
    d.incidentClass == "I3_CRITICAL_INTEGRITY"
    d.disciplineDelta == -20
    d.hardHold == true
    d.reason == "FALSE_PASS"
}

test_sheriff_cannot_self_judge if {
    d := decision with input as base_event("zb.sheriff.verdict", {
        "sheriffId": "SHERIFF",
        "agentId": "SHERIFF",
        "verdictId": "SV1-TEST",
        "taskRef": "T1",
        "incidentClass": "I2_PROCESS",
        "evidence": ["run:1"],
    })
    d.admit == false
    d.reason == "SELF_JUDGEMENT"
}

test_pass_without_evidence_is_rejected if {
    d := decision with input as base_event("zb.agent.result", {
        "agentId": "LESTER",
        "taskRef": "T1",
        "executionId": "E1",
        "status": "PASS",
        "evidence": [],
        "verifiedPass": true,
    })
    d.admit == false
    d.reason == "PASS_WITHOUT_EVIDENCE"
}

test_self_caught_gets_merit_without_discipline_loss if {
    d := decision with input as base_event("zb.agent.result", {
        "agentId": "DUNCAN",
        "taskRef": "T2",
        "executionId": "E2",
        "status": "FAIL",
        "evidence": ["run:2"],
        "selfCaught": true,
        "errorSignature": "HTTP_BODY_BYTE_ARRAY",
    })
    d.admit == true
    d.incidentClass == "I0_SELF_CAUGHT"
    d.disciplineDelta == 0
    d.meritDelta == 1
}

test_safety_violation_is_hard_hold if {
    d := decision with input as base_event("zb.agent.result", {
        "agentId": "DJANGO",
        "taskRef": "T3",
        "executionId": "E3",
        "status": "FAIL",
        "evidence": ["run:3"],
        "safetyViolation": true,
    })
    d.incidentClass == "I4_SAFETY_SECURITY"
    d.hardHold == true
}
