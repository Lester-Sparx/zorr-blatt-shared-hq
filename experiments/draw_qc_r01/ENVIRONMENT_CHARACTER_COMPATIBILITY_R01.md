# ENVIRONMENT_CHARACTER_COMPATIBILITY_R01

STATUS = PROVISIONAL / DURABLE RESEARCH RECORD
SCOPE = VISUAL LANGUAGE COMPATIBILITY ONLY
PRODUCTION_MUTATION = NO
CANON_MUTATION = NO
IMAGE_GENERATION = NO
CUSTOM_CODE = NO

## Source identity

Uploaded environment source:
- filename: `73894d11-37bb-462f-8fbb-8858d83b9baf.png`
- raster: `912x1648`
- SHA256 verified with native `sha256sum`: `313967e83237397b1035a3c254123d0c8570de1110585fc79e6df440cd9cb0ea`

This SHA256 exactly matches the durable binary anchor in issue #199:
- `UNIVERSAL_TEXTURE_STYLE_ANCHOR.png`
- SHA256 `313967e83237397b1035a3c254123d0c8570de1110585fc79e6df440cd9cb0ea`

Character comparison source:
- Duncan C00-C MASTER FRONT SHA256 `57fbec5d9c136a90c6ac262f8011665fa061dca427bf3fb2c3f110d1cb0a69ed`
- C00-A DETAIL/COSTUME/ACCESSORY SHA256 `94c185aea5755e569f8359fd29c6e0b8a1748e1613f2b59e7a3e280205dcbc8e`
- C00-B HEAD YAW SHA256 `7646fa2724fd4372eb9811635dbf71bb052151eaf2d4cdb999159124660a16d1`

## Durable law relationship

Issue #199 explicitly establishes two active anchors:
1. CHARACTER_DRAWING_STYLE_ANCHOR
2. UNIVERSAL_TEXTURE_STYLE_ANCHOR

Therefore the environment source is not a random background candidate; it is the current durable texture/surface anchor against which character rendering compatibility must be evaluated.

## Compatibility finding

### Strong matches

1. LARGE-MASS DISCIPLINE
   - Environment: broad stone slabs, large mountain silhouettes, large cloud masses.
   - Duncan: large ivory suit field, black shirt/hair masses, restrained accessory accents.
   - Shared rule: big shape and silhouette before small detail.

2. TEXTURE HIERARCHY
   - Environment: foreground stone carries meso seams/cracks but almost no uniform grain; distant mountains collapse into layered masses; sky/clouds are broad low-frequency shapes.
   - Duncan: skin/suit are calm fields; hair/black shirt are coherent masses; leather/metal use local highlight accents rather than universal grain.
   - Shared rule: `MACRO > MESO > MICRO`.

3. SHADOW / VALUE ORGANIZATION
   - Environment: large directional cast shadows and broad value groups.
   - Duncan: hard graphic face/neck shadows, limited fold wedges, large black/ivory separation.
   - Shared rule: semantic shadow masses before decorative shading.

4. DETAIL BUDGET
   - Environment remains calmer than the character-facing model sheets.
   - This is desirable production hierarchy rather than a defect: environment should support Tier-1 character silhouette and not compete with it.

5. COLOR ROLE
   - Environment uses muted stone gray/brown and atmospheric blue-gray with a warm sunset accent.
   - Duncan uses ivory/black with sparse gold/silver.
   - These palettes are compatible because the character can remain the higher-contrast local focal object while inheriting scene light color.

### Controlled mismatches / integration risks

1. LINE CONTRAST
   - Duncan model sheets use sharper, darker primary contour and denser facial line hierarchy.
   - Environment contour lines are softer and lower-contrast.
   - This is acceptable if intentionally hierarchical; it becomes a problem only if Duncan is pasted in without scene-light/color integration and reads as a separate asset layer.

2. ATMOSPHERIC SOFTNESS
   - Environment uses distance compression and softer mountain/cloud boundaries.
   - Duncan reference sheets are neutral white-background assets with no atmospheric integration.
   - Actual scene character rendering must inherit atmosphere/light while preserving identity and primary contour readability.

3. CAMERA / PERSPECTIVE
   - Environment is a strongly perspective-driven elevated view over a terrace.
   - Duncan MASTER FRONT is a neutral reference construction, not a shot-matched scene pose.
   - MASTER FRONT cannot be composited literally into this view; the character must be reconstructed in the environment camera while preserving the C00 geometry/identity laws.

4. HIGHLIGHT / LIGHT COLOR
   - Environment has a strong warm sunset source.
   - Duncan reference highlights are neutral model-sheet lighting.
   - Scene usage requires warm environmental influence on ivory/skin/gold while avoiding continuous glossy 3D shading forbidden by #199.

## Qualitative compatibility judgement

- structural visual-language compatibility: HIGH
- texture-frequency compatibility: HIGH
- value/shadow compatibility: HIGH
- palette compatibility: HIGH with scene-light adaptation
- line-language compatibility: MEDIUM-HIGH by intentional foreground/background hierarchy
- direct copy-paste compatibility of MASTER FRONT into this shot: LOW
- redraw/reconstruction compatibility under the same camera/light while preserving identity: HIGH

Overall conclusion:

`ENVIRONMENT + DUNCAN = COMPATIBLE BY DESIGN`

The environment should NOT be sharpened/detail-boosted until it looks like the character sheet. The profitable relationship is:

`CHARACTER = SHARPER / HIGHER LOCAL CONTRAST / TIER-1`

`ENVIRONMENT = CALMER / LOWER LOCAL CONTRAST / ATMOSPHERIC SUPPORT`

while both share:

`BIG SHAPE -> SILHOUETTE -> STRUCTURAL EDGES -> CONTROLLED VALUE BANDS -> SELECTIVE DETAIL -> STOP`

## Current risks to test later

- character contact shadow and ground integration
- sunset color transfer onto ivory suit and skin
- character contour contrast against dark mountain/cloud zones
- whether foreground stone line density competes with feet/lower-leg silhouette at intended shot scale
- perspective-correct character construction at this elevated camera

Any image generation/redraw test requires explicit OWNER command.

## Current state

`ENVIRONMENT_TEXTURE_ANCHOR_MATCH = PROVEN BY SHA256`

`ENVIRONMENT_CHARACTER_LANGUAGE_COMPATIBILITY = PROVISIONAL HIGH`

`DIRECT_MASTER_FRONT_COMPOSITE = NOT VALID`

`NEXT LEGAL ACTION = ANALYSIS/QC ON EXISTING ASSETS ONLY`
