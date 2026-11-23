"""Tests. Mit `python3 -m unittest discover -s tests` laufen lassen.

Was hier steht, sind die Faelle, die mich in der Praxis Zeit gekostet
haben -- nicht die, die sich am leichtesten testen lassen.
"""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import exportabgleich as ea                                    # noqa: E402


def tabelle(text):
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(text)
        pfad = pathlib.Path(fh.name)
    try:
        return ea.read_table(pfad, "utf-8-sig")
    finally:
        pfad.unlink()


class Einlesen(unittest.TestCase):
    def test_bom_verschwindet(self):
        spalten, _ = tabelle("﻿Nr;Wert\n1;a\n")
        self.assertEqual(spalten[0], "Nr")

    def test_semikolon_trotz_komma_im_wert(self):
        # Der Sniffer des csv-Moduls raet hier gern auf Komma.
        spalten, zeilen = tabelle("Nr;Preis\n1;1.234,50\n")
        self.assertEqual(spalten, ["Nr", "Preis"])
        self.assertEqual(zeilen[0]["Preis"], "1.234,50")


class Vergleich(unittest.TestCase):
    LINKS = "Nr;Wert;Warengruppe\n1;49,90;Buero\n2;10,00;Technik\n"
    RECHTS = "Nr;Wert;Warengruppe\n1;49.90;Buero\n3;10,00;Technik\n"

    def vergleiche(self):
        lk, lz = tabelle(self.LINKS)
        rk, rz = tabelle(self.RECHTS)
        return ea.compare(lk, lz, rk, rz, "Nr")

    def test_fehlende_und_neue_zeilen(self):
        erg = self.vergleiche()
        self.assertEqual(erg.only_left, ["2"])
        self.assertEqual(erg.only_right, ["3"])

    def test_formatunterschied_ist_ein_befund(self):
        erg = self.vergleiche()
        self.assertEqual([d.column for d in erg.differences], ["Wert"])

    def test_neue_spalte_faellt_auf(self):
        lk, lz = tabelle("Nr;Wert\n1;a\n")
        rk, rz = tabelle("Nr;Wert;Bestand\n1;a;12\n")
        erg = ea.compare(lk, lz, rk, rz, "Nr")
        self.assertEqual(erg.only_right_columns, ["Bestand"])
        self.assertFalse(erg.clean)

    def test_leerzeichen_am_rand_sind_egal(self):
        lk, lz = tabelle("Nr;Wert\n1;Lampe \n")
        rk, rz = tabelle("Nr;Wert\n1;Lampe\n")
        erg = ea.compare(lk, lz, rk, rz, "Nr")
        self.assertEqual(erg.differences, [])
        self.assertTrue(erg.clean)

    def test_fehlende_schluesselspalte_bricht_ab(self):
        lk, lz = tabelle("Nr;Wert\n1;a\n")
        rk, rz = tabelle("Kennung;Wert\n1;a\n")
        with self.assertRaises(KeyError):
            ea.compare(lk, lz, rk, rz, "Nr")


class Rueckgabewert(unittest.TestCase):
    def test_gleiche_dateien_geben_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "a.csv"
            p.write_text("Nr;Wert\n1;a\n", encoding="utf-8")
            self.assertEqual(ea.main([str(p), str(p), "--key", "Nr"]), 0)

    def test_unterschied_gibt_eins(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = pathlib.Path(tmp) / "a.csv"
            b = pathlib.Path(tmp) / "b.csv"
            a.write_text("Nr;Wert\n1;a\n", encoding="utf-8")
            b.write_text("Nr;Wert\n1;b\n", encoding="utf-8")
            self.assertEqual(ea.main([str(a), str(b), "--key", "Nr"]), 1)


if __name__ == "__main__":
    unittest.main()
