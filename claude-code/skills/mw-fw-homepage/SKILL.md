---
name: mw-fw-homepage
description: Bauplan für die statischen Astro-Kundenhomepages aus dem homepages-Workspace - Projektgerüst, BaseLayout mit Header und Footer, Impressum und Datenschutz als eigene Seiten, weitere Unterseiten wie Angebot oder Blog, SEO- und OG-Checkliste, zeitgesteuerte Rabattbänder und Termine, Inhalte als JSON. Anwenden, wenn eine neue solche Seite entsteht, eine bestehende erweitert wird, oder wenn Fragen zu Aufbau, Rechtstexten, Metadaten, Aktionen oder Terminen auf diesen Seiten kommen.
---

# Statische Kundenhomepage (Astro)

Eine Seite dieser Familie ist: Astro, `output: 'static'`, kein Framework im
Browser, keine Datenbank, kein CMS. Inhalte liegen als JSON neben dem Code, der
Build bäckt alles zu HTML. Was danach noch wandern muss - ein ablaufender
Rabatt, ein vergangener Termin, das Datum des Mittagstischs - korrigiert ein
kurzes Inline-Skript im Browser.

## MaverickWave ist gesetzt

Jede Seite dieser Familie lädt [MaverickWave](https://maverick-wave.m1well.com)
als npm-Paket und baut ihr Markup aus `mw-*`-Klassen. Davon ist auszugehen,
solange nichts anderes dasteht.

**Die Beispiele hier zeigen nur das Gerüst.** Welche `mw-*`-Klasse an welcher
Stelle steht, wie die Tokens heißen und was die Komponenten können, steht im
Skill **`mw-maverick-wave`** - das Framework entwickelt sich weiter, die
Klassennamen hier sind Platzhalter für "hier kommt die passende Komponente
hin". Für jedes Detail an Markup oder Styling: dort nachschlagen, nicht hier.

Sollte eine Seite ohne MaverickWave entstehen, gilt alles außer den
Klassennamen unverändert - Projektgerüst, Layout-Aufteilung, Rechtstexte, SEO,
Zeitsteuerung, Inhaltsdateien.

## Skelett

```
src/
  components/       Abschnitte der Startseite, je eine .astro-Datei
    Header.astro    Footer.astro   Scripts.astro   Icon.astro   icons.ts
  config/
    site.ts         SITE und OG_IMAGE - alles, was pro Projekt abweicht
  content/
    texte.json      jeder sichtbare Satz der Seite
    datenschutz.json
    <fachlich>.json kurse.json, preise.json, workshops.json, aktion.json
  layouts/
    BaseLayout.astro
  pages/
    index.astro  impressum.astro  datenschutz.astro  404.astro
  styles/
    main.scss  _landing.scss  _fonts.scss  [_icons.scss]
  kontakt.ts        Mailadresse und alle mailto-Links an einer Stelle
public/
  favicon.ico  robots.txt  fonts/  images/  favicon/
```

Namen sind deutsch, wo sie Fachliches benennen (`Preise.astro`, `kurse.json`,
`aktion.bis`), englisch bei Technik (`BaseLayout`, `SITE`, `config`). Nicht
mischen innerhalb einer Datei.

## Die harten Regeln

1. **Kein Satz im Markup.** Jeder sichtbare Text kommt aus `content/*.json`.
   Die `.astro`-Datei rendert, sie textet nicht. Ausnahme: ein Wort, das
   zur Struktur gehört ("Euro", "&middot;").
2. **`site.ts` ist die einzige Projektvariable.** Name, Sprache, Themefarbe,
   Preload-Fonts, OG-Bild. Wer eine zweite Seite aus dieser aufsetzt, tauscht
   `site.ts` und `content/` - sonst nichts.
3. **Impressum und Datenschutz sind eigene Seiten**, nie ein Abschnitt oder
   ein Modal. Siehe `references/rechtstexte.md`.
4. **Der Build ist die Wahrheit, der Browser korrigiert nur nach unten.** Ein
   Skript darf etwas ausblenden oder entfernen, das schon im HTML steht. Es
   darf nichts einblenden, was ohne JavaScript fehlt - außer der Rabatt, und
   dort ist die Richtung bewusst: ohne Skript gilt der reguläre Preis.
   Siehe `references/zeitgesteuert.md`.
5. **Kein Drittanbieter im Frontend.** Keine Fonts von Google, kein Analytics,
   keine Karten-Einbettung, kein Cookie-Banner - weil es nichts zu bannern
   gibt. Das ist die Grundlage der Datenschutzerklärung und darf nicht
   nebenbei aufgeweicht werden.
6. **Eigenes CSS nur, wo das Framework nichts hat.** Projektpräfix (`sw-`,
   `fw-`, `hp-`), nie etwas im `mw-`-Namensraum erfinden.

## Referenzen

Nur die laden, die gebraucht wird.

| Datei                                  | Inhalt                                                                                                     |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `references/projekt-setup.md`          | `package.json`, `astro.config.mjs`, Alias, `base` für Beispielseiten, ESLint/Prettier, Deploy, CSP          |
| `references/layout-header-footer.md`   | `BaseLayout.astro`, Header-Varianten, Footer-Blöcke, 404, `Scripts.astro`, Theme ohne Flackern              |
| `references/seo-checkliste.md`         | Metadaten, OG- und Twitter-Karte, Canonical, Sitemap, robots.txt, JSON-LD, Favicons - als abhakbare Liste   |
| `references/rechtstexte.md`            | Gerüst für Impressum und Datenschutz, was pro Branche dazukommt                                            |
| `references/unterseiten.md`            | Warum eigene Seiten, wie in Astro (Route, Collection, Breadcrumb, Rücksprung), wie im Design                |
| `references/zeitgesteuert.md`          | Rabattband und Termine, die 12-Stunden-Regel, Aufteilung Build/Browser, strukturierte Daten dazu            |
| `references/inhalte.md`                | `texte.json`, fachliche JSON, Icons als Inline-SVG, selbstgehostete Schriften, Bilder                       |

## Neue Seite aufsetzen - Reihenfolge

1. Bestehende Seite kopieren, die fachlich am nächsten liegt (Dienstleistung,
   Gastronomie, Produkt), `node_modules`, `dist`, `.git` weglassen.
2. `package.json` Name, `astro.config.mjs` `site` (und `base`, falls
   Beispielseite), `src/config/site.ts`, `src/kontakt.ts`.
3. `content/texte.json` durchgehen - jeden Satz ersetzen, keinen stehen lassen.
4. `content/datenschutz.json` und die Impressumsdaten anpassen, Branchenteil
   ergänzen (`references/rechtstexte.md`).
5. Schriften, Favicon, OG-Bild, Fotos tauschen.
6. Abschnitte der Startseite zusammenstellen, Navigation in `texte.json`
   und die `id` der Sections gegeneinander prüfen.
7. `npm run checkup && npm run build`, dann die Checkliste in
   `references/seo-checkliste.md` abhaken.

## Fallstricke

- **Ein Navigationseintrag ohne seine Section** (oder umgekehrt) bricht die
  Sprungmarken lautlos. Die `href`-Werte in `texte.json` und die `id` der
  `<section>` gehören zusammen geprüft.
- **`base` in `astro.config.mjs` gilt nicht für eigene `href`.** Astro setzt
  es nur vor die Links, die es selbst erzeugt. Alles aus `public/` und jeder
  handgeschriebene Link muss durch den `pfad()`-Helfer -
  `references/projekt-setup.md`.
- **Ein Datum im Build ist das Datum des Builds.** Alles, was "heute",
  "diese Woche" oder "demnächst" bedeutet, braucht die Korrektur im Browser.
- **`noIndex` gehört auf 404, Impressum und Datenschutz**, und die Sitemap
  listet nur, was ranken soll.
- **Beispielseiten** (erfundene Kunden auf `beispiel.formatwerke.de/<name>/`)
  tragen ein Band im Layout, `base` in der Config und `noindex` überall.
