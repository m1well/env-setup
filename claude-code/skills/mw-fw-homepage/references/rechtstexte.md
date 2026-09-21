# Impressum und Datenschutz

Kein Rechtsrat - das Gerüst, das auf diesen Seiten steht, und die Stellen, an
denen es pro Betrieb auseinandergeht. Den fertigen Text prüft der Kunde oder
sein Anwalt.

## Warum eigene Seiten

- **Auffindbar.** Ein Impressum muss "leicht erkennbar, unmittelbar erreichbar
  und ständig verfügbar" sein. Ein Modal oder ein Akkordeon auf der Startseite
  ist keins von dreien.
- **Verlinkbar.** Abmahnungen und Plattformen wollen eine URL, kein
  Sprungziel.
- **Bots.** Ein eigener Pfad bleibt aus der Sitemap und bekommt `noindex` -
  das geht nur, wenn es eine eigene Seite ist. Als Abschnitt der Startseite
  hängt der Rechtstext an deren Ranking und verwässert ihre Beschreibung.
- **Stabil.** Die Startseite wird umgebaut, der Rechtstext nicht.

Beide Seiten deshalb immer:

```
src/pages/impressum.astro      →  /impressum
src/pages/datenschutz.astro    →  /datenschutz
```

Bei einer englischsprachigen Seite `/legal-notice` und `/privacy`.

## Gemeinsames Gerüst

Beide Seiten sehen technisch gleich aus. Die Klassennamen sind Platzhalter -
welche Komponente das jeweils ist, steht im Skill `mw-maverick-wave`.

```astro
<BaseLayout title={`<Marke> - ${daten.titel}`} description="…" noIndex>
  <Header slot="header" nurZurueck />

  <section class="mw-section <praefix>-rechtstext">
    <div class="mw-container">
      <div class="mw-section-head">
        <h1 class="mw-section-head-title">{daten.titel}</h1>
      </div>

      {/* Datenschutz: hier zusaetzlich der Kurzhinweis als Alert */}

      <div class="mw-card mw-card-simple mw-prose">
        …
      </div>
    </div>
  </section>

  <Footer slot="footer" />
</BaseLayout>
```

Vier Dinge sind bei beiden gleich und nicht verhandelbar:

- `noIndex` am Layout
- `<Header nurZurueck />` - keine Abschnittsnavigation, ein Knopf zurück
- die `h1` im Abschnittskopf, darunter genau ein Textblock
- Fließtext in einem Prosa-Container, damit Absätze, Listen und Links
  Typografie bekommen, ohne dass jedes `<p>` eine Klasse trägt

Eine schmale Lesebreite (`<praefix>-rechtstext`) ist der eine sinnvolle Grund
für eigenes CSS auf diesen Seiten.

## Impressum

Reihenfolge der `<h2>`, so wie sie auf allen Seiten steht:

1. **Angaben gemäß § 5 DDG** - Name, Firmierung, Straße, PLZ und Ort
2. **Kontakt** - mindestens E-Mail als `mailto`, Telefon wo vorhanden
3. *(branchenspezifisch, siehe unten)*
4. **Umsatzsteuer** - USt-IdNr. **oder** der Kleinunternehmer-Satz nach § 19 UStG
5. **Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV** - meist dieselbe
   Person, trotzdem eigener Abschnitt
6. **Streitschlichtung** - Link auf die EU-Plattform und der Satz, ob man an
   einem Schlichtungsverfahren teilnimmt
7. **Lizenzen und Nachweise** - nur wenn fremde Fotos, Schriften oder Icons
   drin sind

Die Anschrift kommt aus einer Datenquelle, die auch anderswo verwendet wird
(`content/texte.json` → `impressum.anschrift` oder eine eigene
`Anschrift.astro`), damit Impressum, Footer und strukturierte Daten nicht
auseinanderlaufen.

### Was pro Branche in Abschnitt 3 dazukommt

| Betrieb                        | Abschnitt                                                                 |
| ------------------------------ | --------------------------------------------------------------------------- |
| Handwerk mit Meisterpflicht    | **Berufsbezeichnung und Kammer** - Bezeichnung, verleihender Staat, zuständige Handwerkskammer, HwO |
| Heilberuf (Logopädie, Therapie) | **Berufsbezeichnung und berufsrechtliche Regelungen** - Bezeichnung, verleihender Staat, Kammer, Berufsordnung mit Fundstelle |
| Coaching, Training, Beratung   | **Berufsbezeichnung** - freie Tätigkeit, keine Kammer; ein Satz reicht      |
| Hundeschule                    | **Erlaubnis** - § 11 Abs. 1 Nr. 8f TierSchG, erteilt durch das Veterinäramt |
| Gastronomie                    | Keine Berufsangabe, aber **USt-IdNr.** (fast immer) und je nach Angebot Hinweise zu Allergenen und Zusatzstoffen |
| Software, Produkt              | Keine Berufsangabe; dafür **Lizenzen** und ggf. Angaben zur Gesellschaft (HRB, Geschäftsführer) |

Rechtsform entscheidet mit: GmbH/UG brauchen Registergericht, Registernummer
und alle Geschäftsführer; Einzelunternehmen nichts davon.

## Datenschutz

Struktur als JSON, damit die Seite nur rendert:

```jsonc
{
  "titel": "Datenschutzerklärung",
  "stand": "September 2026",
  "hinweisTitel": "Kurz gesagt",
  "hinweisText": "Diese Seite setzt keine Cookies, bindet nichts von Dritten ein und misst nichts.",
  "abschnitte": [
    { "titel": "1. Verantwortliche Stelle", "absaetze": ["…"] },
    { "titel": "2. Hosting und Server-Logfiles", "absaetze": ["…", { "text": "hervorgehoben" }] }
  ]
}
```

Ein Absatz ist entweder ein String oder ein Objekt mit `text` - letzteres wird
hervorgehoben gerendert. Das braucht man für das Widerspruchsrecht nach
Art. 21 Abs. 4 DSGVO, das gesondert dargestellt werden muss.

Der Kurzhinweis steht oben als Hinweisbox und ist die Kurzfassung, die auch im
Footer wiederholt wird. Beide müssen dasselbe sagen.

### Abschnitte in dieser Reihenfolge

1. **Verantwortliche Stelle** - Name und Kontakt, verweist aufs Impressum
2. **Hosting und Server-Logfiles** - wer hostet, welche Felder der Webserver
   protokolliert, wie lange, ob die IP gekürzt wird
3. **Cookies, Reichweitenmessung und externe Inhalte** - auf diesen Seiten die
   Nullmeldung: keine Cookies, kein Tracking, keine Einbettungen. Deshalb auch
   kein Cookie-Banner
4. **Kontaktaufnahme per E-Mail** - was mit einer Anfrage passiert, wie lange
   sie liegt
5. **Deine/Ihre Rechte** - Auskunft, Berichtigung, Löschung, Einschränkung,
   Datenübertragbarkeit, Widerspruch, Beschwerde bei der Aufsichtsbehörde
6. **Speicherdauer**
7. **SSL-/TLS-Verschlüsselung**
8. **Widerspruch gegen Werbe-E-Mails**

### Was den Text verändert

Jede dieser Entscheidungen zwingt zu einem zusätzlichen oder anderen
Abschnitt - und umgekehrt: steht der Abschnitt im Text, muss die Technik ihn
einlösen.

| Technik                                    | Folge im Text                                                        |
| ------------------------------------------ | ---------------------------------------------------------------------- |
| Hosting beim eigenen Server (Regelfall)    | Logfiles, IP gekürzt, Aufbewahrungsdauer nennen                       |
| Hosting bei GitHub Pages                   | Eigener Abschnitt: US-Anbieter, deren Logs, kein Einfluss darauf      |
| Bild von einem CDN (z. B. Unsplash)        | Eigener Abschnitt: IP geht an den Anbieter                            |
| Zähler same-origin                         | Ein Satz im Logfile-Abschnitt                                         |
| Zähler cross-origin                        | Eigener Abschnitt mit Ziel-Host und Zweck                             |
| Schriften selbst gehostet                  | Nichts - genau deshalb werden sie selbst gehostet                     |
| Kontaktformular statt `mailto`             | Abschnitt zu Formulardaten, Empfänger, Aufbewahrung                   |
| Karte eingebettet                          | Abschnitt zum Anbieter **und** eine Einwilligung davor                |

Der Punkt: solange die Seite nichts von Dritten lädt, bleibt die Erklärung
kurz und ohne Banner. Jede Einbettung kippt das. Wer eine hinzufügt, ändert
die Datenschutzerklärung mit, im selben Commit.

## Pflichtangaben außerhalb der Rechtstexte

Zwei Dinge gehören nicht auf die Rechtsseiten, sondern dorthin, wo sie gelten:

- **Preisangaben.** Ein Satz unter jeder Preisliste, ob die Beträge Endpreise
  sind - bei Kleinunternehmern "Als Kleinunternehmerin nach § 19 UStG weise
  ich keine Umsatzsteuer aus", sonst "inklusive MwSt.". Als eigene kleine
  Komponente, die den Satz aus `texte.json` zieht und überall gleich aussieht.
- **Gastronomie:** Hinweis auf Allergene und Zusatzstoffe an der Karte, nicht
  im Impressum.

- [ ] `stand` aktualisiert, wenn sich am Text etwas ändert
- [ ] Kurzhinweis oben, Footer-Kurzfassung und Abschnitt 3 sagen dasselbe
- [ ] Beide Seiten `noIndex` und nicht in der Sitemap
- [ ] Bei Beispielseiten ein Satz, dass der Text den technischen Stand der
      Beispielseite beschreibt und vor dem Livegang ersetzt wird
