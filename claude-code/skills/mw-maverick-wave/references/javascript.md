# JavaScript & SPA integration

## What `maverick-wave.min.js` is

One vanilla IIFE, no dependencies, ~23 kB. It queries the DOM **once** on
`DOMContentLoaded` and attaches listeners. There is no re-init API, no
`MutationObserver`, no exported module - it is built for a server-rendered or
static page.

## Why a SPA must not load it

- It runs once during bootstrap. Anything rendered afterwards - i.e. everything
  in a routed application - never gets initialised.
- It writes straight into the DOM (class toggles, generated elements, inline
  styles). In Angular that happens outside change detection; in a zoneless app
  the framework never learns about it, and on the next re-render your bindings
  win and the mutation is gone.
- It reads and writes `localStorage` for the theme, competing with whatever
  service you build for the same job.

So: no `"scripts"` entry in `angular.json`, no `import 'maverick-wave.min.js'`
in a Vite entry point. Load the **CSS only** and rebuild the handful of
behaviours in components. Each one is a few lines - the framework's state
classes are the entire contract.

## Behaviour inventory

| Behaviour           | What the shipped JS does                                                                                                                                                                                                                                                        | What to do instead                                                                                                                                                                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Accordion           | Toggles `mw-active` on `mw-accordion-header` and the following `mw-accordion-content`, and writes `aria-expanded` when the header is a `<button>`                                                                                                                               | `[class.mw-active]="isOpen()"` and `[attr.aria-expanded]="isOpen()"` on the header, `mw-active` on the panel                                                                                                                 |
| Tabs                | `data-tab` → panel `id`; sets `mw-active` on nav item and panel, and wires the whole tablist: `role`, `aria-selected`, `aria-controls`, `aria-labelledby`, a roving `tabindex` and arrow/Home/End keys                                                                          | Track the selected index/key, bind `mw-active` on both; drop `data-tab`                                                                                                                                                      |
| Modal               | Click on `mw-modal-close` removes `mw-modal-open` from the overlay                                                                                                                                                                                                              | `[class.mw-modal-open]="isOpen()"`; backdrop click closes. Opening is not in the script at all (the showcase has its own `openModal`)                                                                                        |
| Mobile nav          | Toggles `open` on `mw-menu-btn` and `mw-navbar`, writes `aria-expanded` when the button is a `<button>`, closes on anchor click and on Escape (focus returns to the button)                                                                                                     | One signal, bound to both; reset it on navigation end                                                                                                                                                                        |
| Scroll spy          | Sets `mw-active` on `mw-navbar-link` from the scroll position                                                                                                                                                                                                                   | Router-based: `routerLinkActive="mw-active"`                                                                                                                                                                                 |
| Anchor scrolling    | Intercepts `a[href^="#"]` and runs its own eased scroll - duration scales with distance, capped at 1.4s, cancelled by wheel or touch. Lands on `scroll-padding-top`, moves focus to the target, writes the hash with `replaceState`, and measures a sticky target unpinned      | The router; for in-page anchors `scrollIntoView({ behavior: 'smooth' })` or your own animation                                                                                                                               |
| Theme toggle        | `localStorage['mw-theme']`, toggles `mw-theme-light` / `mw-theme-dark` on `<body>` and `mw-active` on the toggle, wrapped in `mw-theme-switching` on `<html>` so the flip starts no transitions. With nothing stored it takes `prefers-color-scheme` and keeps following it     | A theme service - see `examples/angular-services.md`                                                                                                                                                                         |
| Progress bar        | `IntersectionObserver` sets `width` from `data-value`                                                                                                                                                                                                                           | Bind `[style.width.%]="value()"` on `mw-progress-fill`                                                                                                                                                                       |
| Slider              | On `input`, sets `--value` (track fill) and `data-value` (badge text)                                                                                                                                                                                                           | Bind `[style.--value.%]` and `[attr.data-value]`                                                                                                                                                                             |
| Alerts              | Close button adds `mw-alert-closing` (fade out), then `mw-alert-closed` (`display: none`) after `--mw-duration-base`                                                                                                                                                            | Remove the alert from the list/signal                                                                                                                                                                                        |
| Checkbox lists      | Adds `mw-selected` to the `li`, emits a `checkboxToggle` event, exposes `window.toggleCheckbox`                                                                                                                                                                                 | `[class.mw-selected]="item.checked"`                                                                                                                                                                                         |
| Gallery             | Generates the dots, moves the track, swipe handling, writes `mw-gallery-desc`                                                                                                                                                                                                   | Render dots in the template, bind the track transform and `mw-active` on the current dot                                                                                                                                     |
| Image slider        | Toggles `mw-active` on the overlay image and the control button with the matching `data-index`                                                                                                                                                                                  | Bind `mw-active` from the selected index                                                                                                                                                                                     |
| Kanban board        | Counts the tickets per lane, moves a card between lanes (`data-kanban-move`) and marks the arrival with `mw-kanban-card-moved-forward` / `-back`, clones `mw-kanban-card-template` on save, derives the next key from `data-kanban-prefix`, toggles `mw-active` on the composer | Keep the tickets in a signal/store and render the lanes from it; `mw-active` on the composer, `mw-kanban-editing` on the ticket it replaces. Neither the `<template>` nor the `mw-kanban-composer-*` hook classes are needed |
| Calendar            | Renders the month or week grid from `data-calendar="month                                                                                                                                                                                                                       | week"`, pages with `data-calendar-nav`, draws the status dots from `data-calendar-markers`, toggles `mw-selected`and emits`mw-calendar-select`                                                                               | Render the cells from a signal and bind `mw-calendar-adjacent`, `mw-calendar-weekend`, `mw-calendar-today` and `mw-selected` yourself; none of the `data-calendar-*` attributes are needed |
| Localhost indicator | On a local hostname, prepends `mw-localhost-indicator-pulse` to the header when it carries `mw-localhost-indicator-activated`                                                                                                                                                   | Render the element conditionally                                                                                                                                                                                             |
| Header login button | Swaps the FontAwesome lock icon                                                                                                                                                                                                                                                 | Bind the icon class                                                                                                                                                                                                          |
| Color swatches      | Showcase-only (prints computed hex values); exposes `window.mwRefreshColorSwatches` to read them again after a root colour changed                                                                                                                                              | Not needed                                                                                                                                                                                                                   |
| Dropdown            | Delegated to the document: closes the open `mw-dropdown` on Escape, on a click elsewhere and on a click on a `mw-dropdown-item`, and returns focus to the `summary`                                                                                                             | The `<details>` does the opening, the keyboard and the state on its own. Rebuild only the two behaviours markup cannot express - or bind `[attr.open]` and keep them in the component                                        |
| Language switcher   | Keeps the trigger's flag and code in step with the chosen item, moves `mw-active` and `aria-current`, and fires `mw-language-change` (`detail: { lang, name }`) on the switcher                                                                                                 | Bind the trigger from your locale signal and switch the language in your own i18n service; the menu itself is a `<details>` and needs nothing                                                                                |
| Scroll reveal       | Older browsers only: an `IntersectionObserver` adds `mw-reveal-hidden` to what is still below the fold and swaps it for `mw-reveal-run` on entry, with an `animation-delay` per grid column                                                                                     | A directive per element - see `examples/angular-services.md`                                                                                                                                                                 |
| Header reveal       | Older browsers only: toggles `mw-header-away` and `mw-announcement-away` past 270px of scroll, and adds the transition class one frame later so the bar does not slide away on load                                                                                             | The same two classes bound to a scroll signal, behind the same guard                                                                                                                                                         |
| Parallax            | Older browsers only: writes `--mw-parallax-progress` (0 to 1) on every `mw-parallax-media` from a `requestAnimationFrame` loop                                                                                                                                                  | The same, reading every layer's rect before writing to any of them                                                                                                                                                           |

## Scroll-driven animations

Four things ride the browser's own scroll timeline: `mw-reveal`,
`mw-header-reveal`, `mw-parallax` and the `mw-progress-fill` scrub. Chrome and
Edge have had timelines since 115, Firefox since 158 and Safari since 26, and
there they need no script at all. Older versions get the shipped JS instead.
Each one checks `CSS.supports('animation-timeline', ...)` first and does nothing
where the browser has it.

Without the script an older browser loses the motion and nothing else: cards
stand in place, the picture holds still. The exception is `mw-header-reveal`,
where the bar then sits over the hero from the first paint - a layout
difference, not a missing effect.

## Modals and progress bars

`mwOpenModal(id)` / `mwCloseModal(id)` are on `window` and handle both modal
shapes - the `mw-modal-overlay` div and a `<dialog class="mw-modal">`. Close
buttons and `data-mw-modal="<id>"` triggers are delegated from the document, so
markup rendered later still works. A `<dialog>` needs none of it in a SPA: call
`showModal()` and `close()` on the element.

`mw-progress-fill` takes its target width from `data-value="75"` or an inline
`style="width: 75%"`. Where scroll-driven animations are supported the bar fills
with the scroll position and the script only hands the value over; elsewhere it
falls back to setting the width once the bar comes into view.

## A note on the state class

Since 4.0.0 the script writes `mw-active` and clears both `mw-active` and the
deprecated bare `active` when it switches a state off. That is deliberate: HTML
written against an older version marks the first tab with `active`, and if
switching away only removed `mw-active`, that first tab would stay lit next to
the newly chosen one. In your own components bind `mw-active` and forget the
other spelling exists.

## What works without any JavaScript

Pure CSS, nothing to wire up: hover, focus and press states, the card lift,
tooltips (`data-tooltip`), `mw-rating` (via `data-rating`), the responsive table
card view (`data-label`), all grids and utilities, the body scroll lock while a
modal is open (`body:has(.mw-modal-open)`), the modal turning into a bottom
sheet below 576px, toast entry animations, the sticky table header, the scroll
hint on a tab bar (four gradients, no scroll listener), the kanban empty-lane
placeholder (hidden via `:has()` as soon as the lane holds a ticket), touch
target sizing on a coarse pointer, `prefers-reduced-motion` handling.

`mw-dropdown` is _almost_ in this list: opening, closing, the keyboard and the
open state are all the `<details>` element, so it works with no script at all.
The only two things the shipped JS adds are closing on Escape and closing on a
click somewhere else - worth rebuilding in a SPA, but a menu without them is
still a working menu, not a broken one.

## When you do keep the shipped JS

For a static page, a landing page or a server-rendered site (Thymeleaf, Twig,
Jekyll, plain HTML) it is exactly right - load it at the end of `<body>`. The
only manual part is opening a modal, which the script does not cover:

```html
<script src="maverick-wave.min.js"></script>
<script>
  function openModal(id) {
    document.getElementById(id).classList.add('mw-modal-open');
  }
  function closeModal(id) {
    document.getElementById(id).classList.remove('mw-modal-open');
  }
</script>
```
