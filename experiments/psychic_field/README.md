# ZORR PSYCHIC FIELD LAB

Status: PROVISIONAL PRODUCTION EXPERIMENT / NON-LORE

This lab converts the current optical references into controllable procedural fields instead of copying a single background pattern.

## Why code

The goal is repeatability. A field should have explicit parameters for focus, density, phase, strength, depth and accent. That allows the same visual law to be tested on a face, coat, corridor, weapon, smoke or moving shot without falling back to a canned image preset.

## Modes

- `checker_bulge`: checker grid deforms around a local volume. Useful for face planes, shoulders, spherical distortions and local psychic pressure.
- `vortex`: angular + logarithmic spiral field. Useful for obsession, gaze focus and temporal pressure.
- `stripe_warp`: a calm stripe system bends around a local attractor. Useful for face/body projection and motion deformation.
- `tunnel_checker`: inverse-radial checker field creates optical depth. Useful for interiors/exteriors that collapse toward a focal point.
- `color_islands`: monochrome warped field with only a few deliberate color territories. Useful for adult psychedelic fashion states without rainbow noise.

## Examples

```bash
python3 experiments/psychic_field/psychic_field_lab.py \
  --mode checker_bulge \
  --width 1080 --height 1920 \
  --focus-x 0.50 --focus-y 0.40 \
  --scale 22 --strength 1.55 \
  --output /tmp/zorr_checker_bulge.ppm

python3 experiments/psychic_field/psychic_field_lab.py \
  --mode vortex \
  --focus-x 0.52 --focus-y 0.34 \
  --scale 12 --strength 0.42 \
  --phase 0.15 \
  --color-accent \
  --output /tmp/zorr_vortex.ppm

python3 experiments/psychic_field/psychic_field_lab.py \
  --mode stripe_warp \
  --scale 26 --strength 1.8 \
  --focus-x 0.47 --focus-y 0.38 \
  --output /tmp/zorr_stripe_warp.ppm
```

Convert if needed:

```bash
ffmpeg -y -i /tmp/zorr_checker_bulge.ppm /tmp/zorr_checker_bulge.png
```

## Production integration

The procedural field is not the final image. It becomes one controlled input:

`FIELD -> MASK / PROJECTION -> CHARACTER OR SPACE -> LIGHT/COLOR RESPONSE -> COMPOSITE`

Recommended usage:

- Face: mask the field to selected planes; do not cover the whole face by default.
- Fashion: allow stripes/checkers to follow lapel, shoulder, sleeve or coat motion.
- Interior: align the field with floor/wall perspective or deliberately break that alignment for a psychic event.
- Motion: animate `focus`, `phase`, `strength` and `scale`; do not merely crossfade two patterns.
- FX: combine with one supporting event only, such as slit light or selective color.

## Anti-patterns

FAIL by default:

- unchanged character pasted over checkerboard wallpaper;
- full-frame optical pattern with no focal hierarchy;
- random RGB/chromatic-aberration layer on top of the field;
- equal visual intensity everywhere;
- pattern movement unrelated to character action, gaze or camera;
- using the same vortex/checker solution in every shot.

## Training mapping

`B01 LIGHT` -> use field as projected light/shadow only.

`B02 BLACK MASS` -> let black/white structure replace micro-detail.

`B03 COLOR PLANE` -> interrupt monochrome with 1-3 controlled color territories.

`B04 LINE SUBTRACTION` -> permit field/light to erase selected contour information.

`B05 TEMPORAL EYES` -> local phase displacement around eyes; never global motion blur.

`B06 INNER FRACTURE` -> two incompatible field directions or coordinate systems on one face.

`B07 PSYKODELIC FACE STATE` -> one primary optical field plus one supporting light/color event.

## Current rule

The desired result is not "optical art" by itself. The target is **adult psykodelic fashion anime in which the optical field behaves like an authored psychological force** while identity, silhouette and fashion control remain readable.
