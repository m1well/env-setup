# Example: reactive form

Every control type in one form, with the error handling the framework expects:
`mw-field-has-error` on the wrapper, `mw-field-error` for the message. Nothing
reacts to `ng-invalid` on its own - the bindings below are the whole mechanism.

## Component

```ts
import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { TitleCasePipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-project-form',
  imports: [ReactiveFormsModule, TitleCasePipe],
  templateUrl: './project-form.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProjectFormComponent {
  private readonly fb = inject(FormBuilder);

  protected readonly saving = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(80)]],
    email: ['', [Validators.required, Validators.email]],
    budget: [''], // text + inputmode="decimal", parsed on submit
    type: ['', Validators.required],
    priority: ['normal'],
    description: [''],
    teamSize: [3],
    notify: [true],
    terms: [false, Validators.requiredTrue],
  });

  protected readonly f = this.form.controls;

  // A control shows its error once the user has touched it
  protected invalid(name: keyof typeof this.f): boolean {
    const control = this.f[name];
    return control.invalid && (control.touched || control.dirty);
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    // …persist, then this.saving.set(false)
  }
}
```

## Template

```html
<form class="mw-form" [formGroup]="form" (ngSubmit)="submit()">
  <!-- Group: base data -->
  <div class="mw-form-group">
    <p class="mw-text-muted mw-mb-3">Base data</p>

    <div class="mw-grid-2">
      <div class="mw-field" [class.mw-field-has-error]="invalid('name')">
        <label class="mw-field-label mw-required" for="name"
          >Project name</label
        >
        <input id="name" type="text" class="mw-input" formControlName="name" />
        @if (invalid('name')) {
        <span class="mw-field-error">
          <i class="fas fa-exclamation-circle"></i>
          @if (f.name.hasError('required')) { A name is required. } @else { At
          most 80 characters. }
        </span>
        } @else {
        <span class="mw-field-hint">Shown in the project list.</span>
        }
      </div>

      <div class="mw-field" [class.mw-field-has-error]="invalid('email')">
        <label class="mw-field-label mw-required" for="email">Contact</label>
        <div class="mw-input-group">
          <span class="mw-input-group-prefix"
            ><i class="fas fa-envelope"></i
          ></span>
          <input
            id="email"
            type="email"
            class="mw-input"
            formControlName="email"
          />
        </div>
        @if (invalid('email')) {
        <span class="mw-field-error">
          <i class="fas fa-exclamation-circle"></i> Please enter a valid email
          address.
        </span>
        }
      </div>

      <!-- Money: text + inputmode, never type="number" -->
      <div class="mw-field">
        <label class="mw-field-label" for="budget">Budget</label>
        <div class="mw-input-group">
          <span class="mw-input-group-prefix"
            ><i class="fas fa-euro-sign"></i
          ></span>
          <input
            id="budget"
            type="text"
            inputmode="decimal"
            class="mw-input mw-input-numeric"
            placeholder="0,00"
            formControlName="budget"
          />
          <span class="mw-input-group-suffix">EUR</span>
        </div>
        <span class="mw-field-hint">Comma as decimal separator.</span>
      </div>

      <div class="mw-field" [class.mw-field-has-error]="invalid('type')">
        <label class="mw-field-label mw-required" for="type">Type</label>
        <select id="type" class="mw-select" formControlName="type">
          <option value="" disabled>Choose…</option>
          <option value="internal">Internal</option>
          <option value="customer">Customer project</option>
        </select>
        @if (invalid('type')) {
        <span class="mw-field-error">
          <i class="fas fa-exclamation-circle"></i> Please choose a type.
        </span>
        }
      </div>

      <!-- Full width inside the two-column grid -->
      <div class="mw-field" style="grid-column: 1 / -1">
        <label class="mw-field-label" for="description">Description</label>
        <textarea
          id="description"
          class="mw-textarea mw-textarea-resizable-vertical"
          rows="4"
          formControlName="description"
        ></textarea>
        <span class="mw-field-hint">Markdown is allowed.</span>
      </div>
    </div>
  </div>

  <!-- Group: settings -->
  <div class="mw-form-group">
    <p class="mw-text-muted mw-mb-3">Settings</p>

    <div class="mw-grid-2">
      <div>
        <p class="mw-text-muted mw-text-sm mw-mb-2">Priority</p>
        <div class="mw-radio-group mw-radio-group-inline">
          @for (option of ['low', 'normal', 'high']; track option) {
          <label class="mw-radio">
            <input type="radio" [value]="option" formControlName="priority" />
            <div class="mw-radio-button"></div>
            <div class="mw-radio-label">{{ option | titlecase }}</div>
          </label>
          }
        </div>
      </div>

      <div>
        <p class="mw-text-muted mw-text-sm mw-mb-2">Notifications</p>
        <div class="mw-toggle-group">
          <label class="mw-toggle mw-toggle-success">
            <input type="checkbox" formControlName="notify" />
            <div class="mw-toggle-track"></div>
            <span class="mw-toggle-label">Notify me about changes</span>
          </label>
        </div>
      </div>

      <!-- Slider: both bindings are needed, the framework computes nothing -->
      <div class="mw-field" style="grid-column: 1 / -1">
        <label class="mw-field-label" for="team">Team size</label>
        <div class="mw-slider-container">
          <div
            class="mw-slider-value mw-slider-numeric"
            [attr.data-value]="f.teamSize.value"
          ></div>
          <input
            id="team"
            type="range"
            class="mw-slider mw-slider-primary"
            min="1"
            max="10"
            formControlName="teamSize"
            [style.--value.%]="f.teamSize.value * 10"
          />
        </div>
      </div>
    </div>
  </div>

  <!-- Single control without a field wrapper -->
  <div
    class="mw-checkbox-group"
    [class.mw-form-element-error]="invalid('terms')"
  >
    <label class="mw-checkbox">
      <input type="checkbox" formControlName="terms" />
      <div class="mw-checkbox-box"></div>
      <div class="mw-checkbox-label">I accept the terms.</div>
    </label>
  </div>

  <div class="mw-form-actions">
    <p class="mw-form-actions-hint">Fields marked with * are required.</p>
    <button type="button" class="mw-btn mw-btn-outline" (click)="form.reset()">
      Reset
    </button>
    <button type="submit" class="mw-btn mw-btn-primary" [disabled]="saving()">
      @if (saving()) {
      <span class="mw-spinner-border mw-spinner-sm"></span> Saving… } @else {
      <i class="fas fa-save"></i> Save }
    </button>
  </div>
</form>
```

## Notes

- **The error state is two bindings**: `mw-field-has-error` on the wrapper
  (border and halo) and the `mw-field-error` element (the message). Hint and
  error should not be visible at the same time.
- **For a control without a wrapper** - a checkbox group, radio group or slider
  container - use `mw-form-element-error` instead.
- **`disabled`/`readonly` are attributes**, not classes. With reactive forms use
  `control.disable()`; the muted look comes from the `:disabled` selector.
- **The slider needs two bindings**: `data-value` for the badge text,
  `--value` for the filled part of the track.
- **A spinner inside a button** needs its shape class (`mw-spinner-border`) plus
  a size; the button already provides the gap.
- Multi-column layout comes from `mw-grid-2` inside the group, a full-width
  field from `style="grid-column: 1 / -1"`.

## Number formatting

`mw-text-numeric` aligns from the right edge, so it works with both `1,204.50`
and `1.204,50` - what matters is a constant number of decimals per column. Let
the pipe do it:

```html
<td class="mw-text-numeric">
  {{ invoice.total | currency: 'EUR' : 'symbol' : '1.2-2' }}
</td>
<td class="mw-text-numeric">{{ item.amount | number: '1.2-2' }}</td>
```

```ts
// app.config.ts
import { registerLocaleData } from '@angular/common';
import localeDe from '@angular/common/locales/de';

registerLocaleData(localeDe);

export const appConfig: ApplicationConfig = {
  providers: [{ provide: LOCALE_ID, useValue: 'de-DE' }],
};
```

`'1.2-2'` is the part that keeps the column aligned - it forces exactly two
decimals. `tabular-nums` only takes effect if the loaded font ships tabular
figures; the framework bundles no font.
