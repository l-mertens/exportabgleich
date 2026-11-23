# exportabgleich

Vergleicht zwei Exporte derselben Tabelle und sagt, **wo** sie auseinandergehen.

## Warum

Die Frage „warum zeigen die beiden Berichte verschiedene Zahlen?" liegt bei
mir ungefähr einmal im Monat auf dem Tisch. Meistens endet sie bei einer
Handvoll Datensätze, die in einem der beiden Stände fehlen, oder bei einer
einzigen Spalte, die irgendwo unterwegs umformatiert wurde. Bis man das
weiß, hat man zwei Dateien nebeneinander offen und scrollt.

Das Werkzeug nimmt diesen Teil ab. Es beantwortet nicht, *warum* die Daten
abweichen — aber es sagt in ein paar Sekunden, welche Zeilen und welche
Spalte man sich ansehen muss.

**Nur Standardbibliothek.** Die Rechner, auf denen ich so etwas brauche,
sind selten die, auf denen ich etwas installieren darf.

## Benutzung

```
python3 exportabgleich.py alt.csv neu.csv --key Artikelnummer
```

| Schalter | Wirkung |
|---|---|
| `--key SPALTE` | Schlüsselspalte, über die die Zeilen zugeordnet werden |
| `--encoding` | Vorgabe `utf-8-sig`; für Altsysteme oft `cp1252` |

Rückgabewert `0`, wenn beide Dateien übereinstimmen, sonst `1`.

## Beispiel

Im Ordner `beispiel/` liegen zwei Stände desselben Artikelstamms — einmal
direkt aus dem Vorsystem, einmal so, wie der Bericht ihn sieht.

```
python3 exportabgleich.py beispiel/artikel-vorsystem.csv \
                          beispiel/artikel-bericht.csv --key Artikelnummer
```

```
Spalten
  nur rechts: Bestand

Nur links (1)
  A-1006

Nur rechts (1)
  A-1005

Abweichende Werte (4)
  Preis  (2)
    A-1001:  '49,90'  ->  '49.90'
    A-1004:  '7,95'  ->  '8,45'
  Letzte Aenderung  (1)
    A-1001:  '01.03.2026'  ->  '2026-03-01'
  Warengruppe  (1)
    A-1002:  'Buero'  ->  'Büro'

Unveraendert: 1
```

Die Ausgabe ist nach Spalte gruppiert, weil das in der Praxis die nützlichere
Reihenfolge ist: trägt eine einzige Spalte den ganzen Unterschied, steht die
Ursache meistens schon da.

## Was zu wissen ist

**Leerzeichen am Rand werden ignoriert.** Das ist bei Exporten aus Masken so
oft der einzige Unterschied, dass ich es nicht jedes Mal erklären möchte.

**Der Vergleich läuft zeilenweise über den Schlüssel.** Ohne Schlüssel geht
es nicht, und eine Datei ohne eindeutigen Schlüssel ist ohnehin das größere
Problem.

## Was noch fehlt

Im Beispiel oben sind zwei der vier Befunde gar keine: `49,90` gegen `49.90`
und `01.03.2026` gegen `2026-03-01` sind dieselben Werte in verschiedener
Schreibweise. Das von Hand auszusortieren ist genau die Arbeit, die ich mir
sparen wollte — kommt als Nächstes.

## Tests

```
python3 -m unittest discover -s tests
```

## Lizenz

MIT, siehe `LICENSE`.
