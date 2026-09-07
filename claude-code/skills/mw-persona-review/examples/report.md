---
persona: Julia
task: "Lege eine Rechnung über 250€ an und sende sie per E-Mail"
date: 2026-09-07
mode: browser
url: http://localhost:4200
---

# Persona-Review: Julia - Rechnung anlegen und versenden

## Verlauf

1. Startseite - findet "Rechnungen" in der Seitenleiste, klickt
2. Rechnungsliste - sucht ~15 Sekunden nach dem Anlegen-Button, findet das "+"-Icon oben rechts
3. Formular - füllt Kunde, Betrag, Datum aus, lässt "Zahlungsziel" leer
4. Klick auf "Speichern" - Fehlermeldung erscheint
5. **Abbruch.** Nach der Meldung in Schritt 4 würde Julia jemanden fragen, statt weiterzumachen

## Befunde

### 1 - Fehlermeldung nennt einen Datenbankbegriff (blockierend)

**Fundstelle:** Rechnungsformular, roter Balken unter dem Speichern-Button
> "Constraint violation: dueDate must not be null"

**Was verwirrt:** Zwei Wörter aus Julias verbotenem Vokabular in einem Satz, dazu ein Feldname
in Englisch, den es auf dem Bildschirm gar nicht gibt - das Feld heißt dort "Zahlungsziel".
Julia weiß weder, was sie falsch gemacht hat, noch wo. Sie bricht hier ab.

**Vorschlag:** Feldnahe Meldung am Feld selbst: "Bitte ein Zahlungsziel angeben." Backend-Fehler
nie durchreichen - die Validierung gehört ins Formular, bevor gespeichert wird.

### 2 - Anlegen-Button ist nur ein Icon (störend)

**Fundstelle:** Rechnungsliste, oben rechts - `invoice-list.html:23`
> `<button class="icon-btn" aria-label="Neu"><mw-icon name="plus" /></button>`

**Was verwirrt:** Julia erkennt an einem "+" nicht, dass dort eine Rechnung entsteht. Sie hat
den Button gefunden, aber durch Ausprobieren. Beim nächsten Besuch sucht sie wieder.

**Vorschlag:** Beschriftung dazu: "Neue Rechnung". Icon-only nur bei Aktionen, die sie täglich macht.

### 3 - "Entwurf" als Status ohne Erklärung (kosmetisch)

**Fundstelle:** Rechnungsliste, Spalte "Status"
> "Entwurf"

**Was verwirrt:** Sie liest es, kann es aber nicht einordnen - ist die Rechnung jetzt raus oder nicht?

**Vorschlag:** "Noch nicht versendet".

## Nicht geprüft

- E-Mail-Versand - wegen des Abbruchs in Schritt 4 nicht erreicht
- PDF-Ansicht - nur über den Versand erreichbar

---

Diese Befunde ersetzen keinen echten Nutzertest - bitte stichprobenhaft mit echten Personen abgleichen.
