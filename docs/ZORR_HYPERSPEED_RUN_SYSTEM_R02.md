# ZORR HYPERSPEED RUN SYSTEM R02

Status: PROVISIONAL PRODUCTION SYSTEM
Scope: animation / motion / camera / BG / FX / compositing
Lore status: NON-LORE

## Core production law

Hyper-speed is not a blur filter. It is a coordinated cut built from independent but synchronized timing systems.

`LAYOUT -> MOTION VECTOR -> GENGA -> EXPOSURE/TIMESHEET -> CAMERA -> BG DEPTH -> SPEED BG -> SECONDARY MOTION -> CONTACT -> COMPOSITE`

The compositor may amplify speed, but must not invent speed that is absent from the poses, spacing, camera design, or layout.

## Source-backed production facts

- In Japanese animation, the key animator is responsible for layout and key poses; layout determines the relationship between camera work, subjects, and background structure over the cut.
- The timesheet is a frame-by-frame technical blueprint containing action/cel exposure, camera instructions, and FX/compositing notes.
- PAN is a formal camera instruction. QPAN is a very short high-speed pan; its visuals are commonly simplified and may use streaked BG, speed lines, or minimal detail. Nagare PAN is a rapid pan associated with streamlines.
- Multi-plane differences may be used to create parallax so camera motion does not read as a flat zoom.
- Genga are pose-to-pose key drawings; douga clean them and add in-betweens.

Primary study sources:
- E-SAKUGA — About Sakuga
- Anime GO — Timesheet
- Anime GO — PAN
- Anime GO — QPAN
- Anime GO — T.U/T.B
- OpenToonz documentation — Xsheet / Timeline / FX Schematic

Studio conventions vary. ZORR rules below are production rules derived from those mechanisms, not claims of universal anime practice.

---

# H01 — RUN MECHANICS

## Goal

The body must already read as fast before any FX is added.

Base phase chain:

`CONTACT -> COMPRESSION -> PUSH -> FLIGHT -> CONTACT`

For hyper-speed, do not distribute time evenly. Compress nonessential transition drawings and allocate clarity to the poses that define force and trajectory.

## ZORR pose requirements

- torso has an explicit forward vector;
- pelvis and shoulders do not become a rigid plank;
- front and rear arm produce a readable counter-swing;
- one leg clearly owns support or departure;
- the other leg clearly owns recovery or flight;
- head remains readable enough to preserve identity and intent;
- silhouette must remain legible at thumbnail scale.

### Emotion through run construction

RUN is acting.

- CONTROLLED PURSUIT: stable head, low wasted vertical motion, precise arm path.
- RAGE CHARGE: more shoulder compression, harsher hand shapes, violent spacing, rougher cloth response.
- FEAR ESCAPE: center of mass retreats from threat even while velocity goes forward; hands open more; head checks space.
- DESPERATE RESCUE: chest and reaching arm lead the silhouette; balance may look close to failure.
- DOMINANT HUNT: long efficient stride, quiet face, minimal flailing.

`SPEED != EMOTION`

Every run needs a psychological vector as well as a spatial vector.

---

# H02 — AUTHORED SMEAR TAXONOMY

Blur is optical processing. Smear is a drawing decision.

ZORR provisional smear families:

1. **LIMB STRETCH SMEAR** — hand/foot/forearm/shin elongated through the travel vector.
2. **WEDGE SMEAR** — anatomy temporarily becomes a tapered graphic mass.
3. **MULTIPLE-IMAGE SMEAR** — two or more discrete positions inside one authored drawing.
4. **CONTOUR-LOSS SMEAR** — selected internal anatomy disappears; only motion envelope remains.
5. **CLOTH SMEAR** — coat tail, sleeve, tie, belt end or fabric fold becomes an elongated ribbon shape.
6. **CONTACT SMEAR** — foot or hand deforms specifically around ground/contact impulse.

Rules:
- do not smear every body part at once;
- smear only along a proven motion arc;
- preserve at least one identity anchor in the frame;
- exit the smear into a clean readable pose;
- use fewer lines inside the fastest form.

`CLEAN KEY -> SMEAR -> CLEAN KEY`

is stronger than continuous generalized blur.

---

# H03 — FOLLOW / TSUKE PAN TIMING

The simplest high-speed illusion is to reduce screen-space translation of the character while moving the world relative to them.

Conceptual structure:

`CHARACTER screen position ~= stable`
`BG velocity = opposite run direction`

The character may drift slightly. Perfect lock can feel mechanical.

## Timing separation

Character cycle and camera movement must be authored separately.

Example:
- character acceleration begins frame 5;
- camera catch-up begins frame 7;
- camera reaches tracking speed frame 10;
- character drifts forward 4-8% of frame width during acceleration;
- after lock, BG carries most apparent velocity.

A follow-pan should never erase foot mechanics. Contact still needs a readable surface relationship even if the background is moving rapidly.

---

# H04 — QPAN / NAGARE BG

Use QPAN as punctuation, not as the entire run.

Source-backed note: QPAN is commonly very short, often under 12 frames, and may use simplified/streaked backgrounds. Nagare PAN is a rapid streamline-based variation.

## ZORR transition logic

`REAL BG -> DETAIL REDUCTION -> NAGARE / SPEED BG -> REAL BG`

The speed BG may be a separate designed asset. It does not need to be the original background blurred.

Use it when:
- acceleration exceeds readable environmental detail;
- a direction change needs graphic punctuation;
- the viewer must feel a short burst rather than sustained travel;
- a cut needs a clean transition between spatially readable states.

Do not use it when scene geography is still essential.

---

# H05 — DEPTH / PARALLAX SYSTEM

Apparent speed grows when layers move at different rates.

Recommended cut stack:

`FG OCCLUDERS` — fastest
`NEAR BG` — very fast
`MID BG` — medium
`FAR BG` — slow
`SKY / DISTANT MASS` — near static

This is a production representation, not a fixed physical ratio.

## ZORR parallax law

Foreground should periodically cross the frame to prove speed and depth, but should not constantly block the character.

Useful soft pressure operators:
- wall edge briefly occludes shoulder;
- pillar crosses frame in 1-3 frames;
- floor reflection moves at a different rate from distant wall;
- distant light barely shifts while near architecture streaks.

Avoid uniform scrolling of every layer; it collapses the shot into flat motion graphics.

---

# H06 — CLOTH / HAIR SECONDARY MOTION

The body is the driver. Clothing and hair are delayed systems.

Provisional ZORR model:

`BODY IMPULSE -> garment lag -> overshoot -> recovery`

Different parts have different response times:

- lapel: short lag;
- shirt hem: medium lag;
- jacket tail: longer lag;
- long coat/scarf: longest lag;
- short rigid hair: low amplitude, short lag;
- long hair: higher amplitude, phase-separated locks.

Rules:
- do not align every cloth edge with body velocity;
- acceleration should pull fabric backward;
- sudden direction changes produce overshoot;
- cloth may continue moving after torso has stabilized;
- folds at hyper-speed should simplify into large directional masses.

For adult fashion anime, cloth motion must preserve garment design. Do not turn tailoring into generic flutter noise.

---

# H07 — CONTACT / GROUND RESPONSE

A run feels weightless if the ground never reacts.

Contact hierarchy:

`APPROACH -> TOUCH -> LOAD -> RELEASE -> RESIDUAL`

Possible residuals:
- floor reflection shear;
- dust only if material supports it;
- tiny debris;
- water spray;
- light streak from reflective floor;
- short impact shadow;
- brief sole smear.

The residual effect must inherit the direction of force.

Do not spawn radial particles around every step.

For supernatural characters, perceived mass and actual world response may differ by creature physics. Define that relationship per character rather than assuming human/Earth behavior.

---

# H08 — PHASE RELATIONSHIPS: CHARACTER / CAMERA / BG / FX

Treat the cut as four timing engines:

1. CHARACTER
2. CAMERA
3. BACKGROUND
4. FX

They share events but not identical curves.

Example phase design:

- frame 1-4: character initiates; camera static;
- frame 5-8: character accelerates; camera begins catch-up;
- frame 9-14: camera nearly locks; near BG velocity increases;
- frame 11: first authored smear;
- frame 13-16: cloth reaches maximum lag;
- frame 15-19: QPAN/Nagare burst;
- frame 18: contact FX peaks;
- frame 20-22: character returns to clean pose while residual BG/cloth still decays;
- frame 23-24: short hold or exit.

This phase separation is what makes the shot feel designed rather than globally sped up.

---

# H09 — COMPOSITING ARCHITECTURE

Suggested stack:

`FAR BG`
`MID BG`
`NEAR BG`
`SPEED/NAGARE BG` (conditional)
`CHARACTER MAIN`
`CHARACTER SMEAR / ECHO` (conditional)
`CONTACT FX`
`FG OCCLUDERS`
`SELECTIVE LIGHT`
`FINAL COLOR / VALUE CONTROL`
`CAMERA OUTPUT`

OpenToonz-style Xsheet/Timeline and FX schematic are suitable conceptual models: columns/layers hold scene elements and FX nodes modify the scene through explicit connections.

## Prohibitions

- no global motion blur as the primary speed device;
- no permanent afterimage stack;
- no constant camera shake;
- no full-body neon outline;
- no equal-speed background layers;
- no particle soup;
- no detail-heavy anatomy inside the fastest smear;
- no compositing fix for weak key poses.

---

# H10 — GOLDEN TEST

## Target

Create one 24-frame / 1-second test at 24 fps that proves the entire system.

This is a test cut, not a final universal timing prescription.

### Suggested 24-frame plan

| Frames | Character | Camera | BG | FX |
|---|---|---|---|---|
| 01-03 | readable pre-run/load | static | readable | none |
| 04-05 | compression | static | readable | none |
| 06 | push key | begins | readable | contact hint |
| 07 | smear A | accelerate | near BG picks up | directional smear |
| 08-10 | clean run phase | catch-up | parallax increases | none/light residual |
| 11 | strong contact | near lock | fast near BG | contact response |
| 12 | smear B | locked | fast | authored limb/cloth smear |
| 13-15 | flight/recovery | locked | detail reducing | cloth maximum lag |
| 16-19 | hyper burst | QPAN/Nagare | streamline BG | optional discrete echo |
| 20 | clean destination pose | decelerate | BG detail returns | residual only |
| 21-22 | recoil/recovery | settle | readable | cloth overshoot |
| 23-24 | short hold/exit | settle | readable | none |

## Golden-test PASS criteria

PASS only if:

- speed reads with FX disabled;
- pose silhouette is readable on key frames;
- at least one smear is authored geometry rather than blur;
- camera timing and character timing are separately controllable;
- depth remains understandable before and after the burst;
- foreground, midground and far BG do not share identical velocity;
- cloth/hair lag behind the driver body;
- ground contact communicates force;
- identity remains readable during at least the key poses;
- color/light remain secondary to motion construction;
- the cut has a readable emotional intent.

Verdict: `PASS / RETEST / FAIL`.

For RETEST, repair only the dominant motion subsystem first.

---

# ZORR MOTION LANGUAGE — FINAL WORKING RULES R02

1. **Layout owns spatial logic.**
2. **Genga owns force and readable motion.**
3. **Timesheet owns exposure, camera timing and interdepartmental synchronization.**
4. **Smear is authored geometry.**
5. **BG speed is designed by depth, not one global scroll.**
6. **QPAN/Nagare is punctuation.**
7. **Cloth and hair are delayed physical systems.**
8. **Contact proves weight.**
9. **Afterimages are optional temporal notation, not the default speed effect.**
10. **Compositing amplifies an existing motion design; it does not create one from nothing.**
11. **Each run is an emotional performance.**
12. **At hyper-speed, simplify information instead of adding noise.**

## Canonical shorthand for internal discussion

`POSE -> SPACING -> SMEAR -> CAMERA -> DEPTH -> LAG -> CONTACT -> COMPOSITE`

If this chain fails at an early stage, do not compensate by adding later-stage FX.
