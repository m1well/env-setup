# Projektgerüst

## package.json

```jsonc
{
  "name": "<projekt>-homepage",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --check .",
    "format:fix": "prettier --write .",
    "checkup": "npm run lint:fix && npm run format:fix"
  },
  "dependencies": {
    "@astrojs/sitemap": "^3",
    "astro": "^7",
    "maverick-wave": "^5"
  }
}
```

`checkup` läuft vor jedem Commit. Entwicklungsabhängigkeiten: `eslint`,
`typescript-eslint`, `eslint-plugin-astro`, `eslint-plugin-simple-import-sort`,
`prettier`, `prettier-plugin-astro`, `sass`, und `@fortawesome/fontawesome-free`
nur dann, wenn `tools/icons.mjs` daraus das Icon-SCSS generiert
(`references/inhalte.md`).

Zusatzskripte je nach Projekt: `og` (OG-Bild rendern), `icons`, `favicons`,
`schriften`.

## astro.config.mjs

```js
// @ts-check
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';
import path from 'path';

export default defineConfig({
  site: 'https://<domain>',
  output: 'static',
  // Inline-CSS wuerde die CSP verwerfen - sie kennt kein 'unsafe-inline'.
  build: { inlineStylesheets: 'never' },
  integrations: [sitemap({ filter: page => page === 'https://<domain>/' })],
  server: { port: 4321 },
  vite: {
    // Gleicher Grund: ein inlinter Bundle faellt aus der CSP.
    build: { assetsInlineLimit: 0 },
    resolve: { alias: { '@': path.resolve('./src') } },
  },
});
```

Die beiden `inline`-Zeilen sind kein Stilwunsch: der nginx liefert eine CSP
ohne `unsafe-inline` aus. Fällt eine davon weg, lädt die Seite nackt, und zwar
nur in Produktion, nicht in `astro dev`.

Der `sitemap`-Filter ist bei einer einseitigen Seite eine Positivliste, sobald
es Unterseiten gibt eine Negativliste - `references/seo-checkliste.md`.
Beispielseiten bekommen die Integration gar nicht.

## Pfadalias

`@/` zeigt auf `src/`, konfiguriert an **zwei** Stellen, die zusammen geändert
werden müssen:

- `vite.resolve.alias` in `astro.config.mjs` (für den Build)
- `compilerOptions.paths` in `tsconfig.json` (für Editor und Typprüfung)

## base - nur für Beispielseiten

Erfundene Kunden liegen unter `beispiel.formatwerke.de/<name>/` und brauchen:

```js
site: 'https://beispiel.formatwerke.de',
base: '/hundeschule-pfotenwerk/',
```

Astro setzt `base` **nur** vor Links, die es selbst erzeugt. Alles aus
`public/` und jeder handgeschriebene `href` braucht `src/pfad.ts`:

```ts
const basis = import.meta.env.BASE_URL.replace(/\/$/, '');
export const pfad = (ziel: string) => `${basis}/${ziel.replace(/^\//, '')}`;
```

Betrifft: `<img src>` auf Dateien aus `public/`, Font-Preloads, Favicon-Pfade,
jeden `href` in Navigation, Breadcrumb und Footer. Beim Umzug auf eine eigene
Domain fällt `base` weg, `pfad()` bleibt funktionsfähig und kann später raus.

Beispielseiten tragen außerdem `noindex, nofollow` fest im `BaseLayout` (nicht
nur per Prop) und ein Hinweisband über dem Inhalt.

## tsconfig.json

`astro/tsconfigs/strict` erweitern, `@/*` auf `src/*` mappen. Mehr nicht.

## ESLint

Flat Config. `js.configs.recommended`, `tseslint.configs.recommended`,
`eslintPluginAstro.configs.recommended`, dazu `simple-import-sort` als **error**
für `imports` und `exports` in `.ts` und `.astro`. `dist/`, `.astro/`,
`node_modules/` ignorieren. Für `*.config.{js,mjs}` und `tools/**` die
Node-Globals freischalten.

## Prettier

80 Spalten, einfache Anführungszeichen, Semikolons, `arrowParens: 'avoid'`,
`trailingComma: 'es5'`, `prettier-plugin-astro`. Markdown mit
`proseWrap: 'always'` und doppelten Anführungszeichen - Blogartikel hart auf 80
umbrechen.

## Deploy

**Selbst gehostet (Regelfall).** `release.sh` im Projekt baut und synchronisiert
nach `~/Dev/mindhub/production/homepages/<projekt>/content`:

```bash
npm run build
[ -f dist/index.html ] || exit 1          # nie ein leeres dist ausrollen
rsync -a --delete dist/ "${TARGET_DIR}/"
```

Die Prüfung auf `dist/index.html` und die Prüfung, dass `TARGET_DIR` wirklich
auf `.../*/content` endet, sind die beiden Sicherungen gegen ein `--delete` ins
Falsche. Beide gehören in jedes `release.sh`.

**GitHub Pages (Ausnahme, z. B. m1well).** `.github/workflows/main.yml` mit
`withastro/action@v4` plus `actions/deploy-pages@v4`, `CNAME` im Projekt, und
`echo '' > dist/.nojekyll` im Build-Skript, damit Jekyll die
Unterstrich-Assets nicht schluckt.

## Seitenzähler

Same-origin-Beacon, kein Cookie, keine Kennung, kein Drittanbieter:

```js
const isLocal = ['localhost', '127.0.0.1'].includes(location.hostname);
if (!isLocal && navigator.sendBeacon) {
  const page = location.pathname.replace(/^\/+|\/+$/g, '') || 'home';
  navigator.sendBeacon(`/_c/${page}`);
}
```

Der nginx reicht `/_c/` intern weiter und schneidet die IP. Auf GitHub Pages
gibt es keinen eigenen vhost - dort geht derselbe Beacon cross-origin an einen
eigenen Zähler-Host, und **das muss die Datenschutzerklärung abbilden**.
