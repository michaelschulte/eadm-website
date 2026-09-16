# EADM Website

Quarto rebuild of the [EADM](https://eadm.eu) (European Association for
Decision Making) website, migrated from its WordPress export.

## Rendering locally

```bash
quarto render
quarto preview
```

## Deployment

Every push to `main` publishes the site to a preview on GitHub Pages:
**https://michaelschulte.github.io/eadm-website/** (eadm.eu itself still
serves the WordPress site). The workflow in
`.github/workflows/publish.yml` renders with Quarto and deploys a Pages
artifact; progress shows under the repository's **Actions** tab, where a
deploy can also be re-run by hand ("Run workflow").

CI renders with the `preview` profile (`_quarto-preview.yml`), which adds
a `noindex` tag to every page so the preview stays out of search results.
When the site moves to eadm.eu, drop `--profile preview` from the workflow
and set the custom domain in the repository's Pages settings.

## Changing the design

The design is built around the original EADM logo (the WordPress site's
header image): its red, near-black and gray set the colour scheme, and the
logo itself appears in the navbar, as the home-page heading and as the
favicon.

- **Logo artwork** — `images/brand/`. `eadm-logo.jpg` is the original
  header image, unchanged; `eadm-mark.png` (no tagline, for the navbar) and
  `favicon.png` are crops of it.
- **Colors and fonts** — edit `_brand.yml`. Colours have light and dark
  variants; fonts are Google Fonts (Inter for text, Outfit for headings).
- **Per-mode palette** — `styles-light.scss` / `styles-dark.scss` set the
  navbar, footer, card and border colours for each mode. Their hex values
  mirror `_brand.yml`, so change both together.
- **Layout and components** — `styles.scss` holds the shared rules: navbar,
  page titles, tables, listing cards, the home-page hero and card grid, and
  the footer.
- **Base theme** — the `theme:` key in `_quarto.yml` layers
  `cosmo` → `brand` → palette file → `styles.scss`. Keep `brand` in the
  list: without it the Bootswatch theme's colours and fonts override
  `_brand.yml`.

## Content provenance

Content was migrated from a WordPress export (All-in-One WP Migration
bundle) using the one-time scripts in `tools/`. See
`docs/superpowers/specs/2026-09-14-eadm-website-migration-design.md` for
the migration design, and `CONTENT_AUDIT.md` for exactly what was dropped
or merged during migration and why. The `tools/` scripts are kept for
provenance but are not part of the served site and won't run again
without the original WordPress export and its scratch database import.
