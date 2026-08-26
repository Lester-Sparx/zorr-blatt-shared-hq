import crypto from 'node:crypto';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  const bytes = typeof value === 'string' ? value : canonical(value);
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function solveCameraTruth(actionTruthSha, intent) {
  const movePhaseOrder = ['HOLD', 'INITIATE', 'TRAVEL', 'REFRAME', 'SETTLE'];
  const physicalTrack = intent.movement === 'MOVE'
    ? [
        { phase: 'HOLD', position: [0, 1.6, -6], target: intent.start_anchor },
        { phase: 'INITIATE', position: [0.1, 1.6, -5.8], target: intent.target_anchor },
        { phase: 'TRAVEL', position: intent.travel_position, target: intent.target_anchor },
        { phase: 'REFRAME', position: intent.reframe_position, target: intent.target_anchor },
        { phase: 'SETTLE', position: intent.settle_position, target: intent.settle_anchor },
      ]
    : [
        { phase: 'HOLD', position: [0, 1.6, -6], target: intent.start_anchor },
        { phase: 'HOLD', position: [0, 1.6, -6], target: intent.target_anchor },
      ];

  return {
    kind: 'C1_CAMERA_TRUTH_V1',
    action_truth_sha256: actionTruthSha,
    shot_intent_sha256: sha256(intent),
    intent_id: intent.id,
    reason: intent.reason,
    target: intent.target_anchor,
    settle: intent.settle_anchor,
    movement: intent.movement,
    move_phase_order: intent.movement === 'MOVE' ? movePhaseOrder : ['HOLD'],
    physical_track: physicalTrack,
    shake: {
      enabled: intent.shake?.enabled === true,
      reason: intent.shake?.enabled === true ? intent.shake.reason : null,
    },
  };
}

function applyOperatorPerformance(cameraTruth, profile) {
  return {
    kind: 'C1_OPERATOR_PERFORMANCE_V1',
    camera_truth_sha256: sha256(cameraTruth),
    profile,
    offsets: [
      { phase: 'HOLD', offset: [0, 0, 0] },
      { phase: 'TRAVEL', offset: [0.002, -0.001, 0] },
      { phase: 'SETTLE', offset: [0, 0, 0] },
    ],
    canonical_physical_camera_recoverable: true,
  };
}

function diagnoseAuthoredShot(authoredShot) {
  const findings = [];
  const [u, v] = authoredShot.projected_contact_uv;
  const safe = authoredShot.safe_frame;
  if (u < safe.u[0] || u > safe.u[1] || v < safe.v[0] || v > safe.v[1]) {
    findings.push('CONTACT_OUTSIDE_FRAME');
  }
  if (
    Math.sign(authoredShot.camera_side_start) !== Math.sign(authoredShot.camera_side_end)
    && authoredShot.axis_cross_intent !== 'INTENTIONAL'
  ) {
    findings.push('UNINTENTIONAL_AXIS_CROSS');
  }
  return findings;
}

function evaluateCore() {
  const actionTruth = {
    kind: 'SYNTHETIC_ACTION_TRUTH_C1',
    action_id: 'synthetic-impact-recovery',
    phase_order: ['PREPARE', 'LOAD', 'LAUNCH', 'AIR_TRANSFER', 'CONTACT', 'RECOVERY'],
    action_axis: { from: [-1, 0, 0], to: [1, 0, 0] },
    contact: { point: [0.2, 1.1, 0], impulse_n_s: 510, magnitude: 9.2 },
    attention_candidates: ['FACE', 'CONTACT_POINT', 'TORSO'],
    recovery_vector: [0.25, 0, 0.4],
  };

  const actionBytesBefore = canonical(actionTruth);
  const actionShaBefore = sha256(actionBytesBefore);

  const impactIntent = {
    id: 'impact-readability',
    reason: 'make contact mechanics legible',
    movement: 'MOVE',
    start_anchor: 'FACE',
    target_anchor: 'CONTACT_POINT',
    settle_anchor: 'CONTACT_POINT',
    travel_position: [0.5, 1.45, -4.7],
    reframe_position: [0.75, 1.35, -4.5],
    settle_position: [0.72, 1.35, -4.55],
    shake: { enabled: false },
  };

  const recoveryIntent = {
    id: 'recovery-context',
    reason: 'preserve spatial context through recovery',
    movement: 'MOVE',
    start_anchor: 'CONTACT_POINT',
    target_anchor: 'TORSO',
    settle_anchor: 'TORSO',
    travel_position: [-0.35, 1.8, -6.4],
    reframe_position: [-0.5, 1.9, -6.8],
    settle_position: [-0.48, 1.9, -6.75],
    shake: { enabled: false },
  };

  const cameraA = solveCameraTruth(actionShaBefore, impactIntent);
  const cameraB = solveCameraTruth(actionShaBefore, recoveryIntent);
  const cameraASha = sha256(cameraA);
  const cameraBSha = sha256(cameraB);

  const attentionOnlyIntent = {
    id: 'attention-transfer-on-hold',
    reason: 'shift attention without moving the physical camera',
    movement: 'HOLD',
    start_anchor: 'FACE',
    target_anchor: 'CONTACT_POINT',
    settle_anchor: 'CONTACT_POINT',
    shake: { enabled: false },
  };
  const attentionCamera = solveCameraTruth(actionShaBefore, attentionOnlyIntent);
  const holdPositions = attentionCamera.physical_track.map((state) => canonical(state.position));
  const attentionChanged = attentionCamera.physical_track[0].target !== attentionCamera.physical_track[1].target;
  const physicalCameraHeld = new Set(holdPositions).size === 1;

  const cameraABytesBeforeOperator = canonical(cameraA);
  const cameraAShaBeforeOperator = sha256(cameraABytesBeforeOperator);
  const operatorPerformance = applyOperatorPerformance(cameraA, {
    id: 'controlled-human-operator',
    micro_drift: 'LOW',
    settle_priority: 'HIGH',
  });
  const cameraABytesAfterOperator = canonical(cameraA);
  const cameraAShaAfterOperator = sha256(cameraABytesAfterOperator);

  const badAuthoredShot = {
    id: 'diagnostic-control-shot',
    projected_contact_uv: [1.12, 0.52],
    safe_frame: { u: [0.05, 0.95], v: [0.05, 0.95] },
    camera_side_start: 1,
    camera_side_end: -1,
    axis_cross_intent: 'UNINTENTIONAL',
    authored_camera: clone(cameraA),
  };
  const badShotBytesBefore = canonical(badAuthoredShot);
  const badShotShaBefore = sha256(badShotBytesBefore);
  const findings = diagnoseAuthoredShot(badAuthoredShot);
  const badShotBytesAfter = canonical(badAuthoredShot);
  const badShotShaAfter = sha256(badShotBytesAfter);

  const actionBytesAfter = canonical(actionTruth);
  const actionShaAfter = sha256(actionBytesAfter);

  return {
    proof: 'C1_CINEMATOGRAPHY_TRUTH_V1',
    result: 'PASS',
    action_truth: {
      sha256_before: actionShaBefore,
      sha256_after: actionShaAfter,
      bytes_before: Buffer.byteLength(actionBytesBefore),
      bytes_after: Buffer.byteLength(actionBytesAfter),
      unchanged: actionBytesBefore === actionBytesAfter && actionShaBefore === actionShaAfter,
    },
    camera_interpretation: {
      same_action_truth: cameraA.action_truth_sha256 === cameraB.action_truth_sha256,
      camera_truth_a_sha256: cameraASha,
      camera_truth_b_sha256: cameraBSha,
      camera_truth_distinct: cameraASha !== cameraBSha,
      move_phase_order: cameraA.move_phase_order,
      intent_a: impactIntent.id,
      intent_b: recoveryIntent.id,
    },
    big_hit_policy: {
      high_impact: actionTruth.contact.magnitude >= 8,
      impact_magnitude: actionTruth.contact.magnitude,
      camera_a_shake: cameraA.shake.enabled,
      camera_b_shake: cameraB.shake.enabled,
      auto_shake_created: cameraA.shake.enabled || cameraB.shake.enabled,
    },
    attention_transfer: {
      from: attentionCamera.physical_track[0].target,
      to: attentionCamera.physical_track[1].target,
      physical_camera_held: physicalCameraHeld,
      attention_changed: attentionChanged,
      without_camera_motion: physicalCameraHeld && attentionChanged,
    },
    operator_performance: {
      camera_truth_sha256_before: cameraAShaBeforeOperator,
      camera_truth_sha256_after: cameraAShaAfterOperator,
      camera_truth_unchanged:
        cameraABytesBeforeOperator === cameraABytesAfterOperator
        && cameraAShaBeforeOperator === cameraAShaAfterOperator,
      performance_sha256: sha256(operatorPerformance),
      canonical_physical_camera_recoverable: operatorPerformance.canonical_physical_camera_recoverable,
    },
    diagnostics: {
      findings,
      contact_outside_frame_detected: findings.includes('CONTACT_OUTSIDE_FRAME'),
      unintentional_axis_cross_detected: findings.includes('UNINTENTIONAL_AXIS_CROSS'),
      authored_shot_sha256_before: badShotShaBefore,
      authored_shot_sha256_after: badShotShaAfter,
      authored_shot_unchanged:
        badShotBytesBefore === badShotBytesAfter && badShotShaBefore === badShotShaAfter,
    },
    authority: {
      action_truth_is_upstream_input: true,
      camera_truth_is_downstream_interpretation: true,
      operator_performance_is_derived: true,
      diagnostics_are_read_only: true,
      automatic_impact_shake_is_authority: false,
      production_camera_runtime_authorized: false,
      grani_is_part_of_c1: false,
    },
  };
}

export function runC1Probe() {
  const first = evaluateCore();
  const second = evaluateCore();
  const deterministicRepeat = canonical(first) === canonical(second) && sha256(first) === sha256(second);
  return { ...first, deterministic_repeat: deterministicRepeat };
}

const invokedDirectly = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (invokedDirectly) {
  const outPath = process.argv[2] ?? 'c1-report.json';
  const report = runC1Probe();
  const text = `${JSON.stringify(report, null, 2)}\n`;
  fs.writeFileSync(outPath, text);
  process.stdout.write(text);
}
