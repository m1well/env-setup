# Layout & utilities

## Page skeleton

```html
<body>
  <header class="mw-header">
    <div class="mw-container"><!-- logo + actions --></div>
  </header>

  <main class="mw-main">
    <section id="overview" class="mw-section">
      <div class="mw-container">...</div>
    </section>
    <section id="details" class="mw-section mw-section-alternate">
      <div class="mw-container">...</div>
    </section>
  </main>

  <footer class="mw-footer">
    <div class="mw-container">...</div>
  </footer>
</body>
```

- `mw-main` is a full-height flex column - the footer stays at the bottom on
  short pages.
- `mw-container` is `min(1200px, 100% - 2 * gutter)`, horizontally centered.
  Nest it inside every full-bleed band (header, section, footer), never around
  them. The gutter is fluid - `clamp(1rem, 4.2vw + 0.5rem, 4rem)`, never smaller
  than the safe-area inset (which needs `viewport-fit=cover` on the viewport
  meta to be anything but 0) - so it lands on ~24px at 375px, ~32px at 576px,
  ~40px on a tablet and tops out at 64px, where the 1200px cap takes over. A
  percentage alone keeps too little on a phone and throws away too much on a
  desktop; stepping the gutter at a breakpoint instead would make the container
  jump backwards at the step. Both values are tokens,
  `--mw-container-gutter` and `--mw-container-width`.
- `mw-container-narrow` sits **inside** a `mw-container` and gives the content
  80% of it, back to 90% below `lg` and the full width below `md`. For a column
  of full-width cards, where a 1200px line leaves more empty card than content.
  It centers itself; put nothing else in it that has to line up with the
  headings outside.
- `mw-content` (`flex: 1` + top padding) is the alternative to `mw-section` when
  a page has one single content area. `mw-content-centered` centers it
  vertically over the full viewport - login pages, error pages.
- `<section>` has **no** padding of its own. Always add `mw-section`.

In an Angular app the shell above lives in `app.component.html` and the router
outlet goes inside the `mw-container`:

```html
<main class="mw-main">
  <section class="mw-section">
    <div class="mw-container"><router-outlet /></div>
  </section>
</main>
```

## Header & navigation

The header is fixed, dark in both themes, and expects exactly this structure -
its children are styled through descendant selectors:

```html
<header class="mw-header">
  <div class="mw-container">
    <div class="mw-logo">
      <a href="#start"><img src="logo.svg" alt="Logo" /></a>
    </div>

    <div class="mw-header-actions">
      <nav class="mw-navbar mw-navbar-medium" id="main-nav">
        <ul class="mw-navbar-list">
          <li class="mw-navbar-item">
            <a href="#start" class="mw-navbar-link mw-active">Start</a>
          </li>
          <li class="mw-navbar-item">
            <a href="#docs" class="mw-navbar-link">Docs</a>
          </li>
        </ul>
      </nav>

      <button
        type="button"
        class="mw-theme-toggle mw-ml-5"
        aria-label="Toggle light and dark theme"
      >
        <div class="mw-theme-toggle-slider">
          <div class="mw-theme-toggle-icon"><i class="fas fa-moon"></i></div>
        </div>
      </button>

      <button class="mw-login-btn" type="button" aria-label="Log in">
        <i class="fas fa-lock"></i>
      </button>

      <button
        type="button"
        class="mw-menu-btn"
        aria-label="Menu"
        aria-expanded="false"
        aria-controls="main-nav"
      >
        <span class="mw-menu-btn-burger"></span>
      </button>
    </div>
  </div>
</header>
```

- **Collapse breakpoint follows the item count**: default (1-3 items) collapses
  at `md`, `mw-navbar-medium` (4-5) at `lg`, `mw-navbar-large` (6+) at `xl`.
  Pick the class by how many links you have.
- Below the breakpoint the list becomes a panel under the bar, full width, and
  `mw-menu-btn` appears. Opening it means `open` on **both** `mw-menu-btn` and
  `mw-navbar`, `mw-nav-open` on the `<body>`, and `aria-expanded` on the button -
  below the breakpoint it is the only route to the navigation, so it has to be a
  real `<button>`, not a `<div>`.
- `mw-nav-open` is the state the scrim, the scroll lock and the rules that hold
  the bar and the burger in place all key off. A class the script sets, not
  `:has(.mw-navbar.open)`: the burger is the control that closes the panel, and
  it cannot wait for a selector that has to re-match the document from a class
  change several levels down. Forget it and the panel opens without a scrim, the
  page behind it still scrolls, and on a `mw-header-reveal` bar the burger sits a
  header height below the panel it belongs to.
- The rows stack and run the full width of the panel. From `sm` they turn into a
  wrapping row of pills, so a wide screen below the collapse breakpoint does not
  get a tall band with four links in its left corner.
- The active link carries `mw-active` (bare `active` still works but is
  deprecated).
- `mw-profile-btn` is the signed-in pill, next to or instead of the login button:

```html
<button class="mw-profile-btn" type="button">
  <span class="mw-avatar mw-avatar-initials mw-avatar-xs">MW</span>
  <span class="mw-profile-btn-name">Michael</span>
</button>
```

An icon (`<i class="fas fa-user-circle"></i>`) works instead of the avatar.
Below `md` the name hides and the button becomes a round 40px control, the
same height as the login and burger buttons.

- Header colours have their own tokens (`--mw-header-background`,
  `--mw-header-text-color`, `--mw-header-navbar-list-color`,
  `--mw-header-navbar-list-active-color`, `--mw-header-burgerbutton-color`,
  `--mw-header-border`) so the chrome can be retuned without touching the brand
  palette. All of them derive from `--mw-primary-color`, not from a theme
  colour: the bar is dark in both themes and a light-only project must not have
  to configure dark-theme values to change it. The bar itself is the primary
  darkened toward black, `$header-surface` (14%) - see `theming.md`.

**Reveal on scroll.** `mw-header-reveal` keeps the bar above the screen and
rides it in over the first 420px of scroll - for a page that opens on a
full-bleed hero and wants nothing on top of it. It animates `top` and not a
transform, because a transform on the header would make it the containing block
for anything fixed inside it, at every value including the resting one.
A fixed `mw-announcement` rides along without a class of its own - both cover
the height of the pair, so they arrive as one block rather than the ribbon
catching up. Focus inside either brings both back regardless of the scroll
position, so tabbing never lands on a link that is off screen (WCAG 2.4.11).
Under `prefers-reduced-motion` the bar is simply there, and so it is without
scroll timelines unless `maverick-wave.min.js` is on the page - in Firefox that
is what rides it in (`javascript.md`).

**Something that stays.** `mw-header-keep` on a control inside the bar - the
login button, the burger - holds it in place while the bar rides in behind it:
it travels the bar's own distance the other way, so it waits at the exact
position it will hold in the arrived bar and nothing jumps at the end. On a
narrow screen that is what puts the burger on the hero before the bar exists.
Opening the panel brings the bar in with it and parks the keep controls back on
their own positions - the panel hangs off the bar, and the burger is the X the
moment the panel is out, so it has to sit where the burger sat. One consequence:
the bar loses its fade as soon as one of these is on it, since a group's opacity
cannot be taken back by a child.

```html
<button class="mw-login-btn mw-header-keep" type="button">
  <i class="fas fa-lock"></i>
</button>
```

- Focus on a keep control leaves the bar where it is. The rescue that pulls it
  back (WCAG 2.4.11) is for what hides behind it - a control in front of it is
  on screen already, and without the exception a click on the theme toggle would
  haul in the whole header. Tabbing to anything else in the bar still brings it.
- While it floats it carries a ring and a soft shadow, so a dark control still
  reads on a dark picture; both are gone once the bar is there. That occupies
  `box-shadow`, so a keep element cannot bring a shadow of its own.

**Localhost indicator.** Put `mw-localhost-indicator-activated` on the header
and the shipped JS prepends a pulsing bar when the host is localhost/127.0.0.1/
192.168.\*. In a SPA, reimplement it: add a `<div class="mw-localhost-indicator-pulse">`
as the header's first child under the same condition.

## Footer

```html
<footer class="mw-footer">
  <div class="mw-container">
    <div class="mw-footer-top">
      <div class="mw-footer-column">
        <h3>Product</h3>
        <p>...</p>
      </div>
      <div class="mw-footer-column">
        <h3>Links</h3>
        <ul>
          <li><a href="#">Docs</a></li>
        </ul>
      </div>
    </div>

    <div class="mw-social-links">
      <a href="#" data-tooltip="GitHub"><i class="fab fa-github"></i></a>
    </div>

    <p class="mw-disclaimer">Long-form text under the columns.</p>
    <p class="mw-copyright">&copy; 2026 Example</p>
    <p class="mw-last-updated">Last updated: 2026-08-04</p>
  </div>
</footer>
```

`data-tooltip="..."` is a global attribute hook, not a class - it works on any
element and shows a tooltip above it on hover or keyboard focus. It is pure CSS
(a pseudo element on the trigger), which also means anything that clips its
overflow cuts it off: a scroll container, a tile, or a card carrying a ribbon -
plain cards do not clip.

Three classes steer where it lands, and they combine: `mw-tooltip-below` puts it
under the trigger instead of over it - for a control in a fixed header, where
above is off the screen - and `mw-tooltip-end` / `mw-tooltip-start` line the
bubble up with that edge of the trigger instead of centring it, which is what
keeps a tooltip on an outermost element inside the viewport. The arrow keeps
pointing at the trigger in every combination.

## Sections

| Class                               | Use                                                                                                                                                                                             |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mw-section`                        | Vertical rhythm for a page band - `--mw-section-padding-block`, 3.3rem (2.5rem below `md`, 1.75rem below `sm`); point it at `--mw-section-padding-fluid` for spacing that grows with the screen |
| `mw-section-alternate`              | Diagonal pattern background; combine with `mw-section`                                                                                                                                          |
| `mw-section-title`                  | Centered heading with a decorative primary underline, `2xl` growing to `3xl` up to 576px - landing pages                                                                                        |
| `mw-section-intro`                  | The lead paragraph under a section title - centred, muted, 46rem measure                                                                                                                        |
| `mw-section-subtitle`               | Centered heading with a thin secondary underline, `xl` growing to `2xl` up to 576px                                                                                                             |
| `mw-section-nav` + `mw-section-btn` | Sticky single-row strip of outline-style jump links; parks under the header and scrolls sideways when it overflows                                                                              |

```html
<section class="mw-section mw-section-alternate">
  <div class="mw-container">
    <h2 class="mw-section-title">Components</h2>
    <nav class="mw-section-nav">
      <a href="#buttons" class="mw-section-btn"
        ><i class="fas fa-hand-pointer"></i> Buttons</a
      >
      <a href="#cards" class="mw-section-btn"
        ><i class="fas fa-square"></i> Cards</a
      >
    </nav>
  </div>
</section>
```

The strip sticks at `--mw-header-height` and is `--mw-section-nav-height` tall
(3.7rem). Anything it can cover on a jump needs the sum as `scroll-margin-top`;
a block wrapping a `mw-section-subtitle` gets that from the framework already.

## Page header

The application counterpart to `mw-section-title`: title and subtitle left,
actions right, wrapping when it gets tight. Below `sm` the actions take the full
width.

```html
<header class="mw-page-header">
  <div>
    <h2>Invoices</h2>
    <p>14 entries &middot; 3 drafts</p>
  </div>
  <div class="mw-page-header-actions">
    <button type="button" class="mw-btn mw-btn-outline mw-btn-sm">
      <i class="fas fa-filter"></i> Filter
    </button>
    <button type="button" class="mw-btn mw-btn-primary mw-btn-sm">
      <i class="fas fa-plus"></i> New
    </button>
  </div>
</header>
```

- `h1`-`h3` inside are normalised to `2xl` (`xl` below `sm`), `p` becomes muted
  and small - no extra classes needed.
- `mw-meta-header` fits under the title instead of the `<p>` (see
  `references/components.md`).
- `mw-page-header-plain` removes the bottom rule.

## Hero

```html
<div class="mw-container">
  <div class="mw-hero">
    <div class="mw-home mw-home-content-fade">
      <div class="mw-home-text">
        <h1>Product<span class="mw-text-primary">Name</span></h1>
        <p>Subline</p>
      </div>
      <div class="mw-d-flex mw-gap-8 mw-justify-center mw-mb-7">
        <button class="mw-btn mw-btn-primary mw-btn-lg">Get started</button>
      </div>
    </div>
  </div>
</div>
```

A `mw-container` that contains a `mw-hero` switches to full-bleed, full-height
mode with the background image from `--mw-hero-background`.
`mw-home-content-fade` fades the content in.

The image is treated per theme through `--mw-hero-image-filter` - a filter, not
a tinted overlay: `$hero-filter-dark` (`brightness(0.7)`) against
`$hero-filter-light` (`brightness(1.1)`). A translucent layer can
only darken toward its own colour, so on an already dark photo both themes look
the same until the alpha is high enough that the tint colour is what you see.
Moving the image's brightness reads as a difference even on a dark photo, and
keeps it dark enough for the fixed light ink either way. Any filter list works.

It is applied with `backdrop-filter` on a pseudo element, so the content in
front of the image stays unfiltered.

The ink on that image comes from `--mw-hero-text-color` and does **not** follow
the theme, because the photo does not either - a theme-bound colour would go
dark over an unchanged dark image the moment the light theme is on. It defaults
to the light end of the palette; for a bright photo set it per page:

```css
.hero-page {
  --mw-hero-text-color: var(--mw-light-text-color);
}
```

Components that paint their own surface (`mw-card`, `mw-panel`, `mw-modal`,
`mw-tile`, `mw-calendar`) are exempt and keep the theme's ink - a card in the
hero is still a card.

`mw-btn-outline` is exempt the other way round: inside the hero it takes the
hero's ink plus a dark scrim and a blur, because its usual border and label are
tuned for the page background and go quiet over a photograph. A second call to
action next to `mw-btn-primary` therefore looks different here than it does
further down the page - that is deliberate, not a stray override.

**Scroll cue** - `mw-scroll-hint` is the "scroll down" cue on the lower edge of
the hero. An `<a>` that is a sibling of `mw-hero`, directly in the container:

```html
<div class="mw-container">
  <div class="mw-hero">...</div>
  <a class="mw-scroll-hint" href="#features">
    More <i class="fas fa-chevron-down"></i>
  </a>
</div>
```

It is taken out of the flow, and the hero keeps a strip at its bottom free for
it, so buttons under the hero text never land on top of the cue.
`mw-scroll-hint-end` puts it in the bottom right corner instead - for a hero
whose text is not centred either - and gives the hero its full height back.
Below `md` both variants sit in the corner, because the middle under the text
is taken on a phone. The bobbing stops under `prefers-reduced-motion`.

**Parallax** - `mw-parallax` on the container plus a `mw-parallax-media` child
moves the picture into its own layer. The container drops its own background and
the layer reads `--mw-hero-background`, so the image stays configured in one
place. Every mode runs on the browser's scroll timeline, and on no
`background-attachment: fixed`, which iOS ignores. Older Safari and Firefox have
no timelines; there the shipped JS moves the layers instead, and without it the
picture simply sits still (`javascript.md`).

```html
<header class="mw-header mw-header-reveal">...</header>

<main class="mw-main">
  <section class="mw-section mw-parallax-sticky mw-parallax-rise">
    <div class="mw-container mw-parallax">
      <div class="mw-parallax-media"></div>
      <div class="mw-parallax-media mw-parallax-pattern"></div>
      <div class="mw-hero">...</div>
    </div>
  </section>
  <section class="mw-section">...</section>
</main>
```

On its own, `mw-parallax` drifts the picture against the scroll by
`--mw-parallax-depth` (`10vh`) - the layer overhangs the block by that much top
and bottom, so no edge is ever uncovered.

`mw-parallax-sticky` pins the block to the top of the screen and lets the page
ride up over it. It goes on the element the page content is a **sibling** of -
the section, not the hero - because everything after it is given
`--mw-page-background` and a layer above, or the pinned picture shows through
the transparent ones. The one section directly after it also gets an upward
shadow, so the overlap reads as a surface sliding over the picture instead of a
cut. Fixed values, not the elevation ramp - the shadow falls on the picture
rather than on a theme surface, and the light theme's near layer is cut for
paper and disappears there. It sits at `:where()` weight, so a plain rule of
your own overrides it. Depth drops to `0` there: a pinned block does not travel
through the viewport, so its `view()` timeline stands still with it.
`mw-parallax-rise` puts it at `12vh` and runs the layer on the document's own
scroll instead - the picture lifts, the text stays put. That works out to the
same travel per scrolled pixel as a drifting band at `20vh`, which is measured
over a much longer range. It is a hero move only: the range is the first screen
of document scroll, so further down a page the picture holds still. Several
pinned blocks on one page are fine, each takes over from the one before.

A second `mw-parallax-media` carrying `mw-parallax-pattern` puts a pattern over
the picture. It travels a third of the distance the layer below it does, and
that difference between the two is what reads as depth - one layer alone only
slides. It matters most over a gradient: the travel is vertical, so only an edge
across it - a rule, a grid, a hatch - ever shows the movement, and a gradient
has none. In a hero the layer reads `$mw-hero-pattern`, the way the picture
reads `$mw-hero-image`; anywhere else set `--mw-parallax-pattern-image` on it.
`--mw-parallax-pattern-depth` is the dial, `4vh` next to a risen hero.

Outside a hero the same classes build a standalone band: `mw-parallax`
(`min-height: 60vh`), `mw-parallax-media` as an `<img>` or a div with a
background image, `mw-parallax-content` for what sits on top, and
`mw-parallax-dimmed` to turn the picture down and the text light. Drop the
`mw-container` between section and block and the picture runs full width, with
a `mw-container` inside `mw-parallax-content` around the text instead.

`mw-parallax-slow` is the third mode and the one for a band mid-page: the block
keeps its place in the flow and travels slower than the page, so picture and
text are still moving while the next section closes in from below. Pinning is
the same move with the tempo at zero. `--mw-parallax-slow-travel` (`45vh`) reads
against the block's own height - half the height is half speed, the full height
stands still, past it the block runs backwards. The dial belongs on the element
carrying `mw-parallax-slow`, the height on the `mw-parallax` block inside it;
put the dial on the inner block and it never reaches the animation. Everything
after it gets the same page background and layer that a pinned block gives its
siblings, and the section directly after it the same edge shadow.

Without scroll timelines, or under `prefers-reduced-motion`, the picture stands
still and nothing else changes.

## Grid

All grid classes are `display: grid` with a preset gap (`mw-gap-*` overrides
it). They handle their own column count - no responsive suffixes to manage. One
column is the base and each breakpoint adds to it, so a phone renders them
without evaluating a single media query; the table below reads the same either
way.

| Class             | Columns                                         | Collapses                    |
| ----------------- | ----------------------------------------------- | ---------------------------- |
| `mw-grid-1`       | 1                                               | - (children forced to 100%)  |
| `mw-grid-2`       | 2                                               | 1 below `sm`                 |
| `mw-grid-3`       | 3                                               | 2 below `md`, 1 below `sm`   |
| `mw-grid-4`       | 4                                               | 2 below `lg`, 1 below `sm`   |
| `mw-grid-5`       | 5                                               | 4 / 3 / 2 / 1 down the scale |
| `mw-grid-auto`    | `auto-fill`, min 300px                          | automatic                    |
| `mw-grid-auto-sm` | min 250px                                       | automatic                    |
| `mw-grid-auto-md` | min 350px                                       | automatic                    |
| `mw-grid-flex`    | 12 columns + `mw-col-span-1` … `mw-col-span-12` | single column below `md`     |
| `mw-grid`         | no template, just grid + gap                    | -                            |

`mw-grid-even` is a modifier, not a grid - add it to one of the above and every
row becomes as tall as the tallest instead of as tall as its own contents. For a
column of cards that should end on one line even when one of them carries an
extra sentence.

Every one of them has a `-lg` twin with a wider gap (2.5rem instead of 1.35rem):
`mw-grid-2-lg`, `mw-grid-3-lg`, `mw-grid-4-lg`, `mw-grid-5-lg`, `mw-grid-1-lg`,
`mw-grid-auto-lg`, `mw-grid-flex-lg`, `mw-grid-lg`.

```html
<div class="mw-grid-flex">
  <aside class="mw-col-span-4">Sidebar</aside>
  <div class="mw-col-span-8">Content</div>
</div>
```

**Stacks** - single column, differing horizontal alignment of the children:

| Class                                         | Children                                |
| --------------------------------------------- | --------------------------------------- |
| `mw-grid-stack`                               | natural width, left aligned             |
| `mw-grid-stack-center`                        | centered                                |
| `mw-grid-stack-end`                           | right aligned                           |
| `mw-grid-stack-stretch`                       | full width (same result as `mw-grid-1`) |
| `mw-grid-stack-lg`, `mw-grid-stack-center-lg` | wide-gap twins                          |

**Masonry columns** - `mw-columns-2` and `mw-columns-3`, for cards of unequal
height where a row grid tears a gap under every short one. CSS multi-column:
the children flow into columns and close up, the count steps down with the
viewport (3 → 2 below `lg`, → 1 below `sm`), and every child keeps
`break-inside: avoid` so a break never lands mid-card. Reading order runs top
to bottom, then across - right for testimonials and galleries, wrong for
anything ranked or chronological.

```html
<div class="mw-columns-3">
  <figure class="mw-testimonial">...</figure>
  <figure class="mw-testimonial">...</figure>
</div>
```

## Utilities

**Spacing** - margin `mw-m-*`, `mw-mt-*`, `mw-mb-*`, `mw-ml-*`, `mw-mr-*`,
`mw-mx-*`, `mw-my-*`; padding `mw-p-*`, `mw-pt-*`, `mw-pb-*`, `mw-pl-*`,
`mw-pr-*`, `mw-px-*`, `mw-py-*`; `mw-gap-*`. Keys `0`-`14`, plus negative keys
`1`-`6` for margins only (`mw-mt--3`). Gap shrinks to 75% below `sm`
automatically.

**Display** - `mw-d-flex`, `mw-d-inline-flex`, `mw-d-block`, `mw-d-inline`,
`mw-d-inline-block`, `mw-d-grid`, `mw-d-none`, `mw-d-contents`.

**Responsive display** - `mw-d-{sm|md|lg|xl}-{none|block|flex|inline-flex|grid|inline-block}`.
Mobile-first like everything else here: `mw-d-md-flex` means
"flex from the md breakpoint up", and the unprefixed class beside it is what
applies below that. The pair `mw-d-none mw-d-md-flex` is hidden on a phone and a
row from a tablet on. `mw-hide-mobile` (gone below md) and `mw-hide-desktop`
(gone from md up) spell out the two everyone actually reaches for.

**Text overflow** - `mw-text-truncate` is one line ending in an ellipsis and
carries `min-width: 0` with it, which is the reason truncation "does not work"
nine times out of ten inside a flex row. `mw-text-clamp-2` through `-5` is that
many lines ending in one. `mw-text-break` is for a string with nothing to break
at - a URL, a hash, an API key - and is what keeps a phone page from scrolling
sideways. `mw-text-nowrap` is the opposite.

**Wrapping and measure** - `mw-text-balance` evens out the lines of a short
block so a headline never leaves one word alone (headings get it already);
`mw-text-pretty` only prevents the orphan and is the one for body copy
(paragraphs get it already). `mw-text-measure` caps a column at 68 characters -
past roughly 75 the eye loses the start of the next line on the way back.
`mw-text-eyebrow` is the small spaced upper-case kicker above a heading.
`mw-text-uppercase` carries the letter-spacing capitals need to stay legible
with it; `mw-text-capitalize` is the plain transform.

**Elevation** - `mw-elevation-0` through `-5`, the same ramp every component
uses. See the scale table in `SKILL.md`. Never hand-roll a `box-shadow`.

**Glow** - `mw-glow` plus
`mw-glow-{primary,secondary,info,success,warning,danger}`. Elevation without the
offset, so the surface gives off the light instead of casting it. Once per
screen at most.

**Scroll entrance** - `mw-reveal` lets a block rise briefly as it scrolls into
view, driven by the browser's scroll timeline (`animation-timeline: view()`).
The block stays hidden while it is still below the bottom edge and has arrived
three fifths of the way in - measured along its own entry, so it is never still
transparent once it stands in its place, whatever its height. A block taller
than the screen is capped at one viewport by the entry phase itself. Doubly guarded:
`prefers-reduced-motion` turns it off, and a browser without scroll timelines
renders the block in place instead of leaving it invisible. Firefox is that
browser - there the shipped JS runs the entrance off an `IntersectionObserver`,
so a page without the script keeps the block and loses only the motion
(`javascript.md`). Put it on section content, not on the section itself - a
screen-high band finishes its entrance before its content is halfway up.

A row of cards crosses the viewport edge together, so `mw-reveal` on each of
them rises as one slab. `mw-reveal-stagger` goes on the **grid** instead: every
child reveals, and each one in a row a tenth of that entry after the one
before it - a wave across the row. One class, nothing per card. On `mw-grid-2` to `mw-grid-5` and
their `-lg` variants the wave follows the actual columns at every breakpoint:
four steps in a four-column row, two once it has collapsed to two. Any other
container - `mw-columns-*`, a layout of your own - gets a fixed cycle of three.

```html
<div class="mw-grid-3 mw-reveal-stagger">
  <div class="mw-card">...</div>
  <div class="mw-card">...</div>
  <div class="mw-card">...</div>
</div>
```

The animation lets go once the entrance is done, so a card keeps its hover
lift and an open dropdown inside it is not trapped under the next card.

**Corner accent** - `mw-corner-plain` drops the accent arc that sits on the
two round corners of every card, panel, modal, tile, accordion, calendar,
pagination and login box. Everything else stays: the radii, the border, the
shadow, the hover. It is for a box too small to carry the mark - the arc reaches
about 34px in from its corner, so under roughly 90px the two of them take up
most of the outline and the pair reads as a frame instead of as a detail. A
chip-sized `mw-card-simple`, a swatch, a marker in a layout demo. A card with
content in it never needs this, and it is not the way to switch the signature
off across a project - restyle `--mw-corner-accent` for that.

**Squircle corners** - `mw-squircle` draws the same silhouette with a
superellipse instead of a circular arc: same four radii, fuller curve, and the
corner accent follows. Opt-in, because `corner-shape` only lands in Chromium so
far - everywhere else the box is simply the normal one.

**Aspect ratio** - `mw-aspect-square|video|wide|portrait|photo`. Reserves the
box before the image inside it has loaded, so the page does not reflow when the
picture arrives. The child fills the box and crops rather than stretching.

**Overflow and scrolling** - `mw-overflow-auto`, `mw-overflow-x-auto` (which
also contains the overscroll, so a sideways swipe on a wide table does not walk
the whole page), `mw-overflow-hidden`, and `mw-snap-x` to make a horizontal
strip come to rest on an item instead of halfway between two.

**Numbers** - `mw-text-numeric` is fixed-width digits and nothing else, for a
clock, a counter or an ID that must not jitter while it changes.
`mw-text-currency` adds right alignment and `nowrap` on top, which is what a
money column in a table wants. Do not reach for `mw-text-currency` just to get
the digits - that was the old behaviour of `mw-text-numeric` and the reason
people wrote `font-variant-numeric` out by hand.

### `mw-row-split` - the row with two ends

The most common layout in any application: what it is on the left, the value or
the action on the right, wrapping to two lines when it runs out of room. Card
header, section header, key figure, week row.

```html
<div class="mw-row-split">
  <strong>Invoice 2026-0042</strong>
  <span class="mw-text-currency">1,204.50</span>
</div>
```

Five declarations you would otherwise write again in every component -
including the `flex-wrap` everyone forgets, which is what keeps the left half
from being squashed on a phone.

`mw-row-split` aligns on the baseline, which is right for text against text. Add
`mw-row-split-center` when the two sides differ in height - a heading beside a
button, a label beside an icon.

### `mw-sr-only` - text for screen readers only

```html
<button type="button" class="mw-btn mw-btn-outline">
  <i class="fas fa-trash"></i>
  <span class="mw-sr-only">Delete invoice 2026-0042</span>
</button>
```

Wherever an icon carries the whole message. Not `display: none` and not
`visibility: hidden` - both drop the element out of the accessibility tree,
which is precisely what must not happen.

There are no responsive display variants. Show/hide per breakpoint is the
application's job (media query in your own stylesheet, or `@if` in the
template).

### `mw-d-contents` - wrapper components inside a layout container

Every flex or grid container here styles its **children**. Plain HTML puts them
right there, a SPA usually does not:

```html
<!-- what the CSS expects -->
<div class="mw-grid-2">
  <div class="mw-card">…</div>
  <div class="mw-card">…</div>
</div>

<!-- what a component tree produces - one item, not two -->
<div class="mw-grid-2">
  <app-card>…</app-card>
  <app-card>…</app-card>
</div>
```

Two cards side by side still work, because each host _is_ one item. It breaks
when one host wraps several intended items, or when a host sits between the
container and a single child that brings its own width - the host becomes the
item and shrinks to content width. Nothing errors, the layout is just wrong.

`mw-d-contents` on the host removes its box, so the children become the items:

```typescript
@Component({
  selector: 'app-header',
  host: { class: 'mw-d-contents' },
  …
})
```

The trade-off: an element with `display: contents` has no box, so background,
padding, border and transforms on that host stop working. If you need those, keep
the box and give it `width: 100%` (flex row) or `mw-flex-1` instead.

`mw-header` already absorbs a wrapper on its own, no `mw-d-contents` needed
there. The grid, tag, button-bar, form-action, modal-footer and toast containers
do not.

**Flex** - `mw-flex-row`, `mw-flex-column`, `mw-flex-wrap`, `mw-flex-nowrap`,
`mw-flex-1`, `mw-flex-grow-1`, `mw-flex-shrink-0`,
`mw-justify-start|end|center|between|around|evenly`,
`mw-items-start|end|center|stretch`,
`mw-self-start|end|center|stretch`.

`mw-flex-1` sets `flex: 1` (basis 0, all items equal). `mw-flex-grow-1` only
grows and keeps the content width as the basis - that is the one you want next
to an avatar or an icon. `mw-self-*` is the per-item counterpart to
`mw-items-*`: it goes on the child, for the one that sits differently from the
rest of the row.

**Text** - alignment `mw-text-left|center|right`; colour `mw-text-primary`,
`-secondary`, `-success`, `-warning`, `-danger`, `-info`, `-muted`,
`mw-text-color-dark`, `mw-text-color-light`; weight `mw-text-bold`, `-medium`,
`-normal`, `-light`; `mw-text-italic`; size `mw-text-3xs` … `mw-text-6xl`;
line height `mw-leading-tight|normal|loose`.

`mw-text-numeric` is the one to know: right aligned, tabular lining figures, no
wrap - for money and figures in tables. It is locale agnostic (alignment comes
from the right edge), but the number of decimal places has to be constant per
column.

**Radius** - `mw-radius-none|xs|sm|md|lg|xl|2xl|full`.
