#!/usr/bin/env python3
import json
import os
from datetime import datetime

# Wenn du eine eigene Config-Verwaltung hast, kannst du sie hier importieren
# from .config_manager import ConfigManager

class Mealmaster_mgr:
    """
    Klasse zum Verwalten der MealMaster-Funktionen.
    Lädt z.B. Konfiguration aus einer JSON-Datei und
    kann weitere nützliche Methoden enthalten.
    """
    def __init__(self, config_file: str = "config/settings.json"):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self):
        """ Lädt die Konfiguration aus config_file. """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Fehler beim Laden der JSON-Datei: {e}")
                self.config = {}
        else:
            print(f"Konfigurationsdatei {self.config_file} nicht gefunden.")
            self.config = {}

    def get_config(self, key: str, default=None):
        """
        Gibt einen bestimmten Wert aus der Konfiguration zurück.
        Beispiel: database_uri = manager.get_config('database_uri')
        """
        return self.config.get(key, default)

    def log_login(self, username: str):
        """
        Beispielmethode, um z.B. ein Login-Ereignis zu protokollieren.
        Hier könntest du weitere Funktionen implementieren.
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] User {username} logged in.")
        # Je nach Bedarf könntest du diese Info auch in eine Datei schreiben,
        # an ein Logging-System senden oder in der Datenbank speichern.
