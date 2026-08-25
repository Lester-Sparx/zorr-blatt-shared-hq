# Перед публикацией в GitHub

Нужны четыре разные authenticated GitHub identities:

```text
OWNER
LESTER
DUNCAN
DJANGO
```

Текущие значения `zb-owner`, `zb-lester`, `zb-duncan`, `zb-django` являются
явными deployment placeholders. Перед созданием защищённого repository их надо
заменить на реальные GitHub logins или отдельные GitHub App identities.

Один GitHub login нельзя использовать для нескольких enforcement-ролей: в этом
случае GitHub не сможет доказать независимость QC.

После назначения identities необходимо создать private repository, immutable
release для LOCKED Control Tower artifact, ruleset для `main`, required checks и
CODEOWNERS enforcement. Только затем выполняется live negative-path QC.
