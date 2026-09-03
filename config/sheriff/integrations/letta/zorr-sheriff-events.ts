import { createHmac, randomUUID } from "node:crypto";
import { spawn } from "node:child_process";

const LOGICAL_AGENT = "DUNCAN";
const TARGET_AGENT_ID = String(process.env.SHERIFF_LETTA_AGENT_ID || "").trim();
const HMAC_KEY = String(process.env.SHERIFF_EVENT_HMAC_KEY || "").trim();
const PODMAN = process.env.SHERIFF_PODMAN_PATH || "C:\\Program Files\\Podman\\podman.exe";
const WORKER_CONTAINER = process.env.SHERIFF_WORKER_CONTAINER || "zb-sheriff-sheriff-worker-1";
const PUBLISH_TIMEOUT_MS = 10_000;
const MAX_PAYLOAD_BYTES = 65_536;
const MAX_QUEUE_DEPTH = 64;
const ALLOWED_EVENT_TYPES = new Set(["zb.agent.task.started", "zb.agent.result"]);

const PYTHON_PUBLISHER = [
  "import asyncio,json,os,sys,nats",
  "from sheriff_worker import _validate_event",
  "MAX_PAYLOAD_BYTES=65536",
  "ALLOWED={'zb.agent.task.started','zb.agent.result'}",
  "async def main():",
  " raw=sys.stdin.buffer.read(MAX_PAYLOAD_BYTES+1)",
  " if len(raw)>MAX_PAYLOAD_BYTES: raise ValueError('EVENT_TOO_LARGE')",
  " event=json.loads(raw.decode('utf-8'))",
  " _validate_event(event)",
  " if event['type'] not in ALLOWED: raise ValueError('EVENT_TYPE_NOT_ALLOWED')",
  " nc=await nats.connect(os.environ['SHERIFF_NATS_URL'])",
  " js=nc.jetstream()",
  " ack=await js.publish(event['type'],json.dumps(event,separators=(',',':')).encode(),headers={'Nats-Msg-Id':event['id']})",
  " print(json.dumps({'status':'SHERIFF_EVENT_PUBLISHED','stream':ack.stream,'sequence':ack.seq},separators=(',',':')))",
  " await nc.drain()",
  "asyncio.run(main())",
].join("\n");

function now() {
  return new Date().toISOString();
}

function pseudonym(namespace, value) {
  return createHmac("sha256", HMAC_KEY)
    .update(`${namespace}\0${String(value || "unknown")}`)
    .digest("hex")
    .slice(0, 32);
}

function identityMatches(agentId) {
  return Boolean(TARGET_AGENT_ID && HMAC_KEY && agentId === TARGET_AGENT_ID);
}

function turnRef(conversationId, executionId) {
  return `letta:turn:${pseudonym("conversation", conversationId)}:${executionId}`;
}

function operationRef(kind, value) {
  return `letta:${kind}:${pseudonym(kind, value)}`;
}

function eventEnvelope({ type, subject, taskRef, executionId, data }) {
  const id = `letta:duncan:${randomUUID()}`;
  return {
    specversion: "1.0",
    id,
    source: "zb://letta/duncan",
    type,
    subject,
    time: now(),
    datacontenttype: "application/json",
    data: {
      agentId: LOGICAL_AGENT,
      taskRef,
      executionId,
      ...data,
    },
  };
}

function failureEvent({ kind, operationId, executionId, errorSignature, incidentAttribution }) {
  const taskRef = operationRef(kind, operationId);
  const event = eventEnvelope({
    type: "zb.agent.result",
    subject: taskRef,
    taskRef,
    executionId,
    data: {
      status: "FAIL",
      evidence: [],
      errorSignature,
      verifiedPass: false,
      selfCaught: false,
      incidentAttribution,
      processViolation: false,
      safetyViolation: false,
    },
  });
  event.data.evidence = [`event:${event.id}`];
  return event;
}

function publishEvent(event, onChild) {
  if (!ALLOWED_EVENT_TYPES.has(event.type)) {
    return Promise.reject(new Error("SHERIFF_EVENT_TYPE_NOT_ALLOWED"));
  }
  const payload = JSON.stringify(event);
  if (Buffer.byteLength(payload, "utf8") > MAX_PAYLOAD_BYTES) {
    return Promise.reject(new Error("SHERIFF_EVENT_PAYLOAD_TOO_LARGE"));
  }

  return new Promise((resolve, reject) => {
    const child = spawn(
      PODMAN,
      ["exec", "-i", WORKER_CONTAINER, "python", "-u", "-c", PYTHON_PUBLISHER],
      { windowsHide: true, stdio: ["pipe", "pipe", "pipe"] },
    );
    onChild(child);
    let stdout = "";
    let stderr = "";
    let settled = false;
    let timeoutError = null;
    let stdinError = null;
    let processError = null;
    const finish = (error, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      onChild(null);
      if (error) reject(error);
      else resolve(value);
    };
    const timer = setTimeout(() => {
      timeoutError = new Error("SHERIFF_EVENT_PUBLISH_TIMEOUT");
      child.kill();
    }, PUBLISH_TIMEOUT_MS);

    child.stdout.on("data", (chunk) => {
      if (stdout.length < 4096) stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk) => {
      if (stderr.length < 4096) stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => {
      processError = error;
      if (!child.pid) finish(error);
      else child.kill();
    });
    child.stdin.on("error", (error) => {
      stdinError = error;
      child.kill();
    });
    child.on("close", (code) => {
      if (timeoutError) {
        finish(timeoutError);
        return;
      }
      if (stdinError) {
        finish(new Error(`SHERIFF_EVENT_STDIN_FAILED:${stdinError.code || "UNKNOWN"}`));
        return;
      }
      if (processError) {
        finish(processError);
        return;
      }
      if (code !== 0) {
        finish(new Error(`SHERIFF_EVENT_PUBLISH_FAILED:${code}:${stderr.trim().slice(0, 300)}`));
        return;
      }
      try {
        const receipt = JSON.parse(stdout.trim());
        if (receipt.status !== "SHERIFF_EVENT_PUBLISHED" || !receipt.stream || !Number.isInteger(receipt.sequence)) {
          throw new Error("invalid receipt");
        }
        finish(null, receipt);
      } catch {
        finish(new Error("SHERIFF_EVENT_ACK_INVALID"));
      }
    });
    child.stdin.end(payload);
  });
}

export default function activate(letta) {
  if (!TARGET_AGENT_ID || !HMAC_KEY) {
    letta.diagnostics.report({ severity: "warning", message: "SHERIFF bridge disabled: identity or HMAC key missing." });
    return;
  }

  const disposers = [];
  const executions = new Map();
  const pending = [];
  let draining = false;
  let enabled = true;
  let activeChild = null;

  const reportFailure = (error) => {
    letta.diagnostics.report({
      severity: "warning",
      message: `SHERIFF event bridge unavailable: ${String(error?.message || error).slice(0, 300)}`,
    });
  };
  const drain = async () => {
    if (draining) return;
    draining = true;
    try {
      while (enabled && pending.length) {
        const next = pending.shift();
        try {
          await publishEvent(next, (child) => { activeChild = child; });
        } catch (error) {
          reportFailure(error);
        }
      }
    } finally {
      draining = false;
    }
  };
  const enqueue = (event) => {
    if (pending.length >= MAX_QUEUE_DEPTH) {
      reportFailure(new Error("SHERIFF_EVENT_QUEUE_FULL"));
      return;
    }
    pending.push(event);
    void drain();
  };
  const acceptIdentity = (agentId) => {
    if (identityMatches(agentId)) return true;
    reportFailure(new Error("SHERIFF_LETTA_IDENTITY_MISMATCH"));
    return false;
  };
  const executionFor = (conversationId) => {
    const key = pseudonym("conversation", conversationId);
    if (!executions.has(key)) executions.set(key, randomUUID());
    return executions.get(key);
  };

  if (letta.capabilities.events.turns) {
    disposers.push(letta.events.on("turn_start", (event) => {
      if (!acceptIdentity(event.agentId)) return;
      const executionId = randomUUID();
      executions.set(pseudonym("conversation", event.conversationId), executionId);
      const taskRef = turnRef(event.conversationId, executionId);
      enqueue(eventEnvelope({
        type: "zb.agent.task.started",
        subject: taskRef,
        taskRef,
        executionId,
        data: {},
      }));
    }));
  }

  if (letta.capabilities.events.tools) {
    disposers.push(letta.events.on("tool_end", (event) => {
      if (event.status !== "error" || !acceptIdentity(event.agentId)) return;
      enqueue(failureEvent({
        kind: "tool-call",
        operationId: event.toolCallId,
        executionId: executionFor(event.conversationId),
        errorSignature: `LETTA_TOOL_ERROR:${String(event.toolName).slice(0, 96)}`,
        incidentAttribution: "NONE",
      }));
    }));
  }

  if (letta.capabilities.events.llm) {
    disposers.push(letta.events.on("llm_end", (event, ctx) => {
      if (!event.error || !acceptIdentity(ctx.agent?.id)) return;
      enqueue(failureEvent({
        kind: "provider-request",
        operationId: `${ctx.conversation.id}:${event.error.errorType}:${event.error.retryable}`,
        executionId: executionFor(ctx.conversation.id),
        errorSignature: `LETTA_LLM_ERROR:${String(event.error.errorType).slice(0, 96)}:${event.error.retryable ? "RETRYABLE" : "FINAL"}`,
        incidentAttribution: "SYSTEM_UPSTREAM",
      }));
    }));
  }

  if (letta.capabilities.events.lifecycle) {
    disposers.push(letta.events.on("conversation_close", (event) => {
      if (!identityMatches(event.agentId)) return;
      executions.delete(pseudonym("conversation", event.conversationId));
    }));
  }

  return () => {
    enabled = false;
    pending.length = 0;
    executions.clear();
    if (activeChild) activeChild.kill();
    for (const dispose of disposers.reverse()) dispose();
  };
}

export const __test = { eventEnvelope, failureEvent, identityMatches, pseudonym };
