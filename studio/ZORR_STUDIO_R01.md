# ZORR STUDIO R01

Branch: `duncan/zorr-studio-r01`

## Purpose

This branch is the durable production branch for developing ZORR as a 2D anime studio system.

The final product is drawn 2D anime. Tools exist to serve that result, not to become the product.

## Production hierarchy

DUNCAN PRIME
-> MATH / QC ENGINE
-> DESIGN ENGINE + DRAW ENGINE + SCENE ENGINE
-> KEY DRAWING
-> OPENTOONZ PRIMARY
-> Plastic / Skeleton / Xsheet
-> primary acting
-> secondary motion
-> 2.5D camera / parallax / FX
-> render
-> measured QC

Babylon is optional 3D spatial previz only when a shot proves a real need for geometry, perspective, contact, weapon trajectory, occlusion, architecture, or a difficult camera move.

## Three iron laws

1. GEOMETRY FIRST.
2. MOTION SECOND.
3. STYLE THIRD.

The final authority is the measured rendered output.

## Production laws

- KEY DRAWING FIRST for major pose or identity change.
- Character identity must survive repeated reuse across shots.
- A character design is defective if it cannot be decomposed into logical animatable masses.
- Math/QC controls motion; it does not replace drawing or acting.
- No new framework, bridge, daemon, custom rigging engine, scene editor, or deformation engine before a real blocker is proven.
- Do not force one drawing through deformation beyond its valid range. Add a new key drawing.
- Do not continue broad tool research after a sufficient OSS solution is proven.
- Do not delete Babylon work; preserve it as spatial mathematics and previz evidence.

## First production gate

`OPENTOONZ CHARACTER LIFE SMOKE R01`

- 48 frames
- 1920x1080
- 24 fps
- 1 real ZORR character
- 1 background
- 1 camera
- torso motion
- head motion
- 1 secondary element
- 1 parallax move

Required evidence:

- Identity: face and silhouette remain the same character.
- Rig: deformation does not visibly break the model.
- Acting: breathing/head motion does not read as simple PNG scaling.
- Secondary: hair/cloth/accessory lag adds life.
- Camera: depth and parallax read clearly.
- Render: clean 48-frame output exists.

If OpenToonz Plastic reaches a proven physical limitation, only then evaluate the next mature OSS mechanism.

## Scope discipline

This branch develops the studio, not Babylon infrastructure for its own sake.

Every new task must answer at least one of these questions:

- Does this improve character repeatability?
- Does this improve drawing quality or key-pose production?
- Does this improve acting or secondary motion?
- Does this improve scene readability or camera/parallax?
- Does this improve measurable QC of rendered 2D output?

If none apply, it does not belong in this branch.
