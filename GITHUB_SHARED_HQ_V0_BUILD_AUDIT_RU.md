# GITHUB SHARED HQ v0 — BUILD AUDIT

Статус Лестера:

```text
LOCAL IMPLEMENTATION BUILD PASS
LIVE GITHUB ENFORCEMENT NOT YET PROVEN
ARCHITECTURE REVIEW PENDING
INDEPENDENT QC NOT STARTED
NOT LOCKED
```

## Реализовано

- отдельный external adapter вокруг неизменяемого Control Tower v1;
- pinned CT artifact SHA256 `AAADF06A...65A59EE`;
- один shared control/workflow state для защищённого `main`;
- четыре разные GitHub role identities в registry;
- authenticated Actions-context boundary;
- actual artifact SHA256 calculation before review;
- task revision + live base commit CAS;
- QC/architecture binding к exact revision/artifact/commit;
- self-review rejection;
- stale evidence rejection;
- отдельное OWNER LOCK action без auto-lock;
- G2 и Voice-to-Shot остаются blocked;
- production-value scope guard;
- read-only dashboard renderer;
- восемь именованных required checks и CODEOWNERS paths.
- protected-base BASE→PR HEAD transition validator;
- реальные append-only artifact/review/lock records со schema и hash pointers;
- authenticated OWNER lock proposal, который не пишет напрямую в `main`;
- strict `lastTransition` schema без arbitrary payload;
- persistence-bypass negative tests.

## Локальная проверка

```text
python3 scripts/hq_validate.py — PASS
python3 -m unittest discover -s tests -v — 19/19 PASS
python3 -m py_compile scripts/*.py tests/*.py — PASS
actual locked CT artifact SHA verification — PASS
dashboard render — PASS
```

## Что нельзя доказать локальным архивом

До создания реального private GitHub repository остаются непроверенными:

- branch ruleset и запрет direct/force push;
- required checks на latest PR head и trusted source;
- CODEOWNERS enforcement;
- signed commits;
- stale approval dismissal;
- четыре реальные разные GitHub identities;
- immutable release enforcement;
- GitHub Pages/Actions dashboard links.

Эти пункты не объявляются PASS по audit-файлу. Они должны быть настроены в
GitHub и независимо проверены Дунканом на живом repository.

## FINAL OWNER LOCK HASH FIX

Единственный blocker повторного architecture review исправлен:

```text
task.lockRecord = record_sha256(lock)
```

Один и тот же canonical record hash теперь используется при создании pointer и
при repository validation. Добавлен positive end-to-end тест:

```text
DUNCAN QC PASS
→ DJANGO ARCHITECTURE ACCEPTED
→ authenticated OWNER
→ lock record
→ BASE→HEAD transition validator
→ validate_repository(head)
→ OWNER_LOCKED PASS
```

## A04 PERSISTENCE FIX

Evidence namespaces теперь разрешают только canonical JSON records. Любой
не-JSON файл или изменение такого файла внутри `hq/artifacts`, `hq/reviews` или
`hq/locks` отклоняется repository validator и BASE→HEAD transition validator.

Независимые negative cases воспроизведены в suite:

```text
valid artifact transition + hidden-production.txt → REJECT
valid next QC transition + modification hidden-production.txt → REJECT
```

Исходная нумерация Architecture Contract A01–A20 восстановлена. A06 и другие
live-only guarantees не объявляются доказанными локальным архивом.

## Scope

```text
CONTROL TOWER v1 — LOCKED / UNCHANGED
G2 — BLOCKED
VOICE-TO-SHOT — BLOCKED
ZB CORE WRITES — ABSENT
NEW PRODUCTION GATES — NONE
```
