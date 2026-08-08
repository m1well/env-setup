# Example: static landing page

A complete page without a framework - this is the case the shipped
`maverick-wave.min.js` is built for: accordion, tabs, mobile navigation, theme
toggle and scroll spy all work by themselves. Only opening a modal has to be
wired up by hand.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Acme Analytics</title>

  <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/maverick-wave@3.10.0/maverick-wave.min.css"
  />
  <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
  />

  <style>
    /* Brand colours - one token per family, the rest is derived */
    :root {
      --mw-primary-color: #0f766e;
      --mw-secondary-color: #f39c12;
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
      <nav class="mw-navbar">
        <ul class="mw-navbar-list">
          <li class="mw-navbar-item">
            <a href="#features" class="mw-navbar-link">Features</a>
          </li>
          <li class="mw-navbar-item">
            <a href="#pricing" class="mw-navbar-link">Pricing</a>
          </li>
          <li class="mw-navbar-item">
            <a href="#faq" class="mw-navbar-link">FAQ</a>
          </li>
        </ul>
      </nav>

      <div class="mw-theme-toggle mw-ml-5">
        <div class="mw-theme-toggle-slider">
          <div class="mw-theme-toggle-icon">
            <i class="fas fa-moon"></i>
          </div>
        </div>
      </div>

      <div class="mw-menu-btn"><div class="mw-menu-btn-burger"></div></div>
    </div>
  </div>
</header>

<main class="mw-main">
  <!-- Hero: the container goes full-bleed because it contains mw-hero -->
  <section id="home" class="mw-section">
    <div class="mw-container">
      <div class="mw-hero">
        <div class="mw-home mw-home-content-fade">
          <div class="mw-home-text">
            <h1>Acme <span class="mw-text-primary">Analytics</span></h1>
            <p>Numbers that answer questions instead of raising them.</p>
          </div>
          <div class="mw-d-flex mw-gap-8 mw-justify-center mw-mb-7">
            <button
                    type="button"
                    class="mw-btn mw-btn-primary mw-btn-lg"
                    onclick="openModal('demo')"
            >
              Book a demo
            </button>
            <a href="#features" class="mw-btn mw-btn-outline mw-btn-lg"
            >Learn more</a
            >
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Features -->
  <section id="features" class="mw-section mw-section-alternate">
    <div class="mw-container">
      <h2 class="mw-section-title">Features</h2>

      <div class="mw-grid-3">
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

      <div class="mw-grid-3 mw-mt-8">
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

      <div class="mw-grid-3">
        <div class="mw-card">
          <div class="mw-card-body">
            <h3 class="mw-card-title">Starter</h3>
            <hr class="mw-card-title-divider" />
            <p class="mw-card-text">For small teams getting started.</p>
            <ul class="mw-list mw-list-check">
              <li>3 dashboards</li>
              <li>1 data source</li>
            </ul>
            <div class="mw-card-footer">
              <button type="button" class="mw-btn mw-btn-outline">
                Choose
              </button>
              <span class="mw-text-numeric mw-text-lg">29 €</span>
            </div>
          </div>
        </div>

        <div class="mw-card">
          <div class="mw-card-badge mw-card-addon-success">Popular</div>
          <div class="mw-card-body">
            <h3 class="mw-card-title">Team</h3>
            <hr class="mw-card-title-divider" />
            <p class="mw-card-text">For growing organisations.</p>
            <ul class="mw-list mw-list-check">
              <li>Unlimited dashboards</li>
              <li>SSO</li>
            </ul>
            <div class="mw-card-footer">
              <button type="button" class="mw-btn mw-btn-primary">
                Choose
              </button>
              <span class="mw-text-numeric mw-text-lg">99 €</span>
            </div>
          </div>
        </div>

        <div class="mw-card">
          <div class="mw-card-ribbon mw-card-addon-primary">Enterprise</div>
          <div class="mw-card-body">
            <h3 class="mw-card-title">Custom</h3>
            <hr class="mw-card-title-divider" />
            <p class="mw-card-text">On premise, custom SLA.</p>
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
        </div>
      </div>
    </div>
  </section>

  <!-- FAQ -->
  <section id="faq" class="mw-section mw-section-alternate">
    <div class="mw-container">
      <h2 class="mw-section-title">FAQ</h2>

      <div class="mw-accordion">
        <div class="mw-accordion-item">
          <div class="mw-accordion-header active">
            <h3>Where is the data stored?</h3>
            <i class="fas fa-chevron-down mw-accordion-icon"></i>
          </div>
          <div class="mw-accordion-content active">
            <div class="mw-accordion-content-inner">
              <p>In Frankfurt, in our own data centre.</p>
            </div>
          </div>
        </div>

        <div class="mw-accordion-item">
          <div class="mw-accordion-header">
            <h3>Can I cancel monthly?</h3>
            <i class="fas fa-chevron-down mw-accordion-icon"></i>
          </div>
          <div class="mw-accordion-content">
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
          <p>Book a 20 minute demo - no sales pitch.</p>
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

<script src="https://cdn.jsdelivr.net/npm/maverick-wave@3.10.0/maverick-wave.min.js"></script>
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
- The scroll spy sets `active` on the `mw-navbar-link` whose `href` matches the
  `section[id]` currently in view - the `<section id="…">` elements are the
  contract.
- `mw-navbar` without a size class collapses at `md`. With four to five links
  use `mw-navbar-medium`, with six or more `mw-navbar-large`.
- The hero container becomes full-bleed only because it contains `mw-hero`; the
  other `mw-container` elements stay at `min(1200px, 89%)`.
- Overriding `--mw-primary-color` in a `<style>` block is enough - hover tones,
  translucent backgrounds and the border accent follow via `color-mix()`.
