# S-Series Explorer

Ein kompakter Windows-Dateiexplorer für S-Series-/S1000D-Arbeitsbestände. Die aktive GUI wurde in C# / Windows Forms neu aufgebaut, damit sie ohne Python-Tkinter startet und sich stärker wie ein nativer Windows-Explorer verhält.

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

1. .NET 8 Desktop Runtime oder .NET 8 SDK installieren.
2. Das Repository herunterladen oder klonen.
3. Ohne Python starten:

```powershell
.\run.bat
```

Beim Doppelklick startet `run.bat` die C#-Windows-Forms-Anwendung ueber den Windows Script Host im Hintergrund und schliesst das Startfenster sofort wieder. Wenn eine veroeffentlichte EXE vorhanden ist, wird diese direkt gestartet. Sonst wird `dotnet run` verwendet. Falls .NET fehlt oder die Projektdatei nicht gefunden wird, erscheint eine Fehlermeldung und technische Details werden in `startup.log` im Programmordner geschrieben.

Technischer Konsolenstart fuer Fehlersuche:

```powershell
dotnet run --project .\SSeriesExplorer.WinForms\SSeriesExplorer.WinForms.csproj
```

Der neue Start benötigt kein Python, kein `pip` und keine Tkinter-Komponenten. Für eine einzelne EXE kann die Anwendung mit `dotnet publish` veröffentlicht werden.

### Optionale Veröffentlichung

Wenn keine SDK-Installation auf dem Zielrechner gewünscht ist, kann eine portable Windows-EXE gebaut und der veröffentlichte Ordner verteilt werden.

## Windows-EXE bauen

```powershell
dotnet publish .\SSeriesExplorer.WinForms\SSeriesExplorer.WinForms.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
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
SSeriesExplorer.WinForms/
  Program.cs           C#-Startpunkt und Fehlerprotokoll
  MainForm.cs          Native Windows-Forms-Exploreroberfläche

src/s_series_explorer/
  app.py               Legacy-Python-Oberfläche
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
