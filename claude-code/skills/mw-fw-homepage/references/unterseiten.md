# Eigene Seiten statt Abschnitte

Klassennamen sind Platzhalter - Markup-Details im Skill `mw-maverick-wave`.

## Wann eine eigene Seite

Als Abschnitt der Startseite bleibt, was zur Entscheidung gehört: wer das ist,
was es kostet, wie man anfragt. Eine eigene Seite bekommt, was

- **tiefer geht, als die Startseite verträgt** - das volle Paketangebot mit
  Ablauf und Extras, während die Startseite nur einen Teaser zeigt
- **eine eigene Suchabsicht bedient** - jemand sucht "Welpenkurs Ablauf",
  nicht "Hundeschule Musterhausen"
- **wächst** - ein Blog, eine Terminliste, eine Referenzsammlung
- **verlinkt werden soll** - eine URL, die man in eine Mail schreiben kann
- **aus der Suche raus soll** - Impressum, Datenschutz, 404
  (`references/rechtstexte.md`)

Gegenprobe: Braucht der Inhalt eine eigene `description` und einen eigenen
`title`, die sich sinnvoll von der Startseite unterscheiden? Dann ja.

## Eine feste Unterseite

Beispiel: `/angebot` mit dem vollen Paketangebot.

```astro
---
// src/pages/angebot.astro
import BaseLayout from '@/layouts/BaseLayout.astro';
import StructuredData from '@/components/StructuredData.astro';
import texte from '@/content/texte.json';
---

<BaseLayout title={texte.angebot.titel} description={texte.angebot.beschreibung}>
  <Fragment slot="head">
    <StructuredData seite="angebot" />
  </Fragment>

  <Fragment slot="header">
    <Header zurStartseite />
    <Aktion />
  </Fragment>

  <Pakete alsSeite />
  <Ablauf />
  <Kontakt />

  <Footer slot="footer" />
</BaseLayout>
```

Was dabei zu tun ist:

1. **Eigener Titel und eigene Beschreibung** aus `texte.json`, nicht die der
   Startseite wiederverwenden.
2. **Header-Variante.** Entweder `zurStartseite` (ein Knopf statt Navigation)
   oder `unterseite` - siehe unten.
3. **Abschnittskomponenten wiederverwenden** statt zu kopieren. Eine
   Komponente, die auf beiden Seiten vorkommt, bekommt eine Prop wie
   `alsSeite`, die entscheidet, ob ihre Überschrift eine `h1` oder eine `h2`
   ist. Genau eine `h1` pro Seite.
4. **In die Sitemap**, nicht auf `noIndex`.
5. **Strukturierte Daten pro Seite**, im `head`-Slot.

## Navigation auf Unterseiten

Anker der Startseite (`#preise`) funktionieren auf `/blog` nicht. Der Header
bekommt deshalb eine Prop und rechnet die Ziele um:

```ts
const ziel = (eintrag: { ziel: string }) => {
  if (eintrag.ziel.startsWith('#')) {
    return unterseite ? `${pfad('/')}${eintrag.ziel}` : eintrag.ziel;
  }
  return pfad(eintrag.ziel);
};
```

Aus `#preise` wird auf der Unterseite `/#preise`. Ziele, die schon ein Pfad
sind (`/blog`), laufen nur noch durch `pfad()` - wichtig bei gesetztem `base`
(`references/projekt-setup.md`).

## Eine Sammlung: Blog

**Schema definieren** (`src/content.config.ts`):

```ts
import { glob } from 'astro/loaders';
import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    titel: z.string(),
    datum: z.date(),
    beschreibung: z.string(),
    schlagworte: z.array(z.string()),
  }),
});

export const collections = { blog };
```

`glob()` ist die Content-Layer-API von Astro 5+. Die alten Zugriffe
`post.slug` und `post.render()` gibt es nicht mehr - `entry.id` und
`render(entry)` aus `astro:content`.

**Eine Zugriffsstelle** (`src/blog.ts`), damit Liste, Route und Sitemap nicht
je eigene Regeln bauen:

```ts
export const artikelListe = async () =>
  (await getCollection('blog')).sort(
    (a, b) => b.data.datum.getTime() - a.data.datum.getTime()
  );
export type Artikel = Awaited<ReturnType<typeof artikelListe>>[number];
```

Dort gehören auch Lesezeit (`Wörter / 190`, mindestens 1) und die
Datumsformate hin.

**Zwei Routen:**

```
src/pages/blog/index.astro     Liste
src/pages/blog/[slug].astro    Artikel
```

Die Artikelroute erzeugt ihre Pfade und reicht gleich die Nachbarn mit:

```ts
export async function getStaticPaths() {
  const artikel = await artikelListe();
  return artikel.map((eintrag, i) => ({
    params: { slug: eintrag.id },
    // Die Liste ist neu nach alt sortiert: der Nachbar davor ist der neuere.
    props: { artikel: eintrag, neuerer: artikel[i - 1] ?? null,
             aelterer: artikel[i + 1] ?? null },
  }));
}
```

Im Artikel dann `const { Content } = await render(artikel)` und
`<Content />` in einem Markdown-Container.

- `ogType="article"` setzen
- `<time datetime={iso}>` für das Datum
- Fußzeile mit vorheriger / Übersicht / nächster; fehlt ein Nachbar, ein
  leeres `<span />` als Platzhalter, damit die Dreiteilung stehen bleibt
- Ein Teaser auf der Startseite zieht dieselbe `artikelListe()` und
  schneidet nach zwei oder drei Einträgen ab

## Breadcrumbs

Ab der zweiten Ebene (`/blog/<artikel>`) und auf Listenseiten, die nicht
direkt unter der Wurzel hängen. Erstes Element ist ein Haus-Icon mit
`aria-label`, letztes ist die aktuelle Seite und als solche markiert.

```astro
<nav class="mw-breadcrumbs" aria-label="Sie sind hier">
  <ol class="mw-breadcrumbs-list">
    <li class="mw-breadcrumbs-item">
      <a href={pfad('/')} aria-label="Startseite"><Icon name="haus" /></a>
    </li>
    <li class="mw-breadcrumbs-item"><a href={pfad('/blog')}><span>Blog</span></a></li>
    <li class="mw-breadcrumbs-item mw-breadcrumbs-current">
      <a href="#" class="mw-breadcrumbs-active"><span>{titel}</span></a>
    </li>
  </ol>
</nav>
```

Rechtstexte und 404 bekommen keine - dort steht der Knopf "Zur Startseite" im
Header.

## Design einer Unterseite

- **Kein zweiter Hero.** Der Hero gehört der Startseite. Eine Unterseite
  beginnt mit Abstand nach oben, Breadcrumb (falls tief genug) und dem
  Abschnittskopf mit der `h1`.
- **Dasselbe Chrome.** Gleicher Header, gleicher Footer, gleiche Container-
  breite. Eine Unterseite, die anders aussieht, wirkt wie eine andere Website.
- **Ein Rückweg, der nicht der Zurück-Knopf ist** - Breadcrumb, Knopf im
  Header oder ein Link am Ende des Inhalts.
- **Sektionsrhythmus beibehalten**, auch wenn die Seite nur einen Abschnitt
  hat.
- **Nicht länger als nötig.** Wenn eine Unterseite nach dem Schreiben kürzer
  ist als der Abschnitt, aus dem sie kam, gehört sie zurück auf die
  Startseite.

## Sonderfall: Route, die kein HTML liefert

Eine `.ts`-Datei unter `src/pages/` kann jeden Inhaltstyp ausliefern - nützlich
für ein Stylesheet, das aus Daten berechnet wird und zu groß für `<style>` ist:

```ts
// src/pages/ablauf.css.ts  ->  /ablauf.css
import type { APIRoute } from 'astro';
export const GET: APIRoute = () =>
  new Response(ablaufCss, { headers: { 'Content-Type': 'text/css; charset=utf-8' } });
```

Die Seite verlinkt es im `head`-Slot. Ein CSP-tauglicher Ersatz für ein
`<style is:inline>`.

## Checkliste neue Unterseite

- [ ] Eigener `title` und eigene `description` in `texte.json`
- [ ] Genau eine `h1`
- [ ] Header-Variante gesetzt, Anker zeigen auf `/#…`
- [ ] Breadcrumb ab Ebene zwei
- [ ] In der Sitemap (Filter in `astro.config.mjs` erweitern)
- [ ] Strukturierte Daten im `head`-Slot
- [ ] Bei gesetztem `base`: jeder eigene `href` durch `pfad()`
- [ ] Rückweg vorhanden
