from pathlib import Path
import pytest

from zb_reference_bridge.instance_lock import (
    BridgeInstanceBusy,
    BridgeInstanceLock,
    BridgeRuntimeUnwritable,
)


def test_second_bridge_lock_fails_with_distinct_busy_code(tmp_path: Path):
    first = BridgeInstanceLock(tmp_path)
    second = BridgeInstanceLock(tmp_path)
    first.acquire()
    try:
        with pytest.raises(BridgeInstanceBusy) as exc:
            second.acquire()
        assert exc.value.code == "REFERENCE_BRIDGE_INSTANCE_BUSY"
    finally:
        first.release()


def test_invalid_runtime_root_maps_to_runtime_unwritable(tmp_path: Path):
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")
    lock = BridgeInstanceLock(blocker / "runtime")
    with pytest.raises(BridgeRuntimeUnwritable) as exc:
        lock.acquire()
    assert exc.value.code == "REFERENCE_BRIDGE_RUNTIME_UNWRITABLE"
