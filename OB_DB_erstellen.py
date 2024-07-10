#!/usr/bin/python3
import sqlite3


datenbankname = "Lagerbank2024.db"

def create_database(datenbankname):
    # Verbindung zur Datenbank herstellen
    connection = sqlite3.connect(datenbankname)
    cursor = connection.cursor()

    # Tabelle "Produkte" erstellen
    cursor.execute('''CREATE TABLE IF NOT EXISTS Produkt (
        P_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Beschreibung VARCHAR(100),
        Preis DECIMAL(10, 2),
        Anzahl_verkauft INT
        
    );
    
    ''')
    cursor.connection.commit()
    # Tabelle "Teilnehmer" erstellen
    cursor.execute('''CREATE TABLE IF NOT EXISTS Teilnehmer (
        T_ID INTEGER PRIMARY KEY AUTOINCREMENT, 
        Name VARCHAR(50),
        Checkout BOOLEAN DEFAULT 0
    );
    
    ''')
    cursor.connection.commit()
    # Tabelle "Konto" erstellen
    cursor.execute('''CREATE TABLE IF NOT EXISTS Konto (
        K_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Einzahlung DECIMAL(10, 2),
        Kontostand DECIMAL(10, 2),
        Endkontostand DECIMAL(10, 2),
        Eröffnungsdatum DATE,
        T_ID INT,
        FOREIGN KEY (T_ID) REFERENCES Teilnehmer(T_ID)
    );
    
    ''')
    cursor.connection.commit()
    # Tabelle "Transaktion" erstellen
    cursor.execute('''CREATE TABLE IF NOT EXISTS Transaktion (
        TRANS_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        K_ID INT,
        P_ID INT,  -- Spalte für den Fremdschlüssel zur Produkt-Tabelle
        Typ VARCHAR(50),
        Menge INT,
        Datum DATE,
        FOREIGN KEY (K_ID) REFERENCES Konto(K_ID),
        FOREIGN KEY (P_ID) REFERENCES Produkt(P_ID)  -- Fremdschlüsselbeziehung zu Produkt
    );
    ''')
    cursor.connection.commit()
    
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Einstellungen (
        Name TEXT PRIMARY KEY,
        Wert TEXT NOT NULL
    );
    ''')
    cursor.connection.commit()
    

    cursor.execute('''INSERT INTO Einstellungen (Name, Wert) SELECT 'ErsterTag', '01/01/2024' WHERE NOT EXISTS (SELECT 1 FROM Einstellungen WHERE Name = 'ErsterTag')''')
    cursor.connection.commit()
    print("First Day wurden erfolgreich erstellt!")
    print("01/01/2024")
    
    cursor.execute('''INSERT INTO Einstellungen (Name, Wert) SELECT 'LetzterTag', '10/01/2024' WHERE NOT EXISTS (SELECT 1 FROM Einstellungen WHERE Name = 'LetzterTag')''')
    cursor.connection.commit()
    print("Last Day wurden erfolgreich erstellt!")
    print("10/01/2024")
    
    cursor.execute('''INSERT INTO Produkt (Beschreibung, Preis, Anzahl_verkauft) SELECT 'Wasser', '0.50', '0' WHERE NOT EXISTS (SELECT 1 FROM Produkt WHERE Beschreibung = 'Wasser')''')
    cursor.connection.commit()
    print("Produkt wurde erfolgreich erstellt!")
    print("Wasser")
    # Verbindung schließen
    connection.close()
    print(f'Datenbank "{datenbankname}" wurde erfolgreich erstellt!')

create_database(datenbankname)

