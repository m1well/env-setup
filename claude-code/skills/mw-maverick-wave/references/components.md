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
  `mw-btn-success`, `mw-btn-outline`, `mw-btn-link`, `mw-btn-link-muted`
- Sizes: `mw-btn-sm`, `mw-btn-lg`
- `mw-btn` is `inline-flex` with a gap - icons need no wrapper and no extra class
- `disabled` gets `opacity: .6` and `not-allowed`; there is no disabled class
- `active` (no prefix) gives the pressed/selected look on the coloured variants
- `mw-btn-link` still has the button padding - `mw-p-0` makes it read as inline
  text

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
- Alignment: `mw-button-bar-left`, `-right` (default is centered),
  `mw-button-bar-between` pushes first and last apart.
- Sizes: `mw-button-bar-sm`, `mw-button-bar-lg`.

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
- Image height: 210px, `mw-card-lg` 340px, `mw-card-xl` 480px. Set
  `--mw-card-img-height` on the card for any other height.
  `mw-card-img-contain` shows the whole image instead of cropping it.
- `mw-card-footer` pushes its last child to the right - with a single child that
  means it sits right, not left. Everything is vertically centered, so plain text
  lines up with a button next to it. Below `lg` the footer stacks and children go
  full width.
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
    <div class="mw-accordion-header active">
      <h3>Question</h3>
      <i class="fas fa-chevron-down mw-accordion-icon"></i>
    </div>
    <div class="mw-accordion-content active">
      <div class="mw-accordion-content-inner">Answer</div>
    </div>
  </div>
</div>
```

Open state = `active` (no prefix) on header **and** content. The icon rotates
via the header state. Content taller than 500px scrolls. Toggling is JS - see
`references/javascript.md`.

## Tabs

```html
<div class="mw-tabs">
  <div class="mw-tabs-nav">
    <div class="mw-tabs-nav-item active" data-tab="tab1">Details</div>
    <div class="mw-tabs-nav-item" data-tab="tab2">History</div>
  </div>
  <div class="mw-tabs-content">
    <div class="mw-tabs-panel active" id="tab1">...</div>
    <div class="mw-tabs-panel" id="tab2">...</div>
  </div>
</div>
```

- Variants: `mw-tabs-vertical` (nav on the left, horizontal again below `sm`),
  `mw-tabs-pills`.
- `data-tab` matches the panel `id` - that pairing is only needed for the
  shipped JS. In a SPA, bind `active` yourself and drop the attribute.
- The nav scrolls horizontally on small screens instead of wrapping.

## Modal

```html
<div id="delete-modal" class="mw-modal-overlay">
  <div class="mw-modal mw-modal-sm">
    <div class="mw-modal-header">
      <h4 class="mw-modal-title">Delete invoice</h4>
      <button class="mw-modal-close" type="button">&#120299;</button>
    </div>
    <div class="mw-modal-body">
      <p>This cannot be undone.</p>
    </div>
    <div class="mw-modal-footer">
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
- Sizes: `mw-modal-sm` 370px, default 550px, `mw-modal-lg` 680px,
  `mw-modal-xl` 900px. Height is capped at 80-92dvh, the body scrolls.
- `mw-modal-backdrop` is the click-to-close surface; put the close handler on it.
- `mw-modal-body` takes a `mw-form` directly - the form brings the field gaps,
  the body brings the padding.

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
| `mw-table-responsive-scroll` | Wrapper with a height cap (`--mw-table-scroll-height`, 400px / 260px below `sm`) and vertical scroll                    |
| `mw-table-sticky-head`       | Header stays put while the body scrolls - only works inside a height-limited wrapper, i.e. `mw-table-responsive-scroll` |

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

## Tags

Two forms, picked by count - see also the pitfall list in `SKILL.md`.

**Single chip** (table cells, status columns) - carries its colour itself:

```html
<span class="mw-tag mw-tag-success">Paid</span>
```

Variants: `mw-tag-primary`, `-secondary`, `-success`, `-info`, `-warning`,
`-danger`, `-muted`. Size: `mw-tag-lg`. `mw-tag-muted` is the neutral tone for
states that should not shout (draft, archived).

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
  <div class="mw-timeline-big-step active">
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
  <div class="mw-timeline-simple-step active">
    <div class="mw-timeline-simple-date">2024-03-22</div>
    <div class="mw-timeline-simple-content">
      <div class="mw-card mw-card-simple">...</div>
    </div>
  </div>
</div>
```

The current step gets `active` (no prefix). Any card fits into the content
wrapper.

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

| Class                     | Look                                                                         |
| ------------------------- | ---------------------------------------------------------------------------- |
| `mw-item-list`            | Plain flex column with gaps                                                  |
| `mw-item-list-horizontal` | Row, wrapping; column below `sm`                                             |
| `mw-item-list-cards`      | Wider gaps, for cards                                                        |
| `mw-item-list-compact`    | Bordered box, divided rows, hover indent (nests)                             |
| `mw-item-list-menu`       | Elevated menu card, pointer cursor, press feedback                           |
| `mw-item-list-slide`      | Cards with a sliding accent border on hover (`mw-item-list-slide-secondary`) |
| `mw-item-list-scroll`     | Scroll box, 300px (`-sm` 200, `-lg` 400, `-xl` 500)                          |

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

Variants: `mw-item-list-checkbox-compact`, `-large`, `-secondary`,
`-scroll`. `mw-selected` on the `<li>` is the selected-row highlight - bind it
to the checkbox state yourself in a SPA. The `mw-checkbox-content` block is
optional; a bare `mw-checkbox-label` renders a single-line row.

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

A titled content frame with prev/next controls - not a page-number list.

```html
<div class="mw-pagination">
  <div class="mw-pagination-header">
    <button class="mw-pagination-nav"><i class="fas fa-arrow-left"></i></button>
    <h3 class="mw-pagination-title">Week 10</h3>
    <button class="mw-pagination-nav">
      <i class="fas fa-arrow-right"></i>
    </button>
  </div>
  <div class="mw-pagination-content">...</div>
</div>
```

`mw-pagination-loading` on the container dims the content while it swaps;
`mw-pagination-slide-left` / `-slide-right` are the directional transitions.

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
    <div class="mw-image-slider-overlay-image active" data-index="1">
      <img src="a.jpg" alt="" />
    </div>
  </div>
  <div class="mw-image-slider-controls-grid-3">
    <button class="mw-btn mw-btn-primary active" data-index="0">Base</button>
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
