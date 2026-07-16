# Architektur

## Ziel

S-Series Explorer soll zunächst als schlanke lokale Windows-Anwendung funktionieren und später als Werkzeugkasten für S1000D-/S2000M-Dateibestände wachsen.

## Schichten

1. **Scanner**: liest das Dateisystem, Metadaten und optional SHA-256.
2. **Parser**: zerlegt Dateinamen ohne Dateiendung und interpretiert bekannte Präfixe.
3. **Format-Inspector**: erkennt Metadaten proprietärer Formate, zunächst Corel DESIGNER `.des`.
4. **Comparator**: bildet Paare anhand einer wählbaren Vergleichsstrategie.
5. **UI**: zeigt jedes Objekt als kompakte Zeile mit einzeln sortierbaren Spalten.
6. **Export**: schreibt die aktuell gefilterte Sicht als UTF-8-CSV.

## Designentscheidungen

- Reine Python-Standardbibliothek für den Laufzeitbetrieb.
- Tkinter/ttk, damit auf normalen Windows-Python-Installationen keine GUI-Abhängigkeit nötig ist.
- Parser liefert sowohl rohe Segmente als auch semantische Felder.
- Projektspezifische Regeln werden später als Profile ergänzt und nicht hart in die UI eingebaut.
- Proprietäre Formate werden niemals als sicher erkannt ausgegeben, wenn nur schwache Heuristiken vorliegen.
