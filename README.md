# ZORR BLATT — GITHUB SHARED HQ v0

External GitHub coordination adapter for the LOCKED Control Tower v1.

Local verification:

```bash
python3 scripts/hq_validate.py
python3 -m unittest discover -s tests -v
CONTROL_TOWER_ARTIFACT_PATH=/path/to/ZB_CONTROL_TOWER_v1_METADATA_BOUNDARY_LOCAL_FIX_QC.zip \
  PYTHONPATH=scripts:tests python3 -m unittest discover -s tests \
  -p 'test_control_tower_hash_lock.py' -v
python3 scripts/hq_render_dashboard.py
```

The repository skeleton does not itself prove GitHub-host settings. Before v0
can LOCK, independent QC must inspect the actual private repository ruleset,
required checks, CODEOWNERS enforcement, authenticated identities, immutable
release and protected-main behavior.

Current status: `BUILD CANDIDATE / QC PENDING / NOT LOCKED`.

Authoritative transition PRs are checked by
`scripts/hq_transition_validate.py`, executed from protected BASE through
`pull_request_target`. Manual JSON claims are rejected unless they exactly match
the transition permitted to the authenticated GitHub actor.
