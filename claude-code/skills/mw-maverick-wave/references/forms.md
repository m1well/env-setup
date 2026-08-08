# Forms

## The field pattern

`mw-field` groups label, control, hint and error into one unit. It is the
recommended wrapper for every labelled control and the natural fit for a
reactive form control.

```html
<div class="mw-field">
  <label class="mw-field-label mw-required" for="email">Email</label>
  <input id="email" type="email" class="mw-input" />
  <span class="mw-field-hint">Used for login and notifications.</span>
  <span class="mw-field-error">
    <i class="fas fa-exclamation-circle"></i> Please enter a valid email
    address.
  </span>
</div>
```

- `mw-required` on the label appends a red asterisk (`data-required="true"`
  works too).
- `mw-field-hint` is the small muted helper line, `mw-field-error` the small red
  one. Render only one of them at a time.
- `mw-field-has-error` on the **wrapper** turns the border of the contained
  `mw-input` / `mw-select` / `mw-textarea` red and adds a soft red halo.
- `mw-form-element-error` does the same for a single control that has no field
  wrapper - it also works on `mw-checkbox-group`, `mw-radio-group` and
  `mw-slider-container`.

> **The framework does not style Angular's `ng-invalid` / `ng-touched` classes.**
> Bind the framework classes to the control state yourself:
>
> ```html
> <div
>   class="mw-field"
>   [class.mw-field-has-error]="email.invalid && email.touched"
> >
>   <label class="mw-field-label mw-required" for="email">Email</label>
>   <input id="email" type="email" class="mw-input" formControlName="email" />
>   @if (email.hasError('required') && email.touched) {
>   <span class="mw-field-error">
>     <i class="fas fa-exclamation-circle"></i> Email is required.
>   </span>
>   }
> </div>
> ```
>
> The same applies to any other framework - React: `className={...}`, Vue:
> `:class`. Nothing reacts to validation on its own.

## Form layout

```html
<form class="mw-form">
  <div class="mw-form-group">
    <h4 class="mw-form-group-title">Personal information</h4>
    <div class="mw-grid-2">
      <div class="mw-field">...</div>
      <div class="mw-field">...</div>
    </div>
  </div>

  <div class="mw-form-actions">
    <p class="mw-form-actions-hint">Changes are saved immediately.</p>
    <button type="button" class="mw-btn mw-btn-outline">Cancel</button>
    <button type="submit" class="mw-btn mw-btn-primary">Save</button>
  </div>
</form>
```

- `mw-form` is a flex column with a gap and **no padding** - safe to put
  directly on `mw-modal-body` or `mw-panel-body`. It also works on a `<div>`
  when there is no real form element.
- `mw-form-inline` lays the children out in a row.
- `mw-form-group` is the bordered block for a titled group of fields.
  `mw-form-group-title` is the heading hook inside it - put it on the `<h3>` /
  `<h4>`, otherwise the heading keeps its full document-level size.
- `mw-form-actions` is a right-aligned wrapping button row.
  `mw-form-actions-hint` is a full-width note above the buttons.
  Alignment variants: `mw-form-actions-left`, `mw-form-actions-center`,
  `mw-form-actions-full-width` (stacked, buttons at 100% - login forms).
- Put multi-column layouts inside a group with `mw-grid-2` etc. and let a field
  span everything with `style="grid-column: 1 / -1"`.

## Text inputs

```html
<input type="text" class="mw-input" />
<input type="text" class="mw-input mw-input-sm" />
<input type="text" class="mw-input mw-input-lg" />
```

- Full width by default, `2px` border, focus ring in the primary colour.
- `readonly` renders on a muted surface, `disabled` additionally as
  `not-allowed`. Both are attribute driven - there is no readonly/disabled
  class.
- Date/time work as normal inputs (`type="date" | "time" | "datetime-local"`);
  the native picker indicator is styled.

### Numbers and money

```html
<div class="mw-field">
  <label class="mw-field-label" for="budget">Budget</label>
  <div class="mw-input-group">
    <span class="mw-input-group-prefix"><i class="fas fa-euro-sign"></i></span>
    <input
      id="budget"
      type="text"
      inputmode="decimal"
      class="mw-input mw-input-numeric"
      placeholder="0,00"
    />
    <span class="mw-input-group-suffix">EUR</span>
  </div>
</div>
```

`mw-input-numeric` is the entry counterpart to the `mw-text-numeric` utility:
right aligned, tabular lining figures, native spinners suppressed. A value looks
identical while being typed and once it is rendered into a table.

> **Use `type="text"` + `inputmode="decimal"`, not `type="number"`.** A focused
> number input changes its value when the page is scrolled, and in most locales
> it rejects a comma as decimal separator - the user sees `1234,50` but `.value`
> comes back empty. `inputmode="decimal"` still brings up the numeric keypad on
> mobile. Parsing the comma stays the application's job.

## Input group

Prefix, suffix and buttons glued to the control:

```html
<div class="mw-input-group">
  <span class="mw-input-group-prefix"><i class="fas fa-search"></i></span>
  <input type="text" class="mw-input" placeholder="Search…" />
  <button type="button" class="mw-btn mw-btn-primary">
    <i class="fas fa-search"></i>
  </button>
</div>
```

Sizes: `mw-input-group-sm`, `mw-input-group-lg` - combine them with the matching
`mw-input-sm` / `mw-input-lg` on the control. A prefix or suffix takes an icon,
a symbol (`@`, `https://`) or a short unit.

## Select

```html
<select class="mw-select">
  <option value="" disabled selected>Choose…</option>
  <option>Option A</option>
</select>
```

Sizes: `mw-select-sm`, `mw-select-lg`.

## Textarea

```html
<textarea class="mw-textarea" rows="4"></textarea>
```

Sizes: `mw-textarea-sm`, `mw-textarea-lg`. Resizing is off by default; enable it
with `mw-textarea-resizable`, `mw-textarea-resizable-vertical` or
`mw-textarea-resizable-horizontal`.

## Checkbox

The native input is hidden; `mw-checkbox-box` is the visible control, so the
order of the three children matters.

```html
<div class="mw-checkbox-group mw-checkbox-group-inline">
  <label class="mw-checkbox mw-checkbox-success">
    <input type="checkbox" />
    <div class="mw-checkbox-box"></div>
    <div class="mw-checkbox-label">Send a copy</div>
  </label>
</div>
```

- Sizes: `mw-checkbox-sm`, `mw-checkbox-lg`
- Colours: `mw-checkbox-primary`, `-secondary`, `-success`, `-warning`,
  `-danger`, `-info`
- Disabled: `mw-checkbox-disabled` on the label **plus** the `disabled`
  attribute on the input
- Group: `mw-checkbox-group` (column), `mw-checkbox-group-inline` (row)
- With a heading and a description use `mw-checkbox-content` containing
  `mw-checkbox-header` + `mw-checkbox-label` - see the checkbox item list in
  `references/components.md`

## Radio

Same structure, with `mw-radio-button` as the visible control:

```html
<div class="mw-radio-group">
  <label class="mw-radio">
    <input type="radio" name="plan" value="free" />
    <div class="mw-radio-button"></div>
    <div class="mw-radio-label">Free</div>
  </label>
</div>
```

Sizes `mw-radio-sm`, `-lg`; colours `mw-radio-primary`, `-secondary`,
`-success`, `-warning`, `-danger`, `-info`; `mw-radio-disabled`; groups
`mw-radio-group`, `mw-radio-group-inline`.

## Toggle

```html
<div class="mw-toggle-group">
  <label class="mw-toggle mw-toggle-success">
    <input type="checkbox" checked />
    <div class="mw-toggle-track"></div>
    <span class="mw-toggle-label">Notifications</span>
  </label>
</div>
```

Sizes `mw-toggle-sm`, `-lg`; colours `mw-toggle-primary`, `-secondary`,
`-success`, `-warning`, `-danger` (no `info` variant); `mw-toggle-disabled` plus
the `disabled` attribute; groups `mw-toggle-group`, `mw-toggle-group-inline`.

## Slider

```html
<label>
  <span>Experience</span>
  <div class="mw-slider-container">
    <div class="mw-slider-value mw-slider-numeric" data-value="3"></div>
    <input
      type="range"
      class="mw-slider mw-slider-primary"
      min="0"
      max="10"
      value="3"
    />
  </div>
</label>
```

- The badge prints `data-value`: `mw-slider-numeric` appends `/10`,
  `mw-slider-percent` appends `%`.
- The filled part of the track comes from the custom property `--value` on the
  input (`style="--value: 30%"`).
- Both `data-value` and `--value` are set by the shipped JS on `input`. In a SPA
  bind them yourself - two bindings, see `examples/angular-form.md`.
- Colours: `mw-slider-primary`, `-secondary`, `-success`, `-warning`, `-danger`,
  `-info`; sizes `mw-slider-sm`, `-lg`.

## Login card

A centered, self-contained card for sign-in screens.

```html
<div class="mw-login">
  <div class="mw-login-logo"><img src="logo.svg" alt="" /></div>
  <div class="mw-login-message">Internal area - valid account required.</div>
  <div class="mw-login-message mw-login-message-error">Wrong credentials.</div>

  <form class="mw-form">
    <div class="mw-grid-1">
      <div class="mw-field">
        <label class="mw-field-label mw-required" for="login-email"
          >Email</label
        >
        <div class="mw-input-group">
          <span class="mw-input-group-prefix"
            ><i class="fas fa-envelope"></i
          ></span>
          <input id="login-email" type="email" class="mw-input" required />
        </div>
      </div>
    </div>
    <div class="mw-form-actions mw-form-actions-full-width">
      <button type="submit" class="mw-btn mw-btn-primary">
        <i class="fas fa-sign-in-alt"></i> Sign in
      </button>
    </div>
  </form>
</div>
```

`mw-login-error` on the card flashes a red border after a failed attempt,
`mw-login-message-info` / `mw-login-message-error` colour the message line.
