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
- Every variant dips 1px on `:active`, and the solid ones invert their top
  highlight into an inner shadow. On touch that press is the only feedback there
  is, so do not override it away
- **A link inside a sentence is `mw-link`, not `mw-btn mw-btn-link`.** The base
  class carries a control height, so in running text it lifts that one line to
  2.25rem while the lines around it stay where they are. `mw-p-0` does not help
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
- Active position: `mw-active` on the item.
- `mw-segmented-secondary` switches the active fill to the secondary colour,
  `mw-segmented-auto` shrinks the control to its content instead of filling the
  row. `disabled` works on an item.
- Items reach a 2.5rem minimum height on a coarse pointer.

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
- The footer stacks to full-width children once the **card** is narrower than
  360px, not once the window is - a card in a three-column grid is just as narrow
  on a 1200px desktop as it is on a phone, and now looks the same in both. This
  is a container query: a card that has a footer declares
  `container: mw-card / inline-size` and takes `width: 100%`, so it fills its
  slot instead of sizing to its content. Give such a card an explicit width if
  you need it to hug its content.
- `mw-card-badge` (top right corner) and `mw-card-ribbon` (diagonal banner) are
  absolutely positioned overlays; colour them with `mw-card-addon-primary`,
  `-secondary`, `-success`, `-warning`, `-danger`, `-info`.
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
  `mw-price-sm` (1.5rem) and `mw-price-lg` (3rem) move the whole row at once -
  cents, unit and struck original included. Set the token yourself for any other
  size.
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
  `mw-price-original` at 0.9rem. Below `mw-price-sm` the `em` chain would put
  them under 12px, and that is the size most offer cards run at.
- `mw-price-word` for "On request" or "Free" - bold, so it holds the same slot in
  a row of cards, but set well below a figure. Its line box is scaled back up to
  the amount's, so a word and a number in neighbouring cards land on one line.
- `mw-price-note` is a **sibling** of the row, not a child - inside it, it would
  inherit the price size and join the baseline.
- A `mw-tag` or `mw-badge` placed directly in the row is centred against the
  digits rather than hung off their baseline.

| Class             | What it does                                   |
| ----------------- | ---------------------------------------------- |
| `mw-price-sm/lg`  | Retunes `--mw-price-size`, everything follows  |
| `mw-price-inline` | Old price in front of the new one, on one line |
| `mw-price-center` | Centres the row                                |
| `mw-price-plain`  | Body colour instead of the brand               |

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
  header is neutral.
- Height: `mw-panel-scrollable` (500px), `mw-panel-max-height-sm` (300px),
  `-md` (500px), `-lg` (700px) - the body scrolls, header and footer stay.
- `mw-panel` has `min-height: 100%`, so panels in a grid row end up equally tall.

## Tiles

Compact, clickable info blocks in a fixed 3-column grid.

```html
<div class="mw-tiles mw-tiles-2col">
  <div class="mw-tile">
    <div class="mw-tile-img"><img src="icon.png" alt="" /></div>
    <h3 class="mw-tile-header">Billing</h3>
    <div class="mw-tile-body">
      <p>Invoices and payments</p>
    </div>
    <div class="mw-tile-footer">Updated 2026-01-02</div>
  </div>
</div>
```

Container: `mw-tiles` (3 columns), `mw-tiles-2col`, `mw-tiles-4col`.
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
Toggling is JS - see `references/javascript.md`; the shipped script keeps
`aria-expanded` in step when the header is a button.

## Tabs

```html
<div class="mw-tabs">
  <div class="mw-tabs-nav">
    <div class="mw-tabs-nav-item mw-active" data-tab="tab1">Details</div>
    <div class="mw-tabs-nav-item" data-tab="tab2">History</div>
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
- The nav scrolls horizontally instead of wrapping, and says so: a shadow shows
  on whichever side still has tabs behind it and disappears once that end is
  reached. Pure CSS, no scroll listener. The fade colour comes from
  `--mw-scroll-hint-cover`, which is preset to the page background and
  re-pointed to the card background inside `mw-card`, `mw-panel`, `mw-modal`,
  `mw-tile` and `mw-calendar` - override it if the strip sits on some other
  surface.
- Tab items reach a 2.75rem minimum height on a coarse pointer.

## Modal

```html
<div id="delete-modal" class="mw-modal-overlay">
  <div class="mw-modal mw-modal-sm">
    <div class="mw-modal-header">
      <h4 class="mw-modal-title">Delete invoice</h4>
      <button class="mw-modal-close" type="button">&#120299;</button>
    </div>
    <div class="mw-modal-body">
      <p>Invoice 2026-0042 will be removed.</p>
    </div>
    <div class="mw-modal-footer">
      <p class="mw-actions-note">This action cannot be undone.</p>
      <button class="mw-btn mw-btn-outline">Cancel</button>
      <button class="mw-btn mw-btn-danger">Delete</button>
    </div>
  </div>
  <div class="mw-modal-backdrop"></div>
</div>
```

- The overlay is `display: none` until `mw-modal-open` is added to it. That
  class is the whole open/close mechanism.
- Body scroll lock is automatic: the stylesheet uses
  `body:has(.mw-modal-open)`. Nothing to implement.
- Sizes: `mw-modal-sm` 370px, default 520px, `mw-modal-lg` 720px,
  `mw-modal-xl` 960px. Height is capped at 80-92dvh, the body scrolls.
- `mw-modal-backdrop` is the click-to-close surface; put the close handler on it.
- `mw-modal-body` takes a `mw-form` directly - the form brings the field gaps,
  the body brings the padding.
- `mw-actions-note` is the muted line above the buttons - see below.

Angular: `<div class="mw-modal-overlay" [class.mw-modal-open]="isOpen()">`.

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

Variants: `mw-alert-primary`, `-secondary`, `-success`, `-warning`, `-danger`,
`-info`. `mw-alert-title` and the close button are optional. `mw-alert-closed`
hides a dismissed alert (`display: none`) - in a SPA prefer removing it from the
list instead.

**Toasts** are alerts inside a fixed stack:

```html
<div class="mw-toast-stack mw-toast-stack-top-right">
  <div class="mw-alert mw-alert-success">...</div>
</div>
```

Positions: `mw-toast-stack-top-right` (also the default without a position
class), `-top-center`, `-bottom-right`. Width is capped at
`min(380px, 100vw - 2rem)`, clicks pass through everywhere except on a toast,
the entry animation respects `prefers-reduced-motion`. Auto-dismiss is the
application's job.

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
there - the page scrolls beneath it. Variants: `mw-announcement-secondary`,
`-success`, `-warning`, `-danger`, `-info` (primary is the default).
`mw-announcement-highlight` is the pill in front of the text; the content
element is usually an `<a>` but a plain `<div>` works.
`mw-announcement-static` puts the ribbon into the document flow instead - it
then scrolls with the content and shifts no anchor offset.

The height lives in `--mw-announcement-height` and drives the anchor scroll
offset (`scroll-padding-top`) automatically - a taller ribbon raises the token
instead of fighting the offset.

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
`mw-empty-state-sm`.

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
        <th class="mw-text-numeric">Amount</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td data-label="Name">Jane Doe</td>
        <td data-label="Status">
          <span class="mw-tag mw-tag-success">Paid</span>
        </td>
        <td data-label="Amount" class="mw-text-numeric">1.204,50</td>
      </tr>
    </tbody>
  </table>
</div>
```

| Class                        | Effect                                                                                                                  |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `mw-table`                   | Base: zebra rows, row hover, primary-coloured header                                                                    |
| `mw-table-subtle`            | Quiet grey header with an accent rule - for data-heavy lists                                                            |
| `mw-table-compact`           | Less padding, smaller type                                                                                              |
| `mw-table-hover`             | Stronger row hover                                                                                                      |
| `mw-table-cards`             | Below `md` every row becomes a card; keep `<thead>` (hidden via CSS) and give each cell a `data-label`                  |
| `mw-table-responsive`        | Wrapper, horizontal scroll                                                                                              |
| `mw-table-responsive-hint`   | On top of the wrapper: a soft right edge showing there are more columns. Opt-in - see below                             |
| `mw-table-responsive-scroll` | Wrapper with a height cap (`--mw-table-scroll-height`, 400px / 260px below `sm`) and vertical scroll                    |
| `mw-table-sticky-head`       | Header stays put while the body scrolls - only works inside a height-limited wrapper, i.e. `mw-table-responsive-scroll` |

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

## Kanban

A board is a grid of equally wide lanes; a ticket is a plain `mw-card` with
`mw-kanban-card` on top. Everything except the counters and the composer is CSS.

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

| Class                     | Role                                                                                     |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| `mw-kanban`               | Board. Grid, one column per lane, same width for all of them                             |
| `mw-kanban-plain`         | Board without its own surface or padding - for a board that already sits on a panel      |
| `mw-kanban-compact`       | Tighter padding, description clamped to 2 lines instead of 4, lane floor 90px            |
| `mw-kanban-column`        | Lane: dashed border, flex column                                                         |
| `mw-kanban-column-header` | Title + counter + add button in one row                                                  |
| `mw-kanban-title`         | Lane title, uppercase, truncates                                                         |
| `mw-kanban-count`         | Ticket counter pill                                                                      |
| `mw-kanban-add`           | Sits **on** `mw-btn` - only trims it to the header line height                           |
| `mw-kanban-column-body`   | Ticket stack; fills the lane so the empty state stays centred                            |
| `mw-kanban-card`          | Ticket. Needs `mw-card` next to it                                                       |
| `mw-kanban-card-title`    | Ticket title                                                                             |
| `mw-kanban-card-text`     | Description, clamped to 4 lines (2 on a compact board)                                   |
| `mw-kanban-card-footer`   | Rule + key on the left, avatar and actions on the right                                  |
| `mw-kanban-card-id`       | Ticket key, monospaced so equal-length keys line up across cards                         |
| `mw-kanban-card-actions`  | Right-hand group; resets the avatar margin                                               |
| `mw-kanban-action`        | 26px square icon button (32px below `md`), `mw-kanban-action-danger` turns the hover red |
| `mw-kanban-empty`         | Placeholder; hides itself as soon as the lane holds a ticket or an open composer         |
| `mw-kanban-card-in`       | One-shot entry animation for a freshly created ticket                                    |

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
`-caret` (rotates with the open state on its own). Alignment:
`mw-dropdown-end` anchors the menu to the trigger's right edge,
`mw-dropdown-up` opens it upward.

`mw-active` (or `aria-checked="true"`) marks the current choice, for a menu that
picks rather than acts. Icons inside items keep one column, so labels line up
whether or not every item has one.

The menu is absolutely positioned and is clipped by any ancestor that hides its
overflow. The framework's own containers lift that clip while a menu is open; on
your own it is `:has(.mw-dropdown[open]) { overflow: visible }`.

On a coarse pointer the rows grow to 2.75rem and the menu takes at least the
trigger's full width.

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
  (`mw-info-value`, `mw-info-label`).
- The cursor is `default` because a figure is usually not clickable. On `<a>`
  and `<button>` it turns into a pointer automatically; on anything else use
  `mw-info-clickable`.
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

State classes here are prefixed: `mw-done`, `mw-active`. The horizontal variant
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

Both are chronicles (CV, changelog), not schedulable time axes.

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

## Avatars

```html
<div class="mw-avatar mw-avatar-lg mw-avatar-primary">
  <img src="me.jpg" alt="" />
</div>

<div class="mw-avatar mw-avatar-initials mw-avatar-xs">MW</div>
```

- Sizes: `mw-avatar-xs` 32, `-sm` 64, default 96, `-lg` 144, `-xl` 250 px.
- Shape: `mw-avatar-square`.
- Colours `mw-avatar-primary`, `-secondary`, `-success`, `-warning`, `-danger`,
  `-info` tint the **border**. On `mw-avatar-initials` the same class also tints
  the **surface**, so both can be combined.
- `mw-avatar-initials` centers text and scales the font with the size class -
  the standard display for a signed-in user without a picture.
- `mw-avatar-group` overlaps its avatars; `mw-avatar-group-sm` / `-lg` change
  the overlap.

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

The `mw-checkbox` inside is the ordinary form-element checkbox, so
`mw-checkbox-disabled` and the colour variants (`mw-checkbox-success` and the
rest, see `references/forms.md`) work here too. Row height is a list concern -
use the list's own `-compact` / `-large` modifiers rather than
`mw-checkbox-sm` / `-lg`, which sit on the wrong element to reach the box.

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

The last item takes `mw-breadcrumbs-current` on the `li` and
`mw-breadcrumbs-active` on the anchor. `mw-breadcrumbs-sm` is the small variant,
`mw-breadcrumbs-collapse` hides middle items on narrow screens.

## Pagination

A titled content frame with prev/next controls - not a page-number list. Same
surface and header as `mw-calendar`; only the body differs, and the body is
yours.

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
`transform: translateX(...)` yourself.

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
current button carry `active`.

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
`mw-code-nowrap` disables wrapping. `<code>` on its own is styled as inline code.

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

`mw-techstack-item-sm` is the logo-only chip; the info block is optional.

## Coming soon

```html
<div class="mw-coming-soon">
  <i class="mw-coming-soon-icon fas fa-tools"></i>
  <div class="mw-coming-soon-text">Coming soon</div>
</div>
```
