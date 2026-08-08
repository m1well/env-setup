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

| File                              | Content                                                                                                                |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `examples/angular-list-page.md`   | Full list/CRUD page: page header, meta counters, filter bar, table with status tags, empty state, delete modal, toasts |
| `examples/angular-form.md`        | Reactive form: `mw-field`, validation states, input groups, numeric input, toggles, form actions                       |
| `examples/angular-services.md`    | Theme service, toast service, modal/scroll-lock, tabs and accordion without `main.js`                                  |
| `examples/static-landing-page.md` | Plain HTML page: header, hero, sections, cards, tiles, accordion, footer, theme toggle                                 |

## Setup

### Plain HTML / CDN

```html
<link
        rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/maverick-wave@3.10.0/maverick-wave.min.css"
/>
<link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
/>
...
<script src="https://cdn.jsdelivr.net/npm/maverick-wave@3.10.0/maverick-wave.min.js"></script>
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

`--mw-font-family-base` defaults to `'Poppins', sans-serif`, but no font is
bundled. Load it yourself or override the token.

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

### State classes are not uniform - this is the single most common source of bugs

| Component                                                         | State class                         |
| ----------------------------------------------------------------- | ----------------------------------- |
| Accordion header + content                                        | `active` (no prefix)                |
| Tabs nav item + panel                                             | `active` (no prefix)                |
| Navbar link                                                       | `active` (no prefix)                |
| Timeline step (`mw-timeline-big-step`, `mw-timeline-simple-step`) | `active` (no prefix)                |
| Image slider overlay image + control button                       | `active` (no prefix)                |
| Button, pressed/selected look                                     | `active` (no prefix)                |
| Theme toggle                                                      | `active` (no prefix)                |
| Burger button + navbar drawer                                     | `open` (no prefix)                  |
| Gallery dot                                                       | `mw-active`                         |
| Stepper indicator / label / connector / step                      | `mw-active`, `mw-done`              |
| Checkbox list item (`li`)                                         | `mw-selected`                       |
| Kanban composer (open)                                            | `mw-active`                         |
| Kanban ticket being edited                                        | `mw-kanban-editing`                 |
| Modal overlay                                                     | `mw-modal-open`                     |
| Alert, after dismissal                                            | `mw-alert-closed` (`display: none`) |
| Field wrapper in error                                            | `mw-field-has-error`                |
| Single form control in error                                      | `mw-form-element-error`             |

Angular: `[class.active]="isOpen"` and `[class.mw-active]="i === current"` - the
binding target must match the table exactly.

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

## Component index

Everything below is documented in `references/components.md` unless marked otherwise.

**Actions** `mw-btn` (+ `primary`, `secondary`, `danger`, `success`, `outline`,
`link`, `link-muted`, `sm`, `lg`) · `mw-btn-mini` · `mw-button-bar`

**Containers** `mw-card` (+ `simple`, `lg`, `xl`, `stack`, badge, ribbon) ·
`mw-panel` · `mw-tile` · `mw-accordion` · `mw-tabs` · `mw-modal` ·
`mw-item-list` family

**Data & status** `mw-table` (+ `subtle`, `sticky-head`, `cards`, `compact`,
`hover`, responsive wrappers) · `mw-kanban` (+ `plain`, `compact`) · `mw-tag` /
`mw-tags` · `mw-info` / `mw-info-mini` / `mw-info-counter` · `mw-progress-bar` ·
`mw-rating` · `mw-meta-header` · `mw-stepper` · `mw-timeline-big` /
`mw-timeline-simple`

**Feedback** `mw-alert` · `mw-toast-stack` · `mw-empty-state` ·
`mw-spinner-border` / `mw-spinner-dots` / `mw-spinner-dual-ring` · `mw-skeleton`

**Navigation** `mw-header` + `mw-navbar` · `mw-breadcrumbs` · `mw-pagination` ·
`mw-section-nav` (`references/layout.md`)

**Media & content** `mw-avatar` (+ `initials`, `group`) · `mw-gallery` ·
`mw-image-slider` · `mw-blog-post` · `mw-code-block` / `mw-terminal` ·
`mw-techstack-bucket` · `mw-coming-soon` · `mw-divider` · `mw-list` family

**Forms** (`references/forms.md`) `mw-field` · `mw-input` · `mw-select` ·
`mw-textarea` · `mw-checkbox` · `mw-radio` · `mw-toggle` · `mw-slider` ·
`mw-input-group` · `mw-form` / `mw-form-group` / `mw-form-actions` · `mw-login`

**Layout** (`references/layout.md`) `mw-main` · `mw-container` · `mw-content` ·
`mw-section` · `mw-page-header` · `mw-grid-*` · `mw-hero` · `mw-footer`

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
   `--mw-accent-text-color` there, and `opacity` for disabled states.
   `--mw-accent-text-color` is the text on a **brand** surface, so overriding it
   for a light primary makes it dark everywhere it is used. The fixed grey
   surfaces - tooltip, `mw-btn-mini`, `mw-info-mini`, gallery arrows - therefore
   hardcode white and ignore the token.
8. **`mw-card` already lifts on hover** and `mw-btn` already has `inline-flex`
   plus a gap for icons. Neither has a modifier class for it - adding one from
   memory produces markup that does nothing.
9. **Overriding one root colour is enough.** Hover tones, translucent
   backgrounds and borders are derived with `color-mix()` at runtime. Setting
   `--mw-primary-color-hover` by hand is usually a sign the base token was not
   set.
10. **Browser floor: `color-mix()`** - Chrome 111+, Safari 16.2+, Firefox 113+.
    Older browsers get no colours at all, not merely worse ones.
11. **A component host between a container and its children breaks the layout,
    silently.** Every `mw-*` flex or grid container styles its _children_ -
    `mw-grid-*`, `mw-tags`, `mw-button-bar`, `mw-form-actions`, `mw-modal-footer`,
    `mw-toast-stack`. In plain HTML the children are right there; in a SPA a
    component host often sits in between and becomes the item instead, so it
    shrinks to content width or swallows a whole grid row. Put `mw-d-contents` on
    that host - it then generates no box and the children take the item role
    back. Angular: `host: { class: 'mw-d-contents' }`. `mw-header` handles this
    case on its own, the others do not.
