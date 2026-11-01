from app.lernen.regeln import begriffe, ist_sicher, lernen, regel_finden, rueckgaengig, sicherheit


def test_begriffe() -> None:
    assert begriffe("Mineralwasser medium 12 x 0,75 l") == frozenset({"mineralwasser", "medium"})
    assert begriffe("Süßrahmbutter") == frozenset({"suessrahmbutter"})
    assert begriffe(None) == frozenset()


def test_regel_wird_wiedererkannt_und_ist_nach_bestaetigung_sicher() -> None:
    regeln: list[dict[str, object]] = []
    lernen(regeln, "Mineralwasser medium 12 x 0,75 l", "19", "3400", korrektur=False, zeit="t1")  # type: ignore[arg-type]
    r = regel_finden(regeln, "Mineralwasser medium 12 x 0,75 l", "19.0")  # type: ignore[arg-type]
    assert r and r["konto"] == "3400" and ist_sicher(r)
    assert regel_finden(regeln, "Mineralwasser medium", "7") is None  # anderer Steuersatz  # type: ignore[arg-type]
    assert regel_finden(regeln, "Apfelsaft naturtrüb", "19") is None  # andere Position  # type: ignore[arg-type]


def test_nach_korrektur_drei_bestaetigungen_noetig() -> None:
    regeln: list[dict[str, object]] = []
    lernen(regeln, "Kurierfahrt Stadtgebiet", "19", "4910", korrektur=True, zeit="t1")  # type: ignore[arg-type]
    r = regeln[0]
    assert not ist_sicher(r)  # type: ignore[arg-type]
    lernen(regeln, "Kurierfahrt Stadtgebiet", "19", "4910", korrektur=False, zeit="t2")  # type: ignore[arg-type]
    assert not ist_sicher(r)  # type: ignore[arg-type]
    lernen(regeln, "Kurierfahrt Stadtgebiet", "19", "4910", korrektur=False, zeit="t3")  # type: ignore[arg-type]
    assert ist_sicher(r) and sicherheit(r) > 0.9  # type: ignore[arg-type]


def test_korrektur_aendert_konto_und_setzt_zaehler_zurueck() -> None:
    regeln: list[dict[str, object]] = []
    lernen(regeln, "Backpapier 40 x 60 cm", "19", "3400", korrektur=False, zeit="t1")  # type: ignore[arg-type]
    lernen(regeln, "Backpapier 40 x 60 cm", "19", "3400", korrektur=False, zeit="t2")  # type: ignore[arg-type]
    lernen(regeln, "Backpapier 40 x 60 cm", "19", "4980", korrektur=True, zeit="t3")  # type: ignore[arg-type]
    r = regeln[0]
    assert r["konto"] == "4980" and r["bestaetigungen"] == 1 and r["korrekturen"] == 1 and not ist_sicher(r)  # type: ignore[arg-type]


def test_abschalten_und_rueckgaengig() -> None:
    regeln: list[dict[str, object]] = []
    a1 = lernen(regeln, "Strom Arbeitspreis", "19", "4240", korrektur=False, zeit="t1")  # type: ignore[arg-type]
    a2 = lernen(regeln, "Strom Arbeitspreis", "19", "4240", korrektur=False, zeit="t2")  # type: ignore[arg-type]
    regeln[0]["aktiv"] = False
    assert regel_finden(regeln, "Strom Arbeitspreis", "19") is None  # type: ignore[arg-type]
    assert sicherheit(regeln[0]) == 0.0  # type: ignore[arg-type]
    regeln[0]["aktiv"] = True
    rueckgaengig(regeln, a2)  # type: ignore[arg-type]
    assert regeln[0]["bestaetigungen"] == 1
    rueckgaengig(regeln, a1)  # type: ignore[arg-type]
    assert regeln == []


def test_monatsname_verschiebt_den_fingerabdruck_nicht() -> None:
    regeln: list[dict[str, object]] = []
    lernen(regeln, "Unterhaltsreinigung Gastraum Oktober 2026", "19", "4250", korrektur=False, zeit="t1")  # type: ignore[arg-type]
    r = regel_finden(regeln, "Unterhaltsreinigung Gastraum November 2026", "19")  # type: ignore[arg-type]
    assert r and r["konto"] == "4250"
