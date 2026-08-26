import Beep from 'https://cdn.jsdelivr.net/gh/Klathmon/Beep.js@53a43c1cf69fa4de32f921012c1fe4637aae10d5/src/beep.js';
import {
  alertIdentity,
  normalizeControlRoomState,
  shouldBeep,
} from './state.mjs';

const STATE_URL = '../hq/state/CONTROL_ROOM.json';
const POLL_INTERVAL_MS = 15_000;
const ALARM_SEQUENCE = [
  [880, 100],
  [0, 80],
  [880, 100],
  [0, 80],
  [1200, 160],
];

const elements = {
  agentTableBody: document.querySelector('#agent-table-body'),
  currentGate: document.querySelector('#current-gate'),
  lastUpdate: document.querySelector('#last-update'),
  alertPanel: document.querySelector('#alert-panel'),
  alertTitle: document.querySelector('#alert-title'),
  alertMessage: document.querySelector('#alert-message'),
  alertAction: document.querySelector('#alert-action'),
  armAlarms: document.querySelector('#arm-alarms'),
  dataHealth: document.querySelector('#data-health'),
};

let alarmsArmed = false;
let beeper = null;
let previousAlertIdentity = null;
let lastGoodState = null;

function renderAgents(agents) {
  elements.agentTableBody.replaceChildren();

  for (const agent of agents) {
    const row = document.createElement('tr');
    for (const value of [agent.id, agent.status, agent.currentWork, agent.nextTrigger]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.append(cell);
    }
    elements.agentTableBody.append(row);
  }
}

function renderAlert(alert) {
  const active = alert.level === 'BLOCKER' || alert.level === 'ACTION_REQUIRED';
  elements.alertPanel.hidden = !active;

  if (!active) {
    elements.alertTitle.textContent = 'ALERT';
    elements.alertMessage.textContent = '';
    elements.alertAction.textContent = '';
    return;
  }

  elements.alertTitle.textContent = `${alert.level}: ${alert.title}`;
  elements.alertMessage.textContent = alert.message;
  elements.alertAction.textContent = alert.action ? `ACTION: ${alert.action}` : '';
}

function renderState(state) {
  elements.currentGate.textContent = state.currentGate;
  elements.lastUpdate.textContent = state.updatedAt;
  renderAgents(state.agents);
  renderAlert(state.alert);
}

async function playAlarm() {
  if (!beeper) return;
  try {
    await beeper.beep(ALARM_SEQUENCE.map((note) => [...note]));
  } catch (error) {
    console.error('Control Room alarm playback failed', error);
  }
}

async function loadState() {
  try {
    const response = await fetch(`${STATE_URL}?ts=${Date.now()}`, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`state fetch returned HTTP ${response.status}`);
    }

    const state = normalizeControlRoomState(await response.json());
    const nextIdentity = alertIdentity(state.alert);

    if (shouldBeep({
      armed: alarmsArmed,
      previousIdentity: previousAlertIdentity,
      nextAlert: state.alert,
    })) {
      void playAlarm();
    }

    previousAlertIdentity = nextIdentity;
    lastGoodState = state;
    renderState(state);
    elements.dataHealth.textContent = 'DATA LIVE';
  } catch (error) {
    console.error('Control Room state fetch failed', error);
    elements.dataHealth.textContent = 'DATA STALE / FETCH FAILED';
    if (lastGoodState) {
      renderState(lastGoodState);
    }
  }
}

elements.armAlarms.addEventListener('click', async () => {
  if (alarmsArmed) return;

  try {
    beeper = new Beep(0.35, 'square');
    await beeper.init();
    alarmsArmed = true;
    elements.armAlarms.setAttribute('aria-pressed', 'true');
    elements.armAlarms.textContent = 'ALARMS ARMED';
  } catch (error) {
    beeper = null;
    alarmsArmed = false;
    elements.dataHealth.textContent = 'ALARMS UNAVAILABLE';
    console.error('Control Room alarm initialization failed', error);
  }
});

void loadState();
setInterval(loadState, POLL_INTERVAL_MS);
