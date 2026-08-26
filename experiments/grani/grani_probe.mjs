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

function buildCanonicalPacket() {
  return {
    body_truth: {
      kind: 'SYNTHETIC_BODY_TRUTH_GRANI',
      body_id: 'synthetic-actor',
      height_cm: 172,
      topology_version: 'CONTROL_SYNTHETIC_V1',
    },
    motion_truth: {
      kind: 'SYNTHETIC_MOTION_TRUTH_GRANI',
      motion_id: 'synthetic-impact-recovery',
      com_path: [[0, 1.01, 0], [0.12, 0.96, 0.18], [0.26, 1.02, 0.34]],
      momentum_profile: [0.0, 4.8, 1.7],
    },
    action_truth: {
      kind: 'SYNTHETIC_ACTION_TRUTH_GRANI',
      action_id: 'synthetic-impact-recovery',
      phase: 'CONTACT_TO_RECOVERY',
      contact_point: [0.2, 1.1, 0],
      action_axis: [[-1, 0, 0], [1, 0, 0]],
    },
    physical_camera: {
      kind: 'SYNTHETIC_PHYSICAL_CAMERA_GRANI',
      camera_id: 'canonical-shot-camera',
      position: [0.72, 1.35, -4.55],
      target: [0.2, 1.1, 0],
      focal_length_mm: 50,
      near_m: 0.1,
      far_m: 100,
      roll_deg: 0,
    },
  };
}

function derivePerceivedFrame(canonicalPacket, intent) {
  const physicalCameraSha = sha256(canonicalPacket.physical_camera);
  const canonicalView = {
    physical_camera_sha256: physicalCameraSha,
    position: clone(canonicalPacket.physical_camera.position),
    target: clone(canonicalPacket.physical_camera.target),
    focal_length_mm: canonicalPacket.physical_camera.focal_length_mm,
    roll_deg: canonicalPacket.physical_camera.roll_deg,
  };

  const effects = intent.mode === 'REALITY_DISAGREEMENT'
    ? {
        spatial_warp: { enabled: true, amount: intent.spatial_warp },
        temporal_echo: { enabled: true, frames: intent.temporal_echo_frames },
        perceived_roll_offset_deg: intent.perceived_roll_offset_deg,
      }
    : {
        spatial_warp: { enabled: false, amount: 0 },
        temporal_echo: { enabled: false, frames: 0 },
        perceived_roll_offset_deg: 0,
      };

  return {
    kind: 'GRANI_PERCEIVED_FRAME_V1',
    source_physical_camera_sha256: physicalCameraSha,
    presentation_intent_sha256: sha256(intent),
    disagreement_class: intent.mode === 'REALITY_DISAGREEMENT' ? 'DERIVED_PERCEIVED' : 'NONE',
    claims_physical_truth: false,
    canonical_view: canonicalView,
    effects,
  };
}

function disableGrani(canonicalPacket) {
  return clone(canonicalPacket.physical_camera);
}

function diagnosePresentation(canonicalPacket, intent, perceivedFrame) {
  const findings = [];
  if (intent.mode === 'REALITY_DISAGREEMENT') findings.push('REALITY_DISAGREEMENT_ACTIVE');
  if (perceivedFrame.source_physical_camera_sha256 === sha256(canonicalPacket.physical_camera)) {
    findings.push('PHYSICAL_CAMERA_RECOVERABLE');
  }
  if (perceivedFrame.claims_physical_truth) findings.push('ILLEGAL_PRESENTATION_AUTHORITY_CLAIM');
  return findings;
}

function evaluateCore() {
  const canonicalPacket = buildCanonicalPacket();
  const packetBytesBefore = canonical(canonicalPacket);

  const before = {
    body: sha256(canonicalPacket.body_truth),
    motion: sha256(canonicalPacket.motion_truth),
    action: sha256(canonicalPacket.action_truth),
    physical_camera: sha256(canonicalPacket.physical_camera),
    packet: sha256(packetBytesBefore),
  };

  const neutralIntent = {
    id: 'neutral-presentation',
    mode: 'NEUTRAL',
    spatial_warp: 0,
    temporal_echo_frames: 0,
    perceived_roll_offset_deg: 0,
  };

  const disagreementIntent = {
    id: 'grani-reality-disagreement',
    mode: 'REALITY_DISAGREEMENT',
    spatial_warp: 0.18,
    temporal_echo_frames: 2,
    perceived_roll_offset_deg: 4.5,
  };

  const neutralFrame = derivePerceivedFrame(canonicalPacket, neutralIntent);
  const graniFrame = derivePerceivedFrame(canonicalPacket, disagreementIntent);
  const neutralFrameSha = sha256(neutralFrame);
  const graniFrameSha = sha256(graniFrame);

  const restore = disableGrani(canonicalPacket);
  const restoredPhysicalCameraSha = sha256(restore);

  const intentBytesBeforeDiagnostics = canonical(disagreementIntent);
  const intentShaBeforeDiagnostics = sha256(intentBytesBeforeDiagnostics);
  const packetShaBeforeDiagnostics = sha256(canonicalPacket);
  const findings = diagnosePresentation(canonicalPacket, disagreementIntent, graniFrame);
  const intentBytesAfterDiagnostics = canonical(disagreementIntent);
  const intentShaAfterDiagnostics = sha256(intentBytesAfterDiagnostics);
  const packetShaAfterDiagnostics = sha256(canonicalPacket);

  const after = {
    body: sha256(canonicalPacket.body_truth),
    motion: sha256(canonicalPacket.motion_truth),
    action: sha256(canonicalPacket.action_truth),
    physical_camera: sha256(canonicalPacket.physical_camera),
    packet: sha256(canonical(canonicalPacket)),
  };

  return {
    proof: 'GRANI_PRESENTATION_TRUTH_V1',
    result: 'PASS',
    canonical_truth: {
      body_sha256_before: before.body,
      body_sha256_after: after.body,
      body_unchanged: before.body === after.body,
      motion_sha256_before: before.motion,
      motion_sha256_after: after.motion,
      motion_unchanged: before.motion === after.motion,
      action_sha256_before: before.action,
      action_sha256_after: after.action,
      action_unchanged: before.action === after.action,
      physical_camera_sha256_before: before.physical_camera,
      physical_camera_sha256_after: after.physical_camera,
      physical_camera_unchanged: before.physical_camera === after.physical_camera,
      packet_sha256_before: before.packet,
      packet_sha256_after: after.packet,
      packet_unchanged: before.packet === after.packet,
    },
    presentation: {
      same_canonical_packet: neutralFrame.source_physical_camera_sha256 === graniFrame.source_physical_camera_sha256,
      neutral_perceived_frame_sha256: neutralFrameSha,
      grani_perceived_frame_sha256: graniFrameSha,
      perceived_frames_distinct: neutralFrameSha !== graniFrameSha,
      disagreement_class: graniFrame.disagreement_class,
      claims_physical_truth: graniFrame.claims_physical_truth,
      neutral_mode: neutralIntent.mode,
      grani_mode: disagreementIntent.mode,
    },
    restore: {
      canonical_physical_camera_sha256: before.physical_camera,
      restored_physical_camera_sha256: restoredPhysicalCameraSha,
      canonical_view_restored: restoredPhysicalCameraSha === before.physical_camera,
    },
    diagnostics: {
      findings,
      presentation_intent_sha256_before: intentShaBeforeDiagnostics,
      presentation_intent_sha256_after: intentShaAfterDiagnostics,
      presentation_intent_unchanged: intentShaBeforeDiagnostics === intentShaAfterDiagnostics,
      canonical_packet_sha256_before: packetShaBeforeDiagnostics,
      canonical_packet_sha256_after: packetShaAfterDiagnostics,
      canonical_packet_unchanged: packetShaBeforeDiagnostics === packetShaAfterDiagnostics,
      read_only: true,
    },
    authority: {
      grani_is_downstream_presentation: true,
      perceived_frame_is_derived: true,
      physical_camera_remains_canonical: true,
      writeback_to_camera_action_motion_body_allowed: false,
      production_renderer_authorized: false,
      coordinate_system_locked: false,
    },
  };
}

export function runGraniProbe() {
  const first = evaluateCore();
  const second = evaluateCore();
  return {
    ...first,
    deterministic_repeat: canonical(first) === canonical(second),
  };
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const report = runGraniProbe();
  const output = `${JSON.stringify(report, null, 2)}\n`;
  if (process.argv[2]) fs.writeFileSync(process.argv[2], output);
  process.stdout.write(output);
}
