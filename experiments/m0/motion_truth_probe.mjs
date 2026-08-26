import fs from "node:fs";
import crypto from "node:crypto";
import assert from "node:assert/strict";

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return crypto.createHash("sha256").update(typeof value === "string" ? value : canonical(value)).digest("hex");
}

function finiteVec(v, n = 3) {
  return Array.isArray(v) && v.length === n && v.every(Number.isFinite);
}

function scale(v, s) {
  return v.map((x) => x * s);
}

function norm(v) {
  return Math.sqrt(v.reduce((sum, x) => sum + x * x, 0));
}

const BODY_DNA = {
  schema: "SYNTHETIC_BODY_DNA_V1",
  actor: "anonymous-m0-probe",
  massKg: 72,
  statureCm: 172,
  topologyVersion: "synthetic-control-v1",
  restRigVersion: "synthetic-rest-v1",
};

const SPACE_TRUTH = {
  schema: "SYNTHETIC_SPACE_TRUTH_V1",
  gravityMps2: [0, -9.81, 0],
  groundPlane: { normal: [0, 1, 0], offsetM: 0 },
};

const MOTION_DNA = {
  schema: "SYNTHETIC_MOTION_DNA_V1",
  loadDepthBias: 0.7,
  momentumRetention: 0.65,
  landingSoftness: 0.6,
  reactionDelayMs: 80,
  supportPreference: "LEFT_FIRST",
};

const PHASES = ["PREPARE", "LOAD", "LAUNCH", "AIR_TRANSFER", "CONTACT", "RECOVERY"];
const LANDING_EVENTS = [
  "FIRST_CONTACT",
  "LOAD_ACCEPTANCE",
  "COM_DECELERATION",
  "JOINT_COMPRESSION",
  "TORSO_RESPONSE",
  "SECONDARY_CONTACT",
  "FOOT_SETTLE",
  "STABILIZATION",
];

function deriveState(sample, body) {
  assert(finiteVec(sample.comPosM), `${sample.phase}: invalid COM position`);
  assert(finiteVec(sample.comVelMps), `${sample.phase}: invalid COM velocity`);
  assert(finiteVec(sample.angularVelRadS), `${sample.phase}: invalid angular velocity`);
  assert(Array.isArray(sample.support), `${sample.phase}: support must be explicit`);

  const inertiaProxy = body.massKg * 0.2;
  return {
    t: sample.t,
    phase: sample.phase,
    comPosM: sample.comPosM,
    comVelMps: sample.comVelMps,
    support: [...sample.support],
    linearMomentumKgMps: scale(sample.comVelMps, body.massKg),
    angularMomentumProxy: scale(sample.angularVelRadS, inertiaProxy),
  };
}

function buildActionTrace(body, motionDna) {
  const load = 0.10 + motionDna.loadDepthBias * 0.06;
  const retain = motionDna.momentumRetention;
  const samples = [
    { t: 0.00, phase: "PREPARE", comPosM: [0, 1.00, 0.00], comVelMps: [0, 0, 0], angularVelRadS: [0, 0, 0], support: ["L", "R"] },
    { t: 0.12, phase: "LOAD", comPosM: [0, 1.00 - load, 0.02], comVelMps: [0, -0.85, 0.18], angularVelRadS: [0, 0.20, 0], support: ["L", "R"] },
    { t: 0.24, phase: "LAUNCH", comPosM: [0, 0.98, 0.10], comVelMps: [0, 2.60, 1.70], angularVelRadS: [0, 0.85, 0], support: ["L"] },
    { t: 0.46, phase: "AIR_TRANSFER", comPosM: [0, 1.36, 0.40], comVelMps: [0, 0.45, 1.70 * retain], angularVelRadS: [0, 1.10, 0], support: [] },
    { t: 0.68, phase: "CONTACT", comPosM: [0, 1.04, 0.69], comVelMps: [0, -2.40, 1.05], angularVelRadS: [0, 0.55, 0], support: ["L"] },
    { t: 0.96, phase: "RECOVERY", comPosM: [0, 0.99, 0.83], comVelMps: [0, 0.00, 0.12], angularVelRadS: [0, 0.08, 0], support: ["L", "R"] },
  ];
  return samples.map((s) => deriveState(s, body));
}

function verifyActionTrace(trace) {
  assert.deepEqual(trace.map((s) => s.phase), PHASES, "phase order mismatch");
  for (let i = 1; i < trace.length; i++) {
    assert(trace[i].t > trace[i - 1].t, "time must be strictly monotonic");
  }
  assert(trace.every((s) => finiteVec(s.linearMomentumKgMps)), "linear momentum missing");
  assert(trace.every((s) => finiteVec(s.angularMomentumProxy)), "angular momentum missing");
  assert.deepEqual(trace.find((s) => s.phase === "AIR_TRANSFER").support, [], "air transfer must have no support contact");
  assert(trace.find((s) => s.phase === "CONTACT").support.length > 0, "contact must restore support");
  const contactSpeed = norm(trace.find((s) => s.phase === "CONTACT").comVelMps);
  const recoverySpeed = norm(trace.find((s) => s.phase === "RECOVERY").comVelMps);
  assert(recoverySpeed < contactSpeed, "recovery must absorb impact momentum");
}

function landingTrace() {
  const verticalSpeedMps = [-2.40, -1.85, -1.25, -0.90, -0.55, -0.28, -0.08, 0.00];
  return LANDING_EVENTS.map((event, i) => ({
    event,
    t: 0.680 + i * 0.035,
    verticalSpeedMps: verticalSpeedMps[i],
    supportCount: i < 5 ? 1 : 2,
  }));
}

function verifyLanding(events) {
  assert.deepEqual(events.map((e) => e.event), LANDING_EVENTS, "landing event order mismatch");
  for (let i = 1; i < events.length; i++) {
    assert(events[i].t > events[i - 1].t, "landing time must be monotonic");
    assert(Math.abs(events[i].verticalSpeedMps) <= Math.abs(events[i - 1].verticalSpeedMps), "impact must be progressively absorbed");
  }
  assert.equal(events.at(-1).verticalSpeedMps, 0, "stabilization must end vertical impact velocity");
  assert.equal(events.at(-1).supportCount, 2, "stabilization must end with settled support");
}

function motionTruthForCounterexample({ pose, comVelMps, support, history }, body) {
  return {
    poseHash: sha256(pose),
    support,
    history,
    linearMomentumKgMps: scale(comVelMps, body.massKg),
    speedMps: norm(comVelMps),
  };
}

function poseCounterexample(body, space) {
  const sharedPose = {
    root: [0, 0, 0, 1],
    hips: [0.10, -0.20, 0.05],
    knees: [0.62, 0.58],
    shoulders: [0.18, -0.14],
  };

  const a = motionTruthForCounterexample({
    pose: sharedPose,
    comVelMps: [2.0, 0.0, 0.0],
    support: ["L"],
    history: ["LOAD", "LAUNCH"],
  }, body);

  const b = motionTruthForCounterexample({
    pose: sharedPose,
    comVelMps: [-0.5, -1.5, 0.0],
    support: [],
    history: ["LAUNCH", "AIR_TRANSFER"],
  }, body);

  const actionA = sha256({ body: sha256(body), space: sha256(space), motion: a });
  const actionB = sha256({ body: sha256(body), space: sha256(space), motion: b });

  assert.equal(a.poseHash, b.poseHash, "control poses must be byte-identical");
  assert.notEqual(sha256(a), sha256(b), "same pose with different mechanics must produce different Motion Truth");
  assert.notEqual(actionA, actionB, "same pose with different mechanics must produce different Action Truth");

  return {
    pose_hash: a.poseHash,
    motion_truth_hash_a: sha256(a),
    motion_truth_hash_b: sha256(b),
    action_truth_hash_a: actionA,
    action_truth_hash_b: actionB,
    pose_equal: true,
    motion_truth_distinct: true,
    action_truth_distinct: true,
  };
}

function buildReport() {
  const bodyBeforeBytes = canonical(BODY_DNA);
  const bodyBeforeSha = sha256(bodyBeforeBytes);

  const trace = buildActionTrace(BODY_DNA, MOTION_DNA);
  verifyActionTrace(trace);

  const landing = landingTrace();
  verifyLanding(landing);

  const counterexample = poseCounterexample(BODY_DNA, SPACE_TRUTH);

  const bodyAfterBytes = canonical(BODY_DNA);
  const bodyAfterSha = sha256(bodyAfterBytes);
  assert.equal(bodyAfterBytes, bodyBeforeBytes, "Motion DNA evaluation mutated Body DNA bytes");
  assert.equal(bodyAfterSha, bodyBeforeSha, "Motion DNA evaluation mutated Body DNA hash");

  const motionTruth = {
    phases: trace,
    landing,
    motionDnaHash: sha256(MOTION_DNA),
  };

  return {
    proof: "M0_MOTION_TRUTH_V1",
    result: "PASS",
    laws: {
      pose_is_not_motion: true,
      motion_is_time_dependent_mechanics: true,
      motion_dna_does_not_mutate_body_dna: true,
      action_truth_is_body_plus_space_plus_motion: true,
    },
    body_dna: {
      canonical_bytes: Buffer.byteLength(bodyBeforeBytes),
      sha256_before: bodyBeforeSha,
      sha256_after: bodyAfterSha,
      unchanged: bodyBeforeSha === bodyAfterSha,
    },
    space_truth_sha256: sha256(SPACE_TRUTH),
    motion_dna_sha256: sha256(MOTION_DNA),
    phase_order: PHASES,
    landing_event_order: LANDING_EVENTS,
    trace_sample_count: trace.length,
    landing_event_count: landing.length,
    contact_linear_momentum_kg_mps: trace.find((s) => s.phase === "CONTACT").linearMomentumKgMps,
    recovery_linear_momentum_kg_mps: trace.find((s) => s.phase === "RECOVERY").linearMomentumKgMps,
    pose_counterexample: counterexample,
    motion_truth_sha256: sha256(motionTruth),
    action_truth_sha256: sha256({ body: bodyBeforeSha, space: sha256(SPACE_TRUTH), motion: sha256(motionTruth) }),
    authority: {
      body_dna_is_authority: true,
      motion_dna_is_separate: true,
      motion_truth_is_derived: true,
      action_truth_is_derived: true,
      animation_clip_is_authority: false,
      camera_is_part_of_m0: false,
    },
  };
}

const first = buildReport();
const second = buildReport();
assert.equal(canonical(first), canonical(second), "M0 report must be deterministic across repeated execution");

const report = { ...first, deterministic_repeat: true };
const out = process.argv[2] ?? "m0-report.json";
fs.writeFileSync(out, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));
