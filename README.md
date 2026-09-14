# EADM Website

Quarto rebuild of the [EADM](https://eadm.eu) (European Association for
Decision Making) website, migrated from its WordPress export.

## Rendering locally

```bash
quarto render
quarto preview
```

## Changing the design

The look of the site is deliberately kept swappable:

- **Colors and fonts** — edit `_brand.yml`. Change the hex values in
  `color.palette`, or swap the Google Font names under `typography`.
- **Base theme** — edit the `theme:` key in `_quarto.yml`. It's a
  light/dark pair of built-in Quarto/Bootswatch themes (currently
  `zephyr` / `darkly`); swap either name for any other Bootswatch theme
  Quarto ships (`cosmo`, `flatly`, `litera`, `lux`, ...).
- **Anything else** — small custom CSS rules live in `styles.scss`,
  layered on top of the theme and brand.

## Content provenance

Content was migrated from a WordPress export (All-in-One WP Migration
bundle) using the one-time scripts in `tools/`. See
`docs/superpowers/specs/2026-09-14-eadm-website-migration-design.md` for
the migration design, and `CONTENT_AUDIT.md` for exactly what was dropped
or merged during migration and why. The `tools/` scripts are kept for
provenance but are not part of the served site and won't run again
without the original WordPress export and its scratch database import.
