import test from 'node:test';
import assert from 'node:assert/strict';

import {
  alertIdentity,
  normalizeControlRoomState,
} from '../state.mjs';

const validState = {
  schemaVersion: 1,
  updatedAt: '2026-08-26T12:00:00Z',
  currentGate: 'TEST',
  alert: { level: 'NONE', title: '', message: '', action: '' },
  agents: [],
};

test('normalizeControlRoomState returns a normalized valid state', () => {
  assert.deepEqual(normalizeControlRoomState(validState), validState);
});

test('normalizeControlRoomState rejects an invalid alert level', () => {
  assert.throws(
    () => normalizeControlRoomState({
      ...validState,
      alert: { ...validState.alert, level: 'PANIC' },
    }),
    /invalid alert level/i,
  );
});

test('normalizeControlRoomState rejects missing agents', () => {
  const { agents: _agents, ...withoutAgents } = validState;
  assert.throws(() => normalizeControlRoomState(withoutAgents), /agents/i);
});

test('alertIdentity is stable for unchanged content and changes with material content', () => {
  const alert = {
    level: 'ACTION_REQUIRED',
    title: 'OWNER ACTION',
    message: 'Enable Pages',
    action: 'Settings -> Pages',
  };

  assert.equal(alertIdentity(alert), alertIdentity({ ...alert }));
  assert.notEqual(alertIdentity(alert), alertIdentity({ ...alert, title: 'BLOCKER' }));
  assert.notEqual(alertIdentity(alert), alertIdentity({ ...alert, message: 'Different message' }));
  assert.notEqual(alertIdentity(alert), alertIdentity({ ...alert, action: 'Different action' }));
});
