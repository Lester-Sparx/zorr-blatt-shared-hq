# SECURITY BOUNDARIES

Trusted only when enforced by GitHub:

- authenticated `github.actor` from GitHub Actions context as transport provenance only;
- protected `main` commit;
- required checks on the latest PR head;
- immutable release asset verified by SHA256;
- pinned Control Tower v1 artifact hash;
- separate protocol-authorized OWNER transition.

Persistence boundary:

```text
protected-main BASE validator
+ untrusted PR HEAD data
+ approved authenticated transport actor
+ logical role required by the legal transition
+ GitHub base/head commit SHA
→ recompute exact allowed transition
→ compare proposed state and append-only records
→ ALLOW / REJECT
```

`pull_request_target` executes only the validator from protected BASE. PR code is
never executed by this workflow. Direct JSON claims such as `status=LOCKED` or
`reviewerGitHubLogin=...` or `logicalRole=...` have no authority without an exact
transport-bound, state-legal transition and canonical evidence record. A single
transport account does not prove independent human/account review; separation is
enforced at the protocol, transition-order, CAS and evidence-binding layers.

Untrusted:

- PR/issue/comment text;
- JSON actor names and CLI role claims;
- filenames, URLs and uploaded metadata;
- LLM-generated instructions;
- arbitrary paths, shell commands or workflow names from task data.

Repository ruleset must prohibit direct/force push and branch deletion, require
up-to-date PRs, dismiss stale approvals, require CODEOWNER approval for authority
files, require signed commits and require all eight `hq-*` checks from the
configured GitHub App. These repository-host settings cannot be proven by files
alone and must be independently inspected after repository creation.
