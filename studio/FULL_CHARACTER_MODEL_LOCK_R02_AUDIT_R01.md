# FULL_CHARACTER_MODEL_LOCK_R02 — AUDIT R01

STATUS = FRESH CROSS-SHEET AUDIT
TRACKER = #245
BRANCH = `duncan/zorr-studio-r01`
AUDIT_SCOPE = existing accepted character references only
IMAGE_GENERATION = NO
IMAGE_EDITING = NO

## FRESH PHYSICAL PACK EVIDENCE

Materialized artifact:

`ZORR_CHARACTER_PRO_PACK_R01.zip`

- size = `9,819,822 bytes`
- SHA256 = `a83b7de56d260908837f31153edfd85322cec566e3a0c37ad205db391ddf05e5`
- `unzip -t` = PASS / no compressed-data errors
- included PNG count = `6/6`
- all included PNG dimensions = `1448x1086`
- all six actual PNG SHA256 values match `MANIFEST.json` exactly

Verified included assets:

| Asset | SHA256 | Fresh state |
|---|---|---|
| `HEAD_PITCH_VOLUME_R01.png` | `87b5ae98573241fc82d34f976973d56009b43a9b3f449ac26a9e1d7f057456c4` | verified |
| `BODY_CONSTRUCTION_R01.png` | `08b86bc13a1fb001a9251717ccee3867c9b6573b44cfe7a96bba8fbaf26bb018` | verified |
| `HAIR_TOPOLOGY_R01.png` | `781f708467c5fc4545f709fc70fb5efaf7ba813db7c48aab7f4011bf1e5bd4b7` | verified |
| `HANDS_CANON_R03.png` | `608ecfb9ec482a3a5605044c6b7b64681e90df735281c6741aecbf20e4f3c1ff` | verified |
| `HAND_EXPRESSION_R01.png` | `6ea891870a2c5db8597b411af5885ff4be89a85c851a2154fca95b87323b11c5` | verified |
| `FACE_ACTING_R01.png` | `d900f52d150b59bfaeb49191364e71bf429e3a051ca9dabba2fb8f0aa3aecb33` | verified |

Supplementary accepted/source references inspected for cross-checking existing facts rather than inventing new sheets:

- suit five-view turnaround: Library `file_0000000004f882469dfa7a8b272ac5c4`
- head yaw/turnaround: Library `file_000000008e9082109ebd2941c6fb0fdc`
- costume/accessory sheet: Library `file_0000000037b4821082deb5afcb57227e`

These supplementary references are not new generated assets and do not replace the six-pack baseline.

---

# CROSS-SHEET MATRIX

| Subsystem | Classification | Fresh finding |
|---|---|---|
| HEAD / FACE IDENTITY | `LOCKED_CANDIDATE` | Same mature narrow-eye face, brow mass, long nose wedge, jaw/chin, scar side/trajectory, ear position family and neck identity survive pitch, yaw, neutral and acting views. No second-face redesign found. |
| HAIR TOPOLOGY | `LOCKED_CANDIDATE` within current camera envelope | One black base mass, same front hairline family, swept crown direction, side/rear mass and major cluster logic survive front/3Q/profile/rear/down views. |
| BODY RATIOS | `LOCKED_CANDIDATE` | Nude construction and suited turnaround preserve the same strong shoulder block, narrow waist, long-leg adult proportion and head/body relationship. Suit changes silhouette, not underlying model identity. |
| HAND MODEL | `LOCKED_CANDIDATE` | Canon and acting sheets preserve long adult fingers, palm proportions, thumb root, wrist thickness and cuff/watch relationship. Foreground enlargement reads as perspective rather than a different hand design. |
| IDENTITY MARKERS / ASYMMETRY | `LOCKED_CANDIDATE` | Vertical facial scar, earrings, front hair asymmetry, chain/watch/button family and black/ivory hierarchy remain consistent across inspected sheets. |
| COSTUME ATTACHMENT POINTS | `LOCKED_CANDIDATE` | Existing turnaround + accessory reference establish shoulder seam, collar/lapel root, cuff, waist/belt, jacket hem, trouser waist/knee/ankle and watch/button locations. Full fold/deformation mechanics are intentionally downstream. |
| COMMON SCALE REFERENCE | `LOCKED_CANDIDATE` | Use neutral standing model/head unit from accepted body/turnaround base. Existing source-grounded visual-language envelope remains approximately `7.93–8.14 heads` with `shoulder/head ≈ 2.54–2.58`. Hand scale is governed by `HANDS_CANON_R03` in neutral views; exact numeric hand/head ratio is not invented. |

## HARD CONFLICT SEARCH

Fresh visual cross-check found:

`HEAD_FACE_CONFLICT = NO HARD CONFLICT FOUND`
`HAIR_CONFLICT = NO HARD CONFLICT FOUND`
`BODY_CONFLICT = NO HARD CONFLICT FOUND`
`HAND_CONFLICT = NO HARD CONFLICT FOUND`
`MARKER_CONFLICT = NO HARD CONFLICT FOUND`
`COSTUME_ATTACHMENT_CONFLICT = NO HARD CONFLICT FOUND`

This does **not** mean every drawing is pixel-identical. It means no observed variation changes the identity/model enough to require reopening a subsystem from zero.

---

# ALLOWED OPEN ITEMS

These remain explicit and **do not block current model consistency**:

1. `TOP/CROWN EXTREME HIGH CAMERA` — OPEN only if a real shot proves the existing crown/rear evidence insufficient.
2. `COSTUME_DEFORMATION / FOLD MECHANICS` — OPEN by design; this is the next dedicated gate.
3. `COLOR / SHADOW / LINE FINAL CHARACTER LOCK` — OPEN downstream; previous rejected render experiments remain excluded.
4. `SEPARATED OPENTOONZ SOURCE` — OPEN downstream; current pack is flattened reference truth, not rig/source-layer truth.
5. `FEET / SHOE ACTION MECHANICS` — normal turnaround/accessory evidence exists; a special action sheet is only legal if a shot proves a gap.

None of these requires reopening generic BODY / HAIR / HANDS construction.

---

# MODEL AUTHORITY AFTER AUDIT

The current authority split is:

- `HEAD_PITCH_VOLUME_R01` = head pitch/volume authority
- accepted head-yaw source = yaw/profile identity support
- `HAIR_TOPOLOGY_R01` = hair mass/topology authority
- `BODY_CONSTRUCTION_R01` = body-under-costume authority
- accepted suit turnaround = standing costume silhouette/attachment support
- `HANDS_CANON_R03` = neutral hand model authority
- `HAND_EXPRESSION_R01` = acting/foreground hand authority bounded by canon hand model
- `FACE_ACTING_R01` = expression range authority bounded by head identity
- accepted costume/accessory source = hardware / watch / shoe / belt / lapel facts

If a future drawing conflicts with these references, fix the conflicting subsystem; do not average the conflict into a new design.

---

# GATE VERDICT

Fresh evidence supports:

`SHEET_1 ... SHEET_6 -> ONE CHARACTER MODEL = PASS`

`FULL_CHARACTER_MODEL_LOCK_R02 = PASS`

Meaning of this PASS is intentionally narrow:

- character model consistency is sufficiently proven to stop rebuilding the character foundation;
- BODY / HAIR / HANDS generic research remains frozen;
- this is **not** a final all-production canon lock;
- this is **not** rig/source-layer readiness;
- this is **not** S001 shot readiness;
- this is **not** final color/shadow/material approval.

## NEXT LEGAL GATE

`COSTUME_MECHANICS_R01`

Purpose:
prove deformation/fold behavior of the already-locked character costume at actual force points without redesigning the costume.

After that:

`POSE_MECHANICS_VISUAL_R01 -> CAMERA_LAYOUT_VISUAL_R01 -> approved LINE/COLOR/SHADOW/MATERIAL -> GOLDEN KEYFRAME -> separated OPENTOONZ SOURCE -> S001 PHYSICAL BASE -> OPENTOONZ CUT`
