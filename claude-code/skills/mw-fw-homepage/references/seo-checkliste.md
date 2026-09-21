# SEO, Metadaten, Vorschaubild

Abhaken, bevor eine Seite live geht.

## Kopf jeder Seite

Reihenfolge wie hier - `charset` und `viewport` zuerst, sonst interpretiert der
Browser den Anfang zweimal.

```astro
<meta charset="UTF-8" />
<meta name="viewport"
      content="width=device-width, minimum-scale=1, initial-scale=1, viewport-fit=cover" />
<title>{title}</title>
<meta name="description" content={description} />
<link rel="canonical" href={canonicalUrl} />
{noIndex && <meta name="robots" content="noindex, nofollow" />}
<meta name="format-detection" content="telephone=no,email=no,address=no,date=no" />
```

- [ ] **`viewport-fit=cover`** - ohne das rutscht der Inhalt auf einem Handy
      mit Aussparung unter die runde Ecke. Das Framework budgetiert dafür.
- [ ] **`title` pro Seite eigen**, Muster `<Marke> - <Seite>`, 50-60 Zeichen.
- [ ] **`description` pro Seite eigen**, 140-160 Zeichen, ein vollständiger
      Satz, kein Schlagwortsalat.
- [ ] **`canonical` aus `Astro.url.pathname` und `Astro.site`** - nicht von
      Hand, sonst driftet er.
- [ ] **`format-detection`** verhindert, dass iOS Telefonnummern und Daten im
      Fließtext eigenmächtig verlinkt und das Layout bricht.

## Open Graph und Twitter

```astro
<meta property="og:title" content={title} />
<meta property="og:type" content={ogType} />          {/* website | article */}
<meta property="og:site_name" content={SITE.name} />
<meta property="og:description" content={description} />
<meta property="og:url" content={canonicalUrl} />
<meta property="og:locale" content={SITE.locale} />    {/* de_DE */}
<meta property="og:image" content={previewImage} />
<meta property="og:image:alt" content={previewImageAlt} />
{hatBekannteMasse && (
  <Fragment>
    <meta property="og:image:type" content={OG_IMAGE.type} />
    <meta property="og:image:width" content={OG_IMAGE.width} />
    <meta property="og:image:height" content={OG_IMAGE.height} />
  </Fragment>
)}
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content={title} />
<meta name="twitter:description" content={description} />
<meta name="twitter:image" content={previewImage} />
<meta name="twitter:image:alt" content={previewImageAlt} />
```

- [ ] **`og:image` ist eine absolute URL** (`new URL(pfad, Astro.site)`).
      Relative Pfade zeigt kein Messenger an.
- [ ] **`width`/`height` nur beim Standardbild.** Gibt eine Seite ein eigenes
      Bild mit (ein Artikelbild), sind die Maße unbekannt - dann die drei Tags
      weglassen, statt zu raten.
- [ ] **`og:image:alt`** ist beim Standardbild der Marketingsatz, bei einem
      seitenspezifischen Bild der Seitentitel.
- [ ] Eine separate `ogDescription`-Prop lohnt, wenn die `description` für die
      Suche geschrieben ist: Chat-Vorschauen schneiden nach rund 80 Zeichen.

## Das OG-Bild selbst

1200 × 630, liegt in `public/images/og-image.(png|jpg)`, wird aus einem SVG
gerendert statt fotografiert:

```
tools/og-image.mjs   →  node tools/og-image.mjs   →  public/images/og-image.png
```

Das Skript baut das SVG aus den Markenfarben zusammen und schickt es durch
`sharp`. Vorteil: bei einer Farbänderung wird es neu gerendert, nicht neu
gebaut. Inhalt des Bildes: Marke groß, ein Satz, ein grafisches Element aus
der Seite - kein Text unter 28px, der ist in der Vorschau unlesbar.

- [ ] Bild existiert und ist im Repo (nicht nur lokal generiert)
- [ ] Maße exakt 1200 × 630
- [ ] `OG_IMAGE` in `src/config/site.ts` stimmt mit Datei, Typ und Maßen überein

## Favicons

Zwei Ausbaustufen. Eine **Beispielseite** kommt mit einer einzigen
`public/favicon.svg` aus:

```astro
<link rel="icon" href={pfad('/favicon.svg')} type="image/svg+xml" />
```

Eine **Seite, die live geht**, bekommt den vollen Satz. `public/favicon.ico`
muss dabei **an der Wurzel** liegen - Browser fragen den Pfad ungefragt ab.
Alles andere in `public/favicon/`, gerendert von `Favicons.astro`:

```astro
<link rel="icon" type="image/x-icon" href="/favicon.ico" sizes="32x32" />
<link rel="icon" type="image/png" sizes="96x96" href="/favicon/favicon-96x96.png" />
{SITE.hasSvgFavicon && <link rel="icon" type="image/svg+xml" href="/favicon/favicon.svg" />}
<link rel="apple-touch-icon" sizes="180x180" href="/favicon/apple-touch-icon.png" />
<link rel="manifest" href="/favicon/site.webmanifest" />
<meta name="theme-color" content={SITE.themeColor} />
```

`site.webmanifest`: `name`, `short_name`, `lang`, `start_url`, `scope`,
`display: standalone`, `background_color`, `theme_color`, dazu 192er und 512er
PNG. Das 512er dient gleichzeitig als `logo` in den strukturierten Daten.

- [ ] `favicon.ico` an der Wurzel
- [ ] `theme_color` im Manifest = `SITE.themeColor` = `<meta name="theme-color">`
- [ ] Bei gesetztem `base`: alle Pfade durch `pfad()`

## robots.txt und Sitemap

```
User-agent: *
Allow: /

Sitemap: https://<domain>/sitemap-index.xml
```

`@astrojs/sitemap` erzeugt `sitemap-index.xml` aus dem `site`-Wert. Der Filter
in `astro.config.mjs` hängt davon ab, wie viele Seiten ranken sollen:

```js
// Einseitige Seite: Positivliste
sitemap({ filter: page => page === 'https://<domain>/' })

// Mit echten Unterseiten: Negativliste
sitemap({
  // Impressum und Datenschutz sind noIndex.
  filter: page => !page.includes('/impressum') && !page.includes('/datenschutz'),
})
```

Beide Formen sind in Gebrauch - die Negativliste, sobald es mehr als die
Startseite gibt, weil sie eine neue Unterseite automatisch mitnimmt.

- [ ] Impressum, Datenschutz und 404 stehen **nicht** in der Sitemap
- [ ] Jede echte Unterseite (Angebot, Blog, Artikel) steht drin
- [ ] Beispielseiten bekommen weder `robots.txt` noch Sitemap - sie sind
      ohnehin komplett `noindex`

## noindex - wo überall

| Seite                   | `noIndex` | in der Sitemap |
| ----------------------- | --------- | -------------- |
| Startseite              | nein      | ja             |
| Angebot, Blog, Artikel  | nein      | ja             |
| Impressum               | **ja**    | nein           |
| Datenschutz             | **ja**    | nein           |
| 404                     | **ja**    | nein           |
| ganze Beispielseite     | **ja**    | keine Sitemap  |

Impressum und Datenschutz auf `noindex` ist Absicht: sie sollen erreichbar
sein, aber nicht ranken und keine Anfragen aus der Suche einsammeln.

## Strukturierte Daten (JSON-LD)

Eine Komponente, die aus **denselben JSON-Dateien** liest wie die sichtbare
Seite - Google prüft, ob beides zusammenpasst. Als ein `@graph` mit
untereinander verlinkten `@id`:

```js
const url = pfad => new URL(pfad, Astro.site).href;
const unternehmenId = url('/#unternehmen');
const personId      = url('/#person');

const daten = {
  '@context': 'https://schema.org',
  '@graph': [website, unternehmen, person, ...termine, fragen],
};
```

Bausteine nach Bedarf:

| Typ                                       | Wann                                                 |
| ----------------------------------------- | ------------------------------------------------------ |
| `WebSite`                                 | immer                                                  |
| `LocalBusiness` (oder `Restaurant`, …)    | immer bei einem Betrieb mit Ort                        |
| `Person`                                  | wenn eine Person die Marke trägt, `worksFor` verlinkt  |
| `Event`                                   | pro Termin - `references/zeitgesteuert.md`             |
| `FAQPage`                                 | wenn es einen echten Fragenabschnitt gibt              |
| `BlogPosting`                             | pro Artikel                                            |

Regeln:

- [ ] **Keine Straße** im `LocalBusiness` - die steht im Impressum.
      Postleitzahl, Ort, Region, Land reichen.
- [ ] **Keine `aggregateRating`** aus eigenen Kundenstimmen. Sterne für selbst
      gesammelte Zitate wertet Google als Verstoß.
- [ ] `priceRange` aus den echten Preisen rechnen, nicht schätzen.
- [ ] `areaServed` mit den Orten, die auch im Text stehen.
- [ ] Die Komponente hängt im `head`-Slot der Seite, die sie beschreibt -
      nicht global im Layout.

## Zugänglichkeit, die die Suche mitnimmt

- [ ] Genau eine `<h1>` pro Seite, keine Ebene übersprungen
- [ ] `<main>` mit `id`, davor der Skip-Link
- [ ] `alt` an jedem inhaltstragenden Bild, `alt=""` an Dekoration
- [ ] `aria-label` an Icon-Links (soziale Netze, Breadcrumb-Haus)
- [ ] Externe Links: `target="_blank" rel="noopener noreferrer"`
- [ ] `lang` am `<html>` aus `SITE.lang`

## Vor dem Livegang messen

```bash
npm run build
npx serve dist            # oder npm run preview
```

- [ ] Vorschau in einem Messenger prüfen (OG-Bild, Titel, Beschreibung)
- [ ] Rich-Results-Test für das JSON-LD
- [ ] Lighthouse: Performance, Barrierefreiheit, SEO je ≥ 95 - eine statische
      Seite ohne Drittanbieter hat keine Ausrede
- [ ] Alle Seiten bei 320px Breite ohne waagerechten Überlauf
