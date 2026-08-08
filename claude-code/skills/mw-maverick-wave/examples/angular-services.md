# Example: replacing `main.js` in a SPA

The shipped JavaScript must not be loaded in a SPA
(`references/javascript.md` explains why). These are the replacements - a
service or a component per behaviour, none of them longer than a screen.

## Theme service

The framework only needs one class on `<body>`. Everything else - persistence,
the toggle UI, the initial value - belongs to the application.

```ts
import { Injectable, effect, signal } from '@angular/core';

const STORAGE_KEY = 'mw-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly light = signal(localStorage.getItem(STORAGE_KEY) === 'light');

  constructor() {
    effect(() => {
      const light = this.light();
      document.body.classList.toggle('mw-theme-light', light);
      localStorage.setItem(STORAGE_KEY, light ? 'light' : 'dark');
    });
  }

  toggle(): void {
    this.light.update((value) => !value);
  }
}
```

The framework's own toggle markup, driven by the service:

```html
<div
  class="mw-theme-toggle"
  [class.active]="theme.light()"
  (click)="theme.toggle()"
>
  <div class="mw-theme-toggle-slider">
    <div class="mw-theme-toggle-icon">
      <i
        class="fas"
        [class.fa-sun]="theme.light()"
        [class.fa-moon]="!theme.light()"
      ></i>
    </div>
  </div>
</div>
```

If the stylesheet was compiled with `$mw-theme-mode: 'dark'` or `'light'`, the
class does nothing - hide the toggle in that case
(`getComputedStyle(document.documentElement).getPropertyValue('--mw-internal-theme-mode')`).

## Toast service + outlet

```ts
import { Injectable, signal } from '@angular/core';

export type ToastKind = 'success' | 'warning' | 'danger' | 'info';

export interface Toast {
  id: number;
  kind: ToastKind;
  text: string;
}

@Injectable({ providedIn: 'root' })
export class ToastService {
  private nextId = 0;
  readonly toasts = signal<Toast[]>([]);

  success(text: string) {
    this.push('success', text);
  }
  warning(text: string) {
    this.push('warning', text);
  }
  error(text: string) {
    this.push('danger', text);
  }
  info(text: string) {
    this.push('info', text);
  }

  dismiss(id: number): void {
    this.toasts.update((list) => list.filter((toast) => toast.id !== id));
  }

  private push(kind: ToastKind, text: string): void {
    const toast = { id: this.nextId++, kind, text };
    this.toasts.update((list) => [...list, toast]);
    setTimeout(() => this.dismiss(toast.id), 5000);
  }
}
```

```ts
@Component({
  selector: 'app-toast-outlet',
  template: `
    <div class="mw-toast-stack mw-toast-stack-top-right">
      @for (toast of toasts.toasts(); track toast.id) {
        <div class="mw-alert" [class]="'mw-alert-' + toast.kind">
          <div class="mw-alert-icon">
            <i class="fas" [class]="icon[toast.kind]"></i>
          </div>
          <div class="mw-alert-content">{{ toast.text }}</div>
          <button
            type="button"
            class="mw-btn-mini mw-btn-mini-danger mw-alert-close"
            (click)="toasts.dismiss(toast.id)"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ToastOutletComponent {
  protected readonly toasts = inject(ToastService);
  protected readonly icon: Record<ToastKind, string> = {
    success: 'fa-check-circle',
    warning: 'fa-exclamation-triangle',
    danger: 'fa-times-circle',
    info: 'fa-info-circle',
  };
}
```

Place `<app-toast-outlet />` once in `app.component.html`. The stack is
`position: fixed` and lets clicks through everywhere except on a toast, so it
can sit anywhere in the tree. Auto-dismiss is the `setTimeout` above - the
framework does not provide one. Do not use `mw-alert-closed`; removing the item
from the signal is cleaner.

## Modal

No service needed - the overlay is toggled by one class and the body scroll lock
is pure CSS (`body:has(.mw-modal-open)`).

```ts
@Component({
  selector: 'app-confirm-dialog',
  template: `
    <div class="mw-modal-overlay" [class.mw-modal-open]="open()">
      <div class="mw-modal mw-modal-sm">
        <div class="mw-modal-header">
          <h4 class="mw-modal-title">{{ title() }}</h4>
          <button
            type="button"
            class="mw-modal-close"
            (click)="cancelled.emit()"
          >
            &#120299;
          </button>
        </div>
        <div class="mw-modal-body"><ng-content /></div>
        <div class="mw-modal-footer">
          <button
            type="button"
            class="mw-btn mw-btn-outline"
            (click)="cancelled.emit()"
          >
            Cancel
          </button>
          <button
            type="button"
            class="mw-btn mw-btn-danger"
            (click)="confirmed.emit()"
          >
            Delete
          </button>
        </div>
      </div>
      <div class="mw-modal-backdrop" (click)="cancelled.emit()"></div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConfirmDialogComponent {
  readonly open = input(false);
  readonly title = input('Are you sure?');
  readonly confirmed = output<void>();
  readonly cancelled = output<void>();
}
```

## Accordion

`active` on the header **and** the content - no prefix.

```ts
@Component({
  selector: 'app-faq',
  template: `
    <div class="mw-accordion">
      @for (item of items(); track item.id; let i = $index) {
        <div class="mw-accordion-item">
          <div
            class="mw-accordion-header"
            [class.active]="openIndex() === i"
            (click)="toggle(i)"
          >
            <h3>{{ item.question }}</h3>
            <i class="fas fa-chevron-down mw-accordion-icon"></i>
          </div>
          <div class="mw-accordion-content" [class.active]="openIndex() === i">
            <div class="mw-accordion-content-inner">{{ item.answer }}</div>
          </div>
        </div>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FaqComponent {
  readonly items =
    input.required<{ id: string; question: string; answer: string }[]>();
  protected readonly openIndex = signal(0);

  protected toggle(index: number): void {
    this.openIndex.update((current) => (current === index ? -1 : index));
  }
}
```

## Tabs

`data-tab`/`id` pairing is only for the shipped script - bind `active` instead.

```html
<div class="mw-tabs mw-tabs-pills">
  <div class="mw-tabs-nav">
    @for (tab of tabs; track tab.key) {
    <div
      class="mw-tabs-nav-item"
      [class.active]="active() === tab.key"
      (click)="active.set(tab.key)"
    >
      {{ tab.label }}
    </div>
    }
  </div>
  <div class="mw-tabs-content">
    <div class="mw-tabs-panel" [class.active]="active() === 'details'">…</div>
    <div class="mw-tabs-panel" [class.active]="active() === 'history'">…</div>
  </div>
</div>
```

## Header with mobile navigation

The drawer needs `open` on **both** the burger button and the navbar. Close it
on every navigation.

```ts
@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive],
  template: `
    <header class="mw-header">
      <div class="mw-container">
        <div class="mw-logo">
          <button type="button" routerLink="/">
            <img src="/logo.svg" alt="Home" />
          </button>
        </div>

        <div class="mw-header-actions">
          <nav class="mw-navbar mw-navbar-medium" [class.open]="menuOpen()">
            <ul class="mw-navbar-list">
              @for (item of nav; track item.path) {
                <li class="mw-navbar-item">
                  <a
                    class="mw-navbar-link"
                    [routerLink]="item.path"
                    routerLinkActive="active"
                  >
                    {{ item.label }}
                  </a>
                </li>
              }
            </ul>
          </nav>

          <button class="mw-profile-btn" type="button" (click)="openProfile()">
            <span class="mw-avatar mw-avatar-initials mw-avatar-xs">{{
              initials()
            }}</span>
            <span class="mw-profile-btn-name">{{ user().name }}</span>
          </button>

          <div
            class="mw-menu-btn"
            [class.open]="menuOpen()"
            (click)="menuOpen.set(!menuOpen())"
          >
            <div class="mw-menu-btn-burger"></div>
          </div>
        </div>
      </div>
    </header>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HeaderComponent {
  protected readonly menuOpen = signal(false);

  constructor(router: Router) {
    router.events
      .pipe(
        filter((e) => e instanceof NavigationEnd),
        takeUntilDestroyed()
      )
      .subscribe(() => this.menuOpen.set(false));
  }
}
```

`routerLinkActive="active"` replaces the scroll spy - the framework only cares
about the class name.

## Progress bar

```html
<div class="mw-progress-container">
  <div class="mw-progress-barinfo">
    <span class="mw-progress-label">Upload</span>
    <span class="mw-progress-value mw-progress-percent">{{ percent() }}</span>
  </div>
  <div class="mw-progress-bar">
    <div
      class="mw-progress-fill mw-progress-success"
      [style.width.%]="percent()"
    ></div>
  </div>
</div>
```

`mw-progress-percent` only appends the `%` sign - the number comes from you, and
so does the width.
