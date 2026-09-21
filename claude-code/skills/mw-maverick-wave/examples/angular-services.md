# Example: replacing `main.js` in a SPA

The shipped JavaScript must not be loaded in a SPA
(`references/javascript.md` explains why). These are the replacements - a
service or a component per behaviour, none of them longer than a screen.

## Theme service

The framework only needs one class on `<body>`. Everything else - persistence,
the toggle UI, the initial value - belongs to the application. The second class,
`mw-theme-switching` on `<html>`, is not optional on a page of any size: without
it the flip starts a transition on every element that changes colour.

```ts
import { Injectable, effect, signal } from '@angular/core';

const STORAGE_KEY = 'mw-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  // With nothing stored the stylesheet already follows the OS, so the initial
  // value only has to agree with what is on screen
  readonly light = signal(
    localStorage.getItem(STORAGE_KEY)
      ? localStorage.getItem(STORAGE_KEY) === 'light'
      : matchMedia('(prefers-color-scheme: light)').matches
  );

  constructor() {
    effect(() => {
      const light = this.light();
      const root = document.documentElement;

      root.classList.add('mw-theme-switching');
      document.body.classList.toggle('mw-theme-light', light);
      // the explicit counterpart - without it a dark choice on a light machine
      // falls back to the OS preference
      document.body.classList.toggle('mw-theme-dark', !light);
      void root.offsetHeight; // commit the colours with transitions off
      root.classList.remove('mw-theme-switching');

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
  [class.mw-active]="theme.light()"
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

A `<dialog>` with the same `mw-modal` classes. Escape, the focus trap, the inert
page behind it and the body scroll lock all come from the element, so what is
left to write is opening it.

`[open]="isOpen()"` does **not** work: the attribute opens a non-modal dialog -
no top layer, no backdrop, no focus trap. It has to be `showModal()`, which
needs a directive.

```ts
@Directive({
  selector: 'dialog[appModal]',
  host: {
    '(close)': 'onClose()',
    '(click)': 'onClick($event)',
  },
})
export class ModalDirective {
  readonly isOpen = input(false);
  /** the dialog closed itself - Escape, a backdrop click or a form submit */
  readonly dismiss = output<void>();

  private readonly host =
    inject<ElementRef<HTMLDialogElement>>(ElementRef).nativeElement;

  constructor() {
    const isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

    effect(() => {
      const open = this.isOpen();
      if (!isBrowser) return;
      if (open && !this.host.open) this.host.showModal();
      else if (!open && this.host.open) this.host.close();
    });
  }

  // Only when the dialog closed itself - closing it through the signal already
  // went through whatever set the signal, and reporting that back would run the
  // caller's dismiss handler a second time.
  protected onClose(): void {
    if (this.isOpen()) this.dismiss.emit();
  }

  // A click on the dialog element is a click on its backdrop; the content sits
  // in .mw-modal-header/body/footer inside it. Stands in for `closedby="any"`
  // where that is not supported yet.
  protected onClick(event: MouseEvent): void {
    if (event.target === this.host) this.host.close();
  }
}
```

```ts
@Component({
  selector: 'app-confirm-dialog',
  imports: [ModalDirective],
  template: `
    <dialog
      class="mw-modal mw-modal-sm"
      closedby="any"
      appModal
      [isOpen]="open()"
      (dismiss)="cancelled.emit()"
      aria-labelledby="confirm-title"
    >
      <div class="mw-modal-header">
        <h4 class="mw-modal-title" id="confirm-title">{{ title() }}</h4>
        <button type="button" class="mw-modal-close" (click)="cancelled.emit()">
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
    </dialog>
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

`role="dialog"` and `aria-modal` come from `showModal()`; the title is named
with `aria-labelledby`. Without `autofocus` on something the browser focuses the
first focusable element, usually the close button - put it on the field or the
safe action instead.

In tests, jsdom implements none of `<dialog>` - not `showModal`, `show` or
`close`, only the `open` attribute reflects. Specs that render an open modal
fail with `showModal is not a function` until a setup file adds them.

The `mw-modal-overlay` div toggled by `mw-modal-open` is still styled, for
markup that predates this - it cannot trap focus or make the page inert, so it
is not what to write now.

## Accordion

`mw-active` on the header **and** the content.

```ts
@Component({
  selector: 'app-faq',
  template: `
    <div class="mw-accordion">
      @for (item of items(); track item.id; let i = $index) {
        <div class="mw-accordion-item">
          <button
            type="button"
            class="mw-accordion-header"
            [class.mw-active]="openIndex() === i"
            [attr.aria-expanded]="openIndex() === i"
            [attr.aria-controls]="item.id"
            (click)="toggle(i)"
          >
            <span>{{ item.question }}</span>
            <i class="fas fa-chevron-down mw-accordion-icon"></i>
          </button>
          <div
            class="mw-accordion-content"
            [id]="item.id"
            [class.mw-active]="openIndex() === i"
          >
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
      [class.mw-active]="active() === tab.key"
      (click)="active.set(tab.key)"
    >
      {{ tab.label }}
    </div>
    }
  </div>
  <div class="mw-tabs-content">
    <div class="mw-tabs-panel" [class.mw-active]="active() === 'details'">
      …
    </div>
    <div class="mw-tabs-panel" [class.mw-active]="active() === 'history'">
      …
    </div>
  </div>
</div>
```

## Header with mobile navigation

The panel needs `open` on **both** the burger button and the navbar, plus
`mw-nav-open` on the `<body>` - the scrim, the scroll lock and the rules that
hold the bar and the burger in place all key off that one class, and nothing in
the template can reach the body element. Close it on every navigation.

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
                    routerLinkActive="mw-active"
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

          <button
            type="button"
            class="mw-menu-btn"
            aria-label="Menu"
            aria-controls="main-nav"
            [attr.aria-expanded]="menuOpen()"
            [class.open]="menuOpen()"
            (click)="menuOpen.set(!menuOpen())"
          >
            <span class="mw-menu-btn-burger"></span>
          </button>
        </div>
      </div>
    </header>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HeaderComponent {
  protected readonly menuOpen = signal(false);
  private readonly body = inject(DOCUMENT).body;

  constructor(router: Router) {
    effect(() => this.body.classList.toggle('mw-nav-open', this.menuOpen()));

    router.events
      .pipe(
        filter((e) => e instanceof NavigationEnd),
        takeUntilDestroyed()
      )
      .subscribe(() => this.menuOpen.set(false));
  }
}
```

`routerLinkActive="mw-active"` replaces the scroll spy - the framework only cares
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

## Scroll reveal

`mw-reveal` runs on the browser's scroll timeline and needs nothing from you -
except in Firefox, which ships none, where the block appears without motion.
This directive is the Firefox half: it adds to the class, never replaces it.

```ts
import {
  DestroyRef,
  Directive,
  ElementRef,
  afterNextRender,
  inject,
  signal,
} from '@angular/core';

@Directive({
  selector: '[mwReveal]',
  host: {
    '[class.mw-reveal-hidden]': "state() === 'hidden'",
    '[class.mw-reveal-run]': "state() === 'run'",
    '[style.animation-delay.ms]': 'delay()',
  },
})
export class MwRevealDirective {
  private readonly host =
    inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;

  protected readonly state = signal<'off' | 'hidden' | 'run'>('off');
  protected readonly delay = signal(0);

  constructor() {
    const destroyRef = inject(DestroyRef);

    afterNextRender(() => {
      if (CSS.supports('animation-timeline', 'view()')) return;
      if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      // Already on screen: past its entry range in a timeline browser too
      if (this.host.getBoundingClientRect().top < innerHeight) return;

      this.state.set('hidden');

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (!entry.isIntersecting) return;
          observer.disconnect();
          this.delay.set(this.columnDelay());
          this.state.set('run');
        },
        { threshold: 0.15 }
      );

      observer.observe(this.host);
      destroyRef.onDestroy(() => observer.disconnect());
    });
  }

  // The wave a grid draws in CSS, read back from the columns the browser
  // rendered - one on a phone, so the stagger disappears with them.
  private columnDelay(): number {
    const grid = this.host.parentElement;
    if (!grid?.classList.contains('mw-reveal-stagger')) return 0;
    const columns =
      getComputedStyle(grid).gridTemplateColumns.split(' ').length;
    return ([...grid.children].indexOf(this.host) % columns) * 90;
  }
}
```

A single block carries `mw-reveal`, a grid carries `mw-reveal-stagger` and its
children carry nothing but the directive:

```html
<article class="mw-card mw-reveal" mwReveal>...</article>

<div class="mw-grid-4 mw-reveal-stagger">
  @for (item of items(); track item.id) {
  <article class="mw-card" mwReveal>...</article>
  }
</div>
```

Unlike the shipped script this also covers what a route renders later - the
directive runs per element, not once per page.

`mw-header-reveal` and `mw-parallax` need the same treatment and the same
`CSS.supports` guard. The header is a class toggled past a scroll threshold; the
parallax writes `--mw-parallax-progress` (0 to 1) on each `mw-parallax-media`
from a `requestAnimationFrame` loop, reading every layer's rect before writing
to any of them.
