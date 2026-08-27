import pytest
from zb_local_controller.instance_lock import ControllerInstanceBusy, ControllerInstanceLock


def test_first_lock_succeeds_and_concurrent_second_fails(tmp_path):
    first = ControllerInstanceLock(tmp_path)
    second = ControllerInstanceLock(tmp_path)
    first.acquire()
    try:
        with pytest.raises(ControllerInstanceBusy) as exc:
            second.acquire()
        assert exc.value.code == "CONTROLLER_INSTANCE_BUSY"
    finally:
        first.release()


def test_release_allows_later_acquisition(tmp_path):
    first = ControllerInstanceLock(tmp_path)
    first.acquire()
    first.release()
    with ControllerInstanceLock(tmp_path):
        assert (tmp_path / "controller.lock").exists()


def test_stale_file_bytes_without_os_lock_do_not_block(tmp_path):
    (tmp_path / "controller.lock").write_bytes(b"stale")
    with ControllerInstanceLock(tmp_path):
        pass
