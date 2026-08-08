# Theming, tokens & partial imports

## The model

Twelve colours are configured, everything else is derived from them **at
runtime** with `color-mix()`. Overriding a root token therefore retunes its
whole family - hover tone, translucent backgrounds, borders. That is the
difference to pre-3.4.0, where derived values were baked in at compile time and
a palette switch meant setting 41 variables.

```css
/* loaded after maverick-wave.min.css */
:root {
    --mw-primary-color: #0f766e; /* also retunes hover, backgrounds, border accent */
    --mw-secondary-color: #f39c12;

    --mw-success-color: #218838;
    --mw-warning-color: #d4a310;
    --mw-danger-color: #c82333;
    --mw-info-color: #17a2b8;

    --mw-gray-color: #565656;

    --mw-dark-page-background: #0b111a;
    --mw-dark-text-color: #d6dbdf;
    --mw-light-page-background: #d2d1e1;
    --mw-light-text-color: #1a1a1d;

    --mw-form-elements-background: #efefef;

    /* text on every solid coloured surface */
    --mw-accent-text-color: #ffffff;

    --mw-font-family-base: 'Inter', sans-serif;
}
```

## Which token for what

| Token                                                                                                                                                                              | Role                                                                                                                                             |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--mw-primary-color`                                                                                                                                                               | Brand colour: primary buttons, table headers, focus rings, active states                                                                         |
| `--mw-primary-color-hover`                                                                                                                                                         | Solid hover surface (derived: base + 18% black)                                                                                                  |
| `--mw-primary-background`                                                                                                                                                          | 20% tint - focus halo, scrollbar tracks                                                                                                          |
| `--mw-primary-background-hover`                                                                                                                                                    | 50% tint - row and list hover                                                                                                                    |
| `--mw-primary-info-background`                                                                                                                                                     | 70% tint - alert and info surfaces                                                                                                               |
| `--mw-border-accent`                                                                                                                                                               | Translucent accent **line**: panel rules, dividers, tab underlines                                                                               |
| `--mw-secondary-*`                                                                                                                                                                 | Same set for the second brand colour                                                                                                             |
| `--mw-success/warning/danger/info-color`                                                                                                                                           | Status colours, each with `-color-hover`, `-info-background`, `-info-background-hover`                                                           |
| `--mw-accent-text-color`                                                                                                                                                           | Text on any solid coloured surface (buttons, table/panel headers, badges, stepper dots)                                                          |
| `--mw-gray-color`                                                                                                                                                                  | Neutral foreground: muted icons, tooltips                                                                                                        |
| `--mw-gray-background`                                                                                                                                                             | Subtle neutral surface (20% alpha): zebra rows, disabled fields, tracks, skeletons                                                               |
| `--mw-overlay-background`                                                                                                                                                          | Heavy scrim (60%) behind modals and blocking spinners                                                                                            |
| `--mw-page-background`, `--mw-card-background`, `--mw-footer-background`, `--mw-border`, `--mw-shadow`, `--mw-text-color`, `--mw-text-muted-color`, `--mw-hero-overlay-background` | The **active theme** - aliases pointing at the `--mw-dark-*` or `--mw-light-*` set                                                               |
| `--mw-header-*`                                                                                                                                                                    | Header chrome: `background`, `text-color`, `navbar-list-color`, `navbar-list-active-color`, `burgerbutton-color`, `border` - dark in both themes |
| `--mw-form-elements-background`, `--mw-form-elements-color`                                                                                                                        | Form controls stay light in both themes and therefore have their own pair                                                                        |
| `--mw-font-family-base`, `-heading`, `-mono`                                                                                                                                       | Font stacks (default: system stacks - no font is bundled)                                                                                        |
| `--mw-hero-background`                                                                                                                                                             | Hero image (`url(...)`)                                                                                                                          |
| `--mw-transition`                                                                                                                                                                  | Global transition (`all 0.3s ease`)                                                                                                              |
| `--mw-card-img-height`                                                                                                                                                             | Per-card image height (default `210px`; `mw-card-lg`/`-xl` set it to 340px/480px)                                                                |
| `--mw-card-addon-color`                                                                                                                                                            | Background of `mw-card-badge` / `mw-card-ribbon`; the `mw-card-addon-*` classes set it, override it for a custom colour                          |
| `--mw-table-scroll-height`                                                                                                                                                         | Per-table height cap for `mw-table-responsive-scroll`                                                                                            |
| `--mw-kanban-background`, `--mw-kanban-lane-border`, `--mw-kanban-column-min-height`                                                                                               | Per-board surface, lane border and lane floor (120px, 90px on `mw-kanban-compact`)                                                               |
| `--mw-internal-theme-mode`                                                                                                                                                         | Read-only: what `$mw-theme-mode` was compiled to                                                                                                 |

Two rules that prevent most colour bugs:

1. **Surfaces are opaque, lines are translucent.** For a coloured surface use
   `--mw-*-color` / `--mw-*-color-hover`; for a rule or outline use
   `--mw-border-accent` or `--mw-border`.
2. **`--mw-text-muted-color` is only for text on theme surfaces** (cards, page
   background) - it follows the theme. On a colour surface that stays the same
   in both themes it is always wrong: use `--mw-accent-text-color`, or `opacity`
   for a disabled look.

## Light & dark

- Dark is the base. Light is applied by putting `mw-theme-light` on `<body>` -
  that class only re-points the theme aliases at the `--mw-light-*` set.
- Header, footer chrome and form controls deliberately stay dark/light
  respectively in both themes.
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
  $secondary-color: #f39c12,
  $success-color: #218838,
  $warning-color: #d4a310,
  $danger-color: #c82333,
  $info-color: #17a2b8,
  $gray-color: #565656,
  $dark-background: #0b111a,
  $dark-text-color: #d6dbdf,
  $light-background: #d2d1e1,
  $light-text-color: #1a1a1d,
  $form-elements-background: #efefef,
  $mw-hero-image: url('/assets/hero.jpg')
);
```

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

The full stylesheet is ~147 kB raw / ~22.5 kB gzipped. Marketing components
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

That set compiles to ~98 kB raw / ~15 kB gzipped - a third off the full build.

Details worth knowing:

- **Configuration has to come first.** `abstracts/variables` must be configured
  before any other module loads it, so the `with (...)` line goes at the top of
  the file. Configuring `main` instead pulls in everything again.
- `base` forwards `reset`, `base` and `typography`. If you already have your own
  reset, `@use '.../base/base'` gives you the `:root` block alone (~9 kB with a
  component or two).
- Module names are the file names without the leading underscore:
  `components/_buttons.scss` becomes `components/buttons`.
- Layer index files (`components`, `form-elements`, `layout`, `utilities`,
  `base`) pull in their whole layer - convenient for the small ones
  (`utilities`, `form-elements`), wasteful for `components`.
- Some components expect a sibling: `lists` styles checkbox rows and looks best
  with `form-elements/checkbox`; `tags` uses `mw-btn-mini` from `buttons` for
  its remove button.
