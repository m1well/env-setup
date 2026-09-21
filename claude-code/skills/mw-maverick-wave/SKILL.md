---
name: mw-maverick-wave
description: Complete usage guide for the MaverickWave CSS framework - mw-* classes, --mw-* design tokens, grid, components, forms, theming and integration into Angular, other SPAs or plain HTML. Use whenever markup or styles are written in a project that loads maverick-wave (CSS/SCSS/CDN), when a mw-* class or --mw-* token appears, or when a UI has to be built with it.
---

# MaverickWave

A CSS-only component framework: it ships classes and design tokens, no components,
no directives, no build-time API. You write plain HTML with `mw-*` classes - in a
template, a JSX file, a Twig partial, it makes no difference. Everything below is
therefore framework-neutral; the Angular notes are marked as such because Angular
is the reference integration.

**One rule dominates all others: only use classes that actually exist.** The
framework is not utility-complete, invented class names fail silently (no error,
just unstyled markup). Verify with `grep -o '\.mw-[a-z0-9-]*' dist/maverick-wave.min.css | sort -u`
or, in the framework repo, `npm run verify`.

## Reference files

Load the one you need - do not read them all up front.

| File                       | Content                                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `references/layout.md`     | Page skeleton, grid, container, section, page header, header/navbar, footer, spacing/flex/display/text utilities          |
| `references/components.md` | Every component: markup, variants, sizes, state classes                                                                   |
| `references/forms.md`      | Inputs, select, textarea, checkbox, radio, toggle, slider, input group, `mw-field` pattern, validation                    |
| `references/theming.md`    | Token model, `color-mix` derivation, light/dark, site-wide variants, SCSS configuration, cherry-picking single components |
| `references/javascript.md` | What the shipped `main.js` does, why SPAs must not load it, what to implement instead                                     |

## Examples

| File                              | Content                                                                                                                                           |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `examples/angular-list-page.md`   | Full list/CRUD page: page header, meta counters, filter bar, table with status tags, empty state, delete modal, toasts                            |
| `examples/angular-form.md`        | Reactive form: `mw-field`, validation states, input groups, numeric input, toggles, form actions                                                  |
| `examples/angular-services.md`    | Theme service, toast service, modal/scroll-lock, tabs and accordion without `main.js`                                                             |
| `examples/static-landing-page.md` | Plain HTML page: announcement ribbon, hero with scroll cue, feature and offer cards, testimonials, scroll reveal, accordion, footer, theme toggle |

## Setup

### Plain HTML / CDN

```html
<meta
  name="viewport"
  content="width=device-width, initial-scale=1.0, viewport-fit=cover"
/>
<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/maverick-wave@5/maverick-wave.min.css"
/>
<link
  rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
/>
...
<script src="https://cdn.jsdelivr.net/npm/maverick-wave@5/maverick-wave.min.js"></script>
```

`@5` keeps this snippet current; in a real project pin the exact version so a
build stays reproducible. The JS file is optional and only for
server-rendered/static pages - see below. `viewport-fit=cover` is not optional -
see pitfall 30.

### Angular (or any SPA)

```jsonc
// angular.json
"styles": ["src/assets/maverick-wave.min.css", "src/styles.scss"]
// no "scripts" entry - see the warning below
```

Or from the npm package via SCSS: `@use 'maverick-wave/src/scss/main';`
(details and configuration in `references/theming.md`). The viewport meta above
belongs in `src/index.html` there, with `viewport-fit=cover` just the same.

> **Never load `maverick-wave.min.js` in a SPA.** Everything in it is wired up
> once on `DOMContentLoaded` and writes straight into the DOM. In an Angular
> app that fires once during bootstrap: components rendered later are never
> initialised, and the theme toggle mutates the DOM behind change detection.
> Reimplement the handful of behaviours in your own components -
> `references/javascript.md` lists all of them, `examples/angular-services.md`
> shows the code.

### Icons

The framework styles icon slots but ships no icons. Examples use FontAwesome
(`<i class="fas fa-save"></i>`); any icon element works - inline SVG, an Angular
`fa-icon`, a `<span>` with a webfont.

### Fonts

No font is bundled. The defaults are system stacks - `--mw-font-family-base`
and `-heading` resolve to the platform UI font, `-mono` to Fira Code with the
system monospace stack behind it. Load a font yourself and either set the three
`$font-family-*` variables in SCSS or override the tokens in CSS.

## Naming rules

- Classes: `mw-` prefix, kebab-case: `.mw-button-bar`, `.mw-item-list-compact`
- Tokens: `--mw-` prefix: `--mw-primary-color`, `--mw-border-accent`
- Variants are suffixes on the base class: `mw-btn` + `mw-btn-primary`,
  `mw-alert` + `mw-alert-danger`
- Colour variant names are the same everywhere: `primary`, `secondary`,
  `success`, `warning`, `danger`, `info` (plus `muted` on tags). Not every
  component offers all of them - check `references/components.md`.
- Size variants: `-sm`, `-lg`, sometimes `-xs` / `-xl`. The unsuffixed class is
  the medium size.

### State classes

Since 4.0.0 there is one spelling for "this one is on": **`mw-active`**. It
works on every component that previously wanted a bare `active` - accordion,
tabs, navbar link, timeline step, image slider, button, theme toggle, segmented
control - alongside gallery dot, stepper and kanban composer, which used it all
along. Write `mw-active` and stop looking things up.

The unprefixed `active` is still styled everywhere it used to be, so existing
markup keeps working, but it is deprecated. The shipped `main.js` clears both
when it switches a state off, precisely so a stale `active` in the HTML cannot
leave a second tab lit.

The classes that mean something _other_ than "on" keep their own names:

| Component                                    | State class                                              |
| -------------------------------------------- | -------------------------------------------------------- |
| Anything switchable, "on"                    | `mw-active` (`active` deprecated)                        |
| Burger button + navbar panel                 | `open` (no prefix), plus `mw-nav-open` on `<body>`       |
| Stepper indicator / label / connector / step | `mw-active`, `mw-done`                                   |
| Checkbox list item (`li`)                    | `mw-selected`                                            |
| Calendar day, picked                         | `mw-selected`                                            |
| Kanban ticket being edited                   | `mw-kanban-editing`                                      |
| Modal, older overlay div                     | `mw-modal-open` (a `<dialog>` carries `open` itself)     |
| Alert, dismissing / dismissed                | `mw-alert-closing` → `mw-alert-closed` (`display: none`) |
| Field wrapper in error                       | `mw-field-has-error`                                     |
| Single form control in error                 | `mw-form-element-error`                                  |

`mw-active` and `mw-selected` are not the same thing and not interchangeable:
active is the one of several that is currently showing, selected is a choice the
user made and can undo.

Angular: `[class.mw-active]="i === current"`.

## Scales

**Spacing** (`mw-m-*`, `mw-p-*`, `mw-gap-*` and every internal value):

| key | 0   | 1   | 2    | 3   | 4    | 5   | 6    | 7    | 8   | 9   | 10  | 11  | 12  | 13  | 14  |
| --- | --- | --- | ---- | --- | ---- | --- | ---- | ---- | --- | --- | --- | --- | --- | --- | --- |
| rem | 0   | 0.2 | 0.35 | 0.5 | 0.75 | 1   | 1.35 | 1.75 | 2   | 2.5 | 3.3 | 4.3 | 5.5 | 7   | 9   |

Negative margins exist for keys 1-6 (`mw-mt--3` = -0.5rem). Gap has no negative
keys at all (negative gap is invalid CSS and is not generated).

**Font sizes** (`mw-text-3xs` … `mw-text-6xl`): `3xs` 0.6, `2xs` 0.7, `xs` 0.8,
`sm` 0.9, `base` 1, `md` 1.1, `lg` 1.3, `xl` 1.5, `2xl` 1.8, `3xl` 2.2, `4xl` 2.5,
`5xl` 3, `6xl` 4.3 rem. The utility classes are single steps; `h1`, `h2`,
`mw-section-title` and `mw-section-subtitle` interpolate instead - `h1` runs
`3xl` to `5xl` between 375px and 768px, `h2` `2xl` to `4xl`, the two section
headings one step each up to 576px. The endpoints are the values the old
breakpoint steps had, so a phone and a desktop look the same and only the widths
between them moved.

**Breakpoints**: `xs` 375, `sm` 576, `md` 768, `lg` 992, `xl` 1200, `2xl` 1400 px.
Column grids and most components are mobile-first. The mixins emit range syntax
(`media-up` is `width >= bp`, `media-down` is `width < bp`), so the two never
overlap at the breakpoint itself and neither has to stop a fraction short of it.

**Overriding.** Everything the framework emits sits in
`@layer mw.reset, mw.base, mw.forms, mw.components, mw.layout, mw.utilities`.
Any rule written outside a layer beats all of it, so a single `.mw-card {}` in
your own stylesheet wins - no `!important`, no doubled selectors. `!important`
is not a stronger version of this but a weaker one: important declarations
reverse the layer order and unlayered comes last, so an important rule in
`mw.base` beats an important one of yours even behind an ID selector. The flip
side: third-party CSS loaded unlayered also wins, so pull it into a layer of
its own:
`@import url('font-awesome.css') layer(vendor);` with `@layer vendor, mw;`
declared before it.

**Radius** (`mw-radius-none|xs|sm|md|lg|xl|2xl|full`): 0, 2, 5, 10, 15, 20, 30 px, 50%.
Every one of them is multiplied by `--mw-radius-scale` (default 1), so one number
squares the framework off or rounds it further; `none` and `full` pass through.

**The surface signature.** Every panel-like component - card, panel, modal,
accordion, tile, calendar, pagination, login box - shares one silhouette: sharp
5px corners on the top-left/bottom-right diagonal, round 20px ones on the other,
plus a 2px **corner accent** in the primary tone (`--mw-corner-accent`) sitting
on the two round corners. It is not a class and not opt-in; the components carry
it. `mw-corner-plain` drops the accent on a box too small to hold it - see
`references/layout.md` - and `mw-corners-even` on `<html>` drops the whole
signature site-wide.

**Elevation** (`mw-elevation-0` … `-5`, and `var(--mw-elevation-N)` inside SCSS).
Two shadows per level - a tight contact layer plus a wide ambient one:
`1` resting (inputs, tags), `2` raised (cards, panels at rest), `3` floating
(a card under the pointer), `4` overlay (dropdown, popover, drawer), `5` modal.
`0` is explicitly flat. Never write a `box-shadow` by hand - the twelve one-off
values that used to exist are exactly what this replaced.

**Glow** (`mw-glow`, `mw-glow-{primary,secondary,info,success,warning,danger}`).
The same two-layer idea without the offset, so the surface reads as giving off
the light rather than casting a shadow. For the one element on a screen that has
to be seen first, and for nothing else.

**Motion** `--mw-duration-instant|fast|base|slow|slower` = 110/180/300/520/900ms
plus `--mw-duration-zoom` (650ms, for a large surface actually travelling),
`--mw-ease-out` (things arriving - the default), `--mw-ease-in-out` (A to B and
back), `--mw-ease-spring` (a pop). Two ready-made transitions:
`var(--mw-transition)` for hover and focus states, `var(--mw-transition-fast)`
for anything that should feel instant under the pointer. Both list their
properties explicitly rather than saying `all`. All six durations are multiplied
by `--mw-motion-scale` (default 1), the tempo counterpart to
`--mw-radius-scale`; `prefers-reduced-motion` overrides the result.

**Control sizes** `--mw-control-height-sm|base|lg` = 1.875 / 2.125 / 2.375rem (an
even 30 / 34 / 38px step, moved by `mw-density-compact` and `-roomy`) and
`--mw-control-font-sm|base|lg` = 0.8 / 0.9 / 1rem, shared by `mw-input`,
`mw-select`, `mw-textarea` and `mw-btn`. A field and the button beside it are
the same height by construction. Buttons run one font step above the fields.

**Focus** `--mw-focus-ring-width` 2px, `--mw-focus-ring-offset` 2px,
`--mw-focus-ring-color`, plus `--mw-focus-halo-size` 3px /
`--mw-focus-halo-opacity` 28% for the soft ring a form field gets instead of a
hard outline. SCSS: `@include focus-ring`, `focus-ring-inset`, `field-focus`.

**SCSS helpers** - `@use 'maverick-wave/src/scss/abstracts' as *` brings them in;
none of them survive into the compiled CSS. Full list in `references/theming.md`.

- `fluid($min, $max, $from: 'xs', $to: 'md')` - a clamp between two sizes, each
  end a key of `$font-sizes` or a plain rem/px length. The rem term is the
  point: a vw-only clamp ignores the reader's font size and stops responding to
  zoom. A headline passes `$to: 'xl'`.
- `fluid-container($min, $max, $from, $to)` - the same ramp in `cqi` against the
  container. Use it instead of `fluid()` inside a `@container` block.
- `media-up($bp)` / `media-down($bp)` - the breakpoint map as a query.
- `touch-context($bp: 'md')` - coarse pointer _or_ narrow viewport, the condition
  every target-size rule in the framework hangs under.
- `touch-floor($size: 2.75rem)` - that condition plus a `min-height`.
- `hit-area($grow: 6px, $box: 1.5rem)` - grows the hit area through `::after`
  without touching the silhouette. An element carrying a `data-tooltip` owns that
  pseudo for its arrow, so those are skipped and grow to `$box` instead.
- `hover` / `hover-move`, `focus-ring`, `focus-ring-inset`, `field-focus`,
  `truncate`, `surface`.

## Component index

Everything below is documented in `references/components.md` unless marked otherwise.

**Actions** `mw-btn` (+ `primary`, `secondary`, `danger`, `success`, `outline`,
`ghost`, `ghost-danger`, `link`, `link-muted`, `plain`, `icon`, `block`, `sm`,
`lg`) · `mw-btn-mini` · `mw-link` / `mw-link-muted` (the link in running text) ·
`mw-button-bar`
(+ `left`, `right`, `center`, `between`) · `mw-segmented` · `mw-actions-note`

**Containers** `mw-card` (+ `simple`, `lg`, `xl`, `stack`, badge, ribbon,
feature frame) ·
`mw-panel` · `mw-tile` · `mw-accordion` · `mw-tabs` · `mw-modal` ·
`mw-item-list` family · `mw-offer` (+ `-head`, `-name`) ·
`mw-leader-row` (+ `-label`, `-value`, `-top`, `-dashed`, `-solid`) ·
`mw-date-stamp` (+ `-day`, `-date`, `-body`, `-today`) ·
`mw-contact` (+ `-row`, `-label`)

**Pricing** `mw-price` (+ `-amount`, `-fraction`, `-currency`, `-original`,
`-period`, `-word`, `-note`, `xs`/`sm`/`lg`, `inline`, `center`, `plain`)

**Data & status** `mw-table` (+ `subtle`, `sticky-head`, `cards`, `compact`,
`hover`, responsive wrappers) · `mw-kanban` (+ `plain`, `compact`) ·
`mw-calendar` (+ `compact`, `plain`) · `mw-tag` /
`mw-tags` · `mw-badge` (+ `-dot`, `-status`, `-anchor`, `-float`, `-pulse`) ·
`mw-info` / `mw-info-mini` / `mw-info-counter` · `mw-progress-bar` ·
`mw-rating` · `mw-meta-header` · `mw-stepper` · `mw-timeline-big` /
`mw-timeline-simple`

**Feedback** `mw-alert` · `mw-toast-stack` · `mw-announcement` (+ `-content`,
`-highlight`, `-static`, color variants) · `mw-empty-state` ·
`mw-spinner-border` / `mw-spinner-dots` / `mw-spinner-dual-ring` · `mw-skeleton`

**Navigation** `mw-header` (+ `mw-header-reveal`, `mw-header-keep`) +
`mw-navbar` · `mw-breadcrumbs` · `mw-pagination` ·
`mw-dropdown` (+ `-menu`, `-item`, `-item-danger`, `-divider`, `-label`,
`-caret`, `-end`, `-up`) · `mw-lang-switch` (+ `-code`, `-name`, `-check`,
`inverted`) · `mw-flag` (+ 23 country codes) ·
`mw-section-nav` (`references/layout.md`)

**Media & content** `mw-avatar` (+ `initials`, `group`) · `mw-gallery` ·
`mw-image-slider` · `mw-blog-post` · `mw-testimonial` (+ `-source`, `-detail`,
`-date`, `-featured`) · `mw-prose` · `mw-media` (+ `-caption`) · `mw-code-block` /
`mw-terminal` · `mw-techstack-bucket` · `mw-coming-soon` · `mw-divider` ·
`mw-kbd` · `mw-list` family

**Forms** (`references/forms.md`) `mw-field` · `mw-input` · `mw-select` ·
`mw-textarea` · `mw-checkbox` · `mw-radio` · `mw-toggle` · `mw-slider` ·
`mw-input-group` · `mw-prefilled` · `mw-form` / `mw-form-group` /
`mw-form-actions` · `mw-login`

**Layout** (`references/layout.md`) `mw-main` · `mw-container` (+ `-narrow`) ·
`mw-content` ·
`mw-section` (+ `mw-section-intro`) · `mw-page-header` · `mw-grid-*`
(+ `mw-grid-even`) ·
`mw-columns-2/3` · `mw-row-split` · `mw-hero` (+ `mw-scroll-hint`, `-end`) ·
`mw-parallax` (+ `-media`, `-content`, `-dimmed`, `-sticky`, `-rise`,
`-slow`, `-pattern`) · `mw-footer`

**Utilities** (`references/layout.md`) `mw-sr-only` / `mw-sr-only-focusable` /
`mw-skip-link` · `mw-row-split` (+ `center`) · `mw-text-numeric` /
`mw-text-currency` · `mw-text-truncate` / `mw-text-clamp-2..5` /
`mw-text-break` / `mw-text-nowrap` · `mw-text-balance` / `mw-text-pretty` /
`mw-text-eyebrow` / `mw-text-measure` · `mw-elevation-0..5` · `mw-glow` /
`mw-glow-{primary,secondary,info,success,warning,danger}` ·
`mw-corner-plain` ·
`mw-aspect-square|video|wide|portrait|photo` · `mw-d-{sm,md,lg,xl}-*` /
`mw-hide-mobile` / `mw-hide-desktop` · `mw-overflow-*` / `mw-snap-x` ·
`mw-reveal` / `mw-reveal-stagger` · spacing, flex, display, text

## Pitfalls

1. **`<section>` gets no padding by itself.** Since 3.4.0 the bare element
   selector is gone - write `<section class="mw-section">`. `mw-section-alternate`
   only paints the pattern, it does not space anything.
2. **`mw-form` has no padding** (removed in 3.4.0) - it is a flex column with a
   gap. Safe to put on `mw-modal-body` or `mw-panel-body`.
3. **Use `mw-btn-danger` for destructive actions**, never `mw-btn-secondary`. The
   secondary colour is a brand decision and turns yellow, teal or anything else
   the moment the palette changes.
4. **One tag or many?** `mw-tag` is a standalone chip and carries its own colour -
   right for a table cell. `mw-tags` is a container that colours all its
   `mw-tags-item` children - right for a tag list. Mixing them (`mw-tag` inside
   `mw-tags`) is wrong.
5. **A spinner needs a shape class.** `mw-spinner-primary` alone renders nothing;
   use `mw-spinner-border`, `mw-spinner-dots` or `mw-spinner-dual-ring`.
6. **Sticky table headers need a height-limited scroll container** -
   `mw-table-responsive` only scrolls horizontally. Use
   `mw-table-responsive-scroll` (height via `--mw-table-scroll-height`).
7. **`--mw-text-muted-color` on a coloured surface is always wrong.** It follows
   the theme; buttons, table headers and badges do not. Use
   `--mw-*-accent-text-color` there, and `opacity` for disabled states.
   `--mw-accent-text-color` is the shared label for all six colours; each one
   also has its own `--mw-primary-accent-text-color`,
   `--mw-secondary-accent-text-color`, `--mw-success/warning/danger/info-accent-text-color`,
   defaulting to the shared token. Override a single one when that colour needs
   the opposite label - a neon primary on an otherwise dark palette. The fixed
   grey surfaces - tooltip, `mw-btn-mini`, `mw-info-mini`, gallery arrows -
   hardcode white and ignore all of them.
8. **`mw-card` already lifts on hover** and `mw-btn` already has `inline-flex`
   plus a gap for icons. Neither has a modifier class for it - adding one from
   memory produces markup that does nothing.
9. **Overriding one root colour is enough.** Hover tones, translucent
   backgrounds and borders are derived with `color-mix()` at runtime. Setting
   `--mw-primary-color-hover` by hand is usually a sign the base token was not
   set.
10. **Browser floor: `color-mix()` and `oklch(from ...)`** - Chrome 119+,
    Safari 16.4+, Firefox 128+. Both carry the derived tones, so older browsers
    get no colours at all, not merely worse ones.
11. **Touch targets grow on their own.** On `pointer: coarse` or below 768px,
    `mw-btn` gets a 2.75rem minimum height, `mw-btn-sm`, `mw-input-sm`,
    `mw-select-sm` and `mw-textarea-sm` 2.5rem, a tab 2.75rem, a calendar day
    44px, and list rows / menu items / pager pages / accordion headers 2.75rem.
    `mw-btn-mini` keeps its 18px circle - it sits in tag rows and table cells
    where a bigger one would shift the layout - and grows its _hit area_ to 28px
    via a pseudo-element, and `mw-kanban-action` does the same - its 32px box
    stays and the hit area around it reaches 44px.
    `mw-techstack-item-sm` takes a real 2.5rem minimum instead, because half of
    those chips carry a `data-tooltip` and that owns the pseudo-element.
    Nothing to switch on, and no reason to write the media query again in an
    app: your own control gets `@include touch-floor` for a height or
    `@include hit-area` where the size is the design.
12. **`mw-empty-state` has a `-desc`, not a `-text`.** The parts are
    `mw-empty-state-icon`, `-title`, `-desc`, plus the size variant
    `mw-empty-state-sm`. Invented names fail silently, as always.
13. **`mw-text-numeric` gives digits, `mw-text-currency` gives a money column.**
    The first is only `tabular-nums` - for a clock, a counter, an ID. The second
    adds right alignment and `nowrap`. Before 4.0.0 the first did both, which
    is why people wrote the declaration out by hand.
14. **A component host between a container and its children breaks the layout,
    silently.** Every `mw-*` flex or grid container styles its _children_ -
    `mw-grid-*`, `mw-tags`, `mw-button-bar`, `mw-form-actions`, `mw-modal-footer`,
    `mw-toast-stack`. In plain HTML the children are right there; in a SPA a
    component host often sits in between and becomes the item instead, so it
    shrinks to content width or swallows a whole grid row. Put `mw-d-contents` on
    that host - it then generates no box and the children take the item role
    back. Angular: `host: { class: 'mw-d-contents' }`. `mw-header` handles this
    case on its own, the others do not.
15. **A badge is not a tag.** `mw-tag` names something - a topic, a state - and
    sits in a row of its own kind, with a tinted surface. `mw-badge` carries a
    _count_ or a _status_ and usually sits **on** something, filled rather than
    tinted. Number on a bell: badge. "Draft" next to a title: tag.
16. **A dropdown is a `<details>`, not a div.** `<details class="mw-dropdown">`
    with a `<summary>` trigger - that is where the keyboard handling, the focus
    and the open state come from, and it works without script. The framework JS
    only adds Escape and click-outside. Writing your own div-plus-click loses all
    of it.
17. **An open dropdown can be clipped by anything that hides its overflow.**
    Where the browser supports anchor positioning the menu is `position: fixed`
    and anchored to its trigger, so it escapes the clip on its own. Everywhere
    else it is absolutely positioned and cut off. Either way the framework's own
    containers (panel, card, tile, modal body, responsive table) lift the clip
    while a menu is open. On your own container it is one line:
    `:has(.mw-dropdown[open]) { overflow: visible }`.
18. **Never write `box-shadow` by hand.** Use `var(--mw-elevation-1..5)` or the
    `mw-elevation-*` class. A hand-rolled shadow is the wrong colour in one of
    the two themes - the dark theme's shadow is a light rim over a dark contact
    layer, not a black blur. The one place the ramp is wrong is a shadow that
    lands on a picture instead of on a theme surface: its light-theme layers are
    cut for paper and vanish over a photograph. That is why the edge after a
    parallax block carries fixed values, and why `mw-parallax-dimmed` hardcodes
    its brightness and text-shadow.
19. **Never write a duration or an easing curve by hand** either. Use
    `var(--mw-transition)` for a hover or focus state,
    `var(--mw-transition-fast)` for something that should feel instant, and
    `var(--mw-duration-*)` with `var(--mw-ease-*)` for anything else. That is
    also what makes `prefers-reduced-motion` work - it turns the duration tokens
    down, so anything built on them is covered for free.
20. **A hover effect that _moves_ something needs the `hover` mixin.** On touch
    `:hover` latches after a tap and stays on, so a lifted card stays lifted,
    visibly out of line with its row. `@include hover { transform: ... }` -
    colour changes are fine unguarded, movement is not. The framework's own
    components already do this.
21. **Below 576px a modal is a bottom sheet.** Full width, anchored to the bottom
    edge, rounded on the top two corners, with a grab handle and full-width
    actions in the footer. Nothing to switch on - do not fight it with your own
    media query, and do not put a fixed height on `mw-modal`.
22. **Press states exist on every control**, because a finger never hovers.
    `mw-btn` and friends dip 1px and invert their highlight, `mw-btn-mini` and
    `mw-modal-close` scale down. If you build your own control, give it an
    `:active` - on touch it is the only feedback there is.
23. **Never set a height on a form control.** `mw-input`, `mw-select`,
    `mw-textarea` and `mw-btn` all take their minimum height from the control
    scale, so a field and the button next to it line up on their own. Pick the
    size step (`-sm` / nothing / `-lg`) and leave the height alone - a hand-set
    one puts that control back out of line with everything around it.
24. **Put the size modifier on the input group, not inside it.**
    `mw-input-group-sm` and `-lg` size the prefix, the suffix _and_ the field.
    Adding `mw-input-sm` inside as well is redundant, and mixing the two steps
    is what makes a group look broken.
25. **Loops keep their own timing, entrances go on the scale.** A spinner, a
    skeleton shimmer and a pulse ring are ambient - running them at 300ms would
    be frantic, and they are the one place a hand-written duration is right.
    Anything that plays once - a panel appearing, a card sliding in, a drawer -
    uses `var(--mw-duration-*)`.
26. **`transition: all` is out.** `var(--mw-transition)` lists paint-only
    properties on purpose. The one exception in the framework is the header
    burger, which morphs by animating `top` and `bottom`, and it says so in a
    comment. If your component really does need to animate a size, name that
    property - do not reach for `all`.
27. **A control is a `<button>`, never a styled `<div>`.** `mw-tabs-nav-item`,
    `mw-theme-toggle`, `mw-gallery-dot`, `mw-accordion-header` and `mw-menu-btn`
    are all written for one, and all five shipped as divs and spans - the first
    three until 4.11, the accordion header until 4.12, the burger after that -
    that no keyboard could reach. Each class clears what a `<button>` brings
    with it, so `<button type="button" class="mw-tabs-nav-item" data-tab="...">`
    is the whole markup. The burger is the worst of the five to get wrong:
    below the collapse breakpoint it is the only route to the navigation.
    If you build your own clickable thing: the element decides whether anyone
    without a mouse can use it, the class only decides how it looks.
28. **A link in running text is `mw-link`, not `mw-btn mw-btn-link`.** Since
    4.13.0 there is a class for exactly that. `mw-btn` is `inline-flex` with
    `min-height: var(--mw-control-height)`, so a link written that way pulls its
    own line up to 2.125rem while every line around it keeps the paragraph's
    height - in a footer disclaimer at `font-size: sm` that is nearly double,
    and it reads as a layout bug. `mw-p-0` is not the fix it looks like: the
    height does it, not the padding. `mw-link` is the same look without the
    control height and works on an `<a>` and a `<button>` alike.
    `mw-btn mw-btn-link` stays right where the link really is one of several
    buttons and has to line up with them - a card's actions, a button bar.
29. **`mw-parallax-sticky` goes on the section, not on the hero.** Sticky pins
    inside its parent, and the rule that lifts the page above the pinned picture
    reaches that content as a _sibling_. Put the class on the hero itself and
    nothing pins and nothing covers - no error, no effect, and the picture shows
    through every transparent section below. `mw-parallax` and the
    `mw-parallax-media` child stay where the image is: on the container. Same
    split for `mw-parallax-slow`, and `--mw-parallax-slow-travel` goes with the
    class on the section - on the inner block it never reaches the animation.
    That same sibling rule also puts an upward shadow on the one section
    directly after the block, so the overlap reads as a surface and not a cut.
    It sits at `:where()` weight, so a plain `box-shadow` of your own on that
    section replaces it.
30. **`viewport-fit=cover` belongs in the viewport meta.** The container
    gutter, the mobile nav panel and the modal padding all budget for the
    cutout with `env(safe-area-inset-*)`, and iOS resolves every one of those
    to `0` without it - on a notched phone the content then sits under the
    rounded corner. Nothing errors, which is why the shipped JS writes a
    console warning on localhost when the meta is missing.
31. **Half the layout reads its own width, not the viewport.** `mw-card`,
    `mw-tile`, `mw-stepper`, both timelines and - since 5.13.0 -
    `mw-gallery-container` and `mw-image-slider` are `@container` queries, so
    any of them in a half-width column takes its narrow layout there while the
    window is still a desktop. Two consequences: the query only reaches
    _descendants_, which is why the gallery wrapper around `mw-gallery`,
    `mw-gallery-desc` and `mw-gallery-dots` cannot be dropped; and
    `container-type: inline-size` computes the width as if the element were
    empty, so one dropped into a flex or grid slot needs a width - the
    framework sets `width: 100%` on its own containers already.
