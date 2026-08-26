import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const implPath = path.resolve('experiments/grani/grani_probe.mjs');

test('GRANI proves perceived-frame disagreement is downstream and non-authoritative', async () => {
  assert.equal(existsSync(implPath), true, 'GRANI implementation module must exist');

  const { runGraniProbe } = await import(pathToFileURL(implPath).href);
  assert.equal(typeof runGraniProbe, 'function');

  const report = runGraniProbe();

  assert.equal(report.result, 'PASS');
  assert.equal(report.canonical_truth.body_unchanged, true);
  assert.equal(report.canonical_truth.motion_unchanged, true);
  assert.equal(report.canonical_truth.action_unchanged, true);
  assert.equal(report.canonical_truth.physical_camera_unchanged, true);
  assert.equal(report.presentation.same_canonical_packet, true);
  assert.equal(report.presentation.perceived_frames_distinct, true);
  assert.equal(report.presentation.disagreement_class, 'DERIVED_PERCEIVED');
  assert.equal(report.presentation.claims_physical_truth, false);
  assert.equal(report.restore.canonical_view_restored, true);
  assert.equal(report.diagnostics.presentation_intent_unchanged, true);
  assert.equal(report.diagnostics.canonical_packet_unchanged, true);
  assert.equal(report.deterministic_repeat, true);
});
