# Lagerbank_oB

# Anleitung zur Installation von Python und Bibliotheken

## Python Installation

### Windows

1. **Python herunterladen und installieren:**
   - Besuche die [offizielle Python-Website](https://www.python.org/downloads/) und lade die neueste Version von Python für Windows herunter (z.B. Python 3.9.x).
   - Führe das Installationsprogramm aus und aktiviere das Kontrollkästchen "Add Python to PATH".

2. **Überprüfung der Installation:**
   - Öffne die Eingabeaufforderung (cmd) und führe `python --version` aus, um sicherzustellen, dass Python erfolgreich installiert wurde.

### Linux Mint

1. **Python über Paketverwaltung installieren:**
   - Öffne ein Terminal und gib die folgenden Befehle ein:
     ```
     sudo apt update
     sudo apt install python3
     ```

2. **Überprüfung der Installation:**
   - Gib im Terminal `python3 --version` ein, um sicherzustellen, dass Python erfolgreich installiert wurde.

## Externe Bibliotheken installieren

1. **Pip installieren:**
   - Überprüfe, ob Pip bereits installiert ist, indem du `pip --version` in der Eingabeaufforderung oder im Terminal ausführst.
   - Falls nicht vorhanden:
     - **Windows**: Führe `python -m ensurepip --upgrade` aus, um sicherzustellen, dass Pip installiert ist.
     - **Linux Mint**: Installiere Pip mit dem Befehl `sudo apt install python3-pip`.

2. **Bibliotheken installieren:**
   - Öffne die Eingabeaufforderung (cmd) oder das Terminal und führe folgenden Befehl aus:
     ```
     pip install numpy pandas Flask Flask-Cors cryptography
     ```

## Benutzerdefinierte Module und Konfigurationen

1. **Benutzerdefinierte Module:**
   - Stelle sicher, dass deine benutzerdefinierten Module wie `database` und `config` im gleichen Verzeichnis wie deine Hauptanwendungsdatei (`app.py` oder ähnlich) liegen oder im Python-Pfad verfügbar sind.


## Programm ausführen
1. **Gehen Sie ins Terminal / CMD**
    - Gehen Sie ins Terminal / CMD
    - geben sie folgenden befehl aus
    ```
    python3 app.py 
    ```

