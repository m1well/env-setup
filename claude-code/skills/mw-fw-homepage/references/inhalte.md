# Inhalte, Icons, Schriften, Bilder

## texte.json

Jeder sichtbare Satz der Seite, nach Abschnitt gruppiert - die Gruppen heißen
wie die Komponenten, die sie rendern:

```jsonc
{
  "seite":   { "titel": "…", "beschreibung": "…" },
  "header":  { "logoAlt": "…", "menue": "Menü öffnen",
               "navigation": [{ "text": "Über mich", "ziel": "#ueber-mich" }] },
  "ueberMich": { "titel": "Über mich", "name": "…", "rolle": "…",
                 "absaetze": ["…", "…"] },
  "footer":  { "datenTitel": "…", "hinweis": "…", "impressum": "Impressum" },
  "nichtGefunden": { "titel": "Hier ist nichts", "text": "…", "cta": "…" },
  "impressum": { "titel": "Impressum", "anschrift": { … } }
}
```

Die Komponente holt sich ihre Gruppe im Frontmatter:

```astro
const { ueberMich } = texte;
```

Warum JSON und nicht Markdown oder ein CMS: der Kunde bekommt eine Datei, in
der jeder Satz einmal vorkommt, mit einem Schlüssel, der sagt, wo er landet.
Kein Build-Wissen nötig, und ein Tippfehler bricht höchstens den Satz.

Was **nicht** hineingehört: Klassennamen, HTML-Struktur, URLs von Bildern.

### Betonung im Text

Für fettgesetzte Stellen in einem Fließtextabsatz reicht ein Minimalformat -
`**…**`, sonst nichts:

```ts
// texte.json markiert einzelne Stellen mit **…** - mehr Markdown braucht die
// Seite nicht.
const escape = (wert: string) =>
  wert.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export const betont = (wert: string) =>
  escape(wert).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
```

Gerendert mit `set:html={betont(absatz)}`. Das `escape` davor ist Pflicht -
sonst ist eine Inhaltsdatei eine Einladung zum HTML-Einschleusen.

## Fachliche JSON

Alles, was mehr als Text ist, bekommt eine eigene Datei: `preise.json`,
`kurse.json`, `workshops.json`, `feedback.json`, `mittagstisch.json`,
`aktion.json`, `datenschutz.json`.

Dazu ein TypeScript-Interface mit einem Doc-Kommentar **pro Feld** - das ist
die Bedienungsanleitung für den, der die Datei pflegt:

```ts
export interface Kurs {
  titel: string;
  /** Nur die Zahl, Euro versteht sich. 0 wird als "kostenlos" gezeigt. */
  preis?: string | number;
  /** JJJJ-MM-TT - laesst den Eintrag automatisch ablaufen. */
  datum?: string;
}
```

Zeitabhängige Felder: `references/zeitgesteuert.md`.

## kontakt.ts

Mailadresse, Handles und alle `mailto`-Links an einer Stelle, mit
vorformuliertem Betreff und Anrede:

```ts
export const kontaktMail = 'info@<domain>';
export const instagramHandle = '<handle>';
export const instagramLink = `https://www.instagram.com/${instagramHandle}/`;

const mailto = (betreff: string, rumpf: string) =>
  `mailto:${kontaktMail}?subject=${encodeURIComponent(betreff)}` +
  `&body=${encodeURIComponent(rumpf)}`;

export const mailLink = mailto('Anfrage über <domain>', 'Hallo …,\n\n');

export const buchungsLink = (angebot: string) =>
  mailto(`Buchung: ${angebot}`,
         `Hallo …,\n\nich interessiere mich für "${angebot}".\n\n`);
```

Ein vorausgefüllter Betreff ist der Unterschied zwischen einer Anfrage, die
zugeordnet werden kann, und einer mit dem Betreff "(kein Betreff)".

Telefonnummern zweimal: einmal lesbar (`07123 55 66 77`), einmal als
`tel:+49712355 6677`.

## Icons

Inline-SVG statt Icon-Bibliothek - kein externer Request, keine Schriftdatei,
färbbar über `currentColor`.

```ts
// src/components/icons.ts
// Inline-SVG statt Icon-Bibliothek: kein externer Request. Alle Pfade gehen
// von viewBox "0 0 24 24" aus und werden nur gestrichen.
export const iconPfade = {
  kalender: '<rect x="3" y="5" …/><path d="…"/>',
  uhr: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
} as const;

export type IconName = keyof typeof iconPfade;
```

```astro
---
// src/components/Icon.astro
const { name, groesse = 20, klasse } = Astro.props;
---
<svg class={klasse} xmlns="http://www.w3.org/2000/svg"
     width={groesse} height={groesse} viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="1.7"
     stroke-linecap="round" stroke-linejoin="round"
     aria-hidden="true" focusable="false"
     set:html={iconPfade[name]} />
```

`aria-hidden` und `focusable="false"` an jedem Icon - die Bedeutung trägt der
Text daneben oder ein `aria-label` am Elternelement.

**Variante Font Awesome.** Braucht die Seite Icons, die das Framework selbst
in seinem JavaScript benutzt, generiert `tools/icons.mjs` aus dem npm-Paket
eine `_icons.scss`: jedes gefundene `fa-*` als CSS-Maske, eingefärbt über
`currentColor`. Das Skript scannt `src/` **und** die Framework-Datei, also nach
jedem Framework-Update neu laufen lassen. Kein CDN, keine Webfont-Datei.

## Schriften

Immer selbst ausliefern - das ist die Voraussetzung dafür, dass die
Datenschutzerklärung kurz bleibt.

1. Originale (TTF, OFL-lizenziert) nach `assets-original/fonts/` - der Ordner
   bleibt außerhalb des Builds und muss nicht eingecheckt werden
2. `node tools/schriften.mjs` wandelt sie mit `wawoff2` nach woff2 und legt
   sie in `public/fonts/`; nur die woff2 gehen ins Repo
3. `src/styles/_fonts.scss` deklariert jeden Schnitt:

```scss
// Josefin Sans, selbst ausgeliefert (OFL).
@font-face {
  font-family: 'Josefin Sans';
  src: url('/fonts/JosefinSans-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
```

- `font-display: swap` an jedem Schnitt
- Die `url()` bleiben **absolut** (`/fonts/…`). Dateien aus `public/` löst Vite
  nicht auf; ein relativer Pfad funktioniert nur zufällig, solange keine Route
  tiefer als eine Ebene liegt
- Die Schnitte, die above the fold gebraucht werden, in `SITE.preloadFonts` -
  das Layout schreibt daraus die `<link rel="preload">`
- Vier bis fünf Schnitte sind das Maximum; jeder weitere kostet mehr, als er
  bringt
- Die Lizenz im Impressum nennen, wenn sie es verlangt

## Bilder

Alles aus `public/images/`, in zwei Formaten und zwei Größen, mit `<picture>`:

```astro
<picture>
  <source type="image/webp"
          srcset="/images/profil-260.webp 260w, /images/profil-500.webp 500w"
          sizes="250px" />
  <img src="/images/profil-500.jpg"
       srcset="/images/profil-260.jpg 260w, /images/profil-500.jpg 500w"
       sizes="250px" width="500" height="500"
       loading="lazy" decoding="async" alt="…" />
</picture>
```

- **`width` und `height` immer**, auch wenn CSS die Größe bestimmt - sonst
  springt das Layout beim Laden
- **`loading="lazy" decoding="async"`** an allem außer dem Hero-Bild; das
  Hero-Bild lädt eifrig, es ist der erste Eindruck
- **JPEG als Rückfalltür**, WebP zuerst
- `alt` beschreibt, was zu sehen ist; rein dekorative Bilder bekommen `alt=""`
- Fotos vor dem Einchecken auf die tatsächlich gebrauchte Größe rechnen -
  ein 4000px-Foto in einem 250px-Kreis ist der häufigste
  Performance-Fehler auf solchen Seiten
- Grafiken, die aus Daten oder Markenfarben entstehen (OG-Bild, Diagramme,
  Logos für andere Seiten), nicht zeichnen, sondern als SVG im Skript bauen
  und mit `sharp` rendern - dann ändern sie sich mit der Palette mit

## Eigenes SCSS

```
src/styles/
  main.scss       Framework einbinden und konfigurieren, dann die eigenen Teile
  _fonts.scss     @font-face
  _icons.scss     generiert, nicht von Hand anfassen
  _landing.scss   alles Eigene, in der Reihenfolge der Abschnitte
```

`main.scss` bindet das Framework als **erste** Regel ein - darunter stehen nur
noch Token-Überschreibungen auf `:root`, die sonst die Kaskade verlieren.
Konfiguration, Token-Namen und die Frage, welche Teile des Frameworks
überhaupt geladen werden müssen: Skill `mw-maverick-wave`.

In `_landing.scss`:

- Projektpräfix an jeder eigenen Klasse (`sw-`, `fw-`, `hp-`)
- Reihenfolge wie die Abschnitte der Seite, mit einer Kommentarzeile je
  Abschnitt als Trenner
- Nur, was das Framework nicht hat. Nach einem Framework-Update prüfen, ob
  eine eigene Regel überflüssig geworden ist
- Nie eine Klasse im `mw-`-Namensraum erfinden; eine, die es nicht gibt,
  bleibt still ungestylt
- Eigene `@keyframes` mit Projektpräfix - Keyframe-Namen sind global, ein
  unpräfixierter kollidiert mit dem Framework, und der Verlierer verschwindet
  ohne Fehlermeldung
