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

| File                       | Content                                                                                                          |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `references/layout.md`     | Page skeleton, grid, container, section, page header, header/navbar, footer, spacing/flex/display/text utilities |
| `references/components.md` | Every component: markup, variants, sizes, state classes                                                          |
| `references/forms.md`      | Inputs, select, textarea, checkbox, radio, toggle, slider, input group, `mw-field` pattern, validation           |
| `references/theming.md`    | Token model, `color-mix` derivation, light/dark, SCSS configuration, cherry-picking single components            |
| `references/javascript.md` | What the shipped `main.js` does, why SPAs must not load it, what to implement instead                            |

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
<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/maverick-wave@4.25.0/maverick-wave.min.css"
/>
<link
  rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
/>
...
<script src="https://cdn.jsdelivr.net/npm/maverick-wave@4.25.0/maverick-wave.min.js"></script>
```

Pin the version. The JS file is optional and only for server-rendered/static pages -
see below.

### Angular (or any SPA)

```jsonc
// angular.json
"styles": ["src/assets/maverick-wave.min.css", "src/styles.scss"]
// no "scripts" entry - see the warning below
```

Or from the npm package via SCSS: `@use 'maverick-wave/src/scss/main';`
(details and configuration in `references/theming.md`).

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

| Component                                    | State class                         |
| -------------------------------------------- | ----------------------------------- |
| Anything switchable, "on"                    | `mw-active` (`active` deprecated)   |
| Burger button + navbar drawer                | `open` (no prefix)                  |
| Stepper indicator / label / connector / step | `mw-active`, `mw-done`              |
| Checkbox list item (`li`)                    | `mw-selected`                       |
| Calendar day, picked                         | `mw-selected`                       |
| Kanban ticket being edited                   | `mw-kanban-editing`                 |
| Modal overlay                                | `mw-modal-open`                     |
| Alert, after dismissal                       | `mw-alert-closed` (`display: none`) |
| Field wrapper in error                       | `mw-field-has-error`                |
| Single form control in error                 | `mw-form-element-error`             |

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
`5xl` 3, `6xl` 4.3 rem.

**Breakpoints** (max-width, mobile-first markup / desktop-first media queries):
`xs` 375, `sm` 576, `md` 768, `lg` 992, `xl` 1200, `2xl` 1400 px.

**Radius** (`mw-radius-none|xs|sm|md|lg|xl|2xl|full`): 0, 2, 5, 10, 15, 20, 30 px, 50%.

**The surface signature.** Every panel-like component - card, panel, modal,
accordion, tile, calendar, pagination, login box - shares one silhouette: sharp
5px corners on the top-left/bottom-right diagonal, round 20px ones on the other,
plus a 2px **corner accent** in the primary tone (`--mw-corner-accent`) sitting
on the two round corners. It is not a class and not opt-in; the components carry
it. `mw-corner-plain` drops the accent on a box too small to hold it - see
`references/layout.md`.

**Elevation** (`mw-elevation-0` … `-5`, and `var(--mw-elevation-N)` inside SCSS).
Two shadows per level - a tight contact layer plus a wide ambient one:
`1` resting (inputs, tags), `2` raised (cards, panels at rest), `3` floating
(a card under the pointer), `4` overlay (dropdown, popover, drawer), `5` modal.
`0` is explicitly flat. Never write a `box-shadow` by hand - the twelve one-off
values that used to exist are exactly what this replaced.

**Motion** `--mw-duration-instant|fast|base|slow|slower` = 110/180/300/520/900ms
plus `--mw-duration-zoom` (650ms, for a large surface actually travelling),
`--mw-ease-out` (things arriving - the default), `--mw-ease-in-out` (A to B and
back), `--mw-ease-spring` (a pop). Two ready-made transitions:
`var(--mw-transition)` for hover and focus states, `var(--mw-transition-fast)`
for anything that should feel instant under the pointer. Both list their
properties explicitly rather than saying `all`.

**Control sizes** `--mw-control-height-sm|base|lg` = 2 / 2.25 / 2.5rem (an even
32 / 36 / 40px step) and
`--mw-control-font-sm|base|lg` = 0.8 / 0.9 / 1rem, shared by `mw-input`,
`mw-select`, `mw-textarea` and `mw-btn`. A field and the button beside it are
the same height by construction. Buttons run one font step above the fields.

**Focus** `--mw-focus-ring-width` 2px, `--mw-focus-ring-offset` 2px,
`--mw-focus-ring-color`, plus `--mw-focus-halo-size` 3px /
`--mw-focus-halo-opacity` 28% for the soft ring a form field gets instead of a
hard outline. SCSS: `@include focus-ring`, `focus-ring-inset`, `field-focus`.

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
`mw-item-list` family · `mw-offer` (+ `-head`, `-name`)

**Pricing** `mw-price` (+ `-amount`, `-fraction`, `-currency`, `-original`,
`-period`, `-word`, `-note`, `sm`/`lg`, `inline`, `center`, `plain`)

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

**Navigation** `mw-header` + `mw-navbar` · `mw-breadcrumbs` · `mw-pagination` ·
`mw-dropdown` (+ `-menu`, `-item`, `-item-danger`, `-divider`, `-label`,
`-caret`, `-end`, `-up`) · `mw-section-nav` (`references/layout.md`)

**Media & content** `mw-avatar` (+ `initials`, `group`) · `mw-gallery` ·
`mw-image-slider` · `mw-blog-post` · `mw-testimonial` (+ `-source`, `-detail`,
`-date`, `-featured`) · `mw-prose` · `mw-media` (+ `-caption`) · `mw-code-block` /
`mw-terminal` · `mw-techstack-bucket` · `mw-coming-soon` · `mw-divider` ·
`mw-kbd` · `mw-list` family

**Forms** (`references/forms.md`) `mw-field` · `mw-input` · `mw-select` ·
`mw-textarea` · `mw-checkbox` · `mw-radio` · `mw-toggle` · `mw-slider` ·
`mw-input-group` · `mw-prefilled` · `mw-form` / `mw-form-group` /
`mw-form-actions` · `mw-login`

**Layout** (`references/layout.md`) `mw-main` · `mw-container` · `mw-content` ·
`mw-section` (+ `mw-section-intro`) · `mw-page-header` · `mw-grid-*` ·
`mw-columns-2/3` · `mw-row-split` · `mw-hero` (+ `mw-scroll-hint`, `-end`) · `mw-footer`

**Utilities** (`references/layout.md`) `mw-sr-only` / `mw-sr-only-focusable` /
`mw-skip-link` · `mw-row-split` (+ `center`) · `mw-text-numeric` /
`mw-text-currency` · `mw-text-truncate` / `mw-text-clamp-2..5` /
`mw-text-break` / `mw-text-nowrap` · `mw-text-balance` / `mw-text-pretty` /
`mw-text-eyebrow` / `mw-text-measure` · `mw-elevation-0..5` ·
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
    via a pseudo-element. Nothing to switch on, and no reason to write the media
    query again in an app.
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
17. **An open dropdown is clipped by anything that hides its overflow.** The menu
    is absolutely positioned. The framework's own containers - panel, card, tile,
    modal body, responsive table - lift the clip while a menu is open. On your
    own container it is one line:
    `:has(.mw-dropdown[open]) { overflow: visible }`.
18. **Never write `box-shadow` by hand.** Use `var(--mw-elevation-1..5)` or the
    `mw-elevation-*` class. A hand-rolled shadow is the wrong colour in one of
    the two themes - the dark theme's shadow is a light rim over a dark contact
    layer, not a black blur.
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
    `mw-theme-toggle`, `mw-gallery-dot` and `mw-accordion-header` are all
    written for one, and all four shipped as divs and spans - the first three
    until 4.11, the accordion header until 4.12 - that no keyboard could reach.
    Each class clears what a `<button>` brings with it, so
    `<button type="button" class="mw-tabs-nav-item" data-tab="...">` is the
    whole markup. If you build your own clickable thing: the element decides
    whether anyone without a mouse can use it, the class only decides how it
    looks.
28. **A link in running text is `mw-link`, not `mw-btn mw-btn-link`.** Since
    4.13.0 there is a class for exactly that. `mw-btn` is `inline-flex` with
    `min-height: var(--mw-control-height)`, so a link written that way pulls its
    own line up to 2.25rem while every line around it keeps the paragraph's
    height - in a footer disclaimer at `font-size: sm` that is nearly double,
    and it reads as a layout bug. `mw-p-0` is not the fix it looks like: the
    height does it, not the padding. `mw-link` is the same look without the
    control height and works on an `<a>` and a `<button>` alike.
    `mw-btn mw-btn-link` stays right where the link really is one of several
    buttons and has to line up with them - a card's actions, a button bar.
