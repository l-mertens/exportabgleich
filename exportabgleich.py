#!/usr/bin/env python3
"""Vergleicht zwei Exporte derselben Tabelle und sagt, wo sie auseinandergehen.

Gedacht fuer die Frage, die bei mir ungefaehr einmal im Monat auf dem Tisch
liegt: zwei Berichte zeigen verschiedene Zahlen, beide berufen sich auf
denselben Datenbestand, und niemand weiss, an welcher Stelle sie sich
trennen.

Nur Standardbibliothek. Die Rechner, auf denen ich so etwas brauche, sind
selten die, auf denen ich etwas installieren darf.

    python3 exportabgleich.py alt.csv neu.csv --key Artikelnummer
"""
import argparse
import csv
import dataclasses
import io
import pathlib
import sys


@dataclasses.dataclass
class Difference:
    """Ein Feld, das in beiden Tabellen steht und verschiedene Werte hat."""
    key: str
    column: str
    left: str
    right: str


@dataclasses.dataclass
class Result:
    columns: list = dataclasses.field(default_factory=list)
    only_left_columns: list = dataclasses.field(default_factory=list)
    only_right_columns: list = dataclasses.field(default_factory=list)
    only_left: list = dataclasses.field(default_factory=list)
    only_right: list = dataclasses.field(default_factory=list)
    differences: list = dataclasses.field(default_factory=list)
    identical: int = 0

    @property
    def clean(self) -> bool:
        return not (self.only_left or self.only_right or self.differences
                    or self.only_left_columns or self.only_right_columns)


# ---------------------------------------------------------------------------
# Einlesen
# ---------------------------------------------------------------------------

def sniff_delimiter(sample):
    """Semikolon oder Komma.

    Der Sniffer aus dem csv-Modul raet bei deutschen Exporten gern daneben,
    weil in den Werten Kommas als Dezimaltrenner stehen. Deshalb zaehle ich
    selbst, und zwar nur in der Kopfzeile: dort stehen keine Zahlen.
    """
    zeilen = sample.splitlines()
    kopf = zeilen[0] if zeilen else ""
    return ";" if kopf.count(";") > kopf.count(",") else ","


def read_table(path, encoding):
    """Kopfzeile und Zeilen. Das BOM schluckt `utf-8-sig` still.

    Das ist der haeufigste Grund, warum die erste Spalte eines Excel-Exports
    aussieht wie `Artikelnummer` und trotzdem nicht gefunden wird.
    """
    roh = path.read_text(encoding=encoding)
    leser = csv.DictReader(io.StringIO(roh), delimiter=sniff_delimiter(roh))
    spalten = [s.strip() for s in (leser.fieldnames or [])]
    zeilen = []
    for satz in leser:
        # DictReader liefert None fuer fehlende Felder und sammelt
        # ueberzaehlige unter None ein. Beides faellt hier weg.
        zeilen.append({(k or "").strip(): (v if v is not None else "")
                       for k, v in satz.items() if k is not None})
    return spalten, zeilen


# ---------------------------------------------------------------------------
# Vergleichen
# ---------------------------------------------------------------------------

def compare(left_columns, left_rows, right_columns, right_rows, key):
    if key not in left_columns or key not in right_columns:
        raise KeyError("Schluesselspalte fehlt in einer der Dateien: " + key)

    erg = Result()
    erg.only_left_columns = [s for s in left_columns if s not in right_columns]
    erg.only_right_columns = [s for s in right_columns if s not in left_columns]
    erg.columns = [s for s in left_columns if s in right_columns and s != key]

    links = {zeile.get(key, "").strip(): zeile for zeile in left_rows}
    rechts = {zeile.get(key, "").strip(): zeile for zeile in right_rows}

    erg.only_left = [k for k in links if k not in rechts]
    erg.only_right = [k for k in rechts if k not in links]

    for k, zeile_l in links.items():
        zeile_r = rechts.get(k)
        if zeile_r is None:
            continue
        treffer = False
        for spalte in erg.columns:
            links_wert = zeile_l.get(spalte, "")
            rechts_wert = zeile_r.get(spalte, "")
            if links_wert.strip() != rechts_wert.strip():
                treffer = True
                erg.differences.append(
                    Difference(k, spalte, links_wert, rechts_wert))
        if not treffer:
            erg.identical += 1
    return erg


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

def _liste(titel, eintraege):
    if not eintraege:
        return []
    return [f"{titel} ({len(eintraege)})"] + ["  " + e for e in eintraege] + [""]


def format_report(erg, name_left, name_right):
    aus = ["", f"{name_left}  gegen  {name_right}", ""]

    if erg.only_left_columns or erg.only_right_columns:
        aus.append("Spalten")
        if erg.only_left_columns:
            aus.append(f"  nur links:  {', '.join(erg.only_left_columns)}")
        if erg.only_right_columns:
            aus.append(f"  nur rechts: {', '.join(erg.only_right_columns)}")
        aus.append("")

    aus += _liste("Nur links", erg.only_left)
    aus += _liste("Nur rechts", erg.only_right)

    if erg.differences:
        # Nach Spalte gruppiert: traegt eine einzige Spalte den gesamten
        # Unterschied, steht die Ursache meist schon da.
        nach_spalte = {}
        for d in erg.differences:
            nach_spalte.setdefault(d.column, []).append(d)
        aus.append(f"Abweichende Werte ({len(erg.differences)})")
        for spalte, treffer in sorted(nach_spalte.items(),
                                      key=lambda p: -len(p[1])):
            aus.append(f"  {spalte}  ({len(treffer)})")
            for d in treffer:
                aus.append(f"    {d.key}:  {d.left!r}  ->  {d.right!r}")
        aus.append("")

    aus.append(f"Unveraendert: {erg.identical}")
    aus.append("Die Dateien stimmen ueberein." if erg.clean
               else "Die Dateien stimmen nicht ueberein.")
    aus.append("")
    return "\n".join(aus)


# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("left", type=pathlib.Path, help="erste Datei")
    ap.add_argument("right", type=pathlib.Path, help="zweite Datei")
    ap.add_argument("--key", required=True, metavar="SPALTE",
                    help="Schluesselspalte, ueber die die Zeilen zugeordnet "
                         "werden")
    ap.add_argument("--encoding", default="utf-8-sig",
                    help="Vorgabe utf-8-sig. Fuer Altsysteme oft cp1252")
    args = ap.parse_args(argv)

    try:
        l_spalten, l_zeilen = read_table(args.left, args.encoding)
        r_spalten, r_zeilen = read_table(args.right, args.encoding)
    except UnicodeDecodeError as exc:
        print(f"Datei laesst sich nicht als {args.encoding} lesen: {exc}\n"
              f"Bei Exporten aus aelteren Systemen hilft meist "
              f"--encoding cp1252.", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Datei nicht lesbar: {exc}", file=sys.stderr)
        return 2

    try:
        erg = compare(l_spalten, l_zeilen, r_spalten, r_zeilen, args.key)
    except KeyError as exc:
        print(str(exc).strip("'"), file=sys.stderr)
        print(f"Vorhanden links:  {', '.join(l_spalten)}", file=sys.stderr)
        print(f"Vorhanden rechts: {', '.join(r_spalten)}", file=sys.stderr)
        return 2

    print(format_report(erg, args.left.name, args.right.name))
    return 0 if erg.clean else 1


if __name__ == "__main__":
    sys.exit(main())
