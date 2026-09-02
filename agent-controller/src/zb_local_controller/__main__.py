from __future__ import annotations

import sys
from typing import Any, Callable


RETIRED_CODE = "RETIRED_PRODUCTION_ROUTE"


def main(
    argv: list[str] | None = None,
    *,
    github_factory: Callable[..., Any] | None = None,
    backend_factory: Callable[..., Any] | None = None,
) -> int:
    """Fail closed for the retired local production-execution daemon.

    The package still contains read-only owner-console and historical controller
    modules because they may be useful for evidence inspection.  Production
    execution is deliberately not reachable through the package entrypoint.
    """
    _ = argv, github_factory, backend_factory
    print(
        f"{RETIRED_CODE}: local SALVADOR/ComfyUI production execution is not an active ZORR route; "
        "use the current #251 product phase and select tooling only when that phase requires it.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
