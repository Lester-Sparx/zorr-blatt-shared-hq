from __future__ import annotations
import os
from pathlib import Path


class ControllerInstanceBusy(RuntimeError):
    def __init__(self):
        self.code = "CONTROLLER_INSTANCE_BUSY"
        super().__init__(self.code)


if os.name == "nt":
    import msvcrt

    def _lock(handle):
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

    def _unlock(handle):
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock(handle):
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(handle):
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class ControllerInstanceLock:
    def __init__(self, runtime_root: Path):
        self.runtime_root = Path(runtime_root)
        self.path = self.runtime_root / "controller.lock"
        self._handle = None

    def acquire(self):
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        try:
            _lock(handle)
        except OSError as exc:
            handle.close()
            raise ControllerInstanceBusy() from exc
        self._handle = handle
        return self

    def release(self):
        handle, self._handle = self._handle, None
        if handle is None:
            return
        try:
            _unlock(handle)
        finally:
            handle.close()

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False
