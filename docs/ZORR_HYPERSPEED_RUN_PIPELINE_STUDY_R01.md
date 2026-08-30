# ZORR HYPERSPEED RUN PIPELINE STUDY R01

Status: PROVISIONAL PRODUCTION RESEARCH
Lore status: NON-LORE
Branch intent: motion-language research for ZORR BLATT

## Core thesis

A convincing anime hyperspeed run is not a single effect. It is a coordinated system of independent timing layers planned from layout onward.

`LAYOUT -> KEY POSES -> EXPOSURE/TIMING -> SMEARS -> CAMERA -> BG PARALLAX -> SPEED BG/NAGARE -> SECONDARY MOTION -> CONTACT FX -> COMPOSITING`

The compositor may intensify speed, but must not be required to invent speed that is absent from pose, spacing, or camera design.

## 1. Production order

### 1.1 Storyboard / ekonte
Defines dramatic intent, shot order, rough camera intent, and action beat.

### 1.2 Layout
The key animator establishes the full spatial contract of the cut: character placement, background framework, camera relation, motion direction, scale, start/end state, and the relationship between subject movement and camera movement.

This is the answer to "does the background come first?": not as finished art. The layout comes first as the common spatial blueprint. Character animation and background art then diverge into separate production branches from the same layout.

### 1.3 Genga / key animation
The key animator extracts the decisive poses and motion states. For high-speed motion, the spacing between important drawings may become extremely aggressive and may include authored smear drawings rather than uniformly interpolated poses.

### 1.4 Timesheet / X-sheet
Timing, exposure, cel columns, camera instructions, FX/compositing notes, and inbetween placement are coordinated here. A 24 fps timeline does not imply 24 unique character drawings per second.

### 1.5 Background / moving background branches
The background may remain a normal painted environment, split into depth layers for parallax, or transition into a simplified speed background / nagare field for the highest-speed interval.

### 1.6 Douga / cleanup / inbetween
Inbetweens preserve the timing logic. High-speed cuts must not be automatically "smoothed" until the decisive spacing, holds, and smears lose their character.

### 1.7 Color / paint
Character and FX colors remain subordinate to motion readability. High-speed states may simplify color information.

### 1.8 Photography / compositing
Character, moving BG layers, speed BG, foreground layers, smears/echoes, contact FX, selective light, camera transform, and color treatment are assembled into the final shot.

## 2. Layer architecture

A practical ZORR hyperspeed cut can be organized as:

```
FG-2  near-camera occluder / streak / debris
FG-1  contact dust / floor streak / light cut
C-3   optional temporal echo or authored residual shape
C-2   cloth / hair / accessory secondary-motion layer when separated
C-1   primary character drawing
B-3   speed-line / nagare background state
B-2   moving midground architecture
B-1   distant environment / horizon / skyline
CAM   camera timing and transforms
```

Layers do not need to exist separately in every cut. The principle is separation of responsibilities so each motion system can be timed deliberately.

## 3. Four independent timing engines

A hyperspeed shot should be treated as at least four synchronized but independent systems:

### CHARACTER TIMING
Controls run mechanics, torso compression, arm swing, stride, smear insertion, contact and flight poses.

### CAMERA TIMING
Controls follow pan, pan, quick pan, track, hold, snap, or combinations.

### BACKGROUND TIMING
Controls scroll speed, parallax ratios, foreground occlusion, background simplification, and transitions between normal BG and speed BG.

### FX TIMING
Controls smear visibility, contact streaks, dust, debris, light cuts, afterimages, and impact accents.

Failure mode: forcing all four systems to use the same speed curve. This often produces mechanically uniform motion.

## 4. Follow Pan / Tsuke Pan logic

For a normal crossing shot:

`CHARACTER -> moves through screen; BG approx stable`

For a follow-pan run:

`CHARACTER approx screen-locked; BG moves opposite the travel direction`

This creates the feeling that the camera is travelling with the runner.

ZORR rule: the body should still cycle, compress, push, and recover. Screen-locking the torso is not permission to freeze the character and move only the background.

## 5. QPAN / Nagare Pan logic

QPAN is a very short, forceful camera move. Because the move is rapid, image information is commonly simplified. Nagare Pan is associated with a rapid pan using streamlines / flowing background treatment.

Recommended use in ZORR:

`NORMAL BG -> acceleration -> detail collapse -> NAGARE/SPEED BG -> readable destination or impact -> NORMAL/NEW BG`

The speed background is allowed to be a separate designed drawing, not merely the finished background with a blur filter.

## 6. Parallax architecture

Convincing speed and depth come from relative layer velocities.

Example, not a locked numeric standard:

```
far BG       = slow
mid BG       = medium
near BG      = fast
foreground   = very fast
character    = camera-relative anchor or controlled drift
```

For track-in / track-back type depth moves, near layers change scale faster than distant layers. The same depth principle can reinforce a running shot even when the camera mainly follows horizontally.

ZORR target: speed should be measurable in differences between depth layers, not represented by one global blur amount.

## 7. Character run construction

Base locomotion states:

`CONTACT -> COMPRESSION -> PUSH -> FLIGHT -> CONTACT`

At hyperspeed, do not merely play this cycle faster. Modify spacing, exposure, silhouette, camera timing, and transitional drawings.

### Torso
Usually more stable than extremities so identity and action direction remain readable.

### Arms
Strong counter-swing and authored motion arcs. Hands may require simplified or smeared transitional geometry.

### Legs
May use the largest spatial jumps. Contact should feel brief and decisive; flight poses may become the clearest hero poses.

### Head
Must preserve gaze target and identity while allowing wind pressure, neck tension, and controlled drag.

## 8. Authored smear versus blur

A smear frame is a designed temporary drawing. It may stretch, duplicate, wedge, simplify, or partially omit anatomy in order to describe displacement across time.

`KEY A -> AUTHORED SMEAR -> KEY B`

It is not equivalent to applying a digital blur to a normal drawing.

ZORR smear requirements:

- follows a known motion arc;
- supports the next readable pose;
- preserves the action's dominant vector;
- may violate anatomy temporarily but must not destroy identity across the sequence;
- should be evaluated at playback speed, not only as a still.

## 9. Temporal echo / afterimage

A temporal echo is distinct from a smear. It shows discrete previous or alternate pose states.

Possible structure:

```
current pose = primary
previous pose = reduced value/opacity or alternate render state
older pose = weaker, optional
```

But ZORR should prefer authored discrete shapes over generic repeated opacity copies when the echo is narratively or emotionally important.

Use sparingly. Constant afterimages reduce their impact.

## 10. Secondary motion

Hyperspeed is damaged if clothing, hair, jewelry, coat tails, straps, or loose accessories all move exactly with the torso.

Core principle:

`PRIMARY BODY CHANGE -> DELAY -> SECONDARY FOLLOW -> OVERSHOOT -> RECOVERY`

For adult fashion characters this is essential because cloth motion carries both speed and character elegance.

### Suit / coat example

- torso commits first;
- lapels react shortly after;
- coat tail trails behind travel vector;
- loose edge overshoots during direction change;
- fabric tension increases at shoulder/elbow/hip anchors;
- not every fold is redrawn; large cloth masses remain readable.

## 11. Ground contact

The runner must exchange force with the environment unless the fiction explicitly removes contact.

Possible contact evidence:

- compressed sole shape;
- short floor streak;
- contact shadow displacement;
- reflection distortion;
- dust/debris only when surface supports it;
- one-frame impact accent;
- floor material response.

Failure mode: beautiful running pose floating above a speed background with no believable force transfer.

## 12. Motion hierarchy

For a strong ZORR run shot:

`POSE > SPACING > CAMERA > BG FLOW > SECONDARY MOTION > FX > BLUR`

Blur is last. It may soften a transition but cannot replace the designed motion hierarchy.

## 13. Suggested 24 fps drill

A compact test can be built over approximately 16-24 frames. Exact frame counts remain shot-dependent.

Example study:

```
F01-F03  readable pre-run or incoming pose / real BG
F04      compression
F05      push
F06      smear #1
F07-F08  readable run/flight pose; follow pan engages
F09      smear #2; BG detail begins to collapse
F10-F12  nagare/speed BG; near-FG streaks; cloth lag
F13      optional discrete pose echo
F14      strongest readable flight pose
F15      contact / vector change
F16      short hold or transition into next beat
```

This is a drill template, not a production standard.

## 14. ZORR hyperspeed visual law

The sensation of speed should come from coordinated differences:

`relative position + spacing + exposure + camera velocity + layer velocity + silhouette deformation + secondary-motion lag + contact response`

Not from:

`normal running pose + global directional blur`

## 15. Emotional body language during speed

A run must also communicate who is running and why.

### PREDATORY CHARGE
low forward head, clean gaze target, narrow silhouette, efficient arm drive.

### PANIC
less efficient axis, larger shoulder instability, hands less controlled, uneven stride, gaze searching instead of locking.

### RAGE
more forceful compression, stronger upper-body recruitment, harsher contact, less elegant recovery, possible render-state roughening.

### COLD EXECUTION
minimal wasted motion, stable head, clean stride arcs, reduced secondary noise, deliberate camera tracking.

### EXHAUSTION
collapsed torso, reduced flight phase, late recovery, heavier foot contact, facial and neck micro-tension.

ZORR law: emotion = whole moving image. Facial expression alone is insufficient.

## 16. Current critique of the recent ZORR hyper-run still

Strengths:

- strong forward lean;
- readable fashion silhouette;
- effective dominant travel vector;
- useful temporal echoes;
- speed-oriented background flow;
- clear foreground/background direction.

Weaknesses to target in animation tests:

- stronger authored limb smears;
- more differentiated cloth inertia;
- clearer ground-force exchange;
- stronger separation of far/mid/near background velocities;
- more specific exposure rhythm rather than a uniformly continuous sense of speed.

## 17. QC questions

A cut is not PASS unless most answers are YES:

1. Is the travel vector readable with the background hidden?
2. Is the run mechanically readable with FX hidden?
3. Does the camera have its own explicit timing plan?
4. Are near and far background layers moving differently?
5. Is every smear tied to a known motion arc?
6. Is cloth/hair delayed relative to the primary body?
7. Does ground contact communicate force?
8. Does the emotion read through body language at silhouette scale?
9. Does the shot remain legible when speed-line FX are removed?
10. Does the compositing intensify an already-working motion design instead of hiding a weak one?

## 18. Research terms to continue

- layout / レイアウト
- genga / 原画
- douga / 動画
- timesheet / タイムシート
- X-sheet / exposure sheet
- PAN / パン
- Tsuke PAN / follow pan
- QPAN / Quick Pan
- FLASH PAN
- NAGARE PAN / 流PAN
- TU/TB / Track Up / Track Back
- multiplane
- parallax
- smear frame
- temporal echo / afterimage
- speed background
- action compositing / 撮影
- effects animation
- cloth secondary motion

## 19. Sources studied for R01

- E-SAKUGA, "About SAKUGA" — layout, genga, timesheet responsibilities:
  https://www.esakuga.net/about-sakuga/
- Anime GO, PAN notation — pan timing, timesheet/timechart usage and variations:
  https://animego.erosakuga.com/notation/pan/
- Anime GO, QPAN notation — QPAN, FLASH/ROUGH/EXPRESS/SLIP/NAGARE PAN, simplified streaked BG and short timing:
  https://animego.erosakuga.com/notation/qpan/
- Anime GO, Timesheet — frame count, action/cel columns, camera and FX/compositing instructions:
  https://animego.erosakuga.com/benkyou/timesheet/
- Anime GO, T.U/T.B — layered parallax / relative scale behavior:
  https://animego.erosakuga.com/notation/t-u-t-b/
- OpenToonz Documentation — Xsheet/Timeline layers, cameras, object transforms, 3D stage/depth:
  https://opentoonz.readthedocs.io/en/latest/
- E-SAKUGA, Arifumi Imai Attack on Titan collection — storyboard/keyframes/X-sheet/final cut comparison as action-animation study material:
  https://www.esakuga.net/ebook/anime-attack-on-titan-arifumi-imai-e-sakuga/

## 20. Next research gates

`H01 RUN CYCLE MECHANICS`
`H02 SMEAR TAXONOMY`
`H03 FOLLOW PAN / TSUKE PAN TIMING`
`H04 NAGARE / SPEED BG CONSTRUCTION`
`H05 PARALLAX LAYER CONTRACT`
`H06 CLOTH + HAIR AT HYPERSPEED`
`H07 CONTACT / FLOOR RESPONSE`
`H08 CAMERA + CHARACTER PHASE RELATION`
`H09 COMPOSITING WITHOUT BLUR DEPENDENCE`
`H10 16-24 FRAME GOLDEN TEST`

Do not combine all gates at once. Extract one mechanism, test it, review it at playback speed, and preserve only proven rules.
