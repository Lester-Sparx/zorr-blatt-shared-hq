from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256

class PersistError(RuntimeError):
    def __init__(self, code: str): self.code=code; super().__init__(code)

class CommentWriteAmbiguous(RuntimeError):
    """Transport reports that the write may have succeeded and supplies its remote id."""
    def __init__(self, comment_id: int):
        self.comment_id=comment_id
        super().__init__('COMMENT_WRITE_AMBIGUOUS')

@dataclass(frozen=True)
class RemoteComment:
    comment_id: int
    actor: str
    body: str

@dataclass(frozen=True)
class VerifiedRemote:
    comment_id: int
    actor: str
    body: str
    sha256: str

def persist_and_verify(github, pr_number: int, body: str, *, expected_actor: str="Lester-Sparx", reconcile_comment_id: int|None=None) -> VerifiedRemote:
    comment_id = reconcile_comment_id
    if comment_id is None:
        try:
            comment_id = github.write_comment(pr_number, body)
        except CommentWriteAmbiguous as exc:
            comment_id = exc.comment_id
        except Exception as exc:
            raise PersistError("RECEIPT_WRITE_FAILED") from exc
        if not isinstance(comment_id, int) or comment_id <= 0:
            raise PersistError("RECEIPT_WRITE_FAILED")
    try:
        remote = github.read_comment(comment_id)
    except Exception as exc:
        raise PersistError("RECEIPT_READ_BACK_MISMATCH") from exc
    if not isinstance(remote, RemoteComment) or remote.comment_id != comment_id or remote.actor != expected_actor or remote.body != body:
        raise PersistError("RECEIPT_READ_BACK_MISMATCH")
    return VerifiedRemote(comment_id, remote.actor, remote.body, sha256(body.encode("utf-8")).hexdigest())
