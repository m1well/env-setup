# Example: static landing page

A complete page without a framework - this is the case the shipped
`maverick-wave.min.js` is built for: accordion, mobile navigation, theme toggle
and scroll spy all work by themselves. Only opening a modal has to be wired up
by hand.

The page uses what a landing page reaches for first: an announcement ribbon
under the header, a hero with a scroll cue, feature cards and testimonials that
rise into view as the visitor scrolls, offer cards with a real price row, and an
accordion FAQ.

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Acme Analytics</title>

    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/maverick-wave@4.25.0/maverick-wave.min.css"
    />
    <link
      rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
    />

    <style>
      /* Brand colours - one token per family, the rest is derived */
      :root {
        --mw-primary-color: #0f766e;
        --mw-secondary-color: #b45309;
        --mw-hero-background: url('/assets/hero.jpg');
      }
    </style>
  </head>

  <body>
    <header class="mw-header">
      <div class="mw-container">
        <div class="mw-logo">
          <button type="button" onclick="location.href='#home'">
            <img src="/assets/logo.svg" alt="Acme" />
          </button>
        </div>

        <div class="mw-header-actions">
          <!-- Four links: mw-navbar-medium, so the drawer kicks in one
               breakpoint later than the bare navbar would -->
          <nav class="mw-navbar mw-navbar-medium">
            <ul class="mw-navbar-list">
              <li class="mw-navbar-item">
                <a href="#features" class="mw-navbar-link">Features</a>
              </li>
              <li class="mw-navbar-item">
                <a href="#pricing" class="mw-navbar-link">Pricing</a>
              </li>
              <li class="mw-navbar-item">
                <a href="#voices" class="mw-navbar-link">Voices</a>
              </li>
              <li class="mw-navbar-item">
                <a href="#faq" class="mw-navbar-link">FAQ</a>
              </li>
            </ul>
          </nav>

          <button
            type="button"
            class="mw-theme-toggle mw-ml-5"
            aria-label="Toggle light and dark theme"
          >
            <div class="mw-theme-toggle-slider">
              <div class="mw-theme-toggle-icon">
                <i class="fas fa-moon"></i>
              </div>
            </div>
          </button>

          <div class="mw-menu-btn"><div class="mw-menu-btn-burger"></div></div>
        </div>
      </div>
    </header>

    <!-- The ribbon under the fixed header. It stays put while the page scrolls
         beneath it, and the anchor scroll offset grows by its height on its
         own - #pricing lands below it, not under it -->
    <aside class="mw-announcement mw-announcement-secondary">
      <a class="mw-announcement-content" href="#pricing">
        <span class="mw-announcement-highlight">-20 %</span>
        <span>Launch offer on every plan until 30.09.</span>
      </a>
    </aside>

    <main class="mw-main">
      <!-- Hero: the container goes full-bleed because it contains mw-hero.
           The scroll cue is a sibling of the hero inside that container, and
           the hero keeps a strip at its bottom free for it -->
      <section id="home" class="mw-section">
        <div class="mw-container">
          <div class="mw-hero">
            <div class="mw-home mw-home-content-fade">
              <div class="mw-home-text">
                <h1>Acme <span class="mw-text-primary">Analytics</span></h1>
                <p>
                  Numbers that answer questions instead of raising them. One
                  dashboard for the whole company, live in an afternoon.
                </p>
              </div>
              <div class="mw-d-flex mw-gap-8 mw-justify-center">
                <button
                  type="button"
                  class="mw-btn mw-btn-primary mw-btn-lg"
                  onclick="openModal('demo')"
                >
                  Book a demo
                </button>
                <a href="#features" class="mw-btn mw-btn-secondary mw-btn-lg"
                  >Learn more</a
                >
              </div>
            </div>
          </div>

          <a class="mw-scroll-hint" href="#features">
            More <i class="fas fa-chevron-down"></i>
          </a>
        </div>
      </section>

      <!-- Features -->
      <section id="features" class="mw-section mw-section-alternate">
        <div class="mw-container">
          <h2 class="mw-section-title">Features</h2>
          <p class="mw-section-intro">
            Three things every team asks about on the first call - and the
            numbers behind them.
          </p>

          <!-- mw-reveal-stagger on the grid: every card rises as it scrolls
               in, the second and third of each row a beat later -->
          <div class="mw-grid-3 mw-reveal-stagger">
            <div class="mw-card mw-card-stack">
              <div class="mw-card-stack-header">
                <div class="mw-card-stack-icon">
                  <i class="fas fa-bolt"></i>
                </div>
                <h5 class="mw-card-stack-title">Fast</h5>
              </div>
              <div class="mw-card-stack-body">
                <p class="mw-card-stack-text">
                  Dashboards render in under a second.
                </p>
              </div>
            </div>

            <div class="mw-card mw-card-stack">
              <div class="mw-card-stack-header">
                <div class="mw-card-stack-icon">
                  <i class="fas fa-shield-halved"></i>
                </div>
                <h5 class="mw-card-stack-title">Secure</h5>
              </div>
              <div class="mw-card-stack-body">
                <p class="mw-card-stack-text">EU hosting, SSO, audit log.</p>
              </div>
            </div>

            <div class="mw-card mw-card-stack">
              <div class="mw-card-stack-header">
                <div class="mw-card-stack-icon">
                  <i class="fas fa-plug"></i>
                </div>
                <h5 class="mw-card-stack-title">Connected</h5>
              </div>
              <div class="mw-card-stack-body">
                <div class="mw-tags mw-tags-primary">
                  <span class="mw-tags-item">Postgres</span>
                  <span class="mw-tags-item">BigQuery</span>
                  <span class="mw-tags-item">S3</span>
                </div>
                <p class="mw-card-stack-text">Twelve connectors, no ETL.</p>
              </div>
            </div>
          </div>

          <!-- A single block reveals as one: plain mw-reveal -->
          <div class="mw-grid-3 mw-mt-8 mw-reveal">
            <div class="mw-info mw-info-counter mw-info-primary">
              <div class="mw-info-value">120+</div>
              <div class="mw-info-label">Teams</div>
            </div>
            <div class="mw-info mw-info-counter mw-info-success">
              <div class="mw-info-value">99.9%</div>
              <div class="mw-info-label">Uptime</div>
            </div>
            <div class="mw-info mw-info-counter">
              <div class="mw-info-value">24/7</div>
              <div class="mw-info-label">Support</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Pricing -->
      <section id="pricing" class="mw-section">
        <div class="mw-container">
          <h2 class="mw-section-title">Pricing</h2>
          <p class="mw-section-intro">
            Per workspace, per month. Every plan starts with a 14 day trial.
          </p>

          <!-- mw-offer pushes the price row to the bottom of the body, so the
               three prices line up although the lists differ in length. The
               feature frame reaches above its card - that is what mw-mt-10 is
               for -->
          <div class="mw-grid-3 mw-mt-10 mw-reveal-stagger">
            <article class="mw-card mw-offer">
              <div class="mw-card-body">
                <h3 class="mw-card-title">Starter</h3>
                <hr class="mw-card-title-divider" />
                <p class="mw-card-text">For small teams getting started.</p>
                <ul class="mw-list mw-list-check">
                  <li>3 dashboards</li>
                  <li>1 data source</li>
                </ul>
                <p class="mw-price mw-price-sm">
                  <span class="mw-price-amount">29</span>
                  <span class="mw-price-currency">Euro</span>
                  <span class="mw-price-period">/ month</span>
                </p>
                <p class="mw-price-note">Cancel any time.</p>
                <div class="mw-card-footer">
                  <button type="button" class="mw-btn mw-btn-outline">
                    Choose Starter
                  </button>
                </div>
              </div>
            </article>

            <div class="mw-card-feature mw-card-feature-secondary">
              <p class="mw-card-feature-label">Most booked</p>
              <article class="mw-card mw-offer">
                <div class="mw-card-body">
                  <h3 class="mw-card-title">Team</h3>
                  <hr class="mw-card-title-divider" />
                  <p class="mw-card-text">For growing organisations.</p>
                  <ul class="mw-list mw-list-check">
                    <li>Unlimited dashboards</li>
                    <li>SSO</li>
                    <li>Priority support</li>
                  </ul>
                  <!-- A struck price is invisible to a screen reader - name
                       both prices with mw-sr-only -->
                  <p class="mw-price mw-price-sm">
                    <span class="mw-price-original">
                      <span class="mw-sr-only">Regular price:</span>99 Euro
                    </span>
                    <span class="mw-sr-only">Now:</span>
                    <span class="mw-price-amount">79</span>
                    <span class="mw-price-currency">Euro</span>
                    <span class="mw-tag mw-tag-secondary">-20%</span>
                  </p>
                  <p class="mw-price-note">
                    Per month, launch offer until 30.09.
                  </p>
                  <div class="mw-card-footer">
                    <button type="button" class="mw-btn mw-btn-primary">
                      Choose Team
                    </button>
                  </div>
                </div>
              </article>
            </div>

            <article class="mw-card mw-offer">
              <div class="mw-card-body">
                <h3 class="mw-card-title">Enterprise</h3>
                <hr class="mw-card-title-divider" />
                <p class="mw-card-text">On premise, custom SLA.</p>
                <ul class="mw-list mw-list-check">
                  <li>Everything in Team</li>
                  <li>Named contact</li>
                </ul>
                <p class="mw-price mw-price-sm">
                  <span class="mw-price-word">On request</span>
                </p>
                <p class="mw-price-note">Priced per seat, yearly term.</p>
                <div class="mw-card-footer">
                  <button
                    type="button"
                    class="mw-btn mw-btn-outline"
                    onclick="openModal('demo')"
                  >
                    Contact us
                  </button>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>

      <!-- Voices -->
      <section id="voices" class="mw-section mw-section-alternate">
        <div class="mw-container">
          <h2 class="mw-section-title">Voices</h2>
          <p class="mw-section-intro">
            What teams say after the first quarter.
          </p>

          <!-- Quotes of unequal length: columns, not a grid. The stagger
               works on the column children just the same -->
          <div class="mw-columns-3 mw-reveal-stagger">
            <figure class="mw-testimonial">
              <blockquote>
                The first dashboard was live before the kickoff meeting ended.
              </blockquote>
              <figcaption class="mw-testimonial-source">
                Lena B.
                <span class="mw-testimonial-detail"
                  >&middot; Head of Operations</span
                >
                <time class="mw-testimonial-date" datetime="2026-06"
                  >June 2026</time
                >
              </figcaption>
            </figure>

            <figure class="mw-testimonial">
              <blockquote>
                We replaced three reporting tools with one. Finance stopped
                asking for exports, they open the dashboard themselves - and for
                the first time everyone quotes the same number.
              </blockquote>
              <figcaption class="mw-testimonial-source">
                Daniel K.
                <span class="mw-testimonial-detail">&middot; CFO</span>
              </figcaption>
            </figure>

            <figure class="mw-testimonial">
              <blockquote>Connected our warehouse in an afternoon.</blockquote>
              <figcaption class="mw-testimonial-source">
                Sofia R.
                <span class="mw-testimonial-detail"
                  >&middot; Data Engineer</span
                >
              </figcaption>
            </figure>
          </div>
        </div>
      </section>

      <!-- FAQ -->
      <section id="faq" class="mw-section">
        <div class="mw-container">
          <h2 class="mw-section-title">FAQ</h2>

          <div class="mw-accordion">
            <div class="mw-accordion-item">
              <button
                type="button"
                class="mw-accordion-header mw-active"
                aria-expanded="true"
                aria-controls="faq-storage"
              >
                <span>Where is the data stored?</span>
                <i class="fas fa-chevron-down mw-accordion-icon"></i>
              </button>
              <div class="mw-accordion-content mw-active" id="faq-storage">
                <div class="mw-accordion-content-inner">
                  <p>In Frankfurt, in our own data centre.</p>
                </div>
              </div>
            </div>

            <div class="mw-accordion-item">
              <button
                type="button"
                class="mw-accordion-header"
                aria-expanded="false"
                aria-controls="faq-cancel"
              >
                <span>Can I cancel monthly?</span>
                <i class="fas fa-chevron-down mw-accordion-icon"></i>
              </button>
              <div class="mw-accordion-content" id="faq-cancel">
                <div class="mw-accordion-content-inner">
                  <p>Yes, at the end of every billing period.</p>
                </div>
              </div>
            </div>
          </div>

          <div class="mw-alert mw-alert-info mw-mt-6">
            <div class="mw-alert-icon"><i class="fas fa-lightbulb"></i></div>
            <div class="mw-alert-content">
              <span class="mw-alert-title">Still unsure?</span>
              <!-- A link in running text is mw-link, not a button class - it
                   keeps the line height of the paragraph around it -->
              <p>
                <button
                  type="button"
                  class="mw-link"
                  onclick="openModal('demo')"
                >
                  Book a 20 minute demo</button
                >, no sales pitch.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="mw-footer">
      <div class="mw-container">
        <div class="mw-footer-top">
          <div class="mw-footer-column">
            <h3>Acme Analytics</h3>
            <p>Numbers that answer questions.</p>
          </div>
          <div class="mw-footer-column">
            <h3>Product</h3>
            <ul>
              <li><a href="#features">Features</a></li>
              <li><a href="#pricing">Pricing</a></li>
              <li><a href="#faq">FAQ</a></li>
            </ul>
          </div>
        </div>

        <div class="mw-social-links">
          <a href="#" data-tooltip="GitHub"><i class="fab fa-github"></i></a>
          <a href="mailto:hi@example.com" data-tooltip="Mail"
            ><i class="fa fa-envelope"></i
          ></a>
        </div>

        <p class="mw-copyright">&copy; 2026 Acme</p>
      </div>
    </footer>

    <!-- Modal: markup stays in the DOM, mw-modal-open shows it -->
    <div id="demo" class="mw-modal-overlay">
      <div class="mw-modal">
        <div class="mw-modal-header">
          <h4 class="mw-modal-title">Book a demo</h4>
          <button type="button" class="mw-modal-close">&#120299;</button>
        </div>
        <div class="mw-modal-body">
          <form class="mw-form">
            <div class="mw-field">
              <label class="mw-field-label mw-required" for="demo-email"
                >Email</label
              >
              <div class="mw-input-group">
                <span class="mw-input-group-prefix"
                  ><i class="fas fa-envelope"></i
                ></span>
                <input id="demo-email" type="email" class="mw-input" required />
              </div>
            </div>
          </form>
        </div>
        <div class="mw-modal-footer">
          <button
            type="button"
            class="mw-btn mw-btn-outline"
            onclick="closeModal('demo')"
          >
            Cancel
          </button>
          <button type="button" class="mw-btn mw-btn-primary">Send</button>
        </div>
      </div>
      <div class="mw-modal-backdrop" onclick="closeModal('demo')"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/maverick-wave@4.25.0/maverick-wave.min.js"></script>
    <script>
      // The only thing the shipped script does not cover: opening a modal.
      // Closing works through .mw-modal-close, the backdrop is wired above.
      function openModal(id) {
        document.getElementById(id).classList.add('mw-modal-open');
      }
      function closeModal(id) {
        document.getElementById(id).classList.remove('mw-modal-open');
      }
    </script>
  </body>
</html>
```

## Notes

- The theme toggle needs no code - the script persists the choice under
  `localStorage['mw-theme']` and toggles `mw-theme-light` on `<body>`.
- The scroll spy sets `mw-active` on the `mw-navbar-link` whose `href` matches
  the `section[id]` currently in view - the `<section id="…">` elements are
  the contract.
- `mw-navbar` without a size class collapses at `md`. With four to five links
  use `mw-navbar-medium`, with six or more `mw-navbar-large`.
- The hero container becomes full-bleed only because it contains `mw-hero`; the
  other `mw-container` elements stay at `min(1200px, 89%)`. The scroll cue is a
  sibling of `mw-hero` in that container - the hero reserves a strip at its
  bottom for it, so the buttons never sit on top of the cue.
- `mw-announcement` is fixed below the header. `scroll-padding-top` grows by
  `--mw-announcement-height` automatically, so an anchor scrolled to lands
  below the ribbon. One per page; `mw-announcement-static` puts it in the flow
  instead.
- `mw-reveal-stagger` goes on the grid (or `mw-columns-*`) and reveals every
  child as it scrolls in, the second and third of each three a beat later.
  `mw-reveal` on a single block reveals that block as one. Both are off under
  `prefers-reduced-motion`, and a browser without scroll timelines renders the
  blocks in place - never invisible.
- `mw-offer` on a card pushes the price row to the bottom of the body, so the
  prices in a row line up. The `mw-card-feature` frame around the middle plan
  reaches 29px above its card - the `mw-mt-10` on the grid is that room.
- Overriding `--mw-primary-color` in a `<style>` block is enough - hover tones,
  translucent backgrounds and the border accent follow via `color-mix()`.
