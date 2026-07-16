# S-Series Explorer

Ein kompakter Windows-Dateiexplorer für S-Series-/S1000D-Arbeitsbestände.

## Funktionen

- Dateinamen werden in einer durchgehenden Tabellenzeile in einzelne Segmente zerlegt.
- S1000D-nahe Präfixe wie `DMC`, `PMC`, `ICN`, `COM`, `DDN`, `DML`, `CSN` und `SMC` werden erkannt.
- DMC-Felder werden zusätzlich semantisch interpretiert.
- Auffällige Schreibweisen wie Kleinbuchstaben, Leerzeichen, leere Segmente oder zu kurze DMC/PMC/ICN-Codes werden markiert.
- Zwei Ordner können rekursiv verglichen werden:
  - relativer Pfad,
  - Dateiname ohne Endung,
  - Dateiinhalt per SHA-256.
- Unterschiede werden als **Identisch**, **Geändert**, **Nur Ordner A** oder **Nur Ordner B** dargestellt.
- `.des`-Dateien werden auf Corel-DESIGNER-/CorelDRAW-Formatmarker untersucht.
- Volltextfilter über alle Spalten, Statusfilter, CSV-Export und Explorer-Kontextaktionen.
- Explorer-Navigation mit Adressleiste, Zurück/Vor/Hoch, direktem Öffnen von Ordnern und typischen Dateiaktionen.
- Der Ordnervergleich ist als separate Funktion über das Funktions-Dropdown auswählbar.
- Dateiaktionen im Kontextmenü und per Tastatur: Kopieren, Ausschneiden, Einfügen, Umbenennen, Löschen und neue Ordner erstellen.

## Start unter Windows

1. Python 3.11 oder neuer installieren. Bei der Installation `tkinter` aktiviert lassen.
2. Das Repository herunterladen oder klonen.
3. Ohne Installation und ohne Internetzugriff starten:

```powershell
.\run.bat
```

Beim Doppelklick startet `run.bat` die grafische Anwendung ueber den Windows Script Host im Hintergrund und schliesst das Startfenster sofort wieder. Falls der Start fehlschlaegt, werden technische Details in `startup.log` im Programmordner geschrieben. Alternativ kann direkt `launcher.pyw` gestartet werden.

Technischer Konsolenstart fuer Fehlersuche:

```powershell
py .\launcher.py
```

Der portable Start benötigt weder `pip` noch externe Python-Pakete. Dadurch funktioniert er auch in Firmennetzen, in denen ein Proxy den Zugriff auf PyPI blockiert.

### Optionale Installation

Nur wenn ein Kommando wie `s-series-explorer` systemweit verfügbar sein soll:

```powershell
py -m pip install --no-build-isolation --no-deps -e .
s-series-explorer
```

`--no-build-isolation` verhindert, dass `pip` für den Build erneut `setuptools` aus dem Internet herunterladen will. Sollte die lokale `setuptools`-Version zu alt sein, verwenden Sie stattdessen den portablen Start über `run.bat`.

## Windows-EXE bauen

```powershell
py -m pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --paths src --name S-Series-Explorer launcher.py
```

Die GitHub-Action `build-windows.yml` erzeugt ebenfalls eine EXE als Workflow-Artefakt.

## Corel-DESIGNER-Versionserkennung

Das `.des`-Format ist proprietär. Die Erkennung arbeitet deshalb in mehreren Stufen:

1. ZIP- oder RIFF-Container erkennen,
2. eingebettete Corel-/CDR-Versionsmarker suchen,
3. lesbare Produkt- und Versionszeichenketten auswerten,
4. bei fehlendem Marker transparent `Version nicht erkannt` anzeigen.

Die Zuordnung von Formatcodes zu Produktgenerationen ist eine Best-Effort-Anzeige. Für produktive Freigaben sollten repräsentative `.des`-Beispieldateien aus den tatsächlich eingesetzten Corel-DESIGNER-Versionen als Regressionstests ergänzt werden.

## Projektstruktur

```text
src/s_series_explorer/
  app.py               Desktop-Oberfläche
  filename_parser.py   Dateinamensegmentierung und S1000D-nahe Interpretation
  scanner.py           Ordnerscan und SHA-256
  compare.py           Vergleichslogik
  corel_designer.py    DES-Container- und Versionsanalyse
  csv_export.py        CSV-Ausgabe

tests/                 Unittests
docs/                  Architektur und Roadmap
```

## Geplante nächste Schritte

- konfigurierbare projektspezifische ICN-Syntax,
- echte S1000D-Issue-Profile und BREX-nahe Dateinamensregeln,
- Spaltenprofile speichern,
- Duplikat- und Referenzsuche,
- Explorer-Rechtsklickintegration,
- Dateiaktionen wie Sammeln, Kopieren und kontrolliertes Umbenennen.
