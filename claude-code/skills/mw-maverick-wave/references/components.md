# Components

Colour variants are always one of `primary`, `secondary`, `success`, `warning`,
`danger`, `info` - but not every component offers all six. The lists below are
exhaustive: what is not named does not exist.

## Buttons

```html
<button type="button" class="mw-btn mw-btn-primary">Save</button>
<button type="button" class="mw-btn mw-btn-primary">
  <i class="fas fa-save"></i> Save
</button>
<a href="#" class="mw-btn mw-btn-outline">Link that looks like a button</a>
```

- Variants: `mw-btn-primary`, `mw-btn-secondary`, `mw-btn-danger`,
  `mw-btn-success`, `mw-btn-outline`, `mw-btn-ghost`, `mw-btn-ghost-danger`,
  `mw-btn-link`, `mw-btn-link-muted`
- Shapes: `mw-btn-icon` (square, for an icon-only button), `mw-btn-block`
  (full width)
- Sizes: `mw-btn-sm`, `mw-btn-lg`
- `mw-btn` is `inline-flex` with a gap - icons need no wrapper and no extra class
- `disabled` gets `opacity: .6` and `not-allowed`; there is no disabled class
- `mw-active` gives the pressed/selected look on the coloured variants
- Every variant gives to 97 % on `:active` and springs back (`--mw-ease-spring`),
  the solid ones with an inner shadow. On touch that press is the only feedback
  there is, so do not override it away
- Solid variants are flat - no sheen, no light line, those belong to
  `mw-btn-glass`. They cast a soft shadow in their own colour (`--mw-btn-tone`)
  that grows on hover; `mw-shadows-flat` / `-hard` swap it through
  `--mw-btn-shadow` / `-hover` (keep those list-safe, `0 0 #0000` for none)
- `mw-btn-outline` fills in from the left on hover (a `background-size`
  transition) - restate its hover with `background-size`, not a `background`
  shorthand, or the run-in is gone
- `mw-btn-forward` (since 6.14.0) lets an icon after the label (`svg`, `i` or
  `fa-icon` as the last child) edge out 3px under the pointer; not with reduced
  motion. Opt-in because a leading icon before a bare text label is the last
  child too - in 6.13.0, where it was automatic, that one slid into the text
- `aria-busy="true"` (since 6.13.0) swaps the label for a spinner in its colour
  and keeps the width. `mw-btn-shine` draws a streak of light once per hover -
  for the one hero call to action. Both use a pseudo-element `data-tooltip`
  also needs, so not on a button with a tooltip
- **A link inside a sentence is `mw-link`, not `mw-btn mw-btn-link`.** The base
  class carries a control height, so in running text it lifts that one line to
  2.125rem while the lines around it stay where they are. `mw-p-0` does not help
  - the height does it, not the padding. Keep `mw-btn` only where the link
    really is a button in a row of buttons and has to line up with them
- On a coarse pointer or below 768px `mw-btn` grows to a 2.75rem minimum height
  and `mw-btn-sm` to 2.5rem, on their own

```html
<!-- a button that happens to look like a link -->
<button type="button" class="mw-btn mw-btn-link">Read Article</button>

<!-- a link inside a sentence -->
<p>Built with <a href="https://astro.build" class="mw-link">Astro</a>.</p>
```

### Text links

`mw-link` and `mw-link-muted` are the inline links, added in 4.13.0. Same look
as the two button variants - no box, underline on hover - but without
`inline-flex` and without the control height, which is what makes them sit on
the line instead of above it. `font` and the focus ring are set explicitly, so
a `<button>` in the middle of a paragraph works as well as an `<a>`.

```html
<p>
  Built with <a href="https://astro.build" class="mw-link">Astro</a> and written
  up in the
  <a href="#get-started" class="mw-link-muted">Get Started</a> section.
</p>
```

`mw-link-arrow` (since 6.13.0) goes next to either one for a link that leads on
to more - all projects, the full price list. An arrow ↗ follows the label as a
CSS mask in the link's colour, outside the underline, and edges out under the
pointer except with reduced motion or `mw-hover-static`. No icon markup needed.

```html
<a href="/arbeiten" class="mw-link mw-link-arrow">Alle Arbeiten</a>
```

### Three emphasis levels

`mw-btn-primary` (or any solid colour) **fills**, `mw-btn-outline` **draws a
line**, `mw-btn-ghost` does **neither** until you point at it. Ghost is what a
toolbar, a card's own actions or a row of icon buttons wants - five outlined
boxes in a row fight the content they sit on.

```html
<button type="button" class="mw-btn mw-btn-ghost">Rename</button>
<button type="button" class="mw-btn mw-btn-ghost mw-btn-ghost-danger">
  Remove
</button>
```

Ghost is not `mw-btn-plain`: it keeps the button's shape, padding and hit area
and only leaves them unpainted at rest. `mw-btn-plain` has no look at all.

### Icon-only buttons

```html
<button
  type="button"
  class="mw-btn mw-btn-ghost mw-btn-icon"
  aria-label="Duplicate"
>
  <i class="fas fa-copy"></i>
</button>
```

`mw-btn-icon` makes the button square and follows the size modifier next to it
(`mw-btn-sm` / `mw-btn-lg`), growing to 2.75rem on a coarse pointer. It always
needs an `aria-label` - there is no text to read out. Combine it with any
variant; ghost is usually the right one.

### `mw-btn-plain` - a button with no button in it

For everywhere a `<button>` is the right element and a button is the wrong look:
a calendar day, a time in a request row, a settings tab, a modal backdrop.

```html
<button type="button" class="mw-btn-plain">14:30</button>
```

It clears `appearance`, background, border, padding and margin, inherits font
and colour, and keeps exactly two things: the pointer and the focus ring. Used
on its own - `mw-btn` is neither needed nor wanted next to it.

Not the same as `mw-btn-link`, which is a button dressed as a link and brings
its own colour and control height, nor as `mw-link`, which is the link inside a
sentence.

**Destructive actions use `mw-btn-danger`.** `mw-btn-secondary` is a brand
colour, not a semantic one.

### Mini buttons

Round 18px icon buttons - remove a row, close an alert, drop a tag.

```html
<button type="button" class="mw-btn-mini mw-btn-mini-danger">
  <i class="fas fa-times"></i>
</button>
```

Variants: `mw-btn-mini-primary`, `-secondary`, `-danger`, `-success`. Plain
`mw-btn-mini` is the neutral one. Works on `<a>` as well.

### Button bar

Row of equally treated buttons, centered by default.

```html
<div class="mw-button-bar mw-button-bar-primary">
  <button class="mw-btn">Previous</button>
  <button class="mw-btn">Overview</button>
  <button class="mw-btn">Next</button>
</div>
```

- Colouring: `mw-button-bar-primary`, `-secondary`, `-outline` style the bare
  `mw-btn` children, so the buttons carry no variant class themselves.
  `mw-button-bar-nav` mixes them for prev/center/next navigation.
- Alignment: `mw-button-bar-left`, `-right`, `-center` (which is also the
  default), `mw-button-bar-between` pushes first and last apart.
- Sizes: `mw-button-bar-sm`, `mw-button-bar-lg`.
- Below 576px it stacks and gives every button the full width. Right for a row of
  independent actions - wrong for a switch, see below.

### `mw-actions-note` - one line above a row of actions

```html
<div class="mw-modal-footer">
  <p class="mw-actions-note">This action cannot be undone.</p>
  <button class="mw-btn mw-btn-outline">Cancel</button>
  <button class="mw-btn mw-btn-danger">Delete</button>
</div>
```

Right-aligned, muted, one size smaller. For what the buttons apply to, why one
of them is disabled, or that something cannot be taken back.

- Works in `mw-modal-footer`, `mw-card-footer`, `mw-form-actions` and
  `mw-panel-footer`. It is a child of the action row, not a wrapper around it:
  the line takes the full width and pushes the buttons onto the row below.
- Only rows that actually carry a note start wrapping, so adding one changes
  nothing anywhere else.
- Inside `mw-form-actions` the alignment variants steer it as well -
  `mw-form-actions-left` makes the note left-aligned too.
- `mw-form-actions-hint` is the old, form-only name for the same thing. Still
  styled, but use `mw-actions-note`: the hint name is wrong the moment the line
  sits in a modal.

### Segmented control

Two or three positions of **one** switch: income/expense, offer/quote, a period
picker.

```html
<div class="mw-segmented">
  <button type="button" class="mw-segmented-item mw-active">Income</button>
  <button type="button" class="mw-segmented-item">Expense</button>
</div>
```

- Stays horizontal at every width and splits the row into equal shares - which
  is the whole point. Stacked in a `mw-button-bar`, two positions of a switch
  look like two buttons you could press both of.
- Active position: `mw-active`, `aria-pressed="true"`, `aria-checked="true"`
  or `aria-selected="true"` on the item. Under forced colours it takes
  Highlight.
- `mw-segmented-secondary` switches the active fill to the secondary colour,
  `mw-segmented-auto` shrinks the control to its content instead of filling the
  row - capped at `100%`, so labels wider than a 320px screen truncate instead
  of pushing the row off it. `disabled` or `aria-disabled="true"` works on an
  item.
- Items reach a 2.5rem minimum height on a coarse pointer.

**On native radios** - a label per segment around a radio: the checked one
lights up, the keyboard and the form value are the browser's, and
`formControlName` on the inputs is all Angular needs. A disabled radio dims its
segment, a focused one draws the ring on it.

```html
<div class="mw-segmented" role="radiogroup" aria-label="Billing cycle">
  <label class="mw-segmented-item">
    <input type="radio" name="cycle" value="monthly" checked /> Monthly
  </label>
  <label class="mw-segmented-item">
    <input type="radio" name="cycle" value="yearly" /> Yearly
  </label>
</div>
```

## Cards

```html
<div class="mw-card">
  <div class="mw-card-img">
    <img src="cover.jpg" alt="" />
  </div>
  <div class="mw-card-body">
    <h3 class="mw-card-title">Title</h3>
    <hr class="mw-card-title-divider" />
    <p class="mw-card-subtitle">Subtitle in muted italics</p>
    <p class="mw-card-text">Body copy.</p>
    <div class="mw-card-footer">
      <button class="mw-btn mw-btn-primary">Open</button>
      <span class="mw-text-muted">12 items</span>
    </div>
  </div>
</div>
```

- `mw-card` is the shell; the hover lift is built in and has no modifier class.
  It is a flex column by default, so `mw-card-footer` sticks to the bottom and
  cards in a grid line up without any extra class.
- `mw-card-simple` is the flat variant with even padding for arbitrary content.
  Use it when you only need a padded surface - it stays a block container, so
  inline children keep flowing side by side.
- Image height: 210px, `mw-card-lg` 340px, `mw-card-xl` 480px (260px/340px below
  `sm`). Set `--mw-card-img-height` on the card for any other height.
  `mw-card-img-contain` shows the whole image instead of cropping it.
- `mw-card-footer` pushes its last child to the right - with a single child that
  means it sits right, not left. Everything is vertically centered, so plain text
  lines up with a button next to it. Actions that no longer fit next to each
  other wrap.
- The card measures **itself**, not the window - a card in a three-column grid
  is just as narrow on a 1200px desktop as it is on a phone, and looks the same
  in both. Every card declares `container: mw-card / inline-size` and takes
  `width: 100%`, so it fills its slot instead of sizing to its content. Give a
  card an explicit width if you need it to hug its content.
- What steps on the card's own width: the footer stacks to full-width children
  below 360px, and the title, the subtitle and the body padding step up at
  420px. The image height is the one that still follows the window, because it
  is declared on the card itself and a container cannot query itself.
- `mw-tile` works the same way, and so do `mw-stepper`, both timelines, the
  gallery wrapper and the image slider: the step labels shrink and the two-sided
  timeline collapses to one side once the component is narrow, whatever the
  window does. One catch on tiles: a tile
  clips its overflow, and being a container makes it the containing block for
  `position: fixed`, so a `data-tooltip` **inside** a tile is cut off at its
  edge. Cards do not clip and are unaffected.
- `mw-card-badge` (top right corner) and `mw-card-ribbon` (diagonal banner) are
  absolutely positioned overlays; colour them with `mw-card-addon-primary`,
  `-secondary`, `-success`, `-warning`, `-danger`, `-info`.
- Cards of different sizes on one row rhythm - a services page, a dashboard -
  go in `mw-bento` (`references/layout.md`); the card fills its cell.
- A card does not clip its content, so a tooltip or dropdown inside it can reach
  outside. The exception is `mw-card-ribbon`: that banner has to be cut off at
  the edge, so a card with one as its **direct child** switches to
  `overflow: hidden` and clips everything else too. A ribbon deeper inside - on
  a card nested in another card - does not make the outer one clip.

```html
<div class="mw-card">
  <div class="mw-card-badge mw-card-addon-success">New</div>
  ...
</div>
```

**Feature frame** - wraps a card to lift one option out of a grid of equals,
for the "most booked" plan in a pricing row:

```html
<div class="mw-card-feature mw-card-feature-secondary">
  <p class="mw-card-feature-label">Most booked</p>
  <div class="mw-card">
    <div class="mw-card-body">...</div>
  </div>
</div>
```

- Unlike badge and ribbon this is a **wrapper around** the card, not an overlay
  inside it. The card itself stays untouched - same width, same height, same
  hover as its neighbours - and the frame plus its label bar grow outwards into
  the grid gap.
- Colours are `mw-card-feature-secondary` and `mw-card-feature-info`; primary is
  the default and needs no class. This is a separate set from the
  `mw-card-addon-*` classes that colour badge and ribbon - the frame only comes
  in those three.
- The label is a single line. It is set in uppercase at `2xs` and truncates with
  an ellipsis rather than wrapping, because the 22px bar height is baked into
  the frame's negative margins.
- The frame reaches 29px above the card and 7px below it, so it sticks out of
  its grid cell. Any `mw-grid-*` that directly contains one therefore gets
  `row-gap: 56px` automatically, which leaves 20px between two stacked frames.
  CSS has no per-row gap, so this applies to every row of that grid - expect
  wrapped rows without a frame to sit further apart than usual. That is also why
  the bar is kept low: each extra pixel is charged to every row.
- The space **above the first row** is not covered - the frame reaches into
  whatever sits there. Give the container the room (`mw-mt-10` on the grid, or
  `mw-mb-10` on the heading above it).
- In a layout that is not a `mw-grid-*` - your own flex column, an Angular host
  with its own grid - nothing raises the gap for you. Leave at least 36px
  between stacked items yourself.

**Stack card** - icon + title header with a gradient rule, for feature or
tech-stack grids:

```html
<div class="mw-card mw-card-stack">
  <div class="mw-card-stack-header">
    <div class="mw-card-stack-icon"><i class="fas fa-server"></i></div>
    <h5 class="mw-card-stack-title">Backend</h5>
  </div>
  <div class="mw-card-stack-body">
    <div class="mw-tags"><span class="mw-tags-item">Kotlin</span></div>
    <p class="mw-card-stack-text">Description.</p>
  </div>
</div>
```

## Pricing

Two pieces that are almost always needed together: `mw-price`, the figure on its
own, and `mw-offer`, the card it is sold from.

### Price

One baseline row - what it cost before, what it costs now, the unit, a discount
tag:

```html
<p class="mw-price">
  <span class="mw-price-original">
    <span class="mw-sr-only">Regular price:</span>159 Euro
  </span>
  <span class="mw-sr-only">Now:</span>
  <span class="mw-price-amount"
    >129<span class="mw-price-fraction">,90</span></span
  >
  <span class="mw-price-currency">Euro</span>
  <span class="mw-price-period">/ month</span>
  <span class="mw-tag mw-tag-secondary">-20%</span>
</p>
<p class="mw-price-note">Billed yearly, cancel any time.</p>
```

- Everything in the row is sized in `em` off `--mw-price-size`, so
  `mw-price-xs` (1.3rem), `mw-price-sm` (1.5rem) and `mw-price-lg` (3rem) move
  the whole row at once - cents, unit and struck original included. Set the
  token yourself for any other size.
- `mw-price-original` is muted **and** struck, and it takes its own line
  **above** the new price. Muted alone reads as a footnote; the line is what
  says this is no longer the price. The rule is drawn explicitly, because the
  browser default hairline disappears at this size against a muted tone.
- Stacked is the default because inline the row runs long - "199 Euro 159 Euro
  -20 %" - and the first thing to wrap away when the width gives out is the
  discount tag, the one part that was there to catch the eye. `mw-price-inline`
  puts it back on one line for a wide card or a table row.
- `mw-price-fraction` goes **inside** the amount and sits one step down on the
  baseline, not raised to the cap height - raised cents are a discounter's idiom
  and make a service price read cheaper than it is.
- `mw-price-currency` and `mw-price-period` stop shrinking at 0.8rem, and
  `mw-price-original` at 0.9rem. At `mw-price-xs` the `em` chain would put them
  under 10px, which is where the floor earns its keep.
- `mw-price-word` for "On request" or "Free" - bold, so it holds the same slot in
  a row of cards, but set well below a figure. Its line box is scaled back up to
  the amount's, so a word and a number in neighbouring cards land on one line.
- `mw-price-note` is a **sibling** of the row, not a child - inside it, it would
  inherit the price size and join the baseline.
- A `mw-tag` or `mw-badge` placed directly in the row is centred against the
  digits rather than hung off their baseline.

| Class               | What it does                                   |
| ------------------- | ---------------------------------------------- |
| `mw-price-xs/sm/lg` | Retunes `--mw-price-size`, everything follows  |
| `mw-price-inline`   | Old price in front of the new one, on one line |
| `mw-price-center`   | Centres the row                                |
| `mw-price-plain`    | Body colour instead of the brand               |

A struck-through price is a visual convention a screen reader does not pass on -
`<s>` is announced by almost none of them. Wherever an old and a new price stand
next to each other, name them with `mw-sr-only`, as above. Without it the reader
hears two prices and no way to tell which one is charged.

### Offer card

`mw-offer` goes on a `mw-card` and does the one thing the card cannot: it pushes
the price to the bottom of the body, so the prices in a row line up even though
the feature lists have different lengths.

```html
<article class="mw-card mw-offer">
  <div class="mw-card-body">
    <h3 class="mw-card-title">Studio</h3>
    <hr class="mw-card-title-divider" />
    <p class="mw-card-text">Description.</p>
    <ul class="mw-list mw-list-check">
      <li>10 projects</li>
    </ul>
    <p class="mw-price mw-price-sm">…</p>
    <p class="mw-price-note">Per month, billed yearly.</p>
    <div class="mw-card-footer">
      <button class="mw-btn mw-btn-primary">Choose</button>
    </div>
  </div>
</article>
```

- Bottom-aligned, note included: a card that carries a `mw-price-note` and one
  that does not will **not** have their prices on the same line. Give every card
  in a row a note, or none of them.
- To lift one plan out of the row, wrap it in `mw-card-feature` - the frame is
  the card's, not the offer's.
- A price dropped into a `mw-card-footer` instead needs no modifier: it lines up
  with the button beside it on its own, and `mw-price-sm` keeps it from
  outweighing the action. That is the layout for a dated event, where the price
  is a detail rather than the offer.
- Such a footer keeps its row once the card gets narrow, and gives the action
  half of it. A footer normally stacks its children to full width down there, so
  that two buttons do not squeeze - but a price is a label, not a second action,
  and a full-bleed button under a left-aligned price reads as a banner rather
  than as the end of a card.

**Head band** - name and price in a solid bar at the top, for when the price is
the thing being compared and the feature list is only its justification:

```html
<article class="mw-card mw-offer mw-card-addon-secondary">
  <div class="mw-offer-head">
    <p class="mw-offer-name">Studio</p>
    <p class="mw-price mw-price-sm">…</p>
  </div>
  <div class="mw-card-body">…</div>
</article>
```

The band reads `mw-card-addon-*` for its colour - the same set the card badge and
the ribbon use, primary without one. The price inherits the band's ink, and the
card drops its top corner arc, which the band already owns.

### Billing cycle

A subscription sold on several terms, where the longer one is cheaper. The
switch is a `mw-segmented` **above** the grid, not one per card - three cards
with three switches are three states the visitor has to keep in their head.

```html
<div
  class="mw-segmented mw-segmented-auto"
  role="group"
  aria-label="Billing cycle"
>
  <button type="button" class="mw-segmented-item mw-active" aria-pressed="true">
    Monthly
  </button>
  <button type="button" class="mw-segmented-item" aria-pressed="false">
    6 months <span class="mw-tag mw-tag-secondary">-10%</span>
  </button>
  <button type="button" class="mw-segmented-item" aria-pressed="false">
    Yearly <span class="mw-tag mw-tag-secondary">-20%</span>
  </button>
</div>
```

- The headline figure stays **per month** on every term. "288 Euro" next to
  "30 Euro" is not a comparison a reader can make in their head; the amount that
  actually leaves the account belongs in the `mw-price-note` below
  ("288 Euro charged once for the year, cancel monthly").
- The full monthly rate goes in `mw-price-original`, the saving in a `mw-tag`
  next to it. Both carry `hidden` on the monthly term - the framework resets
  `[hidden]` to `display: none !important`, so it beats a component's own
  `display` and an `el.hidden = true` or an Angular `[hidden]` binding works on
  a `mw-tag` too.
- Wrap the price in `aria-live="polite"` and put `aria-pressed` on the switch
  items. The figure changes without the page moving, which a screen reader
  otherwise never hears.
- Drop trailing zero cents: "24 Euro", not "24,00 Euro". `mw-price-amount` sets
  tabular figures, so the row does not jump when the term changes.
- A tag inside the **active** item drops its colour and outlines itself in the
  item's ink - the colour variants mix their background from the page, and an
  orange pill on the blue fill comes out purple. Inactive items keep the colour,
  which is what makes a visitor click them.

The switching itself is the application's job - the framework ships the look,
not the arithmetic. The showcase wires it in a few lines at the bottom of
`index.html`.

## Panels

A bordered box with a header rule - the "titled section" of an application.

```html
<div class="mw-panel mw-panel-primary">
  <h4 class="mw-panel-header">Filters</h4>
  <div class="mw-panel-body">...</div>
  <div class="mw-panel-footer">
    <button class="mw-btn mw-btn-outline">Reset</button>
    <button class="mw-btn mw-btn-primary">Apply</button>
  </div>
</div>
```

- Header colour: `mw-panel-primary`, `mw-panel-secondary`; without them the
  header is neutral. Title and action sit at opposite ends and wrap to two rows
  when the panel gets too narrow for both.
- Title with a subtitle and several actions: `mw-panel-heading` wraps
  `mw-panel-title` and `mw-panel-subtitle`, `mw-panel-actions` holds the buttons
  at the end. The heading shrinks, so a long title cannot push the actions out.
- `mw-panel-edge-{primary|secondary|success|warning|danger|info}` draws a 3px
  left edge in the ink tone - the one panel in a row that needs attention.
- A `mw-item-list-compact` directly in `mw-panel-body` drops its own box.
- A tooltip inside unclips the panel while it shows; a capped body
  (`-max-height-*`, `-scrollable`) keeps clipping and scrolling.
- Height: `mw-panel-scrollable` (500px), `mw-panel-max-height-sm` (300px),
  `-md` (500px), `-lg` (700px) - the body scrolls, header and footer stay.
- Panels in a grid row end up equally tall on their own - a grid item stretches.
  A height variant opts out with `align-self: start`.

## Tiles

Compact info blocks. The look is on the class, the click is on the element: put
`mw-tile` on an `<a>` or a `<button>` and it gets the hand cursor, the focus ring
and the tap handling. On a `<div>` it stays a plain surface - no cursor, no ring,
because there would be nothing to reach by keyboard.

```html
<div class="mw-tiles mw-tiles-2col">
  <a href="/billing" class="mw-tile">
    <div class="mw-tile-img"><img src="icon.png" alt="" /></div>
    <h3 class="mw-tile-header">Billing</h3>
    <div class="mw-tile-body">
      <p>Invoices and payments</p>
    </div>
    <div class="mw-tile-footer">Updated 2026-01-02</div>
  </a>
</div>
```

Container: `mw-tiles` (1 / 2 at `sm` / 3 at `md`), `mw-tiles-2col` (1 / 2 at
`sm`), `mw-tiles-4col` (1 / 2 at `sm` / 4 at `lg`) - the same ramps `mw-grid-3`,
`-2` and `-4` use, and the full container width like any other grid.
Tile sizes: `mw-tile-sm`, `mw-tile-lg`.

## Accordion

```html
<div class="mw-accordion">
  <div class="mw-accordion-item">
    <button
      type="button"
      class="mw-accordion-header mw-active"
      aria-expanded="true"
      aria-controls="faq-1"
    >
      <span>Question</span>
      <i class="fas fa-chevron-down mw-accordion-icon"></i>
    </button>
    <div class="mw-accordion-content mw-active" id="faq-1">
      <div class="mw-accordion-content-inner">Answer</div>
    </div>
  </div>
</div>
```

The header is a `<button>` - it is the control that opens the panel, and a
`<div>` is not focusable. A heading is not allowed inside a button, so the
question is a `<span>` and the header carries the type itself; a nested `h3`
still renders the same, for markup written before 4.12.

Open state = `mw-active` on header **and** content (bare `active` still works
but is deprecated). The icon rotates via the **header** state - putting the
class on the icon instead does nothing. Content taller than 500px scrolls.
The `mw-accordion-content-inner` wrapper is required and not decoration: the
panel opens by animating a grid row and that wrapper is the row, so content
placed straight into `mw-accordion-content` never collapses when closed.
Toggling is JS - see `references/javascript.md`; the shipped script keeps
`aria-expanded` in step when the header is a button. `aria-expanded="true"` on
the header opens the content after it on its own, without `mw-active` - for
markup an application renders.

## FAQ

```html
<div class="mw-faq">
  <details class="mw-faq-item" id="question-1" name="faq" open>
    <summary class="mw-faq-question">Question</summary>
    <div class="mw-faq-answer">
      <p>Answer</p>
    </div>
  </details>
</div>
```

Variant: `mw-faq-cards` - every question its own card with the corner arc,
the open one framed in the primary colour. Default is a list on hairlines.

Native `<details>`, no script needed: `open` on an item shows it on arrival, a
shared `name` keeps one answer open at a time, find-in-page opens the item that
holds the match. The answer animates through a grid row on `::details-content`
(Chrome 131, Firefox 143, Safari 18.4); older engines open without animation.
Answers grow to full height - no 500px cap as in `mw-accordion`, which makes
this the component for questions and answers on a page. The plus and minus
are drawn in CSS, no icon markup. A link to an item's `id` opens it - see
`references/javascript.md`.

## Tabs

```html
<div class="mw-tabs">
  <div class="mw-tabs-nav">
    <button type="button" class="mw-tabs-nav-item mw-active" data-tab="tab1">
      Details
    </button>
    <button type="button" class="mw-tabs-nav-item" data-tab="tab2">
      History
    </button>
  </div>
  <div class="mw-tabs-content">
    <div class="mw-tabs-panel mw-active" id="tab1">...</div>
    <div class="mw-tabs-panel" id="tab2">...</div>
  </div>
</div>
```

- Variants: `mw-tabs-vertical` (nav on the left, horizontal again below `sm`),
  `mw-tabs-pills`.
- `data-tab` matches the panel `id` - that pairing is only needed for the
  shipped JS. In a SPA, bind `mw-active` yourself and drop the attribute.
- The shipped JS turns the strip into a real tablist: `role`, `aria-selected`,
  `aria-controls`, `aria-labelledby`, a roving `tabindex` and arrow/Home/End
  keys. Without it, that is yours to add - see `references/javascript.md`.
- The nav scrolls horizontally instead of wrapping, and says so: a shadow shows
  on whichever side still has tabs behind it and disappears once that end is
  reached. Pure CSS, no scroll listener. The fade colour comes from
  `--mw-scroll-hint-cover`, which is preset to the page background and
  re-pointed to the card background inside `mw-card`, `mw-panel`, `mw-modal`,
  `mw-tile` and `mw-calendar` - override it if the strip sits on some other
  surface.
- Tab items reach a 2.75rem minimum height on a coarse pointer.
- `aria-selected="true"` on an item marks it like `mw-active` - horizontal,
  vertical and pills alike. `:disabled` or `aria-disabled="true"` dims it.
  Under forced colours the marker and the active pill take Highlight.

## Modal

```html
<dialog id="delete-modal" class="mw-modal mw-modal-sm" closedby="any">
  <div class="mw-modal-header">
    <h4 class="mw-modal-title">Delete invoice</h4>
    <button class="mw-modal-close" type="button" aria-label="Close">
      &#120299;
    </button>
  </div>
  <div class="mw-modal-body">
    <p>Invoice 2026-0042 will be removed.</p>
  </div>
  <div class="mw-modal-footer">
    <p class="mw-actions-note">This action cannot be undone.</p>
    <button class="mw-modal-close mw-btn mw-btn-outline">Cancel</button>
    <button class="mw-btn mw-btn-danger">Delete</button>
  </div>
</dialog>
```

- Escape, the focus trap and `inert` on the page behind it come from the
  element, the page scroll lock from the stylesheet
  (`:root:has(dialog.mw-modal[open])`). There is no overlay wrapper and no
  backdrop element.
- Opened with `showModal()`, closed with `close()`. `main.js` wires the close
  buttons and exposes `mwOpenModal(id)` / `mwCloseModal(id)`, which act on a
  `<dialog>` and ignore anything else; a trigger carrying
  `data-mw-modal="delete-modal"` needs no script of your own.
- `closedby="any"` dismisses it on a backdrop click; where that attribute is not
  understood yet the script handles the click instead.
- Sizes: `mw-modal-sm` 370px, default 520px, `mw-modal-lg` 720px,
  `mw-modal-xl` 960px. Height is capped at 80-92dvh (`--mw-modal-max-height`),
  the body scrolls. Below 576px it becomes a bottom sheet - a drawer does not.
- `mw-modal-full` is the document viewer: up to 1400px wide and a fixed 92dvh
  high, whatever the content - a one-page invoice gets the same box as a
  twelve-page one, and the body takes the room between header and footer.
- `mw-modal-close` is the hook, not a look: on the header X it styles the button,
  on a footer action it only closes. Combine it with `mw-btn mw-btn-primary` and
  the button keeps its own paint.
- `mw-modal-body` takes a `mw-form` directly - the form brings the field gaps,
  the body brings the padding.
- `mw-actions-note` is the muted line above the buttons - see below.
- Name it with `aria-labelledby` pointing at the `mw-modal-title`; `role` and
  `aria-modal` come from `showModal()`. Without `autofocus` the browser focuses
  the first focusable element, usually the close button.

Angular: `[open]="isOpen()"` does **not** work - the attribute opens a non-modal
dialog with no top layer, backdrop or focus trap. It takes a directive calling
`showModal()`, see `examples/angular-services.md`.

The overlay div that predates the `<dialog>` (mw-modal-overlay, its -open
state class and the -backdrop child) was removed in 6.0. Move such markup to
the `<dialog>` above - header, body and footer stay as they are.

### Drawer

The same `<dialog>` as a full-height side panel - filters, a detail view, a
copilot next to the content:

```html
<dialog id="filters" class="mw-modal mw-modal-drawer" closedby="any">
  <div class="mw-modal-header">...</div>
  <div class="mw-modal-body">...</div>
  <div class="mw-modal-footer">...</div>
</dialog>
```

- Against the right edge; `mw-modal-drawer-start` next to it moves it to the
  left. Physical sides, so it does not flip in a right-to-left page. Width `min(420px, 100vw - 2.5rem)`, height `100dvh` with the
  safe-area insets as padding.
- Stays a side panel on a phone, where every other modal turns into a sheet.
  Header and footer stay put, the body scrolls between them.
- Only the inner edge is visible, and it keeps its half of the silhouette with
  the corner arc; under `mw-corners-even` the single mark moves to the inner
  corner.
- Opened and closed like any modal - `data-mw-modal`, `mwOpenModal(id)`, no new
  script. `show()` instead of `showModal()` leaves the page usable and
  scrollable beside it; the drawer then carries `--mw-elevation-4`.
- A navigation that is always there is not a drawer - that is `mw-app-sidebar`
  in `references/layout.md`.

## Alerts & toasts

```html
<div class="mw-alert mw-alert-success">
  <div class="mw-alert-icon"><i class="fas fa-check-circle"></i></div>
  <div class="mw-alert-content">
    <span class="mw-alert-title">Saved</span>
    <p>The invoice was created.</p>
  </div>
  <button type="button" class="mw-btn-mini mw-btn-mini-danger mw-alert-close">
    <i class="fas fa-times"></i>
  </button>
</div>
```

`mw-alert-actions` inside `mw-alert-content` puts Undo or Retry under the
message; `mw-btn-link` and `mw-btn-ghost` in it take the alert's own text colour,
which holds on every status tint. `role="alert"` for what needs attention now,
`role="status"` for a confirmation that can wait. Give the toast stack
`role="status"` and `aria-live="polite"` yourself, so a screen reader reads
each new toast - the framework sets neither.

Variants: `mw-alert-primary`, `-secondary`, `-success`, `-warning`, `-danger`,
`-info`. `mw-alert-title` and the close button are optional. Dismissal runs in
two steps: `mw-alert-closing` fades the alert out over `--mw-duration-base`, then
`mw-alert-closed` hides it (`display: none`) - in a SPA prefer removing it from
the list instead.

**Toasts** are alerts inside a fixed stack:

```html
<div
  class="mw-toast-stack mw-toast-stack-top-right"
  role="status"
  aria-live="polite"
>
  <div class="mw-alert mw-alert-success">...</div>
</div>
```

Positions: `mw-toast-stack-top-right` (also the default without a position
class), `-top-center`, `-bottom-right`, `-bottom-center`. The alert icon inside
a toast takes the text ink - its own tone vanishes on the tint. Width is capped at
`min(380px, 100vw - 2rem)`, clicks pass through everywhere except on a toast,
the entry animation respects `prefers-reduced-motion`. Auto-dismiss is the
application's job. While an `mw-action-bar` is on screen the bottom stack sits
above it (`--mw-action-bar-reserve`); without one nothing moves.

## Announcement

The ribbon glued under the fixed header - a discount, a launch note, a
maintenance window. One per page.

```html
<aside class="mw-announcement mw-announcement-secondary">
  <a class="mw-announcement-content" href="#pricing">
    <span class="mw-announcement-highlight">-20 %</span>
    <span>Summer discount on all coachings until 06.09.</span>
  </a>
</aside>
```

Positioned fixed below the header and one z-index layer under it, and it stays
there - the page scrolls beneath it. It hangs from the island as its lower half:
the same edges, the island squared off where the two meet. Under
`mw-header-bar` it runs full width under the bar. The open mobile menu covers
it. Variants: `mw-announcement-secondary`,
`-success`, `-warning`, `-danger`, `-info` (primary is the default).
`mw-announcement-highlight` is the pill in front of the text; the content
element is usually an `<a>` but a plain `<div>` works.
`mw-announcement-static` puts the ribbon into the document flow instead - it
then scrolls with the content and shifts no anchor offset.

A close button is a `mw-btn-mini mw-announcement-close` as the ribbon's last
child. It sits at the inline end, the text stays centred, and `main.js` sets
`hidden` on the ribbon, which also frees the anchor offset - in a SPA remove the
ribbon instead.

The height lives in `--mw-announcement-height` and drives the anchor scroll
offset (`scroll-padding-top`) automatically - a taller ribbon raises the token
instead of fighting the offset.

On a page whose header carries `mw-header-reveal` the ribbon leaves and arrives
with it, without a class of its own - both cover the height of the pair, so they
come in as one block. Without it the ribbon docks into the island together with
the bar. See `references/layout.md`.

## Action bar

The phone's shortcut to the business - call, directions, book - fixed to the
bottom edge where the thumb already is:

```html
<!-- last in the body -->
<nav class="mw-action-bar" aria-label="Contact">
  <a class="mw-action-bar-item" href="tel:+49891234567">
    <i class="fas fa-phone" aria-hidden="true"></i><span>Call</span>
  </a>
  <a class="mw-action-bar-item" href="https://maps.google.com/?q=...">
    <i class="fas fa-location-dot" aria-hidden="true"></i
    ><span>Directions</span>
  </a>
  <a class="mw-action-bar-item mw-action-bar-primary" href="/booking">
    <i class="fas fa-calendar-check" aria-hidden="true"></i><span>Book</span>
  </a>
</nav>
```

- Two to four items share the width: an icon (`<i>`, `<svg>` or `<img>`) over
  a short label that truncates, at least 2.75rem high. `mw-action-bar-primary`
  fills the one action that matters most.
- Header colours in both themes, so the page has chrome at both ends; the
  safe-area inset is added at the bottom.
- Hidden from `md` (768px) up. `mw-action-bar-always` keeps it there, centred
  with items up to 10rem wide.
- While it is visible the root sets `--mw-action-bar-reserve`
  (`--mw-action-bar-height` 3.75rem plus the inset): that much body padding at
  the foot, the same as `scroll-padding-bottom` so a focused field never ends
  up underneath (WCAG 2.4.11), and `mw-toast-stack-bottom-right` above it.
  Where the bar is hidden, and in print, the reserve is 0.
- `mw-action-bar-embedded` is absolute instead of fixed and reserves nothing -
  for a preview inside a frame, like the showcase's `mw-device-phone`.
- `mw-action-bar-island` floats it as the counterpart to the header island:
  the same glass and side edges, `--mw-header-inset` (14px) off the bottom or
  clear of the home indicator, 4px lower than the flat bar. The reserve
  follows. With `-always` from `md` up it shrinks to a dock around its items.
- z-index key `action-bar` (98): over the page and its menus, under the open
  navigation's scrim, modals and toasts.

## Empty state

```html
<div class="mw-empty-state mw-empty-state-warning mw-empty-state-sm">
  <div class="mw-empty-state-icon"><i class="fas fa-inbox"></i></div>
  <p class="mw-empty-state-title">No results</p>
  <p class="mw-empty-state-desc">Try a different filter.</p>
  <button class="mw-btn mw-btn-outline">Clear filters</button>
</div>
```

Variants: `mw-empty-state-primary`, `-success`, `-warning`, `-danger`. Size:
`mw-empty-state-sm`. `mw-empty-state-inline` is the shape for a table body or a
panel: the icon beside the text, the action under it, everything on the left.
Without an icon the text takes the whole row.

## Spinners

```html
<div class="mw-spinner-container">
  <div class="mw-spinner-border mw-spinner-primary"></div>
</div>
```

- Shapes (one is mandatory): `mw-spinner-border`, `mw-spinner-dual-ring`,
  `mw-spinner-dots` (needs three empty `<div>` children).
- Sizes `mw-spinner-sm`, `mw-spinner-lg`; colours `mw-spinner-primary`,
  `mw-spinner-secondary`.
- `mw-spinner-container` centers in the available space.
  `mw-spinner-container-overlay` lays a dimmed, blurred scrim over the parent -
  the parent needs `position: relative`.
- `mw-spinner-inline` is 1em and the text colour - for a busy button that keeps
  its label (`disabled` on the button, `aria-hidden` on the spinner). Not with
  `aria-busy="true"` on an `mw-btn`: since 6.13.0 that hides the label and every
  child and draws its own spinner, so the inline one never shows.
- With reduced motion or `mw-motion-off` every shape stands still and stays
  visible; under forced colours they draw in the system ink.

## Skeleton

```html
<div class="mw-skeleton-card">
  <div class="mw-skeleton-row">
    <span class="mw-skeleton mw-skeleton-circle"></span>
    <div class="mw-skeleton-body">
      <span class="mw-skeleton mw-skeleton-text" style="width: 55%"></span>
      <span class="mw-skeleton mw-skeleton-text"></span>
    </div>
  </div>
  <span class="mw-skeleton mw-skeleton-rect"></span>
  <span class="mw-skeleton mw-skeleton-title"></span>
  <span class="mw-skeleton mw-skeleton-text"></span>
</div>
```

Shapes: `mw-skeleton-title`, `-text`, `-circle`, `-rect` (+ `-rect-sm`,
`-rect-lg`). Widths are set inline when a line should look ragged.

## Tables

```html
<div class="mw-table-responsive">
  <table class="mw-table mw-table-cards">
    <thead>
      <tr>
        <th>Name</th>
        <th>Status</th>
        <th class="mw-text-currency">Amount</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td data-label="Name">Jane Doe</td>
        <td data-label="Status">
          <span class="mw-tag mw-tag-success">Paid</span>
        </td>
        <td data-label="Amount" class="mw-text-currency">1.204,50</td>
      </tr>
    </tbody>
  </table>
</div>
```

| Class                        | Effect                                                                                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `mw-table`                   | Base: zebra rows, primary-coloured header                                                                                            |
| `mw-table-subtle`            | Quiet grey header with an accent rule - for data-heavy lists                                                                         |
| `mw-table-compact`           | Less padding, smaller type                                                                                                           |
| `mw-table-hover`             | Rows tint under the pointer - off unless this class is set                                                                           |
| `mw-table-cards`             | Below `md` every row becomes a card; keep `<thead>` (hidden via CSS) and give each cell a `data-label`                               |
| `mw-table-responsive`        | Wrapper, horizontal scroll                                                                                                           |
| `mw-table-responsive-hint`   | On top of the wrapper: a soft right edge showing there are more columns. Opt-in - see below                                          |
| `mw-table-responsive-scroll` | Wrapper with a height cap (`--mw-table-scroll-height`, 400px / 260px below `sm`) and vertical scroll                                 |
| `mw-table-sticky-head`       | Header stays put while the body scrolls - only works inside a height-limited wrapper, i.e. `mw-table-responsive-scroll`              |
| `mw-table-sticky-col`        | The first column stays put while a wide table scrolls sideways, with opaque zebra, hover (with `mw-table-hover`) and selection tones |
| `mw-table-bulk`              | Wrapper around the table and a `mw-table-bulk-bar`: the bar shows while any first-cell checkbox is checked                           |

In `mw-table-cards` the value is the cell's direct `span`, `a` or `div` - it
takes the right-hand side of the card row. A dot or icon nested inside it keeps
its own size. A row header (`<th scope="row">` in `tbody`) stands first in its
card and becomes its title.

`mw-table-responsive-hint` is opt-in, unlike the automatic hint on a tab bar,
and works differently for a reason: a table paints its own opaque surface, so
the gradient trick used on `mw-tabs-nav` would sit _behind_ the rows and never
show. A mask sits in front and does show - but a mask has no `local` attachment,
so it cannot fade away once the last column is reached. Put the class on the
tables you know overflow, leave it off the ones that fit.

```html
<div class="mw-table-responsive-scroll" style="--mw-table-scroll-height: 250px">
  <table class="mw-table mw-table-subtle mw-table-sticky-head">
    ...
  </table>
</div>
```

**Sorting and selection.** `aria-sort` on a `th` draws an arrow for `ascending`
or `descending` and a dimmed one for `none`; the `<button>` inside does the
sorting and gets a plain, focusable reset. A row is selected by
`aria-selected="true"`, `mw-selected` or a checked checkbox in its first cell:
tinted, plus an edge on the first cell so it does not rest on colour alone.
Under forced colours the selection takes Highlight.

```html
<div class="mw-table-bulk">
  <div class="mw-table-responsive">
    <table class="mw-table">
      <thead>
        <tr>
          <th><span class="mw-sr-only">Select</span></th>
          <th aria-sort="ascending"><button type="button">Client</button></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><input type="checkbox" aria-label="Select Harbourline" /></td>
          <td>Harbourline</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="mw-table-bulk-bar" role="region" aria-label="Bulk actions">
    <span><span class="mw-table-bulk-count"></span> selected</span>
    <button type="button" class="mw-btn mw-btn-sm mw-btn-primary">
      Export
    </button>
  </div>
</div>
```

The bar sticks to the bottom of the view, dark in both themes like the header.
Left empty, `mw-table-bulk-count` counts the checked rows itself - a CSS
counter, which is why the bar comes after the table in the markup; an app that
knows the number writes it in.

## Kanban

A board is a grid of equally wide lanes; a ticket is a plain `mw-card` with
`mw-kanban-card` on top. Everything except the counters and the composer is CSS.

The board puts as many lanes in a row as fit at 260px each and wraps the rest
onto the next. It measures its own width for that, so a board inside a panel or
a half-width column wraps on a desktop too.

```html
<div class="mw-kanban" style="--mw-kanban-column-min-height: 390px">
  <div class="mw-kanban-column">
    <div class="mw-kanban-column-header">
      <h5 class="mw-kanban-title">In Progress</h5>
      <span class="mw-kanban-count">2</span>
      <button
        type="button"
        class="mw-btn mw-btn-secondary mw-btn-sm mw-kanban-add"
        aria-label="Add ticket to In Progress"
      >
        <i class="fas fa-plus"></i>
      </button>
    </div>

    <div class="mw-kanban-column-body">
      <article class="mw-card mw-kanban-card">
        <div class="mw-card-ribbon mw-card-addon-danger">High</div>
        <p class="mw-kanban-card-title">Sticky table header jitters</p>
        <p class="mw-kanban-card-text">
          On Safari the header shifts by a pixel.
        </p>
        <div class="mw-kanban-card-footer">
          <span class="mw-kanban-card-id">MW-102</span>
          <div class="mw-kanban-card-actions">
            <div class="mw-avatar mw-avatar-xs mw-avatar-initials">jd</div>
            <button
              type="button"
              class="mw-kanban-action"
              aria-label="Move MW-102 one lane left"
            >
              <i class="fas fa-chevron-left"></i>
            </button>
            <button
              type="button"
              class="mw-kanban-action"
              aria-label="Move MW-102 one lane right"
            >
              <i class="fas fa-chevron-right"></i>
            </button>
            <button
              type="button"
              class="mw-kanban-action"
              aria-label="Edit MW-102"
            >
              <i class="fas fa-pen"></i>
            </button>
            <button
              type="button"
              class="mw-kanban-action mw-kanban-action-danger"
              aria-label="Delete MW-102"
            >
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </article>

      <div class="mw-kanban-empty">No tickets</div>
    </div>
  </div>
  ...
</div>
```

| Class                     | Role                                                                                                             |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `mw-kanban`               | Board. Grid, one column per lane, same width for all of them                                                     |
| `mw-kanban-plain`         | Board without its own surface or padding - for a board that already sits on a panel                              |
| `mw-kanban-compact`       | Tighter padding, description clamped to 2 lines instead of 4, lane floor 90px                                    |
| `mw-kanban-column`        | Lane: dashed border, flex column                                                                                 |
| `mw-kanban-column-header` | Title + counter + add button in one row                                                                          |
| `mw-kanban-title`         | Lane title, uppercase, truncates                                                                                 |
| `mw-kanban-count`         | Ticket counter pill                                                                                              |
| `mw-kanban-add`           | Sits **on** `mw-btn` - only trims it to the header line height                                                   |
| `mw-kanban-column-body`   | Ticket stack; fills the lane so the empty state stays centred                                                    |
| `mw-kanban-card`          | Ticket. Needs `mw-card` next to it                                                                               |
| `mw-kanban-card-title`    | Ticket title                                                                                                     |
| `mw-kanban-card-text`     | Description, clamped to 4 lines (2 on a compact board)                                                           |
| `mw-kanban-card-footer`   | Rule + key on the left, avatar and actions on the right                                                          |
| `mw-kanban-card-id`       | Ticket key, monospaced so equal-length keys line up across cards                                                 |
| `mw-kanban-card-actions`  | Right-hand group; resets the avatar margin                                                                       |
| `mw-kanban-action`        | 26px square icon button (32px below `md`, hit area grown to 44px), `mw-kanban-action-danger` turns the hover red |
| `mw-kanban-empty`         | Placeholder; hides itself as soon as the lane holds a ticket or an open composer                                 |
| `mw-kanban-card-in`       | One-shot entry animation for a freshly created ticket                                                            |

- **Priority is the regular `mw-card-ribbon`** and brings its own colour through
  `mw-card-addon-danger|warning|info`. It has to be a **direct child** of the
  card - that is what reserves the space next to the title. No ribbon means no
  priority; there is no separate priority class.
- Lanes are as tall as the fullest one, with `--mw-kanban-column-min-height` as
  the floor (120px, 90px compact). Raise it per board so a board that starts out
  empty still reads as a board.
- Board surface and lane border are `--mw-kanban-background` and
  `--mw-kanban-lane-border` - set them on the board, or drop the surface with
  `mw-kanban-plain`.
- Responsive: below `lg` the lanes reflow into two columns, below `sm` into one.
- The actions are ordinary buttons - which of them exist is your decision. Give
  every one an `aria-label` naming the ticket; the icon alone has no accessible
  name.

### Composer

The inline form for creating and editing a ticket. One per board, moved into the
lane it is needed in.

```html
<form class="mw-kanban-composer mw-active">
  <input type="text" class="mw-input mw-input-sm mw-kanban-composer-title" />
  <textarea class="mw-textarea mw-kanban-composer-text" rows="2"></textarea>
  <div class="mw-kanban-composer-row">
    <select class="mw-select mw-select-sm mw-kanban-composer-priority">
      ...
    </select>
    <select class="mw-select mw-select-sm mw-kanban-composer-assignee">
      ...
    </select>
  </div>
  <div class="mw-kanban-composer-actions">
    <button type="button" class="mw-btn mw-btn-outline mw-btn-sm">
      Cancel
    </button>
    <button type="submit" class="mw-btn mw-btn-primary mw-btn-sm">Save</button>
  </div>
</form>
```

- **`mw-kanban-composer` is `display: none` until it also carries `mw-active`.**
  Rendering it conditionally is not enough - the class has to be there too, or
  the form stays invisible.
- `mw-kanban-composer-row` puts priority and assignee side by side and stacks
  them once the lane gets too narrow; `mw-kanban-composer-actions` is the button
  row and gives its buttons the same 80px floor as a modal footer.
- The `-title`, `-text`, `-priority`, `-assignee` and `-cancel` classes carry no
  styling of their own beyond a min-height on the textarea - they are the hooks
  the shipped JS queries. In a SPA you bind the controls yourself and can drop
  them.
- `mw-kanban-editing` hides the ticket the composer is currently replacing.

## Calendar

A card-shaped surface with a header and a seven column grid. A month is six
rows, a week is one - same classes, same cell size, the only difference is how
many cells you render. Which page is on screen is application state: the shipped
JS renders it from `data-calendar`, an Angular app renders the same markup
itself.

```html
<div
  class="mw-calendar"
  data-calendar="month"
  data-calendar-markers='{"2026-08-19": ["success", "warning"]}'
>
  <div class="mw-calendar-header">
    <button
      type="button"
      class="mw-btn mw-btn-outline mw-btn-sm mw-calendar-nav"
      data-calendar-nav="-1"
      aria-label="Previous month"
    >
      <i class="fas fa-chevron-left"></i>
    </button>

    <div class="mw-calendar-title" aria-live="polite">August 2026</div>

    <button
      type="button"
      class="mw-btn mw-btn-outline mw-btn-sm mw-calendar-nav"
      data-calendar-nav="1"
      aria-label="Next month"
    >
      <i class="fas fa-chevron-right"></i>
    </button>
  </div>

  <div class="mw-calendar-grid">
    <div class="mw-calendar-weekday" aria-hidden="true">Mon</div>
    ...
    <div class="mw-calendar-weekday mw-calendar-weekend" aria-hidden="true">
      Sat
    </div>

    <button
      type="button"
      class="mw-calendar-day mw-calendar-adjacent"
      aria-label="Monday, 27 July 2026"
    >
      <span class="mw-calendar-date">27</span>
    </button>

    <button
      type="button"
      class="mw-calendar-day mw-calendar-today"
      aria-current="date"
      aria-pressed="false"
      aria-label="Wednesday, 19 August 2026"
    >
      <span class="mw-calendar-date">19</span>
      <span class="mw-calendar-dots">
        <span class="mw-calendar-dot mw-calendar-dot-success"></span>
        <span class="mw-calendar-dot mw-calendar-dot-warning"></span>
      </span>
    </button>
    ...
  </div>

  <div class="mw-calendar-legend">
    <span class="mw-calendar-legend-item">
      <span class="mw-calendar-dot mw-calendar-dot-success"></span>
      Slots free
    </span>
    ...
  </div>
</div>
```

| Class                     | Role                                                                                                                                                |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mw-calendar`             | Surface. Same border, radius and shadow as a card, without the hover lift                                                                           |
| `mw-calendar-plain`       | Drops the surface - for a calendar already sitting on a card or panel                                                                               |
| `mw-calendar-compact`     | Date picker density: dots hidden, 29px cells, tighter header and labels                                                                             |
| `mw-calendar-header`      | Arrow, title, arrow                                                                                                                                 |
| `mw-calendar-nav`         | Sits **on** `mw-btn` - only squares it off around the chevron                                                                                       |
| `mw-calendar-title`       | Takes the space between the arrows, stays optically centred                                                                                         |
| `mw-calendar-grid`        | The seven column grid; weekday labels and day cells are its only children                                                                           |
| `mw-calendar-weekday`     | Column label. Decorative - the day buttons carry the weekday themselves                                                                             |
| `mw-calendar-day`         | One day. A `button`, so `:disabled` gives you an unavailable day                                                                                    |
| `mw-calendar-date`        | The number                                                                                                                                          |
| `mw-calendar-adjacent`    | Day of the neighbouring month - muted, still readable                                                                                               |
| `mw-calendar-weekend`     | Saturday/Sunday. Tinted cell; on the label it turns the text secondary                                                                              |
| `mw-calendar-today`       | Outlined in the secondary colour, bold                                                                                                              |
| `mw-selected`             | Filled with the primary colour                                                                                                                      |
| `mw-calendar-dots`        | Dot row, absolutely placed at the bottom of the cell                                                                                                |
| `mw-calendar-dot`         | 5px dot. Colour comes from `--mw-calendar-dot`; the `-primary`, `-secondary`, `-success`, `-warning`, `-danger`, `-info` classes are presets for it |
| `mw-calendar-legend`      | Rule plus a row of dot/label pairs below the grid                                                                                                   |
| `mw-calendar-legend-item` | One dot/label pair                                                                                                                                  |

- **Today is outlined in secondary, the picked day is filled with primary.** Two
  different colours on purpose: an outline and a fill in the same colour read as
  two states of the same thing. Do not give one day both.
- The dots are positioned absolutely, so a day without any keeps the exact same
  height and its number sits on the same line as every other. Two or three per
  day stay readable, more do not. A dot on a picked day keeps its status colour;
  only the untoned one flips to the accent text colour.
- **What a dot means belongs to the caller.** The same calendar reads "request
  pending / booked / time offered" in a scheduling app and something entirely
  different on a public booking page, so the colour is a custom property, not a
  fixed set: `style="--mw-calendar-dot: #7a4fd4"` on the dot, or on the cell to
  colour all of its dots. The six tone classes are named presets for exactly
  that property - use them when they fit, ignore them when they do not.
- **Render the days spilling in from the neighbouring month.** An empty first
  row reads like a broken calendar, not like a short month. `mw-calendar-adjacent`
  is what pushes them back.
- A month gets six rows even when five would do, so the calendar - and
  everything under it - keeps its height while you page through.
- Cell height is fixed (38px, 44px on a coarse pointer, 29px compact), width
  follows the container. No aspect ratio: a full-width calendar would otherwise
  grow rows several hundred pixels tall. A calendar therefore wants a column,
  not the full page width - give it one, or cap it.
- **A week has no class of its own.** Render seven cells instead of forty-two
  and you have one; everything else is identical.
- `mw-calendar-compact` hides the dots and shortens the cell - the dots are what
  a full cell needs its height for, so the two go together. It costs about a
  third of the calendar height and leaves a plain date picker; drop the legend
  there, it has nothing left to explain. 29px is below a comfortable tap target,
  so keep it for pointer-first surfaces. Its grid gap drops to 2px as well, which
  puts the space back into the cells.
- Give every day an `aria-label` with the full date - the bare number is not an
  accessible name. The weekday labels are `aria-hidden`, they would only repeat
  it. With a `button` per day, keep one tab stop for the grid (roving
  `tabindex`) instead of 42.

## Tags

Two forms, picked by count - see also the pitfall list in `SKILL.md`.

**Single chip** (table cells, status columns) - carries its colour itself:

```html
<span class="mw-tag mw-tag-success">Paid</span>
```

Variants: `mw-tag-primary`, `-secondary`, `-success`, `-info`, `-warning`,
`-danger`, `-muted`, `-neutral`. Size: `mw-tag-lg`.

`mw-tag-muted` and `mw-tag-neutral` are not the same and the difference carries
meaning. **Muted** means the label steps back - draft, archived, a shortcoming
("no e-invoice"). **Neutral** is an identifier with no judgement attached and
keeps the normal text colour - a customer number, a document type, a price on a
category ("XRechnung" is a property, not a verdict). Both are also available on
the list container: `mw-tags-muted`, `mw-tags-neutral`.

**List** - the container carries the colour for all its items:

```html
<div class="mw-tags mw-tags-primary">
  <span class="mw-tags-item"
    ><i class="fas fa-check mw-tags-icon"></i>Angular</span
  >
  <span class="mw-tags-item mw-tags-removable">
    Kotlin
    <button type="button" class="mw-btn-mini mw-btn-mini-danger mw-tags-remove">
      <i class="fas fa-times"></i>
    </button>
  </span>
</div>
```

Container variants: `mw-tags-primary`, `-secondary`, `-success`, `-info`,
`-warning`, `-danger`, `-muted`, size `mw-tags-lg`. `mw-tags-remove` only
positions the button - its look comes from `mw-btn-mini` plus a colour variant.

Only a tag that is a link or a button reacts to the pointer; a `span` stays
still, so nothing suggests a click that does nothing.

**Filter chips** - a tag that does something is a `button.mw-tag` or `a.mw-tag`:
it gets the focus ring and a 36px floor on touch. `aria-pressed="true"` (or
`mw-active` on a link) fills it in its colour and puts a tick in front, so the
state never rests on colour alone:

```html
<button type="button" class="mw-tag mw-tag-success" aria-pressed="true">
  Paid
</button>
```

## Badges

A count or a status, not a label. See the pitfall list in `SKILL.md` for the
badge-versus-tag rule: a tag names something and sits in a row of its own kind,
a badge carries a number or a state and usually sits _on_ something.

```html
<span class="mw-badge mw-badge-danger">99+</span>
```

Colours: `mw-badge-primary` (the default), `-secondary`, `-success`, `-warning`,
`-danger`, `-info`, `-muted`, plus `mw-badge-outline`. Sizes: `mw-badge-sm`,
`mw-badge-lg`.

Round on one character, a pill from two on - a `min-width` the padding grows
past. The digits are `tabular-nums`, so a counter ticking 9 to 10 does not shift
what sits beside it.

**On an icon or a button:**

```html
<span class="mw-badge-anchor">
  <button class="mw-btn mw-btn-outline">
    <i class="fas fa-inbox"></i> Inbox
  </button>
  <span class="mw-badge mw-badge-danger mw-badge-float">5</span>
</span>
```

`mw-badge-anchor` on the thing being badged, `mw-badge-float` on the badge. It
hangs half off the corner and carries a ring in the surface colour, so it reads
as a separate object rather than a blob on the icon. The ring follows the
surface automatically inside a card, panel, modal, tile or the header.

**Status:**

```html
<span class="mw-badge-status mw-badge-status-success">
  <span class="mw-badge-dot"></span> Online
</span>
```

`mw-badge-status-{primary|secondary|success|warning|danger|info|muted}` colours
the dot inside it. A bare `mw-badge-dot-{colour}` works on its own too. Add
`mw-badge-pulse` for something actually running - a job, an open connection: a
ring grows out and fades while the dot underneath stays put, so a column of them
in a table stays readable. Not for decoration.

Under forced colours (Windows high contrast) a badge keeps a `CanvasText`
border and a dot keeps its fill in `CanvasText` - the system takes every
other fill away.

## Dropdown

Built on `<details>` / `<summary>`. That is where the keyboard handling, the
focus behaviour and the open state a screen reader can see come from, and it
works with JavaScript switched off. The framework script only adds Escape and
click-outside.

```html
<details class="mw-dropdown">
  <summary class="mw-btn mw-btn-primary">
    Actions <i class="fas fa-chevron-down mw-dropdown-caret"></i>
  </summary>
  <div class="mw-dropdown-menu">
    <div class="mw-dropdown-label">Manage</div>
    <button class="mw-dropdown-item"><i class="fas fa-pen"></i> Edit</button>
    <button class="mw-dropdown-item mw-active">Duplicate</button>
    <button class="mw-dropdown-item" disabled>Move</button>
    <hr class="mw-dropdown-divider" />
    <button class="mw-dropdown-item mw-dropdown-item-danger">
      <i class="fas fa-trash"></i> Delete
    </button>
  </div>
</details>
```

Parts: `mw-dropdown-menu`, `-item`, `-item-danger`, `-divider`, `-label`,
`-caret` (rotates with the open state on its own, and with
`aria-expanded="true"` on a trigger an app opens itself). Alignment:
`mw-dropdown-end` anchors the menu to the trigger's right edge,
`mw-dropdown-up` opens it upward.

`mw-active` (or `aria-checked="true"`, or `aria-current="page"`) marks the
current choice, for a menu that picks rather than acts. Icons inside items keep one column, so labels line up
whether or not every item has one.

Where the browser supports anchor positioning the menu is `position: fixed`,
anchored to its trigger and flipped into whichever side has room, so it escapes
a clipping ancestor by itself. Everywhere else it is absolutely positioned and
is clipped by any ancestor that hides its overflow. The framework's own containers lift that clip while a menu is open; on
your own it is `:has(.mw-dropdown[open]) { overflow: visible }`.

A `<kbd>` or `mw-dropdown-shortcut` at the end of an item sits right-aligned in
the muted ink and drops out on touch, where there is no keyboard to use it on:
`<button class="mw-dropdown-item"><i class="fas fa-copy"></i> Copy <kbd>Ctrl C</kbd></button>`.

The menu is at least 200px wide; `--mw-dropdown-min-width` on the dropdown or a
wrapper changes that. On a coarse pointer the rows grow to 2.75rem and the menu
takes at least the trigger's full width.

## Tooltip beside the trigger

`data-tooltip` itself is in `references/layout.md`. `mw-tooltip-inline-end`
puts the bubble next to the trigger instead of above it - for an icon rail,
where above would cover the item before it:

```html
<a
  class="mw-app-nav-link mw-tooltip-inline-end"
  href="/"
  data-tooltip="Dashboard"
>
  <i class="fas fa-gauge" aria-hidden="true"></i>
  <span class="mw-app-label">Dashboard</span>
</a>
```

It only acts where the browser has anchor positioning (Chrome 129, Firefox 147,
Safari 26): the bubble is then `position: fixed` and escapes the scrolling nav
it sits in. An absolute bubble would be cut off by that same scroll container,
so in the collapsed rail older browsers show no tooltip at all - the label stays
for a screen reader.

## Language switcher

A `mw-dropdown` with a quieter trigger: no fill and no border until it is
hovered, so a header bar does not turn into a row of competing buttons.

```html
<details class="mw-dropdown mw-dropdown-end mw-lang-switch">
  <summary aria-label="Language: Deutsch">
    <span class="mw-flag mw-flag-de"></span>
    <span class="mw-lang-switch-code">de</span>
    <i class="fas fa-chevron-down mw-dropdown-caret"></i>
  </summary>
  <div class="mw-dropdown-menu">
    <button
      type="button"
      class="mw-dropdown-item mw-active"
      aria-current="true"
      data-mw-lang="de"
    >
      <span class="mw-flag mw-flag-de"></span>
      <span class="mw-lang-switch-name" lang="de">Deutsch</span>
      <i class="fas fa-check mw-lang-switch-check"></i>
    </button>
    <button type="button" class="mw-dropdown-item" data-mw-lang="en">
      <span class="mw-flag mw-flag-gb"></span>
      <span class="mw-lang-switch-name" lang="en">English</span>
      <i class="fas fa-check mw-lang-switch-check"></i>
    </button>
  </div>
</details>
```

The two-letter code carries the state, not the flag: a flag is a country and
never a language - no country stands for English. Write each language name in
its own language and put `lang="fr"` on it, so a screen reader pronounces it
instead of spelling it out.

Parts: `mw-lang-switch-code`, `-name`, `-check` (the tick, shown by `mw-active`
on the item and kept in the layout while hidden). `mw-lang-switch-inverted` is
for a dark bar built without `mw-header`; inside `mw-header` those colours apply
on their own.

Flags: `mw-flag` plus `mw-flag-<iso>` for de, at, ch, gb, us, ie, fr, it, es,
pt, nl, be, pl, cz, hu, ro, bg, ua, se, dk, no, fi, tr and jp - CSS gradients, all
in the same 4:3 box whatever the real ratio. Never an emoji flag: Windows ships
no glyphs for them. Anything outside the set goes as an `<img>` or an inline
`<svg>` inside `mw-flag`.

## Keyboard keys

`<kbd>` is styled directly, so a shortcut in prose needs no class:

```html
<p>
  Press
  <span class="mw-kbd-group"
    ><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd></span
  >
  to open the palette, <kbd>Esc</kbd> to close.
</p>
```

`mw-kbd` is the same look for a `<span>` when the markup is not yours to change.
`mw-kbd-group` wraps a combination so the pluses are spaced and the whole thing
cannot wrap apart. `mw-kbd-pressed` shows a key mid-press - the raised bottom
edge drops and the key sits 1px lower.

## Info badges & counters

```html
<span class="mw-info mw-info-primary">Active</span>

<a href="/invoices" class="mw-info mw-info-counter mw-info-success">
  <div class="mw-info-value">150</div>
  <div class="mw-info-label">Invoices</div>
</a>

<span class="mw-info-mini mw-info-mini-danger"
  ><i class="fas fa-times"></i
></span>
```

- `mw-info`: sizes `mw-info-sm`, `-lg`, `-xl`; colours `mw-info-primary`,
  `-secondary`, `-success`, `-warning`, `-danger`, `-info` (tinted background +
  a 6px left border).
- `mw-info-counter` turns it into a big number over a small label
  (`mw-info-value`, `mw-info-label`). With `mw-info-sm` the counter shrinks to
  a row of key figures above a list.
- The cursor is `default` because a figure is usually not clickable. On `<a>`
  and `<button>` it turns into a pointer automatically; on anything else use
  `mw-info-clickable`.
- `mw-info-block` is the same surface carrying a paragraph: 68 characters
  wide, left-aligned, and it does not lift on hover. It sits at the left edge
  like everything else with running text in it - `mw-info-block-center` puts it
  back in the middle of its container.
- `mw-info-mini` is the 20px status dot: sizes `-sm`, `-lg`, `-xl`, colours
  `-primary`, `-secondary`, `-success`, `-warning`, `-danger`, `-info`.

## Progress

```html
<div class="mw-progress-container">
  <div class="mw-progress-barinfo">
    <span class="mw-progress-label">Completion</span>
    <span class="mw-progress-value mw-progress-percent">75</span>
  </div>
  <div class="mw-progress-bar">
    <div class="mw-progress-fill mw-progress-primary" style="width: 75%"></div>
  </div>
</div>
```

- The value element only prints what you put in it; `mw-progress-percent`
  appends `%`, `mw-progress-numeric` appends `/10`. Neither computes anything.
- The fill width is set by you (`style="width: 75%"`). The shipped JS instead
  reads `data-value="75"` and animates it into view - in a SPA bind the style.
- Colours: `mw-progress-primary`, `-secondary`, `-success`, `-warning`,
  `-danger`, `-info` (default fill is the secondary colour).
- Sizes on the container: `mw-progress-sm`, `mw-progress-lg`.
- `mw-progress-hide-info` on the info row hides the labels while keeping the
  layout; `mw-progress-inline-label` on the container puts the text inside the
  bar.
- `mw-progress-indeterminate` on the bar, with `role="progressbar"` and no
  `aria-valuenow`: a segment sweeps the track while nobody knows how long it
  takes, a still hatch where motion is off. `--mw-progress-indeterminate` sets
  its colour.
- `mw-progress-ring` draws `--mw-progress-value` as an arc and animates a new
  value (a registered property). Sizes `mw-progress-ring-sm` / `-lg`, colours
  `mw-progress-ring-primary` and the other five; tune `--mw-progress-ring-size`,
  `--mw-progress-ring-thickness`, `--mw-progress-ring-color`. In Angular:
  `[style.--mw-progress-value.%]="done()"`.
- Under forced colours fill, sweep and arc turn Highlight and the track gets an
  outline; a skeleton turns into GrayText blocks.

## Stat & meter

```html
<div class="mw-card mw-card-simple">
  <div class="mw-stat">
    <span class="mw-stat-label">Monthly revenue</span>
    <span class="mw-stat-value"
      >48.2<span class="mw-stat-unit">k EUR</span></span
    >
    <div class="mw-stat-footer">
      <span class="mw-stat-delta mw-stat-delta-up">+12.4%</span>
      <span class="mw-stat-note">vs. August</span>
    </div>
  </div>
</div>
```

- The value sizes to the stat's own width (`2xl` to `4xl` between 180 and
  420px), not to the window - the same markup in a sidebar and in a wide row.
  Digits are `tabular-nums`.
- `mw-stat-delta-up` / `-down` / `-flat`: the arrow shape carries the
  direction and the sign belongs in the text, so neither depends on colour. Up
  is success, down is danger; `mw-stat-delta-invert` swaps the two for a number
  where up is bad - churn, cost, open tickets.
- `mw-stat-chart` holds an inline `<svg>` sparkline: its `path`, `polyline` or
  `line` gets a 2px non-scaling stroke in the primary ink, whatever the viewBox.
- `mw-stat-group` around several stats lines them up with a rule between them
  once the group is 30rem wide, and stacks them with rules below that.

The meter is the native element, styled:

```html
<span id="storage-label">Storage</span>
<meter
  class="mw-meter"
  aria-labelledby="storage-label"
  min="0"
  max="10"
  low="7"
  high="9"
  optimum="0"
  value="3.1"
>
  3.1 of 10 GB
</meter>
```

- The tone is the browser's reading of `low`, `high` and `optimum`: optimum
  success, sub-optimum warning, worse danger - in Chromium, Safari and Firefox
  alike. No class decides it. With the optimum at 0 less is better, which is
  what a usage limit wants.
- 10px high like the progress bar; `mw-meter-sm` 6px, `mw-meter-lg` 15px. The
  label row above it is `mw-row-split`; point `aria-labelledby` at the label or
  a screen reader announces a bare value.
- A value with no thresholds - an upload, a step count - is `mw-progress-bar`.

## Chat

The pieces an assistant or support chat renders into. Streaming, scrolling and
sending stay the application's job.

```html
<div class="mw-chat" role="log" aria-label="Conversation">
  <div class="mw-chat-message mw-chat-message-user">
    <div class="mw-chat-body">
      <div class="mw-chat-meta"><strong>You</strong><time>09:41</time></div>
      <div class="mw-chat-bubble"><p>Which invoices are still open?</p></div>
    </div>
  </div>
  <div class="mw-chat-note">
    <i class="fas fa-magnifying-glass" aria-hidden="true"></i> Searched 42
    invoices
  </div>
  <div class="mw-chat-message">
    <span class="mw-avatar mw-avatar-xs mw-avatar-initials">AI</span>
    <div class="mw-chat-body">
      <div class="mw-chat-bubble"><p>Three are open.</p></div>
      <div class="mw-chat-actions"><!-- mw-btn-ghost icon buttons --></div>
    </div>
  </div>
</div>
```

- The bubble carries the surface silhouette, sharp on the corner the message
  comes from. `mw-chat-message-user` mirrors the row to the right and tints the
  bubble with the primary. Long URLs and `<pre>` blocks stay inside it.
- The bubble tone is `--mw-chat-bubble`: the card background on the page, the
  muted surface inside a card, panel, modal or tile.
- `mw-chat-note` is the quieter line for tool activity or a system event.
- `mw-chat-typing` takes three empty `<span>`s plus an `mw-sr-only` text;
  `mw-chat-thinking` sweeps a highlight across its own text. Both stand still
  under reduced motion and `mw-motion-off`.
- `role="log"` on the list is what makes a screen reader announce new messages.

```html
<form class="mw-chat-composer">
  <textarea class="mw-textarea" rows="1" aria-label="Message"></textarea>
  <div class="mw-chat-composer-bar">
    <button
      type="button"
      class="mw-btn mw-btn-ghost mw-btn-sm mw-btn-icon"
      aria-label="Attach"
    >
      <i class="fas fa-paperclip"></i>
    </button>
    <button
      type="submit"
      class="mw-btn mw-btn-primary mw-btn-sm mw-btn-icon"
      aria-label="Send"
    >
      <i class="fas fa-arrow-up"></i>
    </button>
  </div>
</form>
```

- Light in both themes like every field, with the focus halo on the whole box.
  The textarea grows with its text up to 12 lines (`field-sizing`); where that
  is missing it is a three-line box.
- The last item of `mw-chat-composer-bar` goes right - the send button.
  Attachments sit between as `mw-tag`s.
- `mw-chat-suggestions` is a wrapping row of `mw-btn` prompt chips, rounded off.

## Rating

```html
<div class="mw-rating-container">
  <p class="mw-rating-info">Product rating</p>
  <div class="mw-rating mw-rating-lg" data-rating="4">
    <i class="mw-rating-icon fas fa-thumbs-up" aria-hidden="true"></i>
    <!-- five icons total -->
  </div>
</div>
```

`data-rating` is `0`-`5` and highlights the first N icons - pure CSS, any icon
works. Sizes: `mw-rating-sm`, `mw-rating-lg`.

## Meta header

Small icon + text counters, e.g. under a page title.

```html
<div class="mw-meta-header">
  <div class="mw-meta-item">
    <i class="fas fa-list"></i><span>Total: 14</span>
  </div>
  <div class="mw-meta-item">
    <i class="fas fa-pen"></i><span>Drafts: 3</span>
  </div>
</div>
```

## Stepper

```html
<div class="mw-stepper">
  <div class="mw-stepper-step">
    <div class="mw-stepper-indicator mw-done"><i class="fas fa-check"></i></div>
    <span class="mw-stepper-label mw-done">Account</span>
  </div>
  <div class="mw-stepper-connector mw-done"></div>
  <div class="mw-stepper-step">
    <div class="mw-stepper-indicator mw-active">2</div>
    <span class="mw-stepper-label mw-active">Details</span>
  </div>
  <div class="mw-stepper-connector"></div>
  <div class="mw-stepper-step">
    <div class="mw-stepper-indicator">3</div>
    <span class="mw-stepper-label">Review</span>
  </div>
</div>
```

State classes here are prefixed: `mw-done`, `mw-active`; `aria-current="step"`
on a `mw-stepper-step` marks it as the current one too, for an app's markup.
Under forced colours the current step takes Highlight, done steps invert and the
connectors stay lines. The horizontal variant
needs the explicit `mw-stepper-connector` elements between the steps; the
vertical one (`mw-stepper-vertical`) draws the line itself and takes
`mw-stepper-content` with `mw-stepper-content-title` / `-desc` instead of a
label:

```html
<div class="mw-stepper-vertical">
  <div class="mw-stepper-step mw-done">
    <div class="mw-stepper-indicator mw-done"><i class="fas fa-check"></i></div>
    <div class="mw-stepper-content">
      <p class="mw-stepper-content-title">Dependencies installed</p>
      <p class="mw-stepper-content-desc">All packages resolved.</p>
    </div>
  </div>
</div>
```

## Timelines

`mw-timeline-big` and `mw-timeline-simple` are chronicles (CV, changelog), not
schedulable time axes.

```html
<div class="mw-timeline-big">
  <div class="mw-timeline-big-step mw-active">
    <div class="mw-timeline-big-date-container">
      <div class="mw-timeline-big-date-main">01/2023 - today</div>
      <div class="mw-timeline-big-date-sub">(3 years)</div>
    </div>
    <div class="mw-timeline-big-content">
      <div class="mw-card">...</div>
      <div class="mw-timeline-big-event">
        <span class="mw-timeline-big-event-date">05/2023</span>
        <span class="mw-timeline-big-event-title">Certification</span>
      </div>
    </div>
  </div>
</div>

<div class="mw-timeline-simple">
  <div class="mw-timeline-simple-step mw-active">
    <div class="mw-timeline-simple-date">2024-03-22</div>
    <div class="mw-timeline-simple-content">
      <div class="mw-card mw-card-simple">...</div>
    </div>
  </div>
</div>
```

The current step gets `mw-active` (bare `active` still works but is
deprecated). Any card fits into the content wrapper.

`mw-timeline-compact` is the third shape, for an activity feed or an audit log:
a dot and a time per line, as many lines as there are, no entrance to wait for.

```html
<ol class="mw-timeline-compact">
  <li class="mw-timeline-compact-item mw-timeline-compact-success">
    <time class="mw-timeline-compact-time" datetime="2026-09-29T09:41">
      Today 09:41
    </time>
    <div class="mw-timeline-compact-body">
      <strong>Mira Brandt</strong> approved invoice 2026-041
    </div>
  </li>
</ol>
```

Dot tones: `mw-timeline-compact-primary`, `-secondary`, `-info`, `-success`,
`-warning`, `-danger`. Under forced colours lines and dots take system colours
and the active date takes Highlight.

## Avatars

```html
<div class="mw-avatar mw-avatar-lg mw-avatar-primary">
  <img src="me.jpg" alt="" />
</div>

<div class="mw-avatar mw-avatar-initials mw-avatar-xs">MW</div>
```

- Sizes: `mw-avatar-xs` 32, `-sm` 64, default 96, `-lg` 144, `-xl` 210 px.
- Shape: `mw-avatar-square`.
- `mw-avatar-landscape` (3:2) and `mw-avatar-portrait` (9:16) for a photo that
  is not square - meant for `-lg` and `-xl`, with 20px corners that
  `mw-avatar-square` still sharpens. Both run larger than the round step:
  landscape `-lg` 273, `-xl` 399 px wide, shrinking to fit a narrower column;
  portrait `-xl` 242 px wide at 9:16, `-lg` 2:3 at 295 px tall.
- Every avatar carries the accent arc on its top-right corner, inside the frame
  (`--mw-corner-accent`). It stays as it is on hover.
- Colours `mw-avatar-primary`, `-secondary`, `-success`, `-warning`, `-danger`,
  `-info` tint the **border**. On `mw-avatar-initials` the same class also tints
  the **surface**, so both can be combined.
- `mw-avatar-initials` centers text and scales the font with the size class -
  the standard display for a signed-in user without a picture.
- `mw-avatar-group` overlaps its avatars; `mw-avatar-group-sm` / `-lg` change
  the overlap. `mw-avatar-more` closes a group with the count of the rest
  (`+4`) - give it `role="img"` and an `aria-label` that says it in words; on a
  plain `div` the label is ignored.
- Hover on an avatar **with an image** zooms the picture and sweeps a light
  across it. Nothing to switch on. It is skipped on `mw-avatar-initials`, on
  touch, under `prefers-reduced-motion` and under `mw-hover-static`.

## Date stamp

The date on a dated card - an event, a changelog entry, a day on a menu. It
answers to the **card**, not the viewport: narrow, it is a muted line above the
title; once the card is wide enough that a single column would leave its right
half empty, the same markup becomes a column on the left.

```html
<article class="mw-card mw-offer">
  <div class="mw-card-body">
    <p class="mw-date-stamp mw-date-stamp-today">
      <span class="mw-date-stamp-day">Fri</span>
      <span class="mw-date-stamp-date">18.09.</span>
    </p>
    <div class="mw-date-stamp-body">
      <h4 class="mw-text-base mw-text-bold mw-mb-2">Baked fish fillet</h4>
      <p class="mw-text-sm mw-text-muted mw-mb-0">In beer batter.</p>
    </div>
    <p class="mw-price mw-price-xs">
      <span class="mw-price-amount">11.90</span>
      <span class="mw-price-currency">Euro</span>
    </p>
  </div>
</article>
```

- `mw-date-stamp-body` wraps everything that is not the stamp or the price. It
  is `display: contents` on a narrow card, so the body still sees the title and
  the price as its own children - which is what `mw-offer` selects on. On a wide
  card it becomes the middle column.
- The price is a **sibling** of the wrapper, not inside it. Give the card one
  and it gets a third column at the right edge; leave it out and the card is two
  columns. With more than one dish per card, put the price on a
  `mw-leader-row` with the dish instead - an empty third track would still
  charge the card a gap.
- Write the day as `Fri`, not `FRI` - the uppercase is `text-transform`, so a
  screen reader still reads a word rather than three letters.
- Day column width, day font size, the column gap and the card's block padding
  all ramp with the **card**, from 420px to 900px wide, via
  `fluid-container()`. A narrow card in a wide window gets narrow-card sizing -
  which is the point of putting the switch in a container query at all.
- `mw-date-stamp-today` drops the muting for a **fill**: on a wide card it spans
  the full card height, rounded to the card's own left corners and cut square
  against the content. A text colour would compete with the price, which is
  already the brand colour.
- Cards in a stack want `mw-grid-even` next to `mw-grid-1`, or the card with the
  longer description ends up taller than the rest of the week.

## Contact

How to reach someone - postal address, phone, mail. It belongs on an
`<address>`, and undoing that element's italics is most of what the component
does; the rest is a label column wide enough that the values line up.

```html
<address class="mw-contact">
  <p class="mw-text-bold">Gasthaus Lamm</p>
  <p>Marktplatz 3<br />72622 Musterhausen</p>
  <p class="mw-contact-row">
    <span class="mw-contact-label">Phone</span>
    <a class="mw-link" href="tel:+497123456789">07123 456789</a>
  </p>
</address>
```

- `<address>` is for the contact details of its nearest `<article>` or of the
  page - not for any postal address that happens to be on it.
- The label column is 5rem and fixed. An auto column is as wide as its own word,
  so "Phone" and "Email" would start their values in different places.
- Wrap phone and mail in `tel:` and `mailto:` links and mark them `mw-link` -
  in a block of plain lines an unstyled link reads as text.
- Opening hours are **not** part of this. A day, its times and a line between
  them is a `mw-leader-row` in a `<dl>`, one row per day, and a note for the
  rest.

## Item lists

Layout containers for arbitrary children - the children need no classes.

| Class                     | Look                                                          |
| ------------------------- | ------------------------------------------------------------- |
| `mw-item-list`            | Plain flex column with gaps                                   |
| `mw-item-list-horizontal` | Row, wrapping; column below `sm`                              |
| `mw-item-list-cards`      | Wider gaps, for cards                                         |
| `mw-item-list-compact`    | Bordered card-surface box, divided rows, hover indent (nests) |
| `mw-item-list-menu`       | Elevated menu card, pointer cursor, press feedback            |
| `mw-item-list-slide`      | Cards sliding sideways with an accent border on hover         |
| `mw-item-list-scroll`     | Scroll box, 300px tall                                        |

Modifiers are additive - keep the base class and add the modifier:
`mw-item-list-scroll` + `-sm` (200px), `-lg` (400px) or `-xl` (500px), and
`mw-item-list-slide` + `-secondary` for the secondary accent.

```html
<div class="mw-item-list-compact">
  <div>Quick settings</div>
  <div>
    Privacy
    <div class="mw-item-list-compact">
      <div>Cookies</div>
    </div>
  </div>
</div>
```

**Checkbox lists** are the one variant with required inner markup - a `<ul>` of
`<li>` each holding a `mw-checkbox`:

```html
<ul class="mw-item-list-checkbox">
  <li class="mw-selected">
    <label class="mw-checkbox">
      <input type="checkbox" checked />
      <span class="mw-checkbox-box"></span>
      <div class="mw-checkbox-content">
        <h4 class="mw-checkbox-header">Task management</h4>
        <p class="mw-checkbox-label">Track your daily tasks</p>
      </div>
    </label>
  </li>
</ul>
```

Add `mw-item-list-checkbox-compact`, `-large` or `-secondary` alongside the
base class; `mw-item-list-checkbox-scroll` is a standalone class that replaces
it. `mw-selected` on the `<li>` is the selected-row highlight - bind it to the
checkbox state yourself in a SPA. The `mw-checkbox-content` block is optional;
a bare `mw-checkbox-label` renders a single-line row.

The `mw-checkbox` inside is the ordinary form-element checkbox, so `disabled`
on the input, `indeterminate` and the colour variants (`mw-checkbox-success`
and the rest, see `references/forms.md`) work here too. Row height is a list concern -
use the list's own `-compact` / `-large` modifiers rather than
`mw-checkbox-sm` / `-lg`, which sit on the wrong element to reach the box.

## Leader row

A label on the left, its value on the right, a dotted line bridging the gap -
the row a menu, a table of contents and an invoice all draw. The markup is two
spans; the line is the row's own `::before`, so it stays out of the
accessibility tree and no filler element needs `aria-hidden`.

```html
<p class="mw-leader-row mw-leader-row-top">
  <span class="mw-leader-row-label mw-text-bold">Roast pork with dumpling</span>
  <span class="mw-leader-row-value mw-text-bold mw-text-primary">17.50</span>
</p>
```

- Label and value is what `<dl>` is for, and since HTML 5.2 a `<div>` may group
  a `<dt>` and its `<dd>` inside one - so the semantic version costs no extra
  element over the `<p>`. Put `mw-leader-row` on that `<div>`. Use it where the
  pair **is** the content; where every row also carries a description, a `<p>`
  stays simpler.
- `mw-leader-row-top` keeps the value beside the **first** line of a wrapping
  label instead of the last. On a menu that is where the price belongs - next to
  the dish, not somewhere down in its description.
- A second `mw-leader-row-value` needs no extra class. Both sit after the
  leader, with a mark in the leader's colour between them - "11.30 - 14.00 |
  17.00 - 23.00". Without it the pair reads as one long range.
- Values are set in tabular figures and never break, so a column of them lines
  up. The label wraps between its words and stops at its longest one; past that
  the whole row wraps, with the values dropping under the label. Nothing shrinks
  to one letter per line.
- Keep `mw-price` out of a leader row: it sets its own baseline and the leader
  would no longer meet it. Plain text in the value span, or the price in a
  column of its own.

`mw-leader-row-dashed` and `mw-leader-row-solid` swap the line style; a single
row retunes with `--mw-leader-row-color`, `--mw-leader-row-style` and
`--mw-leader-row-width`.

## HTML lists

`mw-list` is the base (spacing for `li`), combined with one of:
`mw-list-unstyled`, `mw-list-inline`, `mw-list-link` (underlined anchors),
`mw-list-dot` (coloured markers), `mw-list-check` (✓ prefix).

```html
<ul class="mw-list mw-list-check">
  <li>Done</li>
</ul>
```

## Breadcrumbs

```html
<nav class="mw-breadcrumbs mw-breadcrumbs-collapse" aria-label="Breadcrumb">
  <ol class="mw-breadcrumbs-list">
    <li class="mw-breadcrumbs-item">
      <a href="/"><i class="fas fa-home"></i></a>
    </li>
    <li class="mw-breadcrumbs-item">
      <a href="/invoices"><span>Invoices</span></a>
    </li>
    <li class="mw-breadcrumbs-item mw-breadcrumbs-current">
      <a href="#" class="mw-breadcrumbs-active"><span>2026-001</span></a>
    </li>
  </ol>
</nav>
```

The current item takes `mw-breadcrumbs-current` on the `li` and
`mw-breadcrumbs-active` on the anchor, or `aria-current="page"` on the anchor -
the one a trail an app renders will carry anyway. Position alone marks nothing,
so a last item that is not the current page stays a link. Under forced colours
the current entry is underlined. `mw-breadcrumbs-sm` is the small variant,
`mw-breadcrumbs-collapse` hides middle items on narrow screens.

## Pagination

`mw-pagination` is a titled content frame with prev/next controls. Same
surface and header as `mw-calendar`; only the body differs, and the body is
yours. A numbered page list is `mw-pagination-pages`, below.

```html
<div class="mw-pagination">
  <div class="mw-pagination-header">
    <button
      type="button"
      class="mw-btn mw-btn-outline mw-btn-sm mw-pagination-nav"
      aria-label="Previous week"
    >
      <i class="fas fa-chevron-left"></i>
    </button>

    <div class="mw-pagination-title" aria-live="polite">Week 10</div>

    <button
      type="button"
      class="mw-btn mw-btn-outline mw-btn-sm mw-pagination-nav"
      aria-label="Next week"
    >
      <i class="fas fa-chevron-right"></i>
    </button>
  </div>

  <div class="mw-pagination-content">...</div>
</div>
```

- `mw-pagination-nav` sits **on** `mw-btn` - it only squares the button off
  around the chevron. The arrows carry no accessible name of their own, so give
  each one an `aria-label`; `aria-live="polite"` on the title is what tells a
  screen reader where you landed.
- `mw-pagination-loading` goes on `mw-pagination-content` (not on the
  container) and dims it while the next page is on its way.
- `mw-pagination-slide-left` / `-slide-right` are the directional transitions,
  also on the content.
- The body has a 200px floor so a short page does not collapse the frame. Paging
  is application state - the framework ships no JavaScript for it.

**Numbered pages** - `mw-pagination-pages` for a list or a table:

```html
<nav class="mw-pagination-pages" aria-label="Pages">
  <a
    class="mw-btn mw-btn-outline mw-pagination-nav"
    href="?page=2"
    aria-label="Previous page"
    ><i class="fas fa-chevron-left"></i
  ></a>
  <span class="mw-pagination-status">Page 3 of 12</span>
  <a class="mw-pagination-page" href="?page=1">1</a>
  <a class="mw-pagination-page" href="?page=3" aria-current="page">3</a>
  <span class="mw-pagination-gap" aria-hidden="true">&hellip;</span>
  <a class="mw-pagination-page" href="?page=12">12</a>
  <a
    class="mw-btn mw-btn-outline mw-pagination-nav"
    href="?page=4"
    aria-label="Next page"
    ><i class="fas fa-chevron-right"></i
  ></a>
</nav>
```

`aria-current="page"` (or `mw-active`) marks where you are,
`aria-disabled="true"` dims an arrow that leads nowhere. Below `sm` the numbers
give way to `mw-pagination-status` between the arrows; on touch the page
buttons are 44px.

## Divider

```html
<hr class="mw-divider mw-divider-dashed" />
<div class="mw-divider-text"><span>or</span></div>
<div class="mw-divider-vertical"></div>
```

Variants: `mw-divider-thick`, `mw-divider-dashed`, `mw-divider-primary`,
`mw-divider-secondary`. `mw-divider-text` is a labelled rule (the colour
variants apply to it too), `mw-divider-vertical` needs a flex row with a height.

## Gallery & image slider

```html
<div class="mw-gallery-container">
  <div class="mw-gallery">
    <button type="button" class="mw-gallery-navi mw-gallery-navi-prev">
      &#10094;
    </button>
    <div class="mw-gallery-track">
      <div class="mw-gallery-slide" data-desc="Mountains">
        <img src="1.jpg" alt="" />
      </div>
    </div>
    <button type="button" class="mw-gallery-navi mw-gallery-navi-next">
      &#10095;
    </button>
  </div>
  <div class="mw-gallery-desc">Mountains</div>
  <div class="mw-gallery-dots"></div>
</div>
```

The dots (`mw-gallery-dot`, active one gets `mw-active`) are generated by the
shipped JS, as is the track transform. In a SPA, render the dots and set
`transform: translateX(...)` yourself. Swipe is single-finger and decided by the
dominant axis, so a page scroll that drifts sideways does not page the gallery.

`mw-gallery-container` is a query container (`mw-gallery`), and the caption size,
the dot size and the 4:3 crop follow _its_ width - 688px and 512px - not the
viewport. A gallery in a half-width column therefore takes its narrow layout
there. Keep the wrapper: a container query only reaches descendants, and the
caption and the dots are siblings of `mw-gallery`.

`mw-image-slider` swaps a base image against overlays through indexed buttons:

```html
<div class="mw-image-slider">
  <div class="mw-image-slider-base" data-index="0">
    <img class="mw-image-slider-base-image" src="base.jpg" alt="" />
  </div>
  <div class="mw-image-slider-overlay">
    <div class="mw-image-slider-overlay-image mw-active" data-index="1">
      <img src="a.jpg" alt="" />
    </div>
  </div>
  <div class="mw-image-slider-controls-grid-3">
    <button class="mw-btn mw-btn-primary mw-active" data-index="0">Base</button>
  </div>
</div>
```

Control grids: `mw-image-slider-controls-grid-2`, `-grid-3`. Visible overlay and
current button carry `active`. `mw-image-slider` is its own query container
(`mw-slider`): the three heights (250 / 320 / 370px) and the control columns
switch at 420px and 560px of slider width, because the slider caps at 600px and
past a tablet the viewport says nothing about the room it has.

## Mosaic

Photos of any shape in one grid; a tap opens the lightbox.

```html
<div class="mw-mosaic">
  <figure class="mw-mosaic-item mw-mosaic-big">
    <a href="ridge-full.jpg">
      <img
        src="ridge.jpg"
        alt="Mountain range at sunrise"
        width="800"
        height="450"
        loading="lazy"
      />
    </a>
    <figcaption>First light on the ridge.</figcaption>
  </figure>
  <figure class="mw-mosaic-item">…</figure>
</div>
```

- Two columns on a phone, four at most, from the width of the box it sits in.
- The script shapes each tile from the photo's proportions - the `width` and
  `height` attributes, else the natural size once loaded: `mw-mosaic-wide` from
  1.3:1, `mw-mosaic-tall` from 1:1.25, square otherwise. A shape class set by
  hand wins; `mw-mosaic-big` (2×2) is only ever set by hand. Without the script
  every tile is square.
- `grid-auto-flow: dense` fills the holes and moves tiles away from their source
  order. `reading-flow: grid-rows` makes Tab follow the eye where the browser
  has it (Chromium so far).
- Gaps: `mw-mosaic-gap-sm`, `-gap-lg`.
- The tile crops, the lightbox does not. The `figcaption` is hidden in the tile
  and shown in the lightbox.
- In an application that opens its own viewer the tile holds a `<button>`
  instead of the link - same tile, same press state. Without the script the
  application picks `mw-mosaic-wide` / `-tall` itself, at the same ratios.

### Lightbox

A click on a link that holds an image - inside `mw-mosaic` or any element with
`data-mw-lightbox` - opens the photo full screen instead of following the link.
The script builds the viewer once, a `<dialog class="mw-lightbox">`, with one
slide per image of the group in reading order, the full image from the link's
`href` and the caption copied from the `figcaption`. Swipe, arrow keys or the
arrows page through it; Escape, the cross or a click on the stage beside the
photo close it, and focus returns to the tile of the last photo viewed. A click
with a modifier key stays a link.

Without `main.js`, build it yourself: a `<dialog class="mw-lightbox">` holding
`mw-lightbox-bar` (with `mw-lightbox-prev`, `mw-lightbox-count`,
`mw-lightbox-next` and `mw-lightbox-close`, all `mw-overlay-btn`) and
`mw-lightbox-track` with one `<figure class="mw-lightbox-slide">` per photo. The
track is a scroll-snap strip; the page scroll is locked while the dialog is open.

## Portrait gallery

```html
<div class="mw-portrait-gallery">
  <div
    class="mw-portrait-gallery-track"
    tabindex="0"
    aria-label="Portrait photos"
  >
    <figure class="mw-portrait-gallery-slide">
      <img
        src="cape.jpg"
        alt="Lighthouse on a cliff at dusk"
        width="600"
        height="800"
        loading="lazy"
      />
      <figcaption>
        <strong>North Cape</strong>
        The lamp comes on just after the sun goes.
      </figcaption>
    </figure>
  </div>
</div>
```

- Upright 3:4 slides in a native scroll-snap strip, the next one peeking in.
  One slide below 560px of gallery width, two and a quarter from there, three
  from 880px - a container query, so a gallery in a narrow column stays at one.
  The height is capped at 78svh, which a landscape phone needs.
- `mw-portrait-gallery-tall`: 9:16, for stories, reels and screenshots. A
  `<video>` works in place of an `<img>`.
- Gaps: `mw-portrait-gallery-gap-sm`, `-gap-lg`.
- The script adds the arrows (`mw-portrait-gallery-prev` / `-next`, for a mouse
  only) and the dots (`mw-portrait-gallery-dots` / `-dot`, below 560px, the
  current one `mw-active`).
- A photo more than 1.4× off the slide's shape is shown whole over a blurred
  copy of itself instead of cropped: the script sets `mw-fit-contain` on the
  slide and prepends a `mw-fit-backdrop` image, and checks again on every
  resize. `mw-fit-contain` set by hand forces it, `mw-fit-cover` on the slide
  turns it off.

## Photo feed

The three-column grid from a phone's photo app, in a framed box that scrolls.

```html
<div class="mw-feed">
  <div class="mw-feed-item">
    <button type="button" popovertarget="post-cape">
      <img
        src="cape.jpg"
        alt="Lighthouse on a cliff at dusk"
        width="600"
        height="800"
        loading="lazy"
      />
    </button>
    <figure class="mw-feed-post" id="post-cape" popover>
      <button
        type="button"
        class="mw-overlay-btn mw-feed-post-close"
        popovertarget="post-cape"
        popovertargetaction="hide"
        aria-label="Close"
      >
        &#120299;
      </button>
      <img
        src="cape.jpg"
        alt="Lighthouse on a cliff at dusk"
        width="600"
        height="800"
        loading="lazy"
      />
      <figcaption>
        <p>Stood there until the lamp came on.</p>
        <time datetime="2026-08-12">12 August 2026</time>
      </figcaption>
    </figure>
  </div>
</div>
```

- 3:4 tiles, 2px apart; `mw-feed-square` for square ones.
- Past three rows the box scrolls, with a strip of the next row in view so it
  reads as scrollable. `mw-feed-rows-2` shows two rows, `mw-feed-plain` drops
  the frame.
- No script: the tile is a button with `popovertarget`, the post a `popover`.
  In Angular that is `[attr.popovertarget]` and a matching `[id]`. A tile can be
  an `<a>` to a page of its own instead.
- `time` and `small` in the caption are set as a muted line. The page scroll is
  locked while a post is open.

## Story archive

```html
<div class="mw-stories" aria-label="Story archive">
  <button type="button" class="mw-story" popovertarget="story-coast">
    <span class="mw-story-cover"><img src="beach.jpg" alt="" /></span>
    <span class="mw-story-label">Coast</span>
  </button>
  <div class="mw-story-reel" id="story-coast" popover>
    <div class="mw-story-reel-head">
      <span>Coast</span>
      <label class="mw-overlay-btn mw-story-reel-pause"
        ><input type="checkbox" aria-label="Pause"
      /></label>
      <button
        type="button"
        class="mw-overlay-btn"
        popovertarget="story-coast"
        popovertargetaction="hide"
        aria-label="Close"
      >
        &#120299;
      </button>
    </div>
    <img src="beach.jpg" alt="Beach at sunset" loading="lazy" />
    <video
      src="sunrise.mp4"
      poster="sunrise.jpg"
      autoplay
      muted
      loop
      playsinline
    ></video>
  </div>
</div>
```

- The row scrolls sideways, with a shadow on the side that has more behind it;
  a mouse gets a thin scrollbar.
- Playback is CSS: every frame shows for five seconds, a segmented bar in the
  head counts them off, and holding the story (`:active`) or ticking the pause
  checkbox stops it. Full screen on a phone, phone-shaped (9:16) from `sm` up.
- Twelve frames at most - the timing is written out for twelve. Later frames
  are hidden and the story ends after the twelfth.
- Under `prefers-reduced-motion` nothing plays: the frames become a vertical
  strip to swipe, and the bar follows the scroll where the browser has scroll
  timelines.
- The script adds tap zones (`mw-story-reel-prev` on the left 30%, `-next` on
  the rest), arrow keys, focus on the close button when the story opens, a video
  that starts when its frame comes up and stops with the story, and closes the
  story at its end.

## Presentation deck

A deck is a page of its own: `mw-deck` on `<body>` plus `mw-deck-landscape`
(tablet, laptop, projector) or `mw-deck-portrait` (phone). Modules:
`components/deck` (pulls in `deck-blocks` and `buttons`) for the deck page,
`components/deck-frame` (pulls in `cards`) for the page that embeds it.

```html
<body class="mw-deck mw-deck-landscape">
  <header class="mw-deck-head">
    <span class="mw-deck-brand">Northwind<small>Wholesale offer</small></span>
    <div class="mw-deck-tools">
      <span class="mw-deck-counter">01 / 10</span>
      <button
        type="button"
        class="mw-deck-btn"
        data-deck-fullscreen
        aria-label="Fullscreen"
      >
        <svg class="mw-deck-icon-expand" viewBox="0 0 24 24">…</svg>
        <svg class="mw-deck-icon-collapse" viewBox="0 0 24 24">…</svg>
      </button>
    </div>
  </header>
  <main class="mw-deck-slides">
    <section class="mw-slide mw-slide-split" aria-label="Title">
      <div class="mw-deck-media" data-deck-in="2"><svg>…</svg></div>
      <div>
        <p class="mw-deck-kicker" data-deck-in><b>01</b> Espresso</p>
        <h1 class="mw-deck-title mw-deck-title-xl" data-deck-in="2">
          Coffee they <em>come back for.</em>
        </h1>
      </div>
    </section>
  </main>
  <footer class="mw-deck-foot">
    <div class="mw-deck-progress"></div>
    <div class="mw-deck-arrows">
      <button
        type="button"
        class="mw-deck-btn"
        data-deck-prev
        aria-label="Previous"
      >
        …
      </button>
      <button
        type="button"
        class="mw-deck-btn"
        data-deck-next
        aria-label="Next"
      >
        …
      </button>
    </div>
  </footer>
  <div class="mw-deck-rotate" role="note">…</div>
</body>
```

Portrait wraps head and slides in `mw-deck-stage` with an empty
`mw-deck-segments` first, and puts an optional `mw-deck-aside`
(`mw-deck-kicker`, `mw-deck-aside-title`, a `p`, `mw-deck-arrows`, a link)
before the stage - it shows from `lg` next to the phone.

- **Slides** `mw-slide`. Layout (landscape): `-split` (two columns),
  `-reverse` (first child to the right), `-stack` (head row, content row),
  `-statement` (to the lower edge, portrait too), `-cover` (the first
  `mw-deck-image` fills the slide). Surface: `-surface` (card), `-dark` (the
  header bar's colour), `-primary`, `-cover`. Head, foot and segments take the
  surface of the slide on screen by themselves.
- **Blocks** `mw-deck-kicker` (`b` = number in the brand), `-title` (+`-xl`,
  `em`/`strong` in the brand, `mw-deck-unit`), `-lead`, `-text`, `-media`,
  `-image` (+`-right`, `-zoom`, `-top`, `-top-tall`), `-images` (one wide over
  two, `figcaption`), `-facts` (`dl`, +`-3`), `-figures` (`dl`, value in `dd`
  after `dt`), `-columns`, `-list`, `-chips`, `-actions` (holds `mw-btn`),
  `-jumps` (buttons with `data-deck-goto`, `mw-deck-jump-hint`), `-steps`
  (`ol`), `-notes` (`ol`, numbered like `mw-deck-marker`), `-table`
  (+`mw-deck-table-total` row), `-quote` + `-source`, `-price`, `-package`
  (+`-highlight`), `-legend` (+`-bar`, `-line`), `-swipe`, `-bottom`.
- **Drawings** `mw-deck-drawing` + `mw-deck-draw`: `mw-deck-stroke`,
  `-stroke-bold`, `-stroke-fine` with `pathLength="1"` draw themselves, then
  `mw-deck-area` (+`-muted`, `-light`), `mw-deck-marker` and `text` fade in.
  `mw-deck-dashed` never animates. `mw-deck-illustration` keeps its own
  colours, `mw-deck-flow` runs a dashed line, `mw-deck-cascade` fades its
  children in one by one.
- **Chart** `mw-deck-chart` with `mw-deck-chart-grid`, `-bars` (a `g` per
  column holding `-hit` and `-bar`), `-line`, `-point`, `-value`. Bars in the
  primary, the line in the secondary colour. The SVG is generated, not drawn.
- `data-deck-in` (value 2-7 for later) fades an element in when its slide
  comes up - only once the script added `mw-deck-ready`.
- Knobs on `.mw-deck`: `--mw-deck-title-weight`, `-title-tracking`,
  `-title-leading`, `-title-case`, `--mw-deck-radius`. Colours and fonts come
  from the theme tokens, nothing else to set.
- The chrome - progress, done segments, `mw-deck-counter-current`, the round
  `mw-deck-btn` under the pointer - wears the second colour.
  `mw-deck-accent-primary` on the deck keeps it to the first, `mw-accent-single`
  on `<html>` does the same site-wide.
- The script sets `mw-deck-ready` and `mw-deck-fullscreen`. Before that - or
  when it never runs - the slides keep their scrollbar and the controls that
  need it stay hidden, so the deck still pages by hand.
- Embedding: `<div class="mw-deck-frame"><iframe src="…" allow="fullscreen"
loading="lazy" title="…"></iframe></div>`, `mw-deck-frame-portrait` for a
  phone deck, both inside `mw-deck-embed` with `mw-deck-embed-info` and
  `mw-deck-embed-actions` beside it. `mw-deck-card` on an `mw-card` link keeps
  the 4:3 preview uncropped.

## Device frames

A laptop and a phone drawn in CSS with a page on the glass - for showing a
site the way people meet it. Module `components/devices`.

```html
<div class="mw-devices">
  <div class="mw-device mw-device-laptop">
    <span class="mw-device-screen">
      <img src="shots/desktop.png" alt="The homepage on a laptop" />
    </span>
  </div>
  <button
    type="button"
    class="mw-device mw-device-phone"
    aria-label="Scroll through the phone view"
  >
    <span class="mw-device-screen">
      <img src="shots/phone.png" alt="" />
    </span>
  </button>
</div>
```

- `mw-devices` stands the phone over the laptop's lower right corner, at
  22% of the width; under 30rem it moves below the laptop. Both frames also
  stand alone: `mw-device-laptop` fills its column, `mw-device-phone` takes up
  to 22rem, centred.
- The glass is `mw-device-screen` (a `span`, so it fits inside a button).
  An `img` or `video` in it is a full-page screenshot: as wide as the glass,
  clipped below. An `iframe` is the live page, laid out at
  `--mw-device-viewport` (1280px, the phone sets 390px) and scaled to the
  glass - it scrolls by hand like the real thing.
- **Tour.** While the pointer rests on the laptop the screenshot scrolls to
  its end (fine pointer only, off under reduced motion). A device written as a
  `<button>` tours on a tap: `mw-active` from the script, to the end at
  `--mw-device-tour` (7s, on the motion scale), a pause, and back. A bobbing
  chevron on the glass says it can be tapped and goes while the tour runs.
  Without the script the button does nothing; the hover still works.
- The frames are hardware-coloured in both themes. The shadow is
  `--mw-elevation-4`, so the dark theme gets its light rim.
- Screenshots: take the desktop one at 1280px wide and the phone one at
  390px, full page - the aspect of the glass is 16:10 and 9:19.5, anything
  taller scrolls.

## Before & after

Two pictures of one place on a single frame, split where the reader drags - the
renovated bathroom, the cleared garden, the restored facade:

```html
<div class="mw-compare mw-aspect-video">
  <img class="mw-compare-before" src="before.jpg" alt="The bathroom before" />
  <img class="mw-compare-after" src="after.jpg" alt="The bathroom after" />
  <span class="mw-compare-label">Before</span>
  <span class="mw-compare-label mw-compare-label-after">After</span>
  <input
    type="range"
    class="mw-compare-range"
    min="0"
    max="100"
    value="50"
    aria-label="Move the split between before and after"
  />
</div>
```

- The control is a native range laid invisibly over the whole frame: a finger,
  a mouse and the arrow keys move it, a screen reader reads the value. It needs
  its `aria-label`. The focus ring shows on the round handle.
- main.js writes the value to `--mw-compare-position` (default 50%), which
  clips the after picture and places the line and the handle. Without the
  script the frame stays at 50/50; in a SPA set the property on `input`.
- The frame needs a height - an `mw-aspect-*` class or your own. Both slots
  take an `img` or a wrapper around one (a `<picture>`), covered with
  `object-fit: cover`.
- The frame has the surface silhouette without the arc, `radius('md')` under
  `mw-corners-even`. Labels sit on a dark translucent chip that reads on any
  photo; `mw-compare-label-after` moves one to the right.
- Vertical swipes still scroll the page on a phone (`touch-action: pan-y`).

## Marquee

A strip that keeps moving: partner logos, seals, the one line from a review
everybody should read.

```html
<div class="mw-marquee" role="region" aria-label="Partners" tabindex="0">
  <div class="mw-marquee-track">
    <ul class="mw-marquee-group">
      <li class="mw-marquee-item"><img src="partner.svg" alt="Partner" /></li>
      ...
    </ul>
    <!-- the same items again, for the seam -->
    <ul class="mw-marquee-group" aria-hidden="true" inert>
      <li class="mw-marquee-item"><img src="partner.svg" alt="" /></li>
      ...
    </ul>
  </div>
</div>
```

- The items go in twice. Sliding the track by half its width puts the copy
  where the original started, so the loop has no seam; `aria-hidden` and
  `inert` keep a screen reader and the keyboard on the first group. Each group
  is at least as wide as the strip, so a short list leaves no gap.
- `--mw-marquee-duration` (40s, on the motion scale), `--mw-marquee-gap`,
  `--mw-marquee-fade` (the soft mask at both edges),
  `--mw-marquee-logo-height` (2.25rem). `mw-marquee-reverse` runs the other way.
- The pointer or the focus on the strip holds it still. `tabindex="0"` makes
  the strip focusable when nothing inside it is - without it a keyboard cannot
  stop a loop that never ends (WCAG 2.2.2).
- Logos are greyscale and come into colour under a fine pointer. Text items
  take the muted ink, an icon inside one (`i`, inline `svg` or `.mw-icon`) the
  primary.
- Under reduced motion or `mw-motion-off` nothing moves: the first group wraps
  centred and the copy is hidden.

## Occasions

Seasonal decoration on every surface, switched by one class on `<html>`:
`mw-occasion-snow`, `-christmas`, `-newyear`, `-spring`, `-easter`, `-summer`,
`-autumn`, `-football`, `-birthday`, `-anniversary`. Module
`components/occasions`, about 9 kB gzipped - mostly inline SVG, so the CSP's
`img-src` has to allow `data:`.

- **Surfaces**: `mw-card`, `mw-panel`, `mw-testimonial`, unless nested in one
  another; anything else opts in with `mw-occasion-spot`, one opts out with
  `mw-occasion-skip`. The piece is the surface's `::before`, top left - the
  top right carries the signature arc. Snow, garland and bunting cover
  `min(400px, max(40%, min(50%, 384px)))` of the top edge.
- **While one is on**, surfaces get 2-9px more `margin-top`, `mw-panel` gets
  `overflow: visible`, panel headers and testimonials as much top padding as
  the piece hangs in. A slight overlap with the heading is intended.
- **One surface only**: the effect class on the surface itself
  (`<div class="mw-card mw-occasion-easter mw-occasion-lg">`), size and scroll
  too. It skips the site's occasion; intro and particles stay off.
- `mw-occasion-scroll`: pieces land as their surface scrolls in, main.js adds
  particles scrubbed by the page scroll. Without scroll timelines (Firefox,
  Safari before 26) main.js drives both: an observer plays the arrival once a
  surface enters, and the particles are paused animations parked at the
  scroll progress it writes. `mw-occasion-waiting`, `-arriving` and
  `mw-occasion-driven` are set by the script, never by the markup.
- `mw-occasion-sm` / `-lg` set `--mw-occasion-scale` (0.88 / 1.1, piece size)
  and `--mw-occasion-amount` (0.55 / 1.3: snow depth, drips, baubles,
  particles). main.js reads the amount from CSS - any value set there counts.
- `data-mw-occasion-intro`: five seconds over the page, once per visit; the
  value `preview` plays on every load. Click-through, gone on any input.
- `--mw-occasion-color-1..5` colour confetti, bunting and balloons,
  `--mw-occasion-flag-1..3` the football stripe (black, red, gold).
- Reduced motion: static only. Save-Data: no intro.

**Scheduled**: the entries go on `<html>` as `data-mw-occasions`, and
`src/js/occasions.js` - a classic script in `<head>` - sets today's classes
before the first paint. main.js does not schedule; without the head script
the attribute does nothing.

```json
[
  {
    "effect": "christmas",
    "from": "2026-12-18",
    "until": "2026-12-26",
    "yearly": true,
    "scroll": true,
    "intro": true,
    "size": "sm"
  }
]
```

Local days, `until` included; `yearly` keeps month and day and may run over
New Year; the shortest active window wins; unknown effects are skipped.
Preview on any page with main.js:
`?mw-occasion=autumn&mw-occasion-size=lg&mw-occasion-scroll&mw-occasion-intro`.

## Overlay button

`mw-overlay-btn` is the round 44px button that sits on a photo - dark and
translucent in both themes, with light ink and an inline `<svg>` sized for it.
`:disabled` hides it. The lightbox, the portrait gallery, the feed post and the
story reel use it for their close and arrow buttons.

## Blog post

```html
<article class="mw-blog-post">
  <h2 class="mw-blog-post-title">Title</h2>
  <div class="mw-blog-post-header">
    <div class="mw-blog-post-header-icon"><i class="fas fa-code"></i></div>
    <div class="mw-blog-post-meta">
      <div class="mw-blog-post-meta-item">
        <i class="far fa-calendar"></i><span>2026-04-10</span>
      </div>
    </div>
  </div>
  <img class="mw-blog-post-featured-image" src="cover.jpg" alt="" />
  <div class="mw-blog-post-content-markdown">
    <!-- raw h3/p/ul/blockquote/pre from a markdown renderer -->
  </div>
  <div class="mw-blog-post-footer">
    <button class="mw-btn mw-blog-post-footer-button">
      <i class="fas fa-arrow-left"></i><span>Previous</span>
    </button>
  </div>
</article>
```

`mw-blog-post-content-markdown` styles unclassed HTML - the target for rendered
markdown. `mw-blog-post-content` is the same wrapper for hand-written markup.

## Testimonial

A quote card with its source - a voice about the product. A `figure`, because
quote and attribution belong together:

```html
<figure class="mw-testimonial">
  <blockquote>
    The workshop picked me up after a long day of talking.
  </blockquote>
  <figcaption class="mw-testimonial-source">
    Anna M. <span class="mw-testimonial-detail">&middot; voice workshop</span>
    <time class="mw-testimonial-date" datetime="2026-03">March 2026</time>
  </figcaption>
</figure>
```

The card carries the surface, so inside it the blockquote drops most of its
tint and keeps only the edge and the quotation marks. `mw-testimonial-source`
uses `margin-top: auto` - in a grid of equal-height cards every source line
sits on its card's bottom edge. `mw-testimonial-featured` sets the quote a
size larger, for the one voice lifted above the grid.

`mw-testimonial-date` is optional: a `<time>` on the right edge of the source
line, month and year - a full date is review-platform optics, a bare year
reads as a footnote. It drops to its own line, still right-aligned, when the
source line runs out of room. Leave it out unless the voices are kept fresh: a
dated quote ages, and three from years ago say more about the page than about
the product. The `datetime` attribute is what Schema.org's `datePublished`
would read.

For a wall of testimonials of unequal length, put them in `mw-columns-2` or
`mw-columns-3` (`references/layout.md`) instead of a grid.

## Prose

Long-form running text - a legal page, terms, a plain article. One class on
the container, bare `h2`/`h3`/`p`/`ul` inside:

```html
<div class="mw-card mw-card-simple mw-prose">
  <h2>1. Scope</h2>
  <p>...</p>
  <h2>2. Contact</h2>
  <p>...</p>
</div>
```

Headings are deliberately small (`lg`/`md`, primary ink) - in a document they
structure the reading rather than compete with the page title. First and last
child lose their outer margins, so the container's own padding rules.

## Media

Self-hosted audio and video. The native controls are the player -
`accent-color` already brands them - the wrapper only makes the element sit
right:

```html
<div class="mw-media">
  <video src="/media/intro.mp4" controls preload="metadata"></video>
  <p class="mw-media-caption">Two minutes about how a session works.</p>
</div>
```

`audio` and `video` become full-width blocks; a video also gets the surface
silhouette and a resting shadow. Works with `<audio controls>` the same way.

## Code & terminal

```html
<div class="mw-code-block">
  <div class="mw-code-block-header">
    <span class="mw-code-block-filename">main.kt</span>
    <span class="mw-code-block-language">Kotlin</span>
  </div>
  <div class="mw-code-container">
    <pre><code>fun main() {}</code></pre>
  </div>
</div>

<div class="mw-terminal">
  <span class="mw-terminal-line">npm install maverick-wave</span>
  <span class="mw-terminal-line mw-terminal-output">added 1 package</span>
</div>
```

Token classes for manual highlighting: `mw-code-keyword`, `mw-code-function`,
`mw-code-string`, `mw-code-number`, `mw-code-comment`, `mw-code-operator`. There
is no highlighting engine - wrap spans yourself or plug in Prism/highlight.js.
`mw-code-nowrap` disables wrapping. `<code>` on its own is styled as inline code;
inside a `<pre>` it takes the `pre`'s wrapping - since 6.0, before that it
forced `pre-wrap` and a long line broke mid-word on a phone. A bare `<pre>`
scrolls sideways.

## Tech stack bucket

```html
<div class="mw-techstack-bucket mw-techstack-bucket-dashed">
  <a href="https://angular.dev" class="mw-techstack-item">
    <img class="mw-techstack-logo" src="angular.svg" alt="Angular" />
    <div class="mw-techstack-info">
      <span class="mw-techstack-name">Angular</span>
      <span class="mw-techstack-desc">Frontend</span>
    </div>
  </a>
  <a
    href="#"
    class="mw-techstack-item mw-techstack-item-sm"
    data-tooltip="Docker"
  >
    <img class="mw-techstack-logo" src="docker.svg" alt="Docker" />
  </a>
</div>
```

`mw-techstack-item-sm` is the logo-only chip; the info block is optional. On a
coarse pointer the chip itself grows from 32px to 2.5rem - it often carries a
`data-tooltip`, which owns the pseudo-element a grown hit area would need.

## Coming soon

```html
<div class="mw-coming-soon">
  <i class="mw-coming-soon-icon fas fa-tools"></i>
  <div class="mw-coming-soon-text">Coming soon</div>
</div>
```
