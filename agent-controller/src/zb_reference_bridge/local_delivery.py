from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import os, re
from pathlib import Path
from .config import BridgeConfig
from .contracts import ReferenceDelivery

_DELIVERY_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_MIME_BY_EXT = {".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".webp":"image/webp"}

class ReferenceValidationError(RuntimeError):
    def __init__(self, code:str): self.code=code; super().__init__(code)

@dataclass(frozen=True)
class ValidatedSource:
    path:Path; size_bytes:int; sha256:str; extension:str; mime_type:str

def _unsafe_link(path:Path)->bool:
    try: st=os.lstat(path)
    except OSError: return False
    if path.is_symlink(): return True
    attrs=getattr(st,"st_file_attributes",0); flag=getattr(os,"FILE_ATTRIBUTE_REPARSE_POINT",0x400)
    return bool(attrs & flag)

def _magic_mime(data:bytes)->str|None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"): return "image/png"
    if data.startswith(b"\xff\xd8\xff"): return "image/jpeg"
    if len(data)>=12 and data[:4]==b"RIFF" and data[8:12]==b"WEBP": return "image/webp"
    return None

def validate_delivery_source(config:BridgeConfig, delivery:ReferenceDelivery)->ValidatedSource|None:
    if not _DELIVERY_ID_RE.fullmatch(delivery.delivery_id): raise ReferenceValidationError("REFERENCE_DELIVERY_ID_INVALID")
    name=delivery.source_file_name
    if not isinstance(name,str) or Path(name).name!=name or any(x in name for x in ("/","\\")): raise ReferenceValidationError("REFERENCE_EXTENSION_INVALID")
    ext=Path(name).suffix.lower(); expected_mime=_MIME_BY_EXT.get(ext)
    if expected_mime is None: raise ReferenceValidationError("REFERENCE_EXTENSION_INVALID")
    folder=Path(config.drive_sync_root)/delivery.delivery_id
    if not folder.exists(): return None
    if _unsafe_link(folder) or not folder.is_dir(): raise ReferenceValidationError("REFERENCE_DELIVERY_ID_INVALID")
    try: candidates=[p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in _MIME_BY_EXT]
    except OSError: return None
    if not candidates: return None
    if len(candidates)!=1 or candidates[0].name!=name: raise ReferenceValidationError("REFERENCE_SOURCE_COUNT_INVALID")
    source=candidates[0]
    if _unsafe_link(source): raise ReferenceValidationError("REFERENCE_SOURCE_COUNT_INVALID")
    try: data=source.read_bytes()
    except OSError: return None
    size=len(data)
    if size==0: raise ReferenceValidationError("REFERENCE_EMPTY")
    if size>config.max_source_bytes: raise ReferenceValidationError("REFERENCE_TOO_LARGE")
    if size!=delivery.size_bytes: raise ReferenceValidationError("REFERENCE_SIZE_MISMATCH")
    digest=sha256(data).hexdigest()
    if digest!=delivery.source_sha256: raise ReferenceValidationError("REFERENCE_HASH_MISMATCH")
    actual_mime=_magic_mime(data)
    if actual_mime is None or actual_mime!=expected_mime: raise ReferenceValidationError("REFERENCE_MAGIC_INVALID")
    if delivery.mime_type!=expected_mime: raise ReferenceValidationError("REFERENCE_MIME_INVALID")
    return ValidatedSource(source,size,digest,ext,expected_mime)
