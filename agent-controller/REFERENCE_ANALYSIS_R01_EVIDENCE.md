# Reference Analysis R01 — execution evidence

Candidate branch: `zb/reference-analysis-base-r01`
Base: `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`
Math contract SHA256: `a5926ba1f169d74a5562bd158ab6dc769090467aa7a1146541bd8a565bcac3c8`
OpenCV inspected ref: `2ea6598f64f6f03d9d08db084a60585b0fc585f1`

Byte identity checked against the locally executed candidate:
- `reference_analysis.py` Git blob `b951eb06709793765def4c76a1f3fce1886c89cf`, SHA256 `7f6118639dfc2d60d1fa3e640f8a6ccca07fb8a8f4286bea0fc95771e06595a8`
- `test_reference_analysis.py` Git blob `1847178f496496e40ac01da173553b5a055c4510`, SHA256 `288bf79e48b4de80c034b237f8b5d09d844187c1e26689d4565709d4805e46d6`
- `pyproject.toml` Git blob `31bedc2431e89eb9953cf619dc83253ab069d1e1`, SHA256 `59ef59d306984ba585852a7e26e85940be0ffb894aa2749eef2db54157651b28`

Local isolated verification on those exact source bytes:
- `pytest`: 3 passed.
- No render, generation, or image edit was executed.

Real-reference transfer runs, same deliberately recorded measurement parameters (`epsilon=1.5 px`, `tone sigma=24 px`, `k=6`) for controlled comparison; these are not universal thresholds:

1. `1 Гаммот.png`
- source SHA256 `d0ed48cc8ca1e7053e9272948431f667f644e0a64bd48c3ecd4e47196de64277`
- 1024x1536
- bbox `(75,20,821,1498)` px
- largest raw/simplified contour `8253 -> 459` points
- simplification error mean/rms/max `0.39098 / 0.51320 / 1.59206` px
- structure NPZ SHA256 `3b0c0ec77eb8c73c275698b17a435f6ae29ed1eee18e356c875fd1af35386079`
- manifest SHA256 `566b2efac114143d4a54ce1ac3340d0f5f45c0d7989ab4694a6785d9db37bd64`

2. `f37607a7-fd21-4845-bd4e-62aaf72f76f1.png`
- source SHA256 `d8e226599ccf9cd1c672c09465d3ea19f928395ea397a6eff10c90083a4deafb`
- 1024x1536
- bbox `(0,9,855,1527)` px; contact with left border preserved rather than repaired/invented
- largest contour `9884 -> 520` points
- structure NPZ SHA256 `da53408dacdfa6ef3b8f65c5a4714edf4a3c8e128f06016b610af78d392b6d60`

3. `e28a871e-c77e-4f10-833d-d2ea85e20e61.png`
- source SHA256 `ad031c8ea5749b9c0ad5854c9b6d005210d4f03de75fce1de50872d4c0458edc`
- 1055x1491
- bbox `(195,31,650,1446)` px
- 315 external evidence components retained; R01 does not silently delete small visible components
- largest contour `7899 -> 508` points
- structure NPZ SHA256 `407a66dfe0c3d8e94864934255c856d0ce146a12ab09e6fbd1587c9b072974cb`

Layer status on all three runs:
`L0 PASS, L1 PASS, L2 PASS, L3 PASS, L4 PARTIAL, L5 PARTIAL, L6 PARTIAL, L7 UNKNOWN, L8 PARTIAL, L9 PARTIAL, L10 PASS`.

The PARTIAL/UNKNOWN states are intentional fail-closed behavior. R01 does not infer semantic anatomy or occlusion ordering from insufficient evidence.

Current claim: `REFERENCE_STRUCTURE_STATE_EXECUTED / PARTIAL`, not full engine PASS.
Renderer remains `NOT_STARTED`.
