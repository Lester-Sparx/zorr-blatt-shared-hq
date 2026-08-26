import test from 'node:test';
import assert from 'node:assert/strict';

import {
  alertIdentity,
  normalizeControlRoomState,
  shouldBeep,
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

test('shouldBeep is false before alarms are armed', () => {
  assert.equal(shouldBeep({
    armed: false,
    previousIdentity: null,
    nextAlert: { level: 'BLOCKER', title: 'B', message: 'M', action: 'A' },
  }), false);
});

test('shouldBeep is false for NONE alerts', () => {
  assert.equal(shouldBeep({
    armed: true,
    previousIdentity: null,
    nextAlert: { level: 'NONE', title: '', message: '', action: '' },
  }), false);
});

test('shouldBeep is false for an unchanged active alert', () => {
  const nextAlert = { level: 'ACTION_REQUIRED', title: 'T', message: 'M', action: 'A' };
  assert.equal(shouldBeep({
    armed: true,
    previousIdentity: alertIdentity(nextAlert),
    nextAlert,
  }), false);
});

test('shouldBeep is true for a new BLOCKER alert', () => {
  assert.equal(shouldBeep({
    armed: true,
    previousIdentity: 'NONE|||',
    nextAlert: { level: 'BLOCKER', title: 'T', message: 'M', action: 'A' },
  }), true);
});

test('shouldBeep is true when ACTION_REQUIRED content materially changes', () => {
  assert.equal(shouldBeep({
    armed: true,
    previousIdentity: 'ACTION_REQUIRED|T|old|A',
    nextAlert: { level: 'ACTION_REQUIRED', title: 'T', message: 'new', action: 'A' },
  }), true);
});
