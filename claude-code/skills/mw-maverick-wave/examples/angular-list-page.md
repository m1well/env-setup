# Example: list page with filters, table, modal and toasts

A complete application page built only from framework classes: page header with
counters and actions, a filter panel, a data table with status chips and a
sticky header, loading and empty states, a delete confirmation modal and a toast
stack.

The Angular parts are signals, the new control flow and `inject()` - swap them
for any other framework, the markup does not change.

## Component

```ts
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CurrencyPipe, DatePipe, TitleCasePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { InvoiceService } from './invoice.service';
import { ToastService } from '../shared/toast.service';

type Status = 'paid' | 'open' | 'cancelled' | 'draft';

interface Invoice {
  id: string;
  number: string;
  customer: string;
  issuedAt: Date;
  total: number;
  status: Status;
}

@Component({
  selector: 'app-invoice-list',
  imports: [FormsModule, RouterLink, CurrencyPipe, DatePipe, TitleCasePipe],
  templateUrl: './invoice-list.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InvoiceListComponent {
  private readonly invoices = inject(InvoiceService);
  private readonly toasts = inject(ToastService);

  protected readonly loading = this.invoices.loading;
  protected readonly search = signal('');
  protected readonly status = signal<Status | 'all'>('all');
  protected readonly toDelete = signal<Invoice | null>(null);

  protected readonly filtered = computed(() => {
    const term = this.search().trim().toLowerCase();
    const status = this.status();
    return this.invoices
      .all()
      .filter(
        (invoice) =>
          (status === 'all' || invoice.status === status) &&
          (term === '' ||
            invoice.number.toLowerCase().includes(term) ||
            invoice.customer.toLowerCase().includes(term))
      );
  });

  protected readonly drafts = computed(
    () => this.invoices.all().filter((i) => i.status === 'draft').length
  );

  // Status → tag variant. Keep this mapping in TS, not in the template -
  // it is the only place that knows which colour means what.
  protected readonly tagClass: Record<Status, string> = {
    paid: 'mw-tag-success',
    open: 'mw-tag-warning',
    cancelled: 'mw-tag-danger',
    draft: 'mw-tag-muted',
  };

  protected resetFilters(): void {
    this.search.set('');
    this.status.set('all');
  }

  protected confirmDelete(): void {
    const invoice = this.toDelete();
    if (!invoice) return;

    this.invoices.remove(invoice.id).subscribe({
      next: () => {
        this.toasts.success(`Invoice ${invoice.number} deleted.`);
        this.toDelete.set(null);
      },
      error: () => this.toasts.error('Deleting failed. Please try again.'),
    });
  }
}
```

## Template

```html
<!-- Page header: title, counters, actions -->
<header class="mw-page-header">
  <div>
    <h1>Invoices</h1>
    <div class="mw-meta-header">
      <div class="mw-meta-item">
        <i class="fas fa-list"></i><span>Total: {{ filtered().length }}</span>
      </div>
      <div class="mw-meta-item">
        <i class="fas fa-pen"></i><span>Drafts: {{ drafts() }}</span>
      </div>
    </div>
  </div>

  <div class="mw-page-header-actions">
    <button
      type="button"
      class="mw-btn mw-btn-outline mw-btn-sm"
      (click)="resetFilters()"
    >
      <i class="fas fa-rotate-left"></i> Reset
    </button>
    <button
      type="button"
      class="mw-btn mw-btn-primary mw-btn-sm"
      routerLink="new"
    >
      <i class="fas fa-plus"></i> New invoice
    </button>
  </div>
</header>

<!-- Filter bar -->
<div class="mw-panel mw-mb-6">
  <h4 class="mw-panel-header">Filter</h4>
  <div class="mw-panel-body">
    <div class="mw-form">
      <div class="mw-grid-2">
        <div class="mw-field">
          <label class="mw-field-label" for="search">Search</label>
          <div class="mw-input-group">
            <span class="mw-input-group-prefix"
              ><i class="fas fa-search"></i
            ></span>
            <input
              id="search"
              type="text"
              class="mw-input"
              placeholder="Number or customer…"
              [ngModel]="search()"
              (ngModelChange)="search.set($event)"
            />
          </div>
        </div>

        <div class="mw-field">
          <label class="mw-field-label" for="status">Status</label>
          <select
            id="status"
            class="mw-select"
            [ngModel]="status()"
            (ngModelChange)="status.set($event)"
          >
            <option value="all">All</option>
            <option value="open">Open</option>
            <option value="paid">Paid</option>
            <option value="cancelled">Cancelled</option>
            <option value="draft">Draft</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</div>

@if (loading()) {
<!-- Loading -->
<div class="mw-skeleton-card">
  <span class="mw-skeleton mw-skeleton-title"></span>
  <span class="mw-skeleton mw-skeleton-text"></span>
  <span class="mw-skeleton mw-skeleton-text"></span>
  <span class="mw-skeleton mw-skeleton-text"></span>
</div>
} @else if (filtered().length === 0) {
<!-- Empty -->
<div class="mw-empty-state mw-empty-state-primary">
  <div class="mw-empty-state-icon"><i class="fas fa-file-invoice"></i></div>
  <p class="mw-empty-state-title">No invoices found</p>
  <p class="mw-empty-state-desc">Adjust the filters or create a new invoice.</p>
  <button type="button" class="mw-btn mw-btn-outline" (click)="resetFilters()">
    Reset filters
  </button>
</div>
} @else {
<!-- Table -->
<div class="mw-table-responsive-scroll" style="--mw-table-scroll-height: 520px">
  <table class="mw-table mw-table-subtle mw-table-sticky-head mw-table-cards">
    <thead>
      <tr>
        <th>Number</th>
        <th>Customer</th>
        <th>Date</th>
        <th>Status</th>
        <th class="mw-text-numeric">Total</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      @for (invoice of filtered(); track invoice.id) {
      <tr>
        <td data-label="Number">{{ invoice.number }}</td>
        <td data-label="Customer">{{ invoice.customer }}</td>
        <td data-label="Date">{{ invoice.issuedAt | date: 'dd.MM.yyyy' }}</td>
        <td data-label="Status">
          <span class="mw-tag" [class]="tagClass[invoice.status]">
            {{ invoice.status | titlecase }}
          </span>
        </td>
        <td data-label="Total" class="mw-text-numeric">
          {{ invoice.total | currency: 'EUR' : 'symbol' : '1.2-2' }}
        </td>
        <td data-label="">
          <div class="mw-d-flex mw-gap-2 mw-justify-end">
            <button
              type="button"
              class="mw-btn-mini mw-btn-mini-primary"
              data-tooltip="Edit"
              [routerLink]="[invoice.id]"
            >
              <i class="fas fa-pen"></i>
            </button>
            <button
              type="button"
              class="mw-btn-mini mw-btn-mini-danger"
              data-tooltip="Delete"
              (click)="toDelete.set(invoice)"
            >
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </td>
      </tr>
      }
    </tbody>
  </table>
</div>
}

<!-- Delete confirmation -->
<div class="mw-modal-overlay" [class.mw-modal-open]="toDelete() !== null">
  <div class="mw-modal mw-modal-sm">
    <div class="mw-modal-header">
      <h4 class="mw-modal-title">Delete invoice</h4>
      <button type="button" class="mw-modal-close" (click)="toDelete.set(null)">
        &#120299;
      </button>
    </div>
    <div class="mw-modal-body">
      <p class="mw-text-center">
        <strong>Delete {{ toDelete()?.number }}?</strong>
      </p>
      <p class="mw-text-center mw-text-muted">This action cannot be undone.</p>
    </div>
    <div class="mw-modal-footer">
      <button
        type="button"
        class="mw-btn mw-btn-outline"
        (click)="toDelete.set(null)"
      >
        Cancel
      </button>
      <button
        type="button"
        class="mw-btn mw-btn-danger"
        (click)="confirmDelete()"
      >
        <i class="fas fa-trash"></i> Delete
      </button>
    </div>
  </div>
  <div class="mw-modal-backdrop" (click)="toDelete.set(null)"></div>
</div>
```

## Notes

- **`mw-table-subtle` for data tables.** The default primary header bar is a
  landing-page look; over 200 rows it shouts louder than the data.
- **Sticky needs a height cap.** `mw-table-sticky-head` only works inside
  `mw-table-responsive-scroll`; the height comes from
  `--mw-table-scroll-height` and can be set per table inline.
- **`mw-table-cards` needs `data-label` on every cell**, including the action
  column (empty string is fine) - below `md` each row becomes a card and the
  label is rendered as the cell heading.
- **`mw-text-numeric` on the header cell as well**, otherwise the column heading
  sits left while the figures sit right.
- **`mw-tag`, not `mw-tags`**, for a single status chip in a cell.
- **`mw-btn-danger` for the destructive action** in the modal footer.
- The modal is always in the DOM and toggled through `mw-modal-open`; the body
  scroll lock happens automatically via `body:has(.mw-modal-open)`.
- The toast stack lives in the app shell, not on this page - see
  `angular-services.md`.
