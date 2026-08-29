# R03 agent-alias live blocker evidence

Physical source: GitHub Actions run `33238083814`, job `99062567716`, artifact `9710534496`.

Observed runtime facts:

- `lester / activation` passed.
- The gh-aw firewall discovered a concrete Copilot provider model catalog.
- The reusable source configured `model: copilot/auto`.
- Copilot execution failed before any tool call with `400 The requested model is not supported.`
- The gh-aw harness classified the failure as `model_not_supported` and did not retry.

Repair direction: use the upstream gh-aw built-in `agent` model alias so gh-aw resolves an available concrete model instead of passing the literal `auto` pseudo-model through the Copilot BYOK/proxy path.
