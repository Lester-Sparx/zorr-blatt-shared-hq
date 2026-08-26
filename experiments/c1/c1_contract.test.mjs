import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const implPath = path.resolve('experiments/c1/c1_probe.mjs');

test('C1 proves cinematography is downstream interpretation without mutating Action Truth', async () => {
  assert.equal(existsSync(implPath), true, 'C1 implementation module must exist');

  const { runC1Probe } = await import(pathToFileURL(implPath).href);
  assert.equal(typeof runC1Probe, 'function');

  const report = runC1Probe();

  assert.equal(report.result, 'PASS');
  assert.equal(report.action_truth.unchanged, true);
  assert.equal(report.camera_interpretation.same_action_truth, true);
  assert.equal(report.camera_interpretation.camera_truth_distinct, true);
  assert.deepEqual(report.camera_interpretation.move_phase_order,
    ['HOLD', 'INITIATE', 'TRAVEL', 'REFRAME', 'SETTLE']);
  assert.equal(report.big_hit_policy.high_impact, true);
  assert.equal(report.big_hit_policy.auto_shake_created, false);
  assert.equal(report.attention_transfer.without_camera_motion, true);
  assert.equal(report.operator_performance.camera_truth_unchanged, true);
  assert.equal(report.diagnostics.contact_outside_frame_detected, true);
  assert.equal(report.diagnostics.unintentional_axis_cross_detected, true);
  assert.equal(report.diagnostics.authored_shot_unchanged, true);
  assert.equal(report.deterministic_repeat, true);
});
