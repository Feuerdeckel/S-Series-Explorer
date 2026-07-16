# S-Series Explorer

S-Series Explorer ist ein einfacher Offline-Datei-Explorer mit grafischer Oberfläche.

## Warum Python + Tkinter?

Python mit Tkinter ist für dieses Projekt gut geeignet, weil Tkinter mit Python ausgeliefert wird, keine Online-Dienste benötigt und mit PyInstaller zu einer einzelnen Windows-EXE gebündelt werden kann.

## Funktionen

- Ordner öffnen und durchsuchen
- Dateien mit dem Standardprogramm öffnen
- Neue Dateien und Ordner erstellen
- Kopieren, Ausschneiden und Einfügen
- Umbenennen und Löschen mit Sicherheitsabfrage
- Versteckte Dateien ein- und ausblenden

## Start für Entwickler

```bash
python s_series_explorer.py
```

## Windows-EXE bauen

Auf einem Windows-Rechner mit Python und PyInstaller:

```bash
python -m pip install pyinstaller
python build_exe.py
```

Die fertige Einzeldatei liegt danach unter:

```text
dist/S-Series-Explorer.exe
```

Diese EXE kann auf einen Offline-PC kopiert werden und benötigt zur Laufzeit keine Internetverbindung.
