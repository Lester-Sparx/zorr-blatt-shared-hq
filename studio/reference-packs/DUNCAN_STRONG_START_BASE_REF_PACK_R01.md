# DUNCAN_STRONG_START_BASE_REF_PACK_R01

STATUS = CURRENT DUNCAN START REFERENCE PACK / BYTE-VERIFIED
ROLE = fast visual source for fresh-session production work
CANON = NOT PROMOTED BY THIS RECORD

## EXACT PACK

- file: `DUNCAN_STRONG_START_BASE_REF_PACK_R01.zip`
- bytes: `13502752`
- SHA-256: `3f770d9aabccc53f9cfd2987ade452b8c937b691808783bec95d18f72fb25da9`
- files in ZIP: `19`

## DURABLE RETRIEVAL

Google Drive file ID: `1K8mOumWH44T1T1FFUwSZjJI-LJMr_TdL`

Google Drive URL: `https://drive.google.com/file/d/1K8mOumWH44T1T1FFUwSZjJI-LJMr_TdL/view?usp=drivesdk`

Fresh retrieval was physically verified after upload:

`DRIVE FETCH -> 13,502,752 BYTES -> SHA-256 3f770d9aabccc53f9cfd2987ade452b8c937b691808783bec95d18f72fb25da9`

Any fresh DUNCAN/ZORR session needing this pack should use this exact file ID/URL and verify the SHA only when the pack bytes/locator changed or integrity is in doubt. Routine ref extraction from an unchanged verified pack does not require re-verifying the entire chain.

## EXACT REFERENCE MAP

The filenames inside the ZIP are functionally named correctly. Use the file function literally; do not promote a construction/head/detail sheet into a full-body dressed shot reference.

| File | Type | Coverage | Clothing | View / content | Correct use |
|---|---|---|---|---|---|
| `00_IDENTITY/DUNCAN_MASTER_FRONT_R01.png` | IDENTITY | FULL BODY | DRESSED | FRONT | primary full-body front identity anchor |
| `01_BODY_HEAD/DUNCAN_BODY_CONSTRUCTION_R01.png` | CONSTRUCTION | FULL BODY MULTI-VIEW | UNDRESSED / BODY CONSTRUCTION | FRONT + 3/4 + SIDE + REAR 3/4 + BACK | body proportions, silhouette and view geometry only; **not a dressed shot ref** |
| `01_BODY_HEAD/DUNCAN_HEAD_VOLUME_YAW_PITCH_R01.png` | HEAD CONSTRUCTION | HEAD / SHOULDERS | DRESSED COLLAR VISIBLE | yaw/profile + pitch coverage | head volume, face direction and head angles only; **not full-body** |
| `02_HANDS_HAIR_FACE/DUNCAN_FACE_ACTING_R01.png` | FACE ACTING | HEAD / SHOULDERS | DRESSED COLLAR VISIBLE | expression set | facial acting and expression continuity |
| `02_HANDS_HAIR_FACE/DUNCAN_HAIR_TOPOLOGY_R01.png` | HAIR | HEAD | PARTIAL COLLAR | multi-angle hair/head | hair silhouette/topology and head-angle continuity |
| `02_HANDS_HAIR_FACE/DUNCAN_HANDS_CANON_R03.png` | HANDS | HANDS / WRISTS / SMALL COSTUME CROPS | CUFF DETAILS VISIBLE | palm/back/profile/grip/detail | hand anatomy, cuff and wrist reference |
| `02_HANDS_HAIR_FACE/DUNCAN_HAND_EXPRESSION_R01.png` | HAND ACTING | HANDS + PARTIAL TORSO CROPS | DRESSED CROPS | gestures / interactions | expressive hand poses and hand-to-costume interaction |
| `03_COSTUME/DUNCAN_COSTUME_CONSTRUCTION_ACCESSORY_MAP_R01.png` | COSTUME CONSTRUCTION | FULL FRONT + DETAIL CROPS | DRESSED | front garment + lapel/cuff/waist/trouser/shoe details | costume construction/details; **does not provide dressed side/3/4 turnaround** |
| `04_POSE_CONTROL/DUNCAN_POSE_FRONT_R01.png` | CONTROL DIAGRAM | FULL BODY ABSTRACT | N/A | FRONT | pose skeleton/control only; **not drawing reference** |
| `04_POSE_CONTROL/DUNCAN_BODY_MASK_FRONT_R01.png` | CONTROL MASK | FULL BODY ABSTRACT | N/A | FRONT | body-mask control only |
| `04_POSE_CONTROL/DUNCAN_GARMENT_MASS_FRONT_R01.png` | CONTROL MASK | GARMENT MASS ABSTRACT | N/A | FRONT | garment-mass control only |
| `04_POSE_CONTROL/DUNCAN_COLOR_BLOCK_FRONT_R01.png` | CONTROL BLOCK | FULL BODY ABSTRACT | COLOR/GARMENT BLOCKS | FRONT | coarse color/garment segmentation control |
| `04_POSE_CONTROL/DUNCAN_FRONT_CONTROL_PREVIEW_R01.png` | CONTROL PREVIEW | FRONT CONTROL SET | MIXED | FRONT | preview of control layers only |
| `05_COSTUME_MECHANICS/DUNCAN_COSTUME_MECHANICS_CONTROL_R01.png` | MECHANICS DIAGRAM | ABSTRACT BODY/GARMENT STATES | N/A | W01-W06 diagrams | mechanics planning; **not visual character reference** |
| `05_COSTUME_MECHANICS/DUNCAN_W01_ARM_RAISE_WORKING_PROD_BASE_R01.png` | WORKING PROD BASE | FULL BODY | DRESSED | FRONT / ARM RAISED | approved working visual base for this exact front arm-raise state |
| `06_STYLE/DUNCAN_DRAWING_STYLE_ANCHOR_R01.png` | STYLE ANCHOR | FULL BODY FRONT + FACE/HAND CROPS | DRESSED | style/line/value examples | drawing/line/value/style consistency |
| `99_META/DUNCAN_REF_PACK_INVENTORY_R01.md` | META | N/A | N/A | inventory/status | pack inventory only |
| `99_META/MANIFEST.json` | META | N/A | N/A | hashes/status | exact asset hashes/bytes/status only |
| `INDEX.md` | META | N/A | N/A | pack overview | pack overview only |

## SHOT-REFERENCE MATCH LAW

Before returning or using a visual reference for a shot, match the request on all required fields:

`CHARACTER + COVERAGE + CLOTHING + VIEW + PURPOSE`

Examples:

- `DUNCAN + FULL BODY + DRESSED + FRONT + IDENTITY` -> `DUNCAN_MASTER_FRONT_R01.png`
- `DUNCAN + FULL BODY + UNDRESSED/CONSTRUCTION + SIDE + GEOMETRY` -> side figure inside `DUNCAN_BODY_CONSTRUCTION_R01.png`
- `DUNCAN + HEAD + DRESSED + 3/4 + HEAD VOLUME` -> 3/4 head inside `DUNCAN_HEAD_VOLUME_YAW_PITCH_R01.png`
- `DUNCAN + FULL BODY + DRESSED + SIDE + SHOT REF` -> **NOT PRESENT AS A READY EXACT SHEET IN R01**
- `DUNCAN + FULL BODY + DRESSED + 3/4 + SHOT REF` -> **NOT PRESENT AS A READY EXACT SHEET IN R01**

Never substitute:

`HEAD 3/4 != FULL-BODY 3/4`

`UNDRESSED BODY-CONSTRUCTION SIDE != DRESSED SIDE SHOT REF`

`COSTUME FRONT DETAIL MAP != DRESSED SIDE/3/4 TURNAROUND`

If no exact match exists, state the missing reference explicitly instead of returning a different sheet as if it satisfied the request.

## CURRENT ROOFTOP SHOT CONSEQUENCE

For the current rooftop staging, the pack supplies authoritative ingredients for Duncan identity, body geometry, head angles, costume construction, hands and style, but R01 does **not** contain a ready exact `FULL-BODY + DRESSED + SIDE` or `FULL-BODY + DRESSED + 3/4` shot reference.

Therefore `DUNCAN_BODY_CONSTRUCTION_R01.png` may be used to construct the side/3/4 body geometry, but it must never be shown or treated as the final dressed rooftop character reference.

## INTERNAL ZIP METADATA NOTE

The exact R01 bytes remain unchanged. Its internal `INDEX.md` / `MANIFEST.json` still contain legacy statements such as `PROTOTYPE CHARACTER 01` and `NONE TO ZORR BLATT`. Those are internal historical metadata of this frozen byte pack and must not override fresher current GitHub project authority or the current ZORR production context.

Do not silently edit the ZIP because that would create new bytes and a new SHA/version. If internal pack metadata itself must be corrected, create a separately versioned pack and verify it as new bytes.

## STORAGE NOTE

The current ChatGPT GitHub connector can write repository text state but does not expose binary GitHub Release-asset upload. Therefore this record is the GitHub durable entry point while the exact ZIP bytes are stored in the verified Drive location above. A GitHub binary mirror remains a separate physical upload boundary; do not claim that mirror exists until its exact Release asset is present and hash-verified.
