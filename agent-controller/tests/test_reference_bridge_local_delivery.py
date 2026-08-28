from hashlib import sha256
import os, pytest
from zb_reference_bridge.config import BridgeConfig
from zb_reference_bridge.contracts import ReferenceDelivery
from zb_reference_bridge.local_delivery import ReferenceValidationError, validate_delivery_source

def cfg(tmp_path): return BridgeConfig(repository="Lester-Sparx/zorr-blatt-shared-hq",drive_sync_root=tmp_path/"drive",drive_drop_folder_id="root-id",inbox_root=tmp_path/"inbox",runtime_root=tmp_path/"runtime",quarantine_root=tmp_path/"quarantine")
def delivery(data:bytes,ext="png",mime="image/png",**kw):
    vals=dict(task_id="ZB-REF-001",delivery_id="DELIV-001",drive_folder_id="folder",drive_file_id="file",source_file_name=f"source.{ext}",size_bytes=len(data),source_sha256=sha256(data).hexdigest(),mime_type=mime,source_status="OWNER_PROVIDED_REFERENCE",transport="GOOGLE_DRIVE"); vals.update(kw); return ReferenceDelivery(**vals)
def put(c,d,data):
    f=c.drive_sync_root/d.delivery_id; f.mkdir(parents=True,exist_ok=True); p=f/d.source_file_name; p.write_bytes(data); return p
PNG=b"\x89PNG\r\n\x1a\nabc"; JPEG=b"\xff\xd8\xff\xe0jpeg"; WEBP=b"RIFF\x04\x00\x00\x00WEBPdata"
@pytest.mark.parametrize("data,ext,mime",[(PNG,"png","image/png"),(JPEG,"jpg","image/jpeg"),(JPEG,"jpeg","image/jpeg"),(WEBP,"webp","image/webp")])
def test_canonical_supported_images_validate(tmp_path,data,ext,mime): c=cfg(tmp_path); d=delivery(data,ext,mime); p=put(c,d,data); s=validate_delivery_source(c,d); assert s and s.path==p and s.sha256==sha256(data).hexdigest() and s.mime_type==mime
def test_absent_folder_is_transient(tmp_path): assert validate_delivery_source(cfg(tmp_path),delivery(PNG)) is None
def test_absent_exact_file_is_transient(tmp_path): c=cfg(tmp_path); d=delivery(PNG); (c.drive_sync_root/d.delivery_id).mkdir(parents=True); assert validate_delivery_source(c,d) is None
def test_invalid_delivery_id_traversal_fails_closed(tmp_path):
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(cfg(tmp_path),delivery(PNG,delivery_id="../escape"))
    assert exc.value.code=="REFERENCE_DELIVERY_ID_INVALID"
def test_source_filename_must_be_basename(tmp_path):
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(cfg(tmp_path),delivery(PNG,source_file_name="../source.png"))
    assert exc.value.code=="REFERENCE_EXTENSION_INVALID"
def test_extra_image_fails_closed(tmp_path):
    c=cfg(tmp_path); d=delivery(PNG); put(c,d,PNG); (c.drive_sync_root/d.delivery_id/"other.jpg").write_bytes(JPEG)
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(c,d)
    assert exc.value.code=="REFERENCE_SOURCE_COUNT_INVALID"
def test_zero_bytes_is_hard_failure(tmp_path):
    c=cfg(tmp_path); d=delivery(b""); put(c,d,b"")
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(c,d)
    assert exc.value.code=="REFERENCE_EMPTY"
def test_too_large_is_hard_failure(tmp_path):
    c=cfg(tmp_path); data=PNG+b"x"*(c.max_source_bytes+1-len(PNG)); d=delivery(data); put(c,d,data)
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(c,d)
    assert exc.value.code=="REFERENCE_TOO_LARGE"
def test_size_mismatch_fails_closed(tmp_path):
    c=cfg(tmp_path); d=delivery(PNG,size_bytes=len(PNG)+1); put(c,d,PNG)
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(c,d)
    assert exc.value.code=="REFERENCE_SIZE_MISMATCH"
def test_hash_mismatch_fails_closed(tmp_path):
    c=cfg(tmp_path); d=delivery(PNG,source_sha256="0"*64); put(c,d,PNG)
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(c,d)
    assert exc.value.code=="REFERENCE_HASH_MISMATCH"
def test_magic_mismatch_fails_closed(tmp_path):
    c=cfg(tmp_path); bad=b"not png"; d=delivery(bad); put(c,d,bad)
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(c,d)
    assert exc.value.code=="REFERENCE_MAGIC_INVALID"
def test_mime_mismatch_fails_closed(tmp_path):
    c=cfg(tmp_path); d=delivery(PNG,mime="image/jpeg"); put(c,d,PNG)
    with pytest.raises(ReferenceValidationError) as exc: validate_delivery_source(c,d)
    assert exc.value.code=="REFERENCE_MIME_INVALID"
def test_symlink_source_is_rejected(tmp_path):
    if not hasattr(os,"symlink"): pytest.skip("symlink unavailable")
    c=cfg(tmp_path); d=delivery(PNG); f=c.drive_sync_root/d.delivery_id; f.mkdir(parents=True); target=tmp_path/"outside.png"; target.write_bytes(PNG)
    try: os.symlink(target,f/d.source_file_name)
    except OSError: pytest.skip("symlink not permitted")
    with pytest.raises(ReferenceValidationError): validate_delivery_source(c,d)
