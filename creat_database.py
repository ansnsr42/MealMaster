import sqlite3
import os

# Erstelle das Verzeichnis für die Datenbanken, falls es nicht existiert
os.makedirs("database", exist_ok=True)


def create_recipes_db():
    # Verbindung zur Datenbank für die Seite herstellen
    conn = sqlite3.connect("database/mealmaster.db")
    cursor = conn.cursor()

    # Tabellen für Rezepte und Zutaten anlegen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT(30) NOT NULL,
            ingredients INTEGER,
            quantity TEXT,
            instructions TEXT(400),
            FOREIGN KEY (ingredients) REFERENCES ingredients(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchasinglist (
            ingredients INTEGER,
            quantity TEXT,
            FOREIGN KEY (ingredients) REFERENCES ingredients(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS household (
            ingredients INTEGER,
            FOREIGN KEY (ingredients) REFERENCES ingredients(id)
        )
    ''')

    conn.commit()
    conn.close()


def create_users_db():
    # Verbindung zur Datenbank für die Benutzeranmeldung herstellen
    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    # Tabelle für Benutzer erstellen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            register_date TEXT,
            last_login TEXT,
            ip_address TEXT
        )
    ''')

    conn.commit()
    conn.close()


# Datenbanken und Tabellen erstellen
create_recipes_db()
create_users_db()

print("Datenbanken und Tabellen wurden erfolgreich erstellt.")
