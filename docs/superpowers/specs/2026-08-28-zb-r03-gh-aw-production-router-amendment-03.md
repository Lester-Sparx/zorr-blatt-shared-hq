# ZORR BLATT — R03 GH-AW Production Router — Amendment 03

Date: 2026-08-28
Status: standing R03 OWNER authorization applies
Amends: R03 design + Amendments 01–02
Evidence: gh-aw compile run `33210636363`, sync job `98982784035`

## Finding

The pinned gh-aw compiler successfully generated the exact lock file, but a GitHub Actions `GITHUB_TOKEN` with `contents: write` cannot push a new file under `.github/workflows/**`. GitHub rejected the push with:

`refusing to allow a GitHub App to create or update workflow ... without workflows permission`

This is a platform security boundary, not a gh-aw compiler failure.

## Corrected installation law

R03 MUST NOT add a PAT, App secret, or broader runtime credential merely to let CI rewrite its own workflow definition.

Instead:

1. pinned read-only CI compiles `.md` with exact `github/gh-aw v0.86.2` + exact SHA256;
2. CI uploads the generated `.lock.yml` as immutable artifact;
3. the already-authorized GitHub connector, which has workflow-write authority, performs the one-time installation commit of the exact artifact bytes;
4. every subsequent CI run recompiles read-only and requires zero diff against the committed lock.

The GitHub connector is installation authority only. It is not part of the R03 runtime task path.

## Runtime consequence

No runtime secret is added. `zb-r03-gh-aw-compile` returns to `contents: read` only and contains no self-modifying/push job. Any future source change requires a newly generated exact lock artifact and a trusted installation update before merge.

This preserves the supply-chain property while respecting GitHub's workflow-write boundary.
