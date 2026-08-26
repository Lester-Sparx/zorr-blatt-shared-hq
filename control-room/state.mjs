export const ALERT_LEVELS = new Set(['NONE', 'BLOCKER', 'ACTION_REQUIRED']);
export const AGENT_STATUSES = new Set([
  'ACTIVE',
  'WAITING',
  'HOLD',
  'DONE',
  'BLOCKED',
  'OFFLINE',
  'PROPOSED',
]);

function requireObject(value, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError(`${name} must be an object`);
  }
  return value;
}

function requireString(value, name) {
  if (typeof value !== 'string') {
    throw new TypeError(`${name} must be a string`);
  }
  return value;
}

export function normalizeControlRoomState(raw) {
  requireObject(raw, 'state');

  if (raw.schemaVersion !== 1) {
    throw new TypeError('schemaVersion must be 1');
  }

  const alert = requireObject(raw.alert, 'alert');
  if (!ALERT_LEVELS.has(alert.level)) {
    throw new TypeError(`invalid alert level: ${String(alert.level)}`);
  }

  if (!Array.isArray(raw.agents)) {
    throw new TypeError('agents must be an array');
  }

  return {
    schemaVersion: 1,
    updatedAt: requireString(raw.updatedAt, 'updatedAt'),
    currentGate: requireString(raw.currentGate, 'currentGate'),
    alert: {
      level: alert.level,
      title: requireString(alert.title, 'alert.title'),
      message: requireString(alert.message, 'alert.message'),
      action: requireString(alert.action, 'alert.action'),
    },
    agents: raw.agents.map((agent, index) => {
      requireObject(agent, `agents[${index}]`);
      if (!AGENT_STATUSES.has(agent.status)) {
        throw new TypeError(`invalid agent status: ${String(agent.status)}`);
      }
      return {
        id: requireString(agent.id, `agents[${index}].id`),
        status: agent.status,
        currentWork: requireString(agent.currentWork, `agents[${index}].currentWork`),
        nextTrigger: requireString(agent.nextTrigger, `agents[${index}].nextTrigger`),
      };
    }),
  };
}

export function alertIdentity(alert) {
  requireObject(alert, 'alert');
  return [
    requireString(alert.level, 'alert.level'),
    requireString(alert.title, 'alert.title'),
    requireString(alert.message, 'alert.message'),
    requireString(alert.action, 'alert.action'),
  ].join('|');
}

export function shouldBeep({ armed, previousIdentity, nextAlert }) {
  requireObject(nextAlert, 'nextAlert');
  if (!ALERT_LEVELS.has(nextAlert.level)) {
    throw new TypeError(`invalid alert level: ${String(nextAlert.level)}`);
  }
  if (!armed || nextAlert.level === 'NONE') {
    return false;
  }
  return alertIdentity(nextAlert) !== previousIdentity;
}
