# BaseLayout, Header, Footer

Klassennamen sind hier Platzhalter. Welche Komponente wie heißt und welche
Teile sie braucht: Skill `mw-maverick-wave`.

## BaseLayout.astro

Eine Datei, alle Seiten. Props, Kopfdaten, Gerüst.

```astro
---
import '@/styles/main.scss';
import Favicons from '@/components/Favicons.astro';
import Scripts from '@/components/Scripts.astro';
import { OG_IMAGE, SITE } from '@/config/site';

type Props = {
  title: string;
  description: string;
  ogType?: 'website' | 'article';
  ogImage?: string | null;
  noIndex?: boolean;
};
const { title, description, ogType = 'website', ogImage = null,
        noIndex = false } = Astro.props;

const canonicalUrl = new URL(Astro.url.pathname, Astro.site);
// Nur das Standardbild hat bekannte Masse - nur es bekommt width/height.
const previewImage = new URL(ogImage ?? OG_IMAGE.path, Astro.site);
---

<!doctype html>
<html lang={SITE.lang}>
  <head>
    <!-- Reihenfolge und Inhalt: references/seo-checkliste.md -->
    <Favicons />
    <slot name="head" />
  </head>
  <body class={SITE.bodyClass || undefined}>
    <a class="mw-skip-link" href="#inhalt">Zum Inhalt springen</a>
    <slot name="header" />
    <main id="inhalt" class="mw-main">
      <slot />
    </main>
    <slot name="footer" />
    <Scripts />
  </body>
</html>
```

**Slots statt Props für Chrome.** Header und Footer kommen als benannte Slots
herein, nicht als Flag. So kann eine Seite `<Header nurZurueck />` schicken,
eine andere Header plus Rabattband, eine dritte gar nichts. Der `head`-Slot
nimmt strukturierte Daten und seitenspezifische Stylesheets auf.

**`optionale Props` gehören ins Layout, nicht in jede Seite.** `ogType`,
`ogImage`, `noIndex` haben Vorgabewerte - eine Unterseite setzt nur, was
abweicht.

**Skip-Link vor allem anderen**, `<main>` mit derselben `id` als Ziel.

Das Layout ist zwischen verwandten Projekten fast gleich, aber **nicht**
identisch - jede Seite hat irgendwann etwas Eigenes (ein `data`-Attribut für
die Aktion, einen `banner`-Slot, eine zusätzliche Prop). Eine Änderung wird
portiert, nicht kopiert.

## Theme ohne Flackern

Bei einer Seite mit Themeumschalter steht im `<head>`, vor dem ersten Paint:

```astro
<script is:inline>
  (function () {
    var stored = localStorage.getItem('mw-theme');
    if (stored === 'light' || stored === 'dark') {
      document.documentElement.classList.add('mw-theme-' + stored);
    }
  })();
</script>
```

`is:inline`, sonst verschiebt Astro es ans Ende. Auf `<html>`, weil es im Head
noch keinen `<body>` gibt. Eine Seite mit festem Theme braucht das nicht - dort
steht der Modus in der SCSS-Konfiguration und die Klasse wäre wirkungslos.
Details zu Tokens und Umschalter: Skill `mw-maverick-wave`.

## Header.astro

Ein Header, mehrere Zustände über boolesche Props:

| Prop           | Wofür                                                                 |
| -------------- | ----------------------------------------------------------------------- |
| *(keine)*      | Startseite: Logo, Navigation, Burger                                    |
| `nurZurueck`   | Rechtstexte und 404: Logo und ein Knopf "Zur Startseite", keine Navigation |
| `unterseite`   | Echte Unterseite: Navigation zeigt auf `/#abschnitt`, nicht auf `#abschnitt` |
| `parallax`     | Der Header fährt erst nach dem Hero ein                                 |

```astro
---
interface Props { nurZurueck?: boolean; parallax?: boolean }
const { nurZurueck = false, parallax = false } = Astro.props;
const { header } = texte;
---
<header class:list={['mw-header', parallax && 'mw-header-reveal']}>
  <div class="mw-container">
    <div class="mw-logo"><a href="/"><img … /></a></div>
    <div class="mw-header-actions">
      {!nurZurueck && (
        <nav id="hauptnavigation" class="mw-navbar" aria-label="Bereiche dieser Seite">
          <ul class="mw-navbar-list">
            {header.navigation.map(e => (
              <li class="mw-navbar-item">
                <a href={e.ziel} class="mw-navbar-link">{e.text}</a>
              </li>
            ))}
          </ul>
        </nav>
      )}
      {nurZurueck && <a class="mw-btn mw-btn-primary mw-btn-sm" href="/">Zur Startseite</a>}
      {!nurZurueck && (
        <button type="button" class="mw-menu-btn" aria-label={header.menue}
                aria-controls="hauptnavigation" aria-expanded="false">
          <span class="mw-menu-btn-burger" />
        </button>
      )}
    </div>
  </div>
</header>
```

- **Logo mit `width`/`height`** im Markup, sonst springt der Header beim Laden.
- **Der Burger ist ein `<button>`**, mit `aria-controls` auf die `id` der
  Navigation. Unterhalb der Umbruchbreite ist er der einzige Weg dorthin.
- **`aria-expanded` pflegt das Framework nicht.** Ein `MutationObserver` auf
  die Zustandsklasse des Knopfes hält es nach - in `Scripts.astro`, damit die
  Reihenfolge der Handler egal ist.
- Navigationseinträge stehen in `texte.json`, nicht im Markup.

## Footer.astro

Vier Blöcke, immer dieselbe Reihenfolge:

1. **Soziale Links** - nur die, die es wirklich gibt, extern mit
   `target="_blank" rel="noopener noreferrer"` und `aria-label`.
2. **Datenschutz auf einen Blick** - ein Satz, der sagt, dass die Seite keine
   Cookies setzt, nichts von Dritten einbindet und nichts misst. Das ist die
   Kurzfassung der Datenschutzerklärung und muss mit ihr übereinstimmen.
3. **Gebaut mit** - Astro und MaverickWave, verlinkt.
4. **Rechtliches** - Impressum und Datenschutz, durch einen Mittelpunkt
   getrennt.

Dazu die Copyright-Zeile mit `new Date().getFullYear()` (Build-Zeit reicht -
die Zahl ist ein Jahr lang richtig) und, bei Kundenseiten, "umgesetzt von
formatwerke".

Alle Texte aus `texte.json`. Links in laufendem Text sind Textlinks, keine
Knöpfe - welche Klasse das ist, steht im Skill `mw-maverick-wave`.

## 404.astro

Eigene Seite, `noIndex`, Header mit `nurZurueck`, ein Leerzustand mit Icon,
einem Satz und einem Knopf zurück auf `/`. Titel und Text aus `texte.json`.

Auf GitHub Pages und beim nginx wird `404.html` automatisch ausgeliefert -
nichts zu konfigurieren, aber die Seite muss existieren.

## Scripts.astro

Alles Clientseitige an einer Stelle, vom Layout am Ende von `<body>` gerendert.
Jeder Block ein eigenes `<script>` mit einem Kommentar, warum er nötig ist:

1. `import 'maverick-wave'` - das Framework-JS.
2. `aria-expanded` am Burger nachziehen.
3. Zeitgesteuertes: Rabatt einblenden, abgelaufene Termine entfernen
   (`references/zeitgesteuert.md`).
4. Seitenzähler-Beacon (`references/projekt-setup.md`).
5. Projektspezifisches - Datumsstempel, Öffnungsstatus, Altersangaben.

`Scripts.astro` ist die eine Datei, die sich zwischen verwandten Projekten
regelmäßig unterscheidet.
