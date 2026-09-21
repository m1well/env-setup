# Theming, tokens & partial imports

## The model

Thirteen colours are configured, everything else is derived from them **at
runtime** with `color-mix()` and relative colour syntax. Overriding a root token
therefore retunes its whole family - hover tone, translucent backgrounds,
borders, the theme's surface stack, the ink variant the dark theme needs. That is
the difference to pre-3.4.0, where derived values were baked in at compile time
and a palette switch meant setting 41 variables.

Writing those tokens on `<html>` at runtime is how a palette is swapped without
a reload. It repaints the same breadth the theme flip does and needs the same
guard against a page-wide interpolation - see **Light & dark** below.

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
| `--mw-section-padding-fluid`                                                                                                                                                 | The fluid alternative to the value above - 1.75rem on a phone up to 5.5rem at `xl`. Not applied by itself: set `--mw-section-padding-block: var(--mw-section-padding-fluid)`                                                                                                                                                            |
| `--mw-section-nav-height`                                                                                                                                                    | Height the sticky `mw-section-nav` reserves (3.7rem). Add it to `--mw-header-height` for the `scroll-margin-top` of anything the strip can cover                                                                                                                                                                                        |
| `--mw-root-font-size`                                                                                                                                                        | Percentage the whole rem scale is built on (`100%`). Type, spacing and control heights move with it; px breakpoints do not                                                                                                                                                                                                              |
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

- Every theme token is declared once on `:root` as `light-dark(light, dark)`.
  Which half applies is decided by `color-scheme` on the element that **uses**
  the token, and `:root` carries `color-scheme: light dark` - so a page follows
  the OS until someone chooses otherwise.
- `mw-theme-light` and `mw-theme-dark` on `<body>` are that choice. They set
  little more than `color-scheme`, and every token follows. `mw-theme-dark` is
  not redundant: without it, a reader who picks dark on a machine set to light
  would be pulled straight back to the OS preference.
- Chrome 119-122 and Safari 16.4-17.4 are in the browserslist but predate
  `light-dark()`. `base/_base.scss` keeps the old route for them behind
  `@supports` - dark on `:root`, light by class, no OS tracking.
- `--mw-hero-image-filter` is the one theme value that is not a colour and so
  cannot ride along; it follows `prefers-color-scheme` instead.
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
  does it for static pages using `localStorage` under the key `mw-theme`. With
  nothing stored it takes the OS preference and keeps tracking it live, so
  changing the system theme moves the page until the reader picks a side.
- **Suppress transitions while the class flips.** Colour changes on nearly every
  element at once, and the shared `--mw-transition` turns that into thousands of
  concurrent animations - on a documentation-sized page it is seconds of blocked
  style and layout. `mw-theme-switching` on `<html>` kills them for the flip; the
  forced reflow between the two class changes is what commits the new colours
  before transitions come back.

```ts
const root = document.documentElement;

root.classList.add('mw-theme-switching');
document.body.classList.toggle('mw-theme-light', isLight);
document.body.classList.toggle('mw-theme-dark', !isLight);
void root.offsetHeight; // commit the new colours with transitions off
root.classList.remove('mw-theme-switching');
```

## Site-wide variants

Fifteen classes on `<html>` and six custom properties retune the whole look
without a rebuild. They stack, and none of them need a class per element. The
showcase at https://maverick-wave.m1well.com has a picker for the set, and its
URL carries the choice - a link is how a look gets agreed on before it is built.

| Class                | Effect                                                                                                                                                                              |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mw-corners-even`    | Drops the surface signature - every card, panel and modal becomes an evenly rounded `radius('md')` box                                                                              |
| `mw-accent-single`   | `--mw-secondary-color` follows the primary; `mw-btn-secondary` turns outline so the two stay apart                                                                                  |
| `mw-shadows-flat`    | Elevation 1-3 to `none`. The dropdown (4) and the modal (5) keep their shadow                                                                                                       |
| `mw-surfaces-flush`  | Card, panel and footer background drop to the page colour and the border is redrawn from the ink, because the old one is a neighbouring shade of a surface that is now the page     |
| `mw-hover-static`    | No hover travels - lifts, image zooms and slides go. Colour and border still respond                                                                                                |
| `mw-scroll-static`   | No scroll entrance - `mw-reveal` and `mw-reveal-stagger` blocks sit where they land                                                                                                 |
| `mw-sections-plain`  | The diagonal hatch behind `mw-section-alternate` collapses into the page colour                                                                                                     |
| `mw-headings-caps`   | `h1`-`h3` in capitals with 0.045em tracking                                                                                                                                         |
| `mw-links-underline` | `mw-link`, `mw-link-muted` and `mw-btn-link` carry their underline at rest. The hover signal moves to the stroke, which thickens to 3px - `mw-link` has no colour change of its own |
| `mw-btn-pill`        | `mw-btn` fully rounded. Form fields keep their own radius                                                                                                                           |
| `mw-btn-square`      | `mw-btn` to `border-radius: 0`. The other end of the same axis, and unlike `--mw-radius-scale: 0` it leaves the rest of the page rounded                                            |
| `mw-btn-glass`       | Filled buttons become tinted glass: translucent wash, vertical ramp, specular top edge. No `backdrop-filter` - it would trap a fixed-position tooltip inside the button             |
| `mw-btn-tactile`     | The four solid variants stand on a 3px edge mixed toward black and travel its full height on `:active`. Outline, ghost and link have no fill to darken and are untouched            |
| `mw-density-compact` | Card and panel padding and the three control heights drop one step down the spacing scale. Type is untouched - `--mw-root-font-size` is the switch that scales everything together  |
| `mw-density-roomy`   | The same one step up                                                                                                                                                                |

| Property                     | Effect                                                                                                                      |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `--mw-radius-scale`          | Multiplies the whole radius scale - `0` squares everything off                                                              |
| `--mw-root-font-size`        | Percentage on `html`. The scale is rem, so type, padding and control heights move together; breakpoints are px and stay put |
| `--mw-font-family-heading`   | Headline typeface; body copy is untouched                                                                                   |
| `--mw-container-width`       | Where the content stops growing                                                                                             |
| `--mw-section-padding-block` | Air above and below each section                                                                                            |
| `--mw-section-padding-fluid` | The same, but growing with the screen - point the line above at it                                                          |
| `--mw-motion-scale`          | Multiplies all six duration tokens - `0.6` brisk, `1.6` relaxed. `prefers-reduced-motion` still overrides it                |

**Writing your own.** A variant that retunes a _theme-bound_ token - anything in
the dark/light maps - cannot be written on `:root` alone: `mw-theme-light`
re-declares those on `<body>`, which shadows the root value for the entire
subtree and the switch does nothing in light mode. Target both:

```scss
:root.my-variant,
:root.my-variant .mw-theme-light {
  --mw-card-background: var(--mw-page-background);
}
```

`--mw-elevation-1..5` are the exception and need only `:root`: the ramp is one
set for both themes and reaches the theme through `--mw-shadow-near/-far`, so
there is no second declaration further down the tree to shadow it.

The same trap the other way round: never copy a theme alias _into_ a token on
`:root` (`--mw-x: var(--mw-page-background)`), because up there it still holds
the dark value. Write that rule on the element instead.

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
  // a pattern layer over it, for a hero that parallaxes - see mw-parallax-pattern
  $mw-hero-pattern: repeating-linear-gradient(
      to bottom,
      rgb(255 255 255 / 5%) 0 1px,
      transparent 1px 38px
    ),
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

## Mixins and functions

`@use 'maverick-wave/src/scss/abstracts' as *` brings the whole set in - the
tokens, the functions and the mixins. They exist on the SCSS path only; the
compiled CSS carries none of them, so a CDN project cannot reach them.

Functions read the maps: `spacing('4')`, `font-size('lg')`,
`font-weight('bold')`, `radius('md')`, `breakpoint('md')`, `color('primary-color')`,
`z-index('menu')`, `motion('base')`.

```scss
@use 'maverick-wave/src/scss/abstracts' as *;

.hero-title {
  font-size: fluid(1.95rem, 4.2rem, $to: 'xl');
  margin-bottom: spacing('6');
}

.my-icon-button {
  @include touch-floor;
}

.my-dot {
  @include hit-area(7px);
}
```

- `fluid($min, $max, $from: 'xs', $to: 'md')` - a clamp between two sizes. Each
  end is a key of `$font-sizes` or a plain rem/px length, so a hero that does
  not sit on the scale still gets one. The rem term is what the vw-only form
  throws away: a size in vw alone ignores the reader's font size and stops
  responding to zoom. The default range ends at `md` because that is where the
  stepped heading sizes it replaces reached their largest value - a headline
  that should keep growing passes `$to: 'xl'`.
- `fluid-container($min, $max, $from, $to)` - the same ramp measured against the
  container instead of the viewport, so the slope lands in `cqi`. For anything
  inside a `@container` block: sizing there off `vw` hands a 440px card in a
  1400px window the measurements a 900px card was drawn for. The endpoints are
  container widths, not breakpoint names, because a container has none.
- `media-up($bp)` / `media-down($bp)` - the `$breakpoints` map as range syntax,
  `width >= bp` and `width < bp`, so the two never overlap at the breakpoint.
- `touch-context($bp: 'md')` - coarse pointer _or_ narrow viewport. Every
  target-size rule in the framework hangs under it; put your own control under
  the same condition instead of guessing it.
- `touch-floor($size: 2.75rem)` - that condition plus a `min-height`, and it
  takes a `@content` block for whatever else the control needs there. Not for a
  link inside a sentence: WCAG 2.5.8 exempts those, and a `min-height` there
  pushes the lines of the paragraph apart.
- `hit-area($grow: 6px)` - grows the hit area through `::after` without touching
  the silhouette, for a control whose size is the design. Neighbours need a gap
  of at least twice `$grow`, or two hit areas overlap and a tap lands on the one
  next door. It takes `::after`, so it is out for anything carrying a
  `data-tooltip`.
- `hover` / `hover-move` - a hover effect that only runs where hovering is real.
  See the pitfall on latching `:hover`.
- `focus-ring`, `focus-ring-inset`, `field-focus`, `focus-halo` - the ring, in
  its four shapes.
- `truncate`, `scrollbar`, `surface`, `corner-accent` - the shared silhouette
  and the one-line helpers the components use.

## Overriding a component

Tokens cover colour and rhythm; for anything else write a normal rule. The
framework emits everything inside
`@layer mw.reset, mw.base, mw.forms, mw.components, mw.layout, mw.utilities`,
and an unlayered rule beats every layer regardless of weight:

```css
/* wins over .mw-card, no !important and no doubled selector */
.mw-card {
  border-radius: 12px;
}
```

The same rule cuts the other way: third-party CSS loaded unlayered also beats
the framework, which is what makes an icon font quietly win over `mw-tags-icon`.
Give it a layer of its own:

```css
@layer vendor, mw;
@import url('font-awesome.css') layer(vendor);
```

## Importing only what you need

The full stylesheet is ~281 kB raw / ~40 kB gzipped. Marketing components
(`blog-post`, `gallery`, `content-slider`, `techstack-bucket`, `tiles`,
`coming-soon`, `ratings`, `home`, `hero`) are dead weight in an application, and
Angular bundle budgets notice.

Every layer forwards one module per file, and no `@extend` crosses a file
boundary, so partial imports are safe. **The one thing you must not drop is
`base`** - it carries the `:root` tokens; without it every component renders
colourless. The cascade layer order comes along on its own: every module loads
`abstracts`, which declares it, so a hand-picked subset orders itself the same
way the full build does.

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

That set compiles to ~137 kB raw / ~21 kB gzipped - about half the full build.

Details worth knowing:

- **Configuration has to come first.** `abstracts/variables` must be configured
  before any other module loads it, so the `with (...)` line goes at the top of
  the file. Configuring `main` instead pulls in everything again.
- `base` forwards `reset`, `base` and `typography`. If you already have your own
  reset, `@use '.../base/base'` gives you the `:root` block alone (~15 kB raw /
  ~3 kB gzipped).
- Module names are the file names without the leading underscore:
  `components/_buttons.scss` becomes `components/buttons`.
- Layer index files (`components`, `form-elements`, `layout`, `utilities`,
  `base`) pull in their whole layer - convenient for the small ones
  (`utilities`, `form-elements`), wasteful for `components`.
- Some components expect a sibling: `lists` styles checkbox rows and looks best
  with `form-elements/checkbox`; `tags` uses `mw-btn-mini` from `buttons` for
  its remove button.
