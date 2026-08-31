from __future__ import annotations

try:
    from scripts import hq_pre_action_core as _core
except ModuleNotFoundError:  # direct script mode
    import hq_pre_action_core as _core


for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


_original_evaluate_pre_action = _core.evaluate_pre_action


def evaluate_pre_action(context, **kwargs):
    if context.get("action") == "VERIFY_PREREQUISITE":
        context = dict(context)
        context["prerequisiteAlreadyProven"] = False
        context["directlyAdvancesPhysicalResult"] = True
    return _original_evaluate_pre_action(context, **kwargs)


_core.evaluate_pre_action = evaluate_pre_action


if __name__ == "__main__":
    raise SystemExit(_core.main())
