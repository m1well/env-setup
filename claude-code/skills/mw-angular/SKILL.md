---
name: mw-angular
description: How Angular code is written in my projects - template always in its own file, signal APIs everywhere (input, output, model, viewChild, computed, linkedSignal), domain state in injectable state services backed by signals and rxResource/httpResource, native control flow, atomic design layering (atoms, molecules, organisms, templates, pages), zoneless tests. Apply whenever writing, reviewing or refactoring Angular components, services, templates, routes or specs, and whenever deciding where a new component belongs. Also invoked via /mw-angular.
argument-hint: [optional - file, feature or component to apply the conventions to]
---

# Angular

These are house rules, not a tutorial. Follow them when producing Angular code; when reviewing, flag every violation with the rule it breaks.

**Baseline is Angular v22+.** Check `package.json` before you write. On an older major, say so in one line, then apply the closest thing that version supports instead of silently generating code that doesn't compile - the version-sensitive spots are marked below.

**Consistency beats these rules in existing code.** If a project already does something differently across the board, match it and mention the divergence once. Don't convert a codebase as a side effect of an unrelated task.

## 1. Template and styles live in their own files

Always `templateUrl` and `styleUrl`. Never an inline `template:` or `styles:` - not for "just three lines", not for a test host, not for a shell component. No exceptions, because the exception is where it always starts.

This one is mine, not Angular's - the style guide is silent on it. Reason: a template that has to earn its own file stays a template instead of quietly growing logic, and the diff of a markup change never touches the class file.

## 2. Signal APIs everywhere

The decorator equivalents are gone. If you write one, you got it wrong.

| Use | Not |
| --- | --- |
| `input()` / `input.required()` | `@Input()` |
| `output()` | `@Output()`, `EventEmitter` |
| `model()` for two-way | `@Input()` + `@Output()` pair |
| `viewChild()`, `viewChildren()`, `contentChild()`, `contentChildren()` (`.required` where it must exist) | `@ViewChild()`, `@ContentChild()` |
| `inject()` | constructor injection |
| `host: {}` in the decorator | `@HostBinding`, `@HostListener` |
| `computed()` | getter over signals, `ngOnChanges` |
| `linkedSignal()` | writable state that has to reset when a source changes |

Also:

- **Never set `standalone: true`** (default since v20) and **never set `changeDetection: OnPush`** (default since v22). On v20/v21 `OnPush` still has to be explicit.
- **`effect()` is the last resort.** Only for pushing state *out* of Angular - localStorage, an imperative third-party lib, logging. Never to compute a signal from other signals, never to sync one signal into another: that is `computed()` or `linkedSignal()`. An `effect` that calls `.set()` is a bug that hasn't fired yet.
- **Never `mutate`** - `set()` or `update()`.
- Everything the template touches is `protected`, everything else `private`. `public` only for the component's actual API (`input`, `output`, `model`). Templates can read `protected`, so nothing needs to be public just to be rendered.
- `readonly` on every signal field. The signal reference never changes; only its value does.

## 3. Domain state lives in a state service

One state service per feature or library - `OrdersState`, `CheckoutState`. It owns the feature's domain state; the feature's **page** injects it, renders it and calls methods on it - nothing below the page layer ever sees it (section 5).

- **`providedIn: 'root'`** when the state is genuinely app-wide. When it is scoped to a feature, provide it in that feature's route (`providers: [OrdersState]` on the parent route) so it dies with the route instead of leaking between visits.
- **Writable signals stay private.** Expose `computed()` or `.asReadonly()`. A component must not be able to `.set()` on feature state.
- **Mutations are domain methods**, named after what happens: `selectOrder(id)`, `applyFilter(status)`, `markAsShipped(id)` - not `setSelectedId`. A state service with only setters is a store with extra steps.
- **No RxJS in the state surface.** No `BehaviorSubject`, no `Observable` fields, no `subscribe()` in a component. RxJS is fine *inside* the API service and inside an `rxResource` stream - that is where it earns its keep.
- **Derived values are `computed()`**, never a field kept in sync by hand.

### Server data: resources, never manual subscriptions

- **`httpResource(...)`** for a plain GET straight into state - it is the shortest correct path and handles status, error and reload for you.
- **`rxResource({ params, stream })`** when an RxJS pipeline sits in between: an existing API service returning `Observable`, retry logic, `switchMap` over several calls, a WebSocket. Both are stable since v22; on v20/v21 they are developer preview and still use `params`/`stream`, on v19 the signature is the older `request`/`loader`.
- **A `params` (or URL) function returning `undefined` means "no request"** - that is how a detail resource stays idle until something is selected. Use it instead of an `@if` guard around the call.
- Reads go through the resource. **Writes stay imperative**: call the API service, then `resource.reload()` or update the local signal. Don't try to model a POST as a resource.
- Expose `isLoading`, `error`, `status` from the resource rather than hand-rolled loading flags.
- Put the resource where the data is used. A resource in a root-provided service refetches for the whole app; if only one feature needs it, scope the service to that feature's route.

### What does *not* belong in the state service

Pure view state - which row is expanded, which tab is active, whether a menu is open - stays a `signal()` in the component. It dies with the view and nothing else cares about it. Moving it into the service is how state services turn into a global bag of booleans.

## 4. Templates

- **Native control flow only**: `@if`, `@for`, `@switch`, `@let`, plus `@empty` and `@placeholder`. Never `*ngIf` / `*ngFor` / `*ngSwitch`.
- **`track` is mandatory** on `@for` and must be a stable identity (`order.id`), not `$index` unless the list is genuinely positional.
- **No `ngClass` / `ngStyle`** - `[class.foo]="cond"` and `[style.width.px]="w"`.
- **No logic in the template.** No arithmetic, no string building, no chained ternaries, no method calls that compute something. If the template needs a value, it's a `computed()` on the class. Two exceptions: reading a signal (`order()`, `state.isLoading()`) is not a method call in this sense, and event handlers may of course call methods.
- **`@defer`** for anything heavy and below the fold; `@placeholder` and `@loading` are part of it, not optional extras.
- **`NgOptimizedImage`** for static images.
- **The async pipe is a smell here** - if you have an `Observable` in a template, the state service is doing it wrong. It's only correct for a stream you genuinely can't model as a resource.
- **Accessibility is not a follow-up ticket**: labels on controls, `role`/`aria-*` where semantics need help, visible focus, contrast at WCAG AA. Interactive things are `<button>`, not `<div (click)>`.

## 5. Structure: feature first, atomic design inside

Two orthogonal axes, and they don't compete: **features** slice the app vertically, **atomic design** layers the component tree inside a slice. So no top-level `components/` or `services/` bucket, but within a feature the components are ordered by layer instead of dumped in one folder.

### The layers

| Layer | What it is | Injects | Knows domain types |
| --- | --- | --- | --- |
| **Atom** | one presentational element: button, input, badge, icon | nothing | no |
| **Molecule** | a handful of atoms as one functional unit; UI logic only, like toggling visibility or showing a validation message | nothing | only if feature-local |
| **Organism** | a distinct section of the interface built from molecules and atoms; owns the UI-level business context and emits strongly typed events | nothing | yes |
| **Template** | page skeleton: layout and `ng-content` slots, no data of its own | nothing | no |
| **Page** | route entry point; wires a template and organisms to the state service | state services | yes |

Pages are the only mandatory layer. Everything below is opt-in and has to earn its place - read the next block before creating one.

### Build top-down - the lower layers are opt-in

**This is the rule that keeps atomic design from turning into component sprawl.** A screen starts as a page with a template. Sections become organisms when they earn it - own UI state, repetition, a template that no longer fits on a screen. You only go further down when something actually forces you.

- **Native elements stay native.** A `<button>`, `<span>`, `<input>` or `<dialog>` inside an organism's template is fine and usually correct. Not every button becomes a component - a `UiButton` that only forwards `disabled`, `type` and a click grows one input per use site and buys nothing but indirection.
- **An atom has to earn its existence**: real behaviour or real styling that would otherwise be duplicated across features. A custom input control, a form field that renders its own validation state, an icon button with a loading spinner - those are atoms. A wrapper around a native element with one passthrough input is not.
- The badge in the examples sits deliberately close to that lower bound: two tone variants plus pill styling that would otherwise be copy-pasted into every feature. **If yours has a single `label` input and nothing else, inline the markup instead.**
- Same for molecules: only when a group of elements repeats *and* carries its own UI logic. Otherwise it is just a section of the organism's template.
- **Templates are worth it early**, atoms usually late. A page skeleton with projection slots pays off with the second page that uses it; an atom often never pays off at all.

### Direction and boundaries

- **The dependency direction is one-way**: atom ← molecule ← organism ← page. An atom imports nothing, a molecule imports atoms, an organism imports molecules and atoms, a page imports templates and organisms. A molecule that contains an organism inverts the hierarchy and is the start of a tangled graph - if it seems necessary, that molecule is really an organism.
- **Only pages inject.** No `inject(OrdersState)` in an atom, molecule or organism. Services enter at the page; everything below is fed by `input()` and answers with `output()`. This single rule is what keeps the lower layers reusable and trivial to test - it is the same boundary rule as in section 3, expressed in layers.
- **The placement test is the domain type**, not a gut feeling about reusability: the moment a component's inputs mention `Order` or `Customer`, it belongs to that feature. Domain-free components live in `ui/`, domain-aware ones under `features/<feature>/`. That check is mechanical, "does this feel reusable?" is not.

### Layout

```
src/app/
├─ core/                            app-wide singletons: auth, config, interceptors
├─ ui/                              the design system - domain-free, injects nothing
│  ├─ atoms/ui-badge/
│  ├─ molecules/ui-field/
│  └─ templates/ui-list-layout/
└─ features/
   └─ orders/
      ├─ orders.routes.ts           lazy routes + feature-scoped providers
      ├─ model/order.ts             types, enums - no logic
      ├─ data/orders-api.ts         HttpClient only, returns Observable
      ├─ state/orders-state.ts      signals + resources, the feature's brain
      ├─ molecules/order-summary/   domain-aware, so not in ui/
      ├─ organisms/order-card/
      └─ pages/order-list/
```

### Naming and files

- **The folder carries the layer, the file name never does.** `organisms/order-card/order-card.ts` holding `class OrderCard` with selector `app-order-card` - never `order-card-organism.ts`, never `OrderCardOrganism`, never `app-order-card-organism`. The words atom, molecule, organism, template and page are vocabulary for talking and for structuring folders; they are not part of any identifier a developer types. The `Component` / `Service` suffixes are out too since the v20 style guide (`OrderList`, not `OrderListComponent`). A project on the old scheme keeps the old scheme, see the consistency rule at the top.
- **Name after function, not after layer or context**: `UiBadge`, `OrderSummary`, `OrderCard`. `UiInput`, never `LoginInput` - context baked into a shared component's name is an instruction not to reuse it. And if a name only makes sense once you know its layer, it is the wrong name.
- **Files sit next to each other and share a name**: `order-card.ts`, `.html`, `.css`, `.spec.ts`.
- **No barrel files inside the app.** Only at a real library boundary (an Nx lib's public API); inside a feature they buy nothing and invite import cycles.
- **In an Nx workspace, make the layering buildable**: `libs/ui/atoms`, `libs/ui/molecules`, `libs/features/orders`, with tags and `@nx/enforce-module-boundaries` denying the upward imports. A lint rule catches the inversion; a convention in a README does not.

## 6. Tests

Zoneless is the default since v21 and Vitest is the CLI's default runner for new projects - so:

- **`await fixture.whenStable()`**, not `fixture.detectChanges()`. Forcing change detection tests a timing that production never has.
- **No `fakeAsync` / `tick`** with Vitest - there is no zone.js patch under it. Use native `async`/`await` and Vitest fake timers. (Karma projects keep `fakeAsync`; check which runner the project uses before writing a spec.)
- **`vi.fn()` / `vi.spyOn()`**, not `jasmine.createSpy` / `spyOn`.
- **Signal inputs are set via `fixture.componentRef.setInput('order', value)`** - never by assigning to the field.
- **`output()` is subscribable**: `component.selected.subscribe(spy)`.
- **State services are tested without a component**: `TestBed.inject(OrdersState)`, then `await TestBed.inject(ApplicationRef).whenStable()` to let resources settle. Fake the API service, not `HttpClient`, when the service goes through one; use `provideHttpClientTesting()` when it uses `httpResource` directly.
- **`TestBed.tick()` drives a resource synchronously** when you need to intercept its request before answering it - `whenStable()` would wait for a response that hasn't been flushed yet. Order is: change the signal, `TestBed.tick()`, `expectOne(...).flush(...)`, then `await` stability.
- **Test through the rendered DOM and the public surface**, not internals. Assert on what the template shows and what the service exposes - a test that reaches for a private signal will break on every refactor.
- Test names say the behaviour, not the mechanics: `clears the selection when the filter changes`, not `should call set`.

## Examples

Worked, self-consistent reference implementation of a small `orders` feature, one file per layer - read the relevant one before writing new code of that shape:

| File | Layer | Shows |
| --- | --- | --- |
| `examples/order.ts` | model | types and enums, no logic |
| `examples/orders-api.ts` | data | thin `HttpClient` layer, `Observable` out |
| `examples/orders-state.ts` | state | the core: private signals, `computed`, `linkedSignal` reset, `rxResource` and `httpResource` side by side, domain methods |
| `examples/ui-badge.*` | atom | domain-free, imports nothing, `input()` only - and near the lower bound of what deserves to be a component at all |
| `examples/ui-list-layout.*` | template | projection slots, empty class on purpose |
| `examples/order-summary.*` | molecule | composes the atom, UI-level `computed`, still no DI |
| `examples/order-card.*` | organism | composes the molecule, `input.required`, `model`, typed `output`, `host` bindings - injects nothing |
| `examples/order-list.*` | page | the only injecting layer: state service, `viewChild.required`, local view state, native control flow |
| `examples/orders-state.spec.ts` | - | service test: resources settling, filter reload, `linkedSignal` reset, `httpResource` via `HttpTestingController` |
| `examples/order-card.spec.ts` | - | component test: `setInput`, `whenStable`, output spy, composition asserted through the real molecule and atom |

Note that no file name and no class name mentions its layer - that is the convention, not an omission. The layer only shows up in the folder and, here, in the table above plus a one-line comment at the top of each example; those comments exist because the examples lie flat in one folder, they don't belong in real code.

They are reference snippets, not a runnable project - in a real app each component sits in its own folder as shown in section 5, and `@ui/...` imports assume a tsconfig path alias. Copy the shape, not the domain.
