# CorridorKey für EffectCraft

Community-Add-on zur lokalen Greenscreen-Freistellung mit CorridorKey 2.0 auf einer NVIDIA-Grafikkarte. Die Oberfläche unterstützt alle elf Sprachen von EffectCraft 0.16. Georgisch ist als zwölfte Übersetzung für neuere Hosts vorbereitet.

**Version 0.8.0. Linux geprüft; Windows experimentell.**

## Installation

Benötigt werden die EffectCraft-Desktop-App, Python 3.11 oder 3.12, Git sowie `ffmpeg` und `ffprobe` im Suchpfad. Benötigt wird eine NVIDIA-GPU der RTX-30-Serie oder neuer. Der NVIDIA-Treiber muss zur verwendeten PyTorch-Ausgabe mit CUDA 12.8 passen. Geprüft wurde EffectCraft 0.16.0 unter Linux mit Python 3.12 und einer RTX 3080 Laptop GPU mit 16 GB. Die Webversion und macOS-Inferenz werden nicht unterstützt.

Lade dieses Add-on-Repository herunter und entpacke es. Öffne im entpackten Ordner ein Terminal. Unter Linux:

```bash
python3 setup_effectcraft.py --effectcraft "/absoluter/Pfad/zu/EffectCraft.AppImage"
```

Unter Windows in PowerShell:

```powershell
py -3.12 setup_effectcraft.py --effectcraft "C:\Pfad\Zu\EffectCraft.exe"
```

Der Installer lädt den offiziellen CorridorKey-Quellcode unverändert in einer festgelegten Version, richtet eine eigene Python-Umgebung ein und lädt die Modelle. Rechne mit mehreren GB für die Umgebung und rund 5 GB für die Modelle, zusätzlich zu Medien und Korrekturdaten. Lies vorher die [Lizenz](../LICENSE) und den [Lizenzstatus](LICENSING.md).

Aktiviere in EffectCraft **Allow Scripts to Write Files and Access Network**. Speichere dein Projekt und schließe EffectCraft einmal regulär, falls es ohne Steuerverbindung gestartet wurde. Danach unter Linux:

```bash
./integrations/effectcraft/start_bridge.sh --launch
```

Unter Windows:

```powershell
.\venv\Scripts\python.exe integrations\effectcraft\launch.py
```

Der Starter öffnet die App und das verbundene Panel. Er beendet keine laufende EffectCraft-Instanz.

## Benutzung

1. Ein gespeichertes Projekt öffnen und eine entsperrte Videoebene auswählen.
2. Unter Vorschau eine kurze Vorschau ab dem Abspielkopf berechnen.
3. Unter Clip Zeitbereich und Ausgabe wählen, dann Freistellen starten.
4. Das fertige Ergebnis einfügen. Original und Originalton bleiben im Projekt.
5. Kanten und Farbsäume nachträglich korrigieren, sofern Korrekturdaten aufbewahrt wurden.

Die weiteren Funktionen und Einschränkungen stehen in der [Bedienungsanleitung](../integrations/effectcraft/README.md). [Ausführliche Installation](INSTALL.md) und [Fehlerbehebung](TROUBLESHOOTING.md) sind auf Englisch dokumentiert. Technische Protokolle und native Fehlermeldungen bleiben im Original; die Bedien- und Statusmeldungen sind übersetzt.

Unser eigener Wrapper-Code steht unter MIT. Das separat heruntergeladene CorridorKey und die Modelle behalten ihre eigenen Lizenzen und Nutzungsbedingungen. Das Add-on ist unabhängig vom offiziellen kostenpflichtigen CorridorKey-Plugin.

Der Wrapper ruft die originale CorridorKey-Kommandozeile als eigenes Programm auf. Es gibt keine Runtime-Patches und keine Modellimporte in unserem Python-Code. Das Modell wird pro KI-Auftrag neu geladen; nachträgliche Korrekturen aus Bilddaten bleiben möglich. Diese technische Trennung bedeutet keine zugesicherte Ausnahme von Lizenzbedingungen. Siehe [Architektur](WRAPPER_ARCHITECTURE.md) und [Lizenzstatus](LICENSING.md).

## Neue Komfortfunktionen in 0.7

Im Tab **Detailprüfung** lassen sich einzelne Ausgabebilder, Vergrößerung, Prüfhintergrund und der Vorher/Nachher-Trennpunkt einstellen. A/B merkt fertige Ergebnisse; zuerst korrigieren und berechnen lassen, danach die jeweilige Variante merken. Ein Wechsel verändert das Projekt nicht; eingefügt wird weiterhin ausdrücklich.

Der **Masken-Assistent** zeigt das tatsächliche Referenzbild. Die Bildnummer ist nullbasiert und bezieht sich auf die Quelldatei; leer bedeutet den Anfang des verarbeiteten Bereichs einschließlich Vorlauf. „Abspielkopf übernehmen“ rechnet die Timeline-Position um. Eine Bildmaske muss dieselben Pixelmaße haben. Für die grobe Farbauswahl verschiedene Farben des Motivs markieren, zum Beispiel Kleidung, Gesicht, Hände und Haare, und Grün/Blau als Entfernen markieren. Die Punkte erscheinen grün beziehungsweise rot. Die Auswahl vor der Berechnung prüfen und bei Bedarf weitere Punkte ergänzen. Sie wird automatisch als grobe Startmaske verwendet und ist keine semantische KI-Freistellung.

Ein Referenzbild nach dem Bereichsanfang benötigt eine passende Startmaske und zwei KI-Durchläufe. Der Rückwärtslauf nutzt temporäre Bilddateien statt eines unbeschränkten RAM-Puffers. Das kostet zusätzliche Ladezeit und Speicherplatz. Ein Maskenvideo bleibt an den ursprünglichen Zeitablauf gebunden; dafür die Referenz automatisch lassen. Ebenenmasken werden am Referenzbild als Momentaufnahme kombiniert; animierte Masken werden nicht über die gesamte Aufnahme exportiert.

Unter **Clip** lassen sich Grün, Blau oder keine zusätzliche Saumkorrektur wählen. Unter **Kanten** können deckender Kern und weiche Randabdeckung getrennt korrigiert werden. Im Tab **Service** bleibt das Zeitfenster standardmäßig automatisch. Manuelle Fenster sind keine direkte Kopie des Vorwärts-/Rückwärts-Reglers aus dem offiziellen Plugin und garantieren keine bestimmte Qualitätsverbesserung. GPU-Werte beziehen sich auf den gesamten Speicherverbrauch aller Anwendungen.

Nach einem Update laufende Aufträge beenden und den alten lokalen Dienst schließen, dann den Installer erneut ausführen und über den gemeinsamen Starter öffnen. Das neue Panel verlangt einen Dienst mit Unterstützung für die neuen Funktionen.

## Freistellung direkt weiterbearbeiten

Unter **Kanten** ist „Eingefügtes Ergebnis direkt aktualisieren“ standardmäßig aktiv. Das erste Ergebnis wird wie bisher eingefügt. Danach Kanten oder Farbsäume ändern und „Korrektur ohne neue KI ausgeben“ wählen: Nach der Berechnung aktualisiert sich die vorhandene Freistellung automatisch. Es entsteht keine zusätzliche Ebene. Ebenenname, Animationen, Effekte, Masken und Timing bleiben bestehen. Rückgängig macht die Aktualisierung rückgängig; erneutes Einfügen wendet dieselbe fertige Korrektur wieder an.

Wurde die Ergebnisebene gesperrt, ihre Quelle ausgetauscht oder ihr Medium mehrfach verwendet, überschreibt das Plugin sie nicht. Auch ein anderer verarbeiteter Zeitbereich benötigt eine neue Ebene. Dafür die direkte Aktualisierung ausschalten. Das Originalmaterial und die fertigen Dateien werden nicht überschrieben.
