# Aktionen und Termine, die von selbst ablaufen

Das Problem: die Seite ist statisch gebaut. Ein Rabatt bis zum 6. September
steht am 7. noch da, ein Workshop vom Samstag am Sonntag auch - bis jemand neu
deployt. Und niemand deployt sonntags.

Die Lösung ist überall dieselbe und hat zwei Hälften.

## Das Prinzip

**Der Build entscheidet, was ins HTML kommt.** Abgelaufenes fliegt schon dort
raus - wer ohne JavaScript kommt, sieht keinen Rabatt vom letzten Jahr.

**Der Browser entscheidet, was davon sichtbar bleibt.** Jedes zeitabhängige
Element trägt seinen Ablaufzeitpunkt als `data`-Attribut. Ein Skript vergleicht
ihn mit `new Date()` und räumt auf.

Die Richtung ist die Regel aus `SKILL.md`, Punkt 4: **das Skript darf nur nach
unten korrigieren.** Ein Termin, der schon vorbei ist, verschwindet. Ein
Termin, der noch nicht im HTML steht, erscheint nicht. Ohne JavaScript bleibt
der Stand des Builds stehen - nie ein falscher Preis, höchstens ein alter
Termin.

Beim Rabatt ist die Richtung genau umgekehrt gewählt, und zwar bewusst: der
Rabatt steht im HTML, ist aber per CSS versteckt, bis das Skript ihn
freischaltet. Ohne JavaScript gilt der **reguläre** Preis. Lieber kein Rabatt
als ein abgelaufener.

## Die 12-Stunden-Regel

Ein Termin gilt bis zum Ende seines Tages. Verschwindet er um 00:00:01, ist er
nachts weg, während jemand noch auf der Seite ist - und wer am Sonntagmorgen
nach dem Samstagstermin sucht, findet keinen Hinweis mehr, dass es ihn gab.

Deshalb: **Tagesende plus 12 Stunden.** Das Datum im Text bleibt der letzte
Tag, sichtbar ist der Eintrag bis zum Mittag danach.

```ts
const tagesende = (datum: string) => {
  const tag = new Date(`${datum}T23:59:59`);
  return Number.isNaN(tag.getTime()) ? null : tag;
};

const NACHLAUF_STUNDEN = 12;

const sichtbarBis = (datum: string) => {
  const tag = tagesende(datum);
  if (!tag) return null;
  tag.setHours(tag.getHours() + NACHLAUF_STUNDEN);
  return tag;
};
```

`new Date('2026-09-06T23:59:59')` ohne `Z` ist Ortszeit - genau das ist
gewollt, der Betrieb denkt in seiner Zeitzone. Ein ungültiges Datum gibt
`null`, und `null` heißt überall "läuft nicht ab" statt "sofort weg": lieber
ein Eintrag zu viel als ein verschluckter.

## Ablage

```
src/pflegbar/
  typen.ts     Was in den JSON-Dateien stehen darf, mit Doc-Kommentar je Feld
  lesen.ts     Die JSON-Dateien einlesen und typisieren
  regeln.ts    Alle Zeit- und Formatregeln
src/content/
  aktion.json
  workshops.json
```

`pflegbar` ("was der Kunde selbst pflegt") trennt die Dateien, die jemand ohne
Codekenntnis anfasst, vom Rest. Die Doc-Kommentare in `typen.ts` sind die
Anleitung dafür:

```ts
export interface Workshop {
  titel: string;
  /**
   * JJJJ-MM-TT. Sortiert und laesst den Eintrag verschwinden - zwoelf Stunden
   * nach dem genannten Tag, dafuer braucht es kein Deployment.
   */
  datum: string;
  uhrzeit?: string;
  ort?: string;
  /** Nur die Zahl, Euro versteht sich. 0 wird als "kostenlos" gezeigt. */
  preis?: string | number;
  text?: string;
  ausgebucht?: boolean;
}

export interface Aktion {
  /** 0 heisst: kein Banner. Sonst die Prozentzahl, die im Banner steht. */
  prozent: number;
  /** Letzter Tag als JJJJ-MM-TT, einschliesslich. Leer heisst: unbefristet. */
  bis?: string;
  /** Ohne das Enddatum - das haengt die Seite selbst an. */
  text: string;
}
```

Bei kleineren Seiten reicht eine einzelne `src/aktion.ts` mit Typ, Daten und
Regeln zusammen.

---

# Rabattband

## 1. Regeln

```ts
export const aktionLaeuft = (aktion: Aktion, heute = new Date()) => {
  const prozent = Number(aktion?.prozent);
  if (!Number.isFinite(prozent) || prozent <= 0) return false;
  if (aktion.bis) {
    const ende = sichtbarBis(aktion.bis);
    if (!ende || heute > ende) return false;
  }
  return true;
};

// Fuer data-aktion-bis am <html>: leer heisst unbefristet,
// null heisst keine Aktion - dann steht auch nichts im HTML.
export const aktionEnde = (aktion: Aktion, heute = new Date()) => {
  if (!aktionLaeuft(aktion, heute)) return null;
  const ende = aktion.bis ? sichtbarBis(aktion.bis) : null;
  return ende ? ende.toISOString() : '';
};

// Schmales Leerzeichen zwischen Zahl und Prozentzeichen.
export const rabattText = (aktion: Aktion) => `-${Number(aktion.prozent)} %`;

// Immer abgerundet: aufgerundet bekaeme die Kundin weniger als versprochen.
export const rabattPreis = (aktion: Aktion, betrag: number) =>
  Math.floor(betrag * (1 - Number(aktion.prozent) / 100));

// Das Enddatum haengt die Seite an, nicht die Inhaltsdatei - so steht es im
// Band immer im gleichen Format und kann nie vom "bis" abweichen.
export const aktionText = (aktion: Aktion) => {
  const ende = aktion.bis ? tagesende(aktion.bis) : null;
  if (!ende) return aktion.text;
  const datum = ende.toLocaleDateString('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  });
  return `${aktion.text} bis ${datum}`;
};
```

`prozent: 0` ist der Ausschalter - kein Datum ändern, keine Datei löschen.

## 2. Das Attribut am `<html>`

Im `BaseLayout`:

```astro
const aktionsEnde = aktionEnde(aktion);
---
<html lang={SITE.lang} data-aktion-bis={aktionsEnde}>
```

Drei Zustände, die das Skript unterscheiden muss:

| `aktionEnde()` | Attribut im HTML       | Bedeutung              |
| -------------- | ---------------------- | ---------------------- |
| `null`         | fehlt ganz             | keine Aktion           |
| `''`           | `data-aktion-bis=""`   | unbefristet            |
| ISO-String     | `data-aktion-bis="…"`  | läuft zu dem Zeitpunkt ab |

Astro lässt ein Attribut mit `null` oder `undefined` weg - deshalb `null` für
"keine Aktion".

## 3. Das Band

```astro
{
  aktionLaeuft(aktion) && (
    <aside class="mw-announcement mw-announcement-secondary <praefix>-nur-aktion">
      <a class="mw-announcement-content" href="#preise">
        <span class="mw-announcement-highlight">{rabattText(aktion)}</span>
        <span>{aktionText(aktion)}</span>
      </a>
    </aside>
  )
}
```

Es hängt im `header`-Slot **unter** dem Header, nicht im Fluss - welche
Komponente das ist und was sie für den Scroll-Versatz braucht, steht im Skill
`mw-maverick-wave`. Verlinkt auf den Abschnitt, in dem der Rabatt etwas nützt.

## 4. Zwei Klassen, eine Richtung

```scss
// Der Rabatt steht im HTML und wird erst sichtbar, wenn das Skript die Klasse
// gesetzt hat. Hier wird nur ausgeblendet, nie eingeblendet - sonst muesste
// jede Regel das display des Frameworks nachbauen.
html:not(.<praefix>-aktion-laeuft) .<praefix>-nur-aktion { display: none; }
html.<praefix>-aktion-laeuft      .<praefix>-ohne-aktion { display: none; }
```

`-nur-aktion` trägt alles, was nur mit Rabatt sichtbar ist (Band, Aktionspreis,
Prozent-Chip), `-ohne-aktion` den regulären Preis. Nie `display` selbst
setzen - nur wegnehmen.

## 5. Das Skript

```js
// Rabatt: im HTML steht er schon, sichtbar wird er erst hier. So faellt er
// am Enddatum von selbst weg, ohne neuen Build. Ohne dieses Script bleibt es
// beim regulaeren Preis - nie andersherum.
const aktionsEnde = document.documentElement.dataset.aktionBis;
if (
  aktionsEnde !== undefined &&
  (aktionsEnde === '' || new Date(aktionsEnde) >= new Date())
) {
  document.documentElement.classList.add('<praefix>-aktion-laeuft');
}
```

## 6. Preise mit und ohne Rabatt

Beide Beträge stehen im HTML, das CSS entscheidet:

```astro
{mitRabatt && (
  <span class="mw-price-original <praefix>-nur-aktion">
    <span class="mw-sr-only">Regulärer Preis:</span>{zahl} Euro
  </span>
)}
{mitRabatt && <span class="mw-sr-only <praefix>-nur-aktion">Jetzt:</span>}
<span class:list={['mw-price-amount', mitRabatt && '<praefix>-ohne-aktion']}>{zahl}</span>
{mitRabatt && (
  <span class="mw-price-amount <praefix>-nur-aktion">{rabattPreis(aktion, zahl)}</span>
)}
```

Die Klassen sind hier nur Platzhalter für "Preiskomponente des Frameworks" -
wie die Teile wirklich heißen, steht im Skill `mw-maverick-wave`. Worauf es
ankommt: **beide Zahlen im HTML**, die Sichtbarkeit über die zwei
Aktions-Klassen, und je ein nur für Screenreader sichtbarer Einschub davor -
zwei Zahlen nebeneinander werden sonst ohne Erklärung vorgelesen.

Eine Preiskomponente kapselt das einmal und bekommt `betrag` und `rabatt` als
Props. Nicht jeder Preis ist rabattiert - Workshops sind es bei stimmwohl
ausdrücklich nicht.

Sonderfälle, die die Komponente schon kennen muss:
`0` wird zu "kostenlos" ohne Währung, ein leerer String bleibt leer, ein
Freitext ("Auf Anfrage") wird als Wort gesetzt statt als Betrag. Prüfung auf
`!== undefined && !== ''`, nicht auf truthy - sonst fällt die `0` raus.

## 7. Bedingtes Band (formatwerke-Variante)

Wenn das Band nur in Aktionszeiten existiert, reserviert der Scroll-Versatz
des Frameworks trotzdem Platz dafür, solange die Markup-Bedingung greift.
Dann den Versatz-Anteil im Nicht-Aktions-Fall nullen statt den ganzen
`scroll-padding-top` zu überschreiben - welches Token das ist, steht im Skill
`mw-maverick-wave`.

---

# Termine

## 1. Regeln

```ts
export const kuenftigeTermine = (eintraege: readonly Workshop[], heute = new Date()) =>
  eintraege
    .filter(e => { const ende = sichtbarBis(e.datum); return !ende || heute <= ende; })
    .sort((a, b) => a.datum.localeCompare(b.datum));

// Wert fuers data-Attribut an der Karte.
// Leer heisst freier Text statt Datum - der laeuft nie ab.
export const terminEnde = (e: Workshop) => {
  const ende = sichtbarBis(e.datum);
  return ende ? ende.toISOString() : '';
};

// Freier Text statt Datum bleibt unveraendert stehen - lieber ein ungewohntes
// Format als ein verschluckter Termin.
export const datumText = (e: Workshop) => {
  const tag = tagesende(e.datum);
  if (!tag) return e.datum;
  return tag.toLocaleDateString('de-DE', {
    weekday: 'short', day: 'numeric', month: 'long', year: 'numeric',
  });
};
```

Sortiert wird über `localeCompare` auf dem ISO-String - bei `JJJJ-MM-TT` ist
das die Datumsreihenfolge, ohne `Date`-Objekte zu bauen.

## 2. Markup

```astro
{termine.length > 0 ? (
  <>
    <div data-workshop-termine>
      <div class="mw-grid-2-lg">
        {termine.map(e => <WorkshopKarte eintrag={e} />)}
      </div>
      <p>{workshops.mindestzahl}</p>
    </div>
    {/* Faellt im Browser der letzte Termin weg, tritt dieser Block an die
        Stelle der Liste - siehe Scripts.astro. */}
    <template data-workshop-leer>
      <WorkshopsLeer />
    </template>
  </>
) : (
  <WorkshopsLeer />
)}
```

Jede Karte trägt `data-termin-bis={terminEnde(eintrag)}`.

Das `<template>` ist der Kniff: den Leerzustand kennt nur der Build, aber
gebraucht wird er unter Umständen erst im Browser. Als `<template>` ist er im
HTML vorhanden, ohne gerendert zu werden.

## 3. Das Skript

```js
// Workshops: abgelaufene Termine stehen noch im HTML und fallen erst hier
// raus. So verschwindet ein Termin zwoelf Stunden nach seinem Tag, ohne
// neuen Build. Ohne dieses Script bleibt er stehen - nie umgekehrt.
const termine = document.querySelector('[data-workshop-termine]');
if (termine) {
  const jetzt = new Date();
  termine.querySelectorAll('[data-termin-bis]').forEach(karte => {
    const bis = karte.dataset.terminBis;
    if (bis && new Date(bis) < jetzt) karte.remove();
  });

  const leer = document.querySelector('template[data-workshop-leer]');
  if (leer && !termine.querySelector('[data-termin-bis]')) {
    termine.replaceWith(leer.content.cloneNode(true));
  }
}
```

`bis && …` lässt leere Werte stehen - der Freitext-Termin bleibt.

## 4. Leerzustand

Kein "Keine Termine" als kahle Zeile, sondern ein Leerzustand mit Icon, einem
Satz ("Der nächste Termin steht noch nicht fest") und einem Knopf, der zur
Anfrage führt. Er ist der häufigste Zustand der Sektion und verdient dieselbe
Sorgfalt wie die volle Liste.

## 5. Strukturierte Daten für Termine

Jeder künftige Termin wird ein `Event` im `@graph`
(`references/seo-checkliste.md`). Zwei Feinheiten:

**Zeitzone.** Google will einen Versatz sehen, sonst rät es:

```ts
const versatz = (datum: string) => {
  const zone = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Europe/Berlin', timeZoneName: 'longOffset',
  }).formatToParts(new Date(`${datum}T12:00:00Z`))
    .find(t => t.type === 'timeZoneName')?.value;
  return zone && zone !== 'GMT' ? zone.replace('GMT', '') : '+00:00';
};
```

Über `Intl` und nicht fest `+02:00`, sonst stimmt es im Winter nicht.

**Uhrzeit aus Freitext.** Das Feld ist Freitext ("10:00 - 13:00 Uhr"); genommen
werden die ersten beiden `HH:MM` darin, das erste als `startDate`, das zweite
als `endDate`.

Dazu: `eventAttendanceMode` aus dem Ort (enthält er "online" oder fehlt er,
ist es online), `offers` mit `price` und `availability`
(`SoldOut` bei ausgebucht), `isAccessibleForFree` bei Preis `0`.

Die Termine kommen aus **derselben** `kuenftigeTermine()`-Funktion wie die
sichtbare Liste. Ein Termin, der auf der Seite weg ist, darf nicht im JSON-LD
stehen.

---

# Andere zeitabhängige Inhalte

Dasselbe Muster, andere Daten:

| Fall                        | Build rendert                    | Browser korrigiert                              |
| --------------------------- | -------------------------------- | ------------------------------------------------- |
| Wochenkarte / Mittagstisch  | Die Woche des Build-Tages        | Datumsstempel und "heute"-Markierung wandern mit  |
| Öffnungsstatus              | nichts (versteckt)               | "Jetzt geöffnet" / "öffnet morgen um …"           |
| Alter, Betriebsjahre        | Wert zur Build-Zeit als Fallback | Neu gerechnet aus einem `data`-Attribut           |
| "seit X Monaten"            | dito                             | dito                                              |

Regel für alle: **der Build liefert einen sinnvollen Fallback**, das Skript
ersetzt ihn. Kein leeres Element, das erst JavaScript füllt.

Beim Rechnen mit Datumsangaben aus Strings: selbst zerlegen statt
`new Date('2026-09-06')` - letzteres parst als UTC-Mitternacht und verschiebt
den Tag für alle westlich von UTC.

## Checkliste

- [ ] Ablaufzeitpunkt als `data`-Attribut, nicht im Skript hartkodiert
- [ ] Nachlauf 12 Stunden, an einer Stelle als Konstante
- [ ] Ungültiges Datum → läuft nie ab (nicht: sofort weg)
- [ ] Ohne JavaScript ist der Stand richtig, nur eventuell alt
- [ ] Rabatt: ohne JavaScript gilt der reguläre Preis
- [ ] Leerzustand vorhanden und im `<template>`, wenn die Liste leer laufen kann
- [ ] Strukturierte Daten lesen dieselbe Filterfunktion wie die Anzeige
- [ ] `prozent: 0` schaltet die Aktion ab, ohne dass etwas gelöscht wird
