# CorridorKey für EffectCraft – v0.6

Dockbares Panel für die Desktop-Version von EffectCraft. Die Verarbeitung läuft
lokal mit CorridorKey auf einer NVIDIA-Grafikkarte. Das Original bleibt im Projekt;
Ergebnisse werden als eigene Ebenen eingefügt. Unter EffectCraft 0.16.0 auf Linux
mit echter CUDA-Inferenz geprüft.

## Externer Wrapper 0.6

Diese Fassung startet die unveränderte originale CorridorKey-Kommandozeile als
eigenes Programm. Runtime-Patches und Importe von CorridorKey-Modulen entfallen.
Die eigene Bildnachbearbeitung verarbeitet exportierte lineare EXR-Dateien.
GPU-Warmhalten entfällt; das Modell lädt je KI-Auftrag neu. Korrekturen aus
aufbewahrten Bilddaten benötigen weiterhin keinen KI-Lauf. Der temporäre
Platzbedarf enthält immer Float-EXR-Zwischendaten. Die Lizenzfrage ist damit
nicht automatisch geklärt.

## Sprachen

Das Panel unterstützt alle elf Sprachen von EffectCraft 0.16. Zusätzlich ist die
georgische Übersetzung für Hosts vorbereitet, die Georgisch bereits anbieten.
Auf älteren Hosts wird dafür lesbares Englisch mit einem Hinweis verwendet.
Die Sprache folgt den EffectCraft-Einstellungen; unter Dienst → Sprache kann
sie für das Panel geändert werden. Anschließend das Panel neu öffnen.
Dateinamen, eigene Vorlagen und technische Diagnosen werden nicht übersetzt.

Das eigenständige Add-on-Repository enthält einen Einrichtungshelfer
`setup_effectcraft.py`, der den offiziellen CorridorKey-Code und die Modelle
separat herunterlädt. Den vollständigen Einstieg findest du in der README im
Repository-Hauptordner. Die folgenden manuellen Befehle setzen eine fertig
installierte, unveränderte CorridorKey-Umgebung voraus.

## Funktionen aus Version 0.4

- **Kanten ohne erneute KI-Verarbeitung:** Im Tab Kanten die Werte ändern und
  „Korrektur ohne neue KI ausgeben“ wählen. Das erzeugt eine eigene Variante
  aus den ursprünglichen Vordergrund- und Maskendaten. Despill, Schwarz/Weiß,
  Ausdehnung, Weichheit und MOV/EXR-Ausgabe sind nachträglich veränderbar.
  Bereits eingefügte Varianten mit gleichem Zeitbereich werden beim Einfügen
  der neuen Version ausgeblendet. Undo stellt die vorherige Variante wieder her.
- **Bewegte Vorschau im Panel:** Abspielen/Pause, Zeitleiste zum Scrubben und
  Schachbrett-, Masken-, Original- oder Vergleichsansicht. Diese leichte Vorschau
  verwendet bis zu acht Bilder pro Sekunde; der Export behält seine native
  Bildrate. Je Ergebnis bleiben höchstens drei Fenster von sechs Sekunden
  als kleine Vorschaubilder gespeichert. Fehlende Fenster werden bei Bedarf
  im Hintergrund erzeugt. Die KI-Warteschlange muss dafür nicht frei sein.
- **Aufträge wiederholen:** Im Tab Aufträge unverändert wiederholen oder
  mit den aktuellen Einstellungen neu rechnen. Für geänderte Einstellungen
  die Ursprungsebene auswählen. Der ursprüngliche Auftrag und seine Dateien
  bleiben erhalten. „Auftragseinstellungen laden“ übernimmt dessen Reglerwerte.
- **Projektpaket:** Im Tab Dateien „Projekt samt Medien sammeln“ wählen und
  einen Zielordner auswählen. Auch ungespeicherte Änderungen werden über eine
  Projektkopie übernommen; das geöffnete Projekt wird nicht gespeichert oder
  ersetzt. Medien, EXR-Sequenzen, zugehörige Korrekturdaten und Vorlagen werden
  kopiert, die kopierten Mediendateien per SHA-256 geprüft und Pfade relativ
  abgelegt. Nur fertiggestellte Pakete erscheinen als endgültiger Ordner.
  Die enthaltene `.ecproj` kann nach dem Verschieben geöffnet werden; das Panel
  übernimmt die Korrekturdaten automatisch. Bereits eingefügte Ebenen werden
  erkannt und nicht erneut als ausstehender Import angeboten.
- **Speicher verwalten:** Im Tab Dateien stehen belegter Auftrags-, Vorschau-
  und Korrekturspeicher, freier Plattenplatz und — sofern verfügbar —
  Grafikspeicher. „Platzbedarf abschätzen“ zeigt das Rohdatenvolumen des
  ausgewählten Bereichs vor Kompression; die tatsächlichen Dateien sind
  materialabhängig. Für den ausgewählten Auftrag oder alle abgeschlossenen
  Aufträge zunächst eine Aufräumvorschau berechnen, dann die angezeigten
  Zwischendaten entfernen. Aktive Player, laufende Korrekturen und bekannte
  Projektreferenzen sind geschützt. Fertige MOVs, EXR-Ausgaben und Quellen
  werden niemals durch diese Aufräumfunktion gelöscht.

Korrekturdaten werden standardmäßig aufbewahrt und benötigen zusätzlichen
Speicher. Unter Dienst kann das für neue KI-Aufträge ausgeschaltet werden.
Für Ergebnisse aus älteren Versionen ist zunächst ein neuer KI-Lauf mit
aktivierten Korrekturdaten nötig: Die fertigen Videos enthalten diese Rohdaten
nicht. Gelöschte Korrekturdaten lassen sich ebenfalls nur durch erneute
KI-Verarbeitung ersetzen. Ihre Entfernung ist deshalb eine eigene, standardmäßig
**ausgeschaltete** Option beim Aufräumen.

Das Projektpaket sammelt in der Projektdatei ausgewiesene Medien und Sequenzen.
Externe Fonts, zusätzlich benötigte Effekt-Plugins und nicht in der Projektdatei
aufgeführte Dateien anderer Werkzeuge gehören nicht zum Paket. Ein Paket ist
separat und wird durch die Aufräumfunktion nicht verändert.

Dateiaktionen laufen im Hintergrund und können im Panel abgebrochen werden.
Beim erneuten Öffnen des Panels wird der Status einer noch laufenden Dateiaktion
wiederhergestellt. Ein Dienstneustart bricht Dateiaktionen ab; unvollständige
Pakete werden entfernt.

## Einrichten und starten

Die CorridorKey-Umgebung, Modellgewichte und ffmpeg müssen eingerichtet sein.

```bash
venv/bin/python integrations/effectcraft/bridge.py --check
venv/bin/python integrations/effectcraft/install.py --effectcraft /pfad/zu/EffectCraft.AppImage
integrations/effectcraft/start_bridge.sh --launch
```

EffectCraft benötigt die bereits freigegebene Einstellung **Allow Scripts to Write
Files and Access Network**. Das Panel liegt unter **Window → CorridorKey**.
Port und Token werden automatisch aus einer privaten Verbindungsdatei gelesen.
Der gemeinsame Starter verwendet die lokale EffectCraft-Steuerschnittstelle
auf Port 9877 und den Dienst auf 9878. So funktioniert die Statusaktualisierung
auch in Version 0.16, die Skript-Timer noch nicht ausführt.

Ein bereits geöffnetes EffectCraft wird wiederverwendet. Falls es ohne
Steuerschnittstelle gestartet wurde, das Projekt selbst sichern, EffectCraft
normal schließen und anschließend über den gemeinsamen Starter öffnen.
Der Starter beendet keine laufende EffectCraft-Instanz.

Nur den Dienst starten:

```bash
venv/bin/python integrations/effectcraft/bridge.py --background
```

Andere Anschlüsse und Ausgabeverzeichnisse sind mit `--port`,
`--effectcraft-port`, `--connection-file` und `--output-dir` konfigurierbar.
`CORRIDORKEY_PYTHON` kann den Interpreter des Starters überschreiben.
Unter Windows: Python-Umgebung entsprechend mit `venv\Scripts\python.exe` aufrufen.
Die neue Version wurde unter Windows und macOS nicht praktisch geprüft.

## Arbeiten mit dem Panel

Das Projekt zuerst speichern und eine oder mehrere entsperrte Videoebenen
in der Timeline auswählen. Bis zu 32 offene Aufträge sind möglich. Sie laufen
nacheinander auf der GPU; das Panel und die Komposition bleiben bedienbar.

**Clip**

- Grüne Farbsäume entfernen: Aus, Leicht, Mittel oder Stark.
- Zeitbereich: gesamte Quelldatei, getrimmte Ebene oder Schnittmenge der Ebene
  mit dem Arbeitsbereich. Start/Ende werden auf Quellbilder ausgerichtet.
  Stretch und interpretierte Bildrate werden bei Zuordnung und Import berücksichtigt.
  Da EffectCraft Ebenenstarts auf Kompositionsbilder rastert, kann zusätzlicher
  Vorlauf nötig sein. Dieser wird mitgerechnet, bleibt in der Timeline aber ausgeblendet.
- Ausgabe: ProRes 4444 MOV mit Straight Alpha oder lineare EXR-Sequenz als Half/Float.
- Startmaske: PNG/JPG mit Dateiauswahl oder manuell eingegebenem Pfad.
  Weiß bleibt, Schwarz wird entfernt. Das Bild gehört zum **ersten Bild des
  tatsächlich verarbeiteten Bereichs inklusive eventuell notwendigem Vorlauf**. Bei mehreren Ebenen wird dieselbe Bilddatei verwendet.
- Maskenvideo: muss Bildrate und Bildanzahl der gesamten Quelldatei haben.
  Für einen Ausschnitt wird es synchron mitbeschnitten.
- Ebenenmaske: eine geschlossene Add-Maske wird am ersten Quellbild des Bereichs
  als Startbild übernommen, einschließlich Bezier-Kurven, Invertierung,
  Deckkraft, normaler Weichheit und Ausdehnung. Variable Federpunkte,
  andere Modi und mehrere kombinierte Masken werden ausdrücklich abgewiesen.
  Eine animierte Ebenenmaske wird als Momentaufnahme übernommen.

**Kanten**

Schwarz-/Weißpunkt in Prozent, Kantenvergrößerung oder -verkleinerung von −32
bis +32 Ausgabepixeln und Weichheit von 0 bis 16 Pixeln. Die Regler bearbeiten
nur die Alpha-Abdeckung. Eigene Vorlagen speichern diese Einstellungen sowie
Despill, Ausgabe, Maskengenauigkeit und Speichermodus. Maskenpfade und
Ebenenbezüge bleiben auftragsbezogen.

**Vorschau**

Eine kurze Vorschau ab dem Abspielkopf, innerhalb des ausgewählten Bereichs,
mit halber Modellauflösung; Dauer 0,04 bis 10 Sekunden. Sie wird in voller
Bildgröße ausgegeben und bleibt klar als Vorschau gekennzeichnet.
Das Ergebnis lässt sich direkt abspielen und auf Schachbrett, als Maske,
im Original oder geteilt Vorher/Nachher durchsehen. Das Vorschauvideo kann im normalen Videoplayer geöffnet werden.
Vorschauen lassen sich nicht als finales Ergebnis einfügen: Dafür **Freistellen**
verwenden. Die finalen Ergebnisse bieten dieselben Einzelbildansichten.

**Aufträge**

Auftrag auswählen, Status prüfen, einzeln abbrechen oder alle offenen Aufträge
abbrechen. **Ergebnis einfügen** übernimmt den ausgewählten finalen Auftrag;
**Neueste fertige Ergebnisse einfügen** übernimmt pro Ursprungsebene das
neueste fertige finale Ergebnis. Ältere Varianten bleiben einzeln auswählbar.
Jedes Einfügen hat eine eigene Undo-Gruppe. Bereits eingefügte Ergebnisse
werden nicht erneut eingefügt. Nach Undo kann das Ergebnis wieder benutzt werden.
Neue Aufträge überschreiben frühere Ergebnisse nicht.

Die Auftragsdateien bleiben gespeichert. Nach Dienstneustart werden fertige
Ergebnisse wiederhergestellt; unterbrochene Aufträge werden als Fehler markiert
und nicht automatisch neu gestartet. Beim Wechsel des Projekts wird dessen
Auftragsliste geladen. Ergebnisse werden nur mit der ursprünglichen Ebene,
Quelle und unverändertem Timing verbunden.

**Dienst**

Speichersparmodus, Originalbild nach Einfügen ausblenden, Korrekturdaten,
Sprachwahl und technische Details. Die originale Kommandozeile lädt das Modell
für jeden KI-Auftrag neu und gibt dessen Grafikspeicher beim Beenden frei.
Der Status zeigt tatsächliche Analysefenster und Laufzeit, keine erfundene
Gesamt-Prozentzahl.

## Import und Grenzen

- Ausgaben liegen in `out_effectcraft/<auftrags-id>/`, einschließlich Log,
  Auftragsbeschreibung und Vorschaubildern. Nicht löschen oder verschieben,
  solange das EffectCraft-Projekt die Dateien referenziert.
- Die Quelldatei wird ohne hineingerenderte EffectCraft-Effekte und
  Transformationen verarbeitet. Beim Einfügen werden Animationen, Effekte und
  Masken der Ebene übernommen. Masken aus EffectCraft wirken damit weiterhin
  als Ebenenmasken; eine Startmaske dient zusätzlich als Hinweis für die KI.
- Das Originalbild wird auf Wunsch ausgeblendet; dessen Ton bleibt aktiv.
  Bei Teilbereichen bleiben vor und nach dem Ausschnitt separate Originalbild-
  Abschnitte ohne zusätzlichen Ton erhalten. Ein Undo macht den ganzen Import
  einschließlich dieser Abschnitte rückgängig.
- EffectCraft 0.16 unterstützt `AVLayer.replaceSource` noch nicht. Deshalb baut
  das Panel dort eine unabhängige Ebene über die Property-API auf.
  3D, Time Remapping, Track Mattes und aktive Layer Styles vorher als Video
  rendern. Zeitbeschnitt benötigt positive Geschwindigkeit ohne Time Remapping.
- Unterstützte Quellen: MOV, MP4, MKV, AVI, WebM, M4V, MXF. Noch keine Precomps
  oder Bildsequenzen als Eingabe. Anamorphe Pixel, Halbbilder, variable Bildraten,
  komplexe Expressions-Abhängigkeiten und HDR/Log-/ACES-Eingabepipelines sind
  nicht umfassend geprüft. EXR-Ausgabe ist linear; daraus folgt keine vollständige
  Farbmanagement-Unterstützung für solche Eingaben.
- Abbrechen wird zwischen Verarbeitungsschritten geprüft. Reagiert ein
  GPU-Schritt nicht innerhalb von 20 Sekunden, wird der Worker samt Kindern
  beendet und beim nächsten Auftrag neu geladen. Teildateien bleiben als
  abgebrochene Ergebnisse sichtbar und werden nicht eingefügt. Große
  Zwischendateien werden nach dem Auftrag entfernt.
- Panel-Schließen beendet keine laufenden Aufträge. Der lokale Dienst bindet
  ausschließlich an `127.0.0.1` und verlangt seinen zufälligen Token.

## Prüfungen

```bash
venv/bin/python -m unittest discover -s integrations/effectcraft -p 'test_*.py' -v
node integrations/effectcraft/test_panel.cjs
```

Die Tests prüfen Validierung, Queue-Reihenfolge, Abbruch, Wiederherstellung,
Mattenberechnung, Maskenrasterung und Panel-Verhalten. Native Prüfungen wurden
zusätzlich in einer getrennten EffectCraft-Testinstanz mit kurzen Testclips
und der echten GPU durchgeführt.

Zusätzlich zur synthetischen Prüfung wurden drei kurze Ausschnitte aus dem
vorhandenen Projektvideo bei 3, 8 und 14 Sekunden in nativer Auflösung geprüft:
Haare, Spitzenärmel, Bewegung, Vordergrunderhalt und entfernter grüner Hintergrund.
Der Identitätstest für die nachträgliche Korrektur ergab exakt gleiche decodierte
MOV-Bilder; geänderte Einstellungen benötigen keinen erneuten Modelllauf.
Ein echtes Projektpaket wurde verschoben, erneut in EffectCraft geöffnet und
anschließend erfolgreich aus den mitgenommenen Korrekturdaten bearbeitet.
