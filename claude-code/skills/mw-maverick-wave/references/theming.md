# Theming, tokens & partial imports

## The model

Thirteen colours are configured, everything else is derived from them **at
runtime** with `color-mix()` and relative colour syntax. Overriding a root token
therefore retunes its whole family - hover tone, translucent backgrounds,
borders, the theme's surface stack, the ink variant the dark theme needs. That is
the difference to pre-3.4.0, where derived values were baked in at compile time
and a palette switch meant setting 41 variables.

Browser floor for that: `color-mix()` **and** `oklch(from ...)` - Chrome 119+,
Safari 16.4+, Firefox 128+. The same range is declared as `browserslist` in
`package.json`, so Autoprefixer and cssnano target exactly it.

```css
/* loaded after maverick-wave.min.css */
:root {
  --mw-primary-color: #0f766e; /* also retunes hover, backgrounds, border accent */
  --mw-secondary-color: #f39c12;

  --mw-success-color: #157f4b;
  --mw-warning-color: #bda817;
  --mw-danger-color: #c42b1c;
  --mw-info-color: #14618f;

  --mw-gray-color: #5a6478;

  --mw-dark-page-background: #171f30;
  --mw-dark-text-color: #e8ecf1;
  --mw-light-page-background: #f2f5f8;
  --mw-light-text-color: #0c1119;

  --mw-form-elements-background: #f4f7fb;

  /* text on every solid coloured surface, and the one token that cannot be
     derived: light brand colours need a dark label, dark ones a light label */
  --mw-accent-text-color: #ffffff;
  /* per colour override of that label, for a palette that does not sit on one
     side of the lightness scale */
  --mw-primary-accent-text-color: #0b0f0a;

  --mw-font-family-base: 'Inter', sans-serif;
}
```

## Which token for what

| Token                                                                                                                                                                        | Role                                                                                                                                                                                                                                                                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--mw-primary-color`                                                                                                                                                         | Brand colour as a **fill**: primary buttons, table headers, bars, badges - the label on top is `--mw-primary-accent-text-color`                                                                                                                                                                                                         |
| `--mw-primary-text-color`                                                                                                                                                    | Brand colour as **ink** on a theme surface: text, icons, focus rings, accent borders. Derived by clamping OKLch lightness (`max(l, .68)` on dark, `min(l, .55)` on light), so a colour already in range is used untouched                                                                                                               |
| `--mw-primary-color-hover`                                                                                                                                                   | Solid hover surface (derived: base + `$hover-shift` black, in both themes)                                                                                                                                                                                                                                                              |
| `--mw-primary-background`                                                                                                                                                    | 20% tint - focus halo, alert/badge/tag surface, scrollbar tracks                                                                                                                                                                                                                                                                        |
| `--mw-primary-background-hover`                                                                                                                                              | 45% tint - row and list hover                                                                                                                                                                                                                                                                                                           |
| `--mw-primary-info-background`                                                                                                                                               | Alias of `--mw-primary-background`, so a component can interpolate one name across all six colours                                                                                                                                                                                                                                      |
| `--mw-border-accent`                                                                                                                                                         | Translucent accent **line**: panel rules, dividers, tab underlines. Theme-aware (70% of `--mw-*-text-color`)                                                                                                                                                                                                                            |
| `--mw-secondary-*`                                                                                                                                                           | Same set for the second brand colour                                                                                                                                                                                                                                                                                                    |
| `--mw-success/warning/danger/info-color`                                                                                                                                     | Status colours, each with `-text-color`, `-color-hover`, `-info-background`, `-info-background-hover`                                                                                                                                                                                                                                   |
| `--mw-accent-text-color`                                                                                                                                                     | Text on any solid coloured surface (buttons, table/panel headers, badges, stepper dots)                                                                                                                                                                                                                                                 |
| `--mw-primary-accent-text-color`                                                                                                                                             | Per colour override of that label. Same for `secondary`, `success`, `warning`, `danger`, `info`. Defaults to `--mw-accent-text-color`, so set one only when a colour needs the opposite label - a neon primary on a dark palette                                                                                                        |
| `--mw-gray-color`                                                                                                                                                            | Neutral foreground: muted icons, tooltips                                                                                                                                                                                                                                                                                               |
| `--mw-gray-background`                                                                                                                                                       | Subtle neutral surface (20% alpha): zebra rows, disabled fields, tracks, skeletons                                                                                                                                                                                                                                                      |
| `--mw-corner-accent`                                                                                                                                                         | The accent arc on the two round corners of every card, panel, modal and tile. Theme-aware: the full `--mw-*-text-color` tone in the dark theme, held to 80% in the light one, where the same blue carries far more contrast on a near-white card. Restyle it to recolour the signature, or `mw-corner-plain` on a single box to drop it |
| `--mw-surface-muted`                                                                                                                                                         | Alias of `--mw-gray-background` under the name you reach for: a slightly set-off area _inside_ a card - hint block, framed paragraph, form summary                                                                                                                                                                                      |
| `--mw-overlay-background`                                                                                                                                                    | Heavy scrim (60%) behind modals and blocking spinners                                                                                                                                                                                                                                                                                   |
| `--mw-page-background`, `--mw-card-background`, `--mw-footer-background`, `--mw-border`, `--mw-shadow`, `--mw-text-color`, `--mw-text-muted-color`, `--mw-hero-image-filter` | The **active theme** - aliases pointing at the `--mw-dark-*` or `--mw-light-*` set                                                                                                                                                                                                                                                      |
| `--mw-header-*`                                                                                                                                                              | Header chrome: `background`, `text-color`, `navbar-list-color`, `navbar-list-active-color`, `burgerbutton-color`, `burgerbutton-open-color`, `border` - dark in both themes. The two burger tokens default to the primary and secondary label ink, because the burger sits on those two surfaces                                        |
| `--mw-form-elements-background`, `--mw-form-elements-color`                                                                                                                  | Form controls stay light in both themes and therefore have their own pair                                                                                                                                                                                                                                                               |
| `--mw-font-family-base`, `-heading`, `-mono`                                                                                                                                 | Font stacks - system stacks by default (`-mono` leads with Fira Code); no font is bundled. Configurable in SCSS, see below                                                                                                                                                                                                              |
| `--mw-hero-background`, `--mw-hero-text-color`                                                                                                                               | Hero image (`url(...)`) and the ink on it. Fixed across themes - the photo does not change with the theme, so its text must not either. Defaults to the light end of the palette                                                                                                                                                        |
| `--mw-transition`                                                                                                                                                            | Hover and focus states - an explicit paint-only property list at `--mw-duration-base`, never `all`                                                                                                                                                                                                                                      |
| `--mw-card-img-height`                                                                                                                                                       | Per-card image height (default `210px`; `mw-card-lg`/`-xl` set it to 340px/480px, 260px/340px below `sm`)                                                                                                                                                                                                                               |
| `--mw-card-addon-color`                                                                                                                                                      | Background of `mw-card-badge` / `mw-card-ribbon`; the `mw-card-addon-*` classes set it, override it for a custom colour                                                                                                                                                                                                                 |
| `--mw-card-addon-text-color`                                                                                                                                                 | Label on that badge/ribbon; the `mw-card-addon-*` classes point it at the matching `--mw-*-accent-text-color`                                                                                                                                                                                                                           |
| `--mw-progress-ink`                                                                                                                                                          | Label inside `mw-progress-inline-label`; the `mw-progress-*` colour classes point it at the matching `--mw-*-accent-text-color`                                                                                                                                                                                                         |
| `--mw-table-scroll-height`                                                                                                                                                   | Per-table height cap for `mw-table-responsive-scroll`                                                                                                                                                                                                                                                                                   |
| `--mw-kanban-background`, `--mw-kanban-lane-border`, `--mw-kanban-column-min-height`                                                                                         | Per-board surface, lane border and lane floor (120px, 90px on `mw-kanban-compact`)                                                                                                                                                                                                                                                      |
| `--mw-container-gutter`, `--mw-container-width`                                                                                                                              | Page gutter of `mw-container` (fluid `clamp(1rem, 4.2vw + 0.5rem, 4rem)`, never below the safe-area inset) and the width derived from it (`min(1200px, 100% - 2 * gutter)`)                                                                                                                                                             |
| `--mw-section-padding-block`                                                                                                                                                 | Top/bottom rhythm of `mw-section` (3.3rem, stepping down to 2.5rem below `md` and 1.75rem below `sm`)                                                                                                                                                                                                                                   |
| `--mw-calendar-dot`                                                                                                                                                          | Colour of a single calendar dot - set it per dot or per cell; the `mw-calendar-dot-*` classes are presets for it                                                                                                                                                                                                                        |
| `--mw-scroll-hint-cover`                                                                                                                                                     | Colour the scroll hint on a tab bar fades into. Preset to the page, re-pointed to the card background inside `mw-card`, `mw-panel`, `mw-modal`, `mw-tile`, `mw-calendar`                                                                                                                                                                |
| `--mw-elevation-1` … `-5`                                                                                                                                                    | Every shadow in the framework. Two layers per level - contact plus ambient. Never write a `box-shadow` by hand: a hand-rolled one is the wrong colour in one of the two themes                                                                                                                                                          |
| `--mw-shadow-near`, `--mw-shadow-far`                                                                                                                                        | The two tones the ramp above is mixed from, per theme                                                                                                                                                                                                                                                                                   |
| `--mw-transition-fast`                                                                                                                                                       | The same property list at `--mw-duration-fast` - for a state change that should feel instant under the pointer                                                                                                                                                                                                                          |
| `--mw-duration-instant\|fast\|base\|slow\|slower`                                                                                                                            | 110 / 180 / 300 / 520 / 900ms. Anything built on these is covered by `prefers-reduced-motion` for free                                                                                                                                                                                                                                  |
| `--mw-duration-zoom`                                                                                                                                                         | 650ms, for a large surface actually travelling - an image scaling inside a card, a slider track                                                                                                                                                                                                                                         |
| `--mw-ease-out`, `--mw-ease-in-out`, `--mw-ease-spring`                                                                                                                      | Things arriving (the default) / A to B and back / a pop                                                                                                                                                                                                                                                                                 |
| `--mw-control-height-sm\|·\|lg`, `--mw-control-font-sm\|·\|lg`, `--mw-control-line-height`                                                                                   | One size scale for input, select, textarea and button, so a field and the button beside it line up by construction                                                                                                                                                                                                                      |
| `--mw-focus-ring-width\|offset\|color`                                                                                                                                       | The keyboard focus ring                                                                                                                                                                                                                                                                                                                 |
| `--mw-focus-halo-size\|opacity`                                                                                                                                              | The soft ring a form field gets instead of a hard outline                                                                                                                                                                                                                                                                               |
| `--mw-internal-theme-mode`                                                                                                                                                   | Read-only: what `$mw-theme-mode` was compiled to                                                                                                                                                                                                                                                                                        |

`--mw-container-gutter`, `--mw-container-width` and `--mw-section-padding-block`
are the knobs a good default cannot settle, because the right answer differs per
project: what reads as generous on a landing page costs visible content in an
application with a sticky header. Override the gutter, not the width - the width
is derived from it and keeps the 1200px cap.

Two rules that prevent most colour bugs:

1. **Fill or ink.** A colour that _fills_ something is `--mw-*-color`; a colour
   _drawn on_ a theme surface - text, icon, focus ring, accent border, thin
   divider - is `--mw-*-text-color`. A colour picked to carry a label is by
   definition unreadable on the page it sits on, so ink is always the
   `-text-color` variant. For a generic rule or outline use `--mw-border-accent`
   or `--mw-border`.
2. **`--mw-text-muted-color` is only for text on theme surfaces** (cards, page
   background) - it follows the theme. It is a true gray with `$muted-tint`
   (23%) of the primary mixed in, not a stepped-back text colour, so it stays
   gray no matter how tinted the palette is. On a colour surface that stays the same
   in both themes it is always wrong: use `--mw-*-accent-text-color`, or
   `opacity` for a disabled look.

3. **Elevation, motion and focus are tokens too.** `var(--mw-elevation-1..5)`
   for any shadow, `var(--mw-transition)` / `var(--mw-transition-fast)` for a
   hover or focus state, `var(--mw-duration-*)` with `var(--mw-ease-*)` for
   anything else, and `--mw-focus-ring-*` / `--mw-focus-halo-*` for the ring.
   A hand-rolled shadow is the wrong colour in one of the two themes: the dark
   theme's shadow is a light rim over a dark contact layer, not a black blur.
   A hand-rolled duration also opts out of `prefers-reduced-motion`, which works
   by turning the duration tokens down.

4. **The header has two knobs of its own.** `$header-surface` sets how dark the
   bar sits under the primary colour (lower is darker); `$header-active-tint`
   sets how far the active navbar link is lifted off it (lower is a stronger,
   more saturated blue, higher is paler with more contrast against the bar).
   Both are `!default` in `abstracts/_variables.scss`.

## Light & dark

- Dark is the base. Light is applied by putting `mw-theme-light` on `<body>` -
  that class only re-points the theme aliases at the `--mw-light-*` set.
- Card, footer and border are derived from the page background by scaling its
  OKLch lightness and chroma by one factor. A card steps **away from the text
  colour** - darker than the page in the dark theme, lighter in the light one.
  A near-black `--mw-dark-page-background` leaves no headroom underneath and
  cards collapse into it; keep it around OKLch lightness 0.24.
- The card and footer factors are `!default` SCSS knobs, so the distance
  between a card and the page is one number per theme: `$card-surface-dark`
  (0.85), `$card-surface-light` (1.05), `$footer-surface-dark` (0.75),
  `$footer-surface-light` (0.95). Below 1 steps toward black, above 1 toward
  white - read 0.85 as "the card sits at 85% of the page's lightness". Toward 1
  is a flatter, borderless look; further apart makes cards read as raised
  panels. Keep the footer further out than the card in the dark theme and on
  the other side in the light one, or the footer stops reading as chrome. The
  border factor is not configurable - it runs against the card by design.
- Footer chrome and form controls deliberately stay dark/light respectively in
  both themes, and so does the header - see the next point for where its colour
  comes from.
- The header bar is **not** part of that surface stack. It is
  `--mw-primary-color` darkened straight toward black - `$header-surface` (14%)
  is how much of the colour survives, the same shade ramp a colour tool prints.
  It sits well past the bottom of that ramp so the hue reads as a tint on
  near-black, not as a colour of its own. That matters for a light-only project:
  while the bar was derived from the dark page background, its colour was frozen
  at the framework default nobody had configured. Every `--mw-header-*` token
  now follows the primary, and each is still overridable on its own.
- The ink on the bar is mixed off the same primary: `--mw-header-text-color` is
  `tint(92%)` and `--mw-header-navbar-list-active-color` - the current page and
  the hover tone both - is `tint(35%)`, so the active item reads as the brand
  colour rather than a washed-out pastel. Do not reach for
  `--mw-primary-text-color` here: that bound is calibrated against the page
  background and lets a mid-dark primary through untouched, which on this much
  darker bar lands around 2:1. At the default bar the active tone clears 5:1 on
  every palette; a near-black primary is the one case that falls short (~3.5:1,
  the bar is near-black too) - override the token there.
- Raising `$header-surface` for a lighter bar eats into that margin, since only
  the bar moves and the ink stays put. Past roughly 30% check the active tone,
  or move it down with the bar.
- Persisting the choice, the toggle UI and the initial class are the
  application's job in a SPA (`examples/angular-services.md`). The shipped JS
  does it for static pages using `localStorage` under the key `mw-theme`.

```ts
document.body.classList.toggle('mw-theme-light', isLight);
```

## SCSS configuration

Only `@use ... with (...)` works - a plain assignment before the `@use` has no
effect, because the root colours are declared with `!default`.

```scss
@use 'maverick-wave/src/scss/main' with (
  $mw-theme-mode: 'switchable',
  // 'switchable' | 'dark' | 'light'
  $primary-color: #0f766e,
  $secondary-color: #b45309,
  $success-color: #15803d,
  $warning-color: #a16207,
  $danger-color: #b91c1c,
  $info-color: #0e7490,
  $gray-color: #64748b,
  $dark-background: #172127,
  $dark-text-color: #e8eef0,
  $light-background: #f2f6f7,
  $light-text-color: #172127,
  $form-elements-background: #f5f9fa,
  $accent-text-color: #f2fafa,
  // the derivation knobs, all optional
  $hover-shift: 15%,
  $ink-lightness-dark: 0.68,
  $ink-lightness-light: 0.55,
  $muted-tint: 12%,
  // the surface stack - distance of card and footer from the page
  $card-surface-dark: 0.85,
  $card-surface-light: 1.05,
  $footer-surface-dark: 0.75,
  $footer-surface-light: 0.95,
  // the header bar - how much of the primary survives darkening toward black
  $header-surface: 16%,
  // how far the active navbar link sits off the primary colour - lower is a
  // stronger, more saturated blue, higher is paler with more contrast
  $header-active-tint: 25%,
  $mw-hero-image: url('/assets/hero.jpg'),
  // ink on that image - fixed, because the image is
  $mw-hero-text-color: var(--mw-dark-text-color),
  // per-theme treatment of that image - a filter, not an overlay, so the two
  // themes differ visibly even when the photo is already dark
  $hero-filter-dark: brightness(0.5),
  $hero-filter-light: brightness(1.15) saturate(1.2),
  $font-family-base: (
    'Inter',
    sans-serif,
  ),
  $font-family-heading: (
    'Inter',
    sans-serif,
  ),
  $font-family-mono: (
    'JetBrains Mono',
    monospace,
  )
);
```

The three font stacks are the one place where the parentheses matter: a
comma-separated stack is a Sass list, and without them the commas would read as
further arguments to `with (...)`. A single family (`$font-family-base: 'Inter'`)
needs none.

`$mw-theme-mode: 'dark'` or `'light'` compiles a single theme - the other set of
variables is omitted and `mw-theme-light` has no effect. The theme toggle
component reads `--mw-internal-theme-mode` and disables itself.

Overriding a value that is not on the list above is done in CSS afterwards -
they are all `var()` references anyway:

```scss
@use 'maverick-wave/src/scss/main' with (
  $primary-color: #0f766e
);

:root {
  /* break out of the derived scale for one token */
  --mw-primary-background-hover: color-mix(
    in srgb,
    var(--mw-primary-color) 35%,
    transparent
  );
}
```

## Importing only what you need

The full stylesheet is ~200 kB raw / ~31 kB gzipped. Marketing components
(`blog-post`, `gallery`, `content-slider`, `techstack-bucket`, `tiles`,
`coming-soon`, `ratings`, `home`, `hero`) are dead weight in an application, and
Angular bundle budgets notice.

Every layer forwards one module per file, and no `@extend` crosses a file
boundary, so partial imports are safe. **The one thing you must not drop is
`base`** - it carries the `:root` tokens; without it every component renders
colourless.

```scss
// styles.scss - configure first, then pick
@use 'maverick-wave/src/scss/abstracts/variables' with (
  $primary-color: #0f766e
);

@use 'maverick-wave/src/scss/base'; // :root tokens + reset + typography

@use 'maverick-wave/src/scss/layout/grid';
@use 'maverick-wave/src/scss/layout/main';
@use 'maverick-wave/src/scss/layout/page-header';
@use 'maverick-wave/src/scss/layout/section';

@use 'maverick-wave/src/scss/components/alerts';
@use 'maverick-wave/src/scss/components/buttons';
@use 'maverick-wave/src/scss/components/cards';
@use 'maverick-wave/src/scss/components/empty-state';
@use 'maverick-wave/src/scss/components/modals';
@use 'maverick-wave/src/scss/components/panels';
@use 'maverick-wave/src/scss/components/skeleton';
@use 'maverick-wave/src/scss/components/spinners';
@use 'maverick-wave/src/scss/components/tables';
@use 'maverick-wave/src/scss/components/tags';
@use 'maverick-wave/src/scss/components/toasts';

@use 'maverick-wave/src/scss/form-elements'; // or single files
@use 'maverick-wave/src/scss/utilities';
```

That set compiles to ~100 kB raw / ~17 kB gzipped - half the full build.

Details worth knowing:

- **Configuration has to come first.** `abstracts/variables` must be configured
  before any other module loads it, so the `with (...)` line goes at the top of
  the file. Configuring `main` instead pulls in everything again.
- `base` forwards `reset`, `base` and `typography`. If you already have your own
  reset, `@use '.../base/base'` gives you the `:root` block alone (~11 kB with a
  component or two).
- Module names are the file names without the leading underscore:
  `components/_buttons.scss` becomes `components/buttons`.
- Layer index files (`components`, `form-elements`, `layout`, `utilities`,
  `base`) pull in their whole layer - convenient for the small ones
  (`utilities`, `form-elements`), wasteful for `components`.
- Some components expect a sibling: `lists` styles checkbox rows and looks best
  with `form-elements/checkbox`; `tags` uses `mw-btn-mini` from `buttons` for
  its remove button.
