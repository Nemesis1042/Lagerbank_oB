# Standard-Bibliotheken
import os   # Für Dateioperationen
import time # Für Zeitverzögerungen
import sqlite3  # Für Datenbankzugriff
import threading    # Für Multithreading
from datetime import datetime # Für Zeitstempel

# Externe Bibliotheken
import numpy as np  #
import pandas as pd     # Für Datenverarbeitung und -analyse
#import cv2  # Für Kamera- und Bildverarbeitungsfunktionen
#import pyzbar # Für Barcode-Scanning

#import pygame  # Für Soundeffekte
import shutil   # Für Dateioperationen
from crypt import methods   # Für Verschlüsselungsalgorithmen
from typing import List, Tuple, Callable    # Für Typenangaben

# Flask und zugehörige Erweiterungen
from flask import Flask, Response, render_template, request, redirect, url_for, flash, jsonify  # Für Webanwendungen
# Benutzerdefinierte Module
from database import Database, get_db_connection    # Für Datenbankzugriff

# Konfigurationen
from config import db_backup    # Für Backup-Konfiguration

# Initialisierung der Flask-App
app = Flask(__name__)
os.system('python3 OB_DB_erstellen.py')
app.config.from_object('config.Config')

# Funktionen
def get_users_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Name FROM Teilnehmer ORDER BY Name")
    users = cursor.fetchall()
    conn.close()
    return [user['Name'] for user in users]

def get_products_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Beschreibung FROM Produkt")
    products = cursor.fetchall()
    conn.close()
    return [product['Beschreibung'] for product in products]

def get_db():
    return sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].split('///')[-1])

def submit_purchase(user, product, quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Teilnehmer-ID und Kontostand abrufen
        cursor.execute("SELECT T_ID FROM Teilnehmer WHERE Name = ?", (user,))
        user_row = cursor.fetchone()
        if user_row is None:
            print("Teilnehmer nicht gefunden!")
            return False
        T_ID = user_row['T_ID']
        
        cursor.execute("SELECT Kontostand FROM Konto WHERE T_ID = ?", (T_ID,))
        account_row = cursor.fetchone()
        if account_row is None:
            print("Konto nicht gefunden!")
            return False
        Kontostand = account_row['Kontostand']
        
        # Produktpreis und Produkt-ID abrufen
        cursor.execute("SELECT P_ID, Preis FROM Produkt WHERE Beschreibung = ?", (product,))
        product_row = cursor.fetchone()
        if product_row is None:
            print("Produkt nicht gefunden!")
            return False
        P_ID = product_row['P_ID']
        Preis = product_row['Preis']
        
        # Prüfen, ob genug Guthaben vorhanden ist
        total_price = quantity * Preis
        if total_price > Kontostand:
            print("Nicht genügend Guthaben!")
            return False
        
        # Transaktion einfügen
        cursor.execute("INSERT INTO Transaktion (K_ID, P_ID, Typ, Menge, Datum) VALUES ((SELECT K_ID FROM Konto WHERE T_ID = ?), ?, ?, ?, ?)",
                       (T_ID, P_ID, 'Kauf', quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Konto- und Produkt-Updates durchführen
        cursor.execute("UPDATE Konto SET Kontostand = Kontostand - ? WHERE T_ID = ?", (total_price, T_ID))
        cursor.execute("UPDATE Produkt SET Anzahl_verkauft = Anzahl_verkauft + ? WHERE P_ID = ?", (quantity, P_ID))
        
        # Änderungen speichern
        conn.commit()
        print("Transaktion hinzugefügt!")
        return True
    except Exception as e:
        print(f"Fehler beim Hinzufügen der Transaktion: {e}")
        return False
    finally:
        conn.close()

'''
# def barcode_scanner():
#     cap = cv2.VideoCapture(0)
#     barcode_value = None
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             return None

#         decoded_objects = pyzbar.decode(frame)
#         if decoded_objects:
#             barcode_value = decoded_objects[0].data.decode("utf-8")
#             if barcode_value == "Brake":
#                 return None
#             return barcode_value
#             # End of Selection
'''
    
def add_transaction(db, TN_Barcode, P_Barcode, menge):
    TN_ID = db.execute_select("SELECT T_ID FROM Teilnehmer WHERE TN_Barcode = ?", (TN_Barcode,))
    if not TN_ID:
        raise ValueError("TN_Barcode nicht gefunden!")
    TN_ID = TN_ID[0][0]

    P_ID = db.execute_select("SELECT P_ID FROM Produkt WHERE P_Barcode = ?", (P_Barcode,))
    if not P_ID:
        P_ID = db.execute_select("SELECT P_ID FROM Produkt_plus WHERE P_Barcode = ?", (P_Barcode,))
        if not P_ID:
            raise ValueError("P_Barcode nicht gefunden!")
    P_ID = P_ID[0][0]

    db.execute_update("INSERT INTO Transaktion (K_ID, P_ID, Typ, Menge, Datum) VALUES ((SELECT K_ID FROM Konto WHERE T_ID = ?), ?, 'Kauf', ?,datetime('now', 'localtime'))", (TN_ID, P_ID, menge))

def fetch_users(db: Database) -> List[str]:
    users = [user[0] for user in db.execute_select("SELECT Name FROM Teilnehmer ORDER BY Name")]  # Ruft Benutzernamen aus der Datenbank ab
    return users

def fetch_products(db: Database) -> List[str]:
    products = [product[0] for product in db.execute_select("SELECT Beschreibung FROM Produkt ORDER BY Preis")]  # Ruft Produktbeschreibungen aus der Datenbank ab
    return products
'''
def fetch_p_barcode(db: Database) -> str:
    p_barcode = db.execute_select("SELECT P_Barcode FROM Produkt ") # Ruft den Produktbarcode aus der Datenbank ab
    return p_barcode

def fetch_p_barcode_plus(db: Database) -> str:
    p_barcode_plus = db.execute_select("SELECT Barcode FROM Produkt_Barcode ") # Ruft den Produktbarcode aus der Datenbank ab
    return p_barcode_plus

def fetch_tn_barcode(db: Database) -> str:
    tn_barcode = db.execute_select("SELECT TN_Barcode FROM Teilnehmer ")  # Ruft den Benutzerbarcode aus der Datenbank ab
    return tn_barcode
'''
def fetch_transactions(db: Database, user_id: int) -> List[Tuple]:
    transactions = db.execute_select("SELECT * FROM Transaktion WHERE K_ID = ? ORDER BY Datum DESC", (user_id,))  # Ruft Transaktionen für einen bestimmten Benutzer ab
    return transactions


@app.route('/update_product_dropdowns', methods=['GET'])
def update_product_dropdowns_route():
    db = Database()
    products = fetch_products(db)  # Ruft Produktbeschreibungen ab
    return jsonify({'products': products})

@app.route('/')
def index():
    return render_template('index.html')

'''
@app.route('/scan', methods=['POST'])
'''
'''
def scan_barcode():
    cap = cv2.VideoCapture(0)
    barcode_value = None
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.release()
            cv2.destroyAllWindows()
            return jsonify({"error": "Kamerafehler!"}), 500
        decoded_objects = pyzbar.decode(frame)
        if decoded_objects:
            barcode_value = decoded_objects[0].data.decode("utf-8")
            if barcode_value == "Brake":
                cap.release()
                cv2.destroyAllWindows()
                return jsonify({"error": "Barcode Brake erkannt"}), 400
            cap.release()
            cv2.destroyAllWindows()
            return jsonify({"barcode": barcode_value})
        cv2.imshow("Barcode Scanner", frame)
        key = cv2.waitKey(50)  # 50 ms delay
        if key & 0xFF == ord('q') or key & 0xFF == 27:  # 27 is the ASCII code for ESC
            cap.release()
            cv2.destroyAllWindows()
            return jsonify({"error": "Scan abgebrochen"}), 400
'''

@app.route('/add_buy', methods=['GET', 'POST'])
def add_buy():
    if request.method == 'POST':
        user = request.form['user']
        product = request.form['product']
        quantity = int(request.form['quantity'])
        success = submit_purchase(user, product, quantity)
        if success:
            #play_beep()
            print('Kauf erfolgreich hinzugefügt', 'success')
        else:
            print('Fehler beim Hinzufügen des Kaufs', 'danger')
        return redirect(url_for('add_buy'))
    users = get_users_from_db()
    products = get_products_from_db()
    return render_template('add_buy.html', users=users, products=products)

@app.route('/submit_buy', methods=['POST'])
def submit_buy():
    user = request.form['user']
    product = request.form['product']
    quantity = int(request.form['quantity'])
    success = submit_purchase(user, product, quantity)
    if success:
        #play_beep()
        print('Purchase submitted successfully', 'success')
    else:
        print('Error submitting purchase', 'danger')
    return redirect(url_for('add_buy'))

@app.route('/watch')
def watch():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Produkt';")
    if not cursor.fetchone():
        conn.close()
        return "Die Tabelle 'Produkt' existiert nicht in der Datenbank.", 404
    produkt_infos = cursor.execute("SELECT P_ID, Beschreibung, ROUND(Preis, 2) as Preis FROM Produkt").fetchall()
    produkt_summen = ", ".join([f"SUM(CASE WHEN Transaktion.P_ID = {pid} THEN Transaktion.Menge ELSE 0 END) AS '{desc} ({preis:.2f}€)'" for pid, desc, preis in produkt_infos])
    sql_query = f"""
        SELECT 
            Teilnehmer.Name,
            Konto.Einzahlung AS Einzahlung_€,
            printf('%04.2f', ROUND(Konto.Kontostand, 2)) AS Kontostand_€,
            printf('%04.2f', ROUND(Konto.Endkontostand, 2)) AS Endkontostand_€,
            {produkt_summen}
        FROM Teilnehmer 
        JOIN Konto ON Teilnehmer.T_ID = Konto.T_ID
        LEFT JOIN Transaktion ON Konto.K_ID = Transaktion.K_ID
        GROUP BY Teilnehmer.T_ID, Teilnehmer.Name, Konto.Einzahlung, ROUND(Konto.Kontostand, 2)
        ORDER BY Teilnehmer.Name;
    """
    result = cursor.execute(sql_query).fetchall()
    conn.close()
    df = pd.DataFrame(result, columns=[desc[0] for desc in cursor.description])
    return render_template('watch.html', tables=df.to_html(classes='data', header="true", index=False))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == '1':
            return redirect(url_for('admin'))
        else:
            flash('Invalid password, try again.', 'danger')
    return render_template('login.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        user = request.form['user']
        amount = float(request.form['amount'])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Name FROM Teilnehmer WHERE Name = ?", (user,))
        if cur.fetchone():
            print('Benutzer existiert bereits!', 'danger')
        else:
            cur.execute("INSERT INTO Teilnehmer (Name) VALUES (?)", (user,))
            t_id = cur.execute("SELECT T_ID FROM Teilnehmer WHERE Name = ?", (user,)).fetchone()[0]
            cur.execute("INSERT INTO Konto (Einzahlung, Kontostand, Eröffnungsdatum, T_ID) VALUES (?, ?, ?, ?)",
                        (amount, amount, datetime.now().strftime("%d.%m.%Y"), t_id))
            cur.execute("INSERT INTO Transaktion (K_ID, P_ID, Typ, Menge, Datum) VALUES (?, ?, ?, ?, ?)", (t_id, 0, 'Einzahlung', amount, datetime.now().strftime("%d.%m.%Y %H:%M:%S")))
            conn.commit()
            print('Benutzer erfolgreich hinzugefügt.', 'success')
        conn.close()
        return redirect(url_for('admin'))
    return render_template('add_user.html')

@app.route('/add_fund', methods=['GET', 'POST'])
def add_fund():
    if request.method == 'POST':
        user = request.form['user']
        amount = float(request.form['amount'])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Name FROM Teilnehmer WHERE Name = ?", (user,))
        if not cur.fetchone():
            print('Benutzer nicht gefunden!', 'danger')
        else:
            
            user_balance = cur.execute("SELECT Kontostand FROM Konto JOIN Teilnehmer ON Konto.T_ID = Teilnehmer.T_ID WHERE Teilnehmer.Name = ?", (user,)).fetchone()
            if user_balance:
                new_balance = user_balance['Kontostand'] + amount
                cur.execute("UPDATE Konto SET Kontostand = ? WHERE T_ID = (SELECT T_ID FROM Teilnehmer WHERE Name = ?)", (new_balance, user))
                cur.execute("INSERT INTO Transaktion (K_ID, P_ID, Typ, Menge, Datum) VALUES ((SELECT T_ID FROM Teilnehmer WHERE Name = ?), 0, 'Einzahlung', ?, ?)", (user, amount, datetime.now().strftime("%d.%m.%Y %H:%M:%S")))
                conn.commit()
                print(f'{amount} € erfolgreich hinzugefügt.', 'success')
            else:
                print('Benutzer hat kein Kontoguthaben!', 'danger')
        conn.close()
        return redirect(url_for('admin'))
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Name FROM Teilnehmer")
        users = [row[0] for row in cur.fetchall()]
        conn.close()
        return render_template('add_fund.html', users=users)

@app.route('/withdraw_fund', methods=['GET', 'POST'])
def withdraw_fund():
    if request.method == 'POST':
        user = request.form['user']
        amount = float(request.form['amount'])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Name FROM Teilnehmer WHERE Name = ?", (user,))
        if not cur.fetchone():
            print('Benutzer nicht gefunden!', 'danger')
        else:
            current_balance = cur.execute("SELECT Kontostand FROM Konto JOIN Teilnehmer ON Konto.T_ID = Teilnehmer.T_ID WHERE Teilnehmer.Name = ?", (user,)).fetchone()
            current_balance = current_balance['Kontostand'] if current_balance else 0
            user_balance = cur.execute("SELECT Kontostand FROM Konto JOIN Teilnehmer ON Konto.T_ID = Teilnehmer.T_ID WHERE Teilnehmer.Name = ?", (user,)).fetchone()
            if user_balance:
                if amount > user_balance['Kontostand']:
                    print('Unzureichendes Guthaben!', 'danger')
                else:
                    new_balance = user_balance['Kontostand'] - amount
                    cur.execute("UPDATE Konto SET Kontostand = ? WHERE T_ID = (SELECT T_ID FROM Teilnehmer WHERE Name = ?)", (new_balance, user))
                    cur.execute("INSERT INTO Transaktion (K_ID, P_ID, Typ, Menge, Datum) VALUES ((SELECT T_ID FROM Teilnehmer WHERE Name = ?), 0, 'Auszahlung', ?, ?)", (user, amount, datetime.now().strftime("%d.%m.%Y %H:%M:%S")))
                    conn.commit()
                    print(f'{amount} € erfolgreich abgehoben.', 'success')
            else:
                print('Benutzer hat kein Kontoguthaben!', 'danger')
        conn.close()
        return redirect(url_for('admin'))
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Name FROM Teilnehmer")
        users = [row[0] for row in cur.fetchall()]
        conn.close()
        return render_template('withdraw_fund.html', users=users)

@app.route('/edit_user', methods=['GET', 'POST'])
def edit_user():
    if request.method == 'POST':
        selected_user = request.form.get('selected_user')
        action = request.form.get('action')
        conn = get_db_connection()
        cur = conn.cursor()
        if action == 'update':
            new_name = request.form.get('new_name')
            if not selected_user or not new_name:
                print('Bitte füllen Sie alle Felder aus.', 'danger')
                return redirect(url_for('edit_user'))
            try:
                cur.execute("UPDATE Teilnehmer SET Name = ? WHERE Name = ?", (new_name, selected_user))
                conn.commit()
                print('Benutzername erfolgreich aktualisiert.', 'success')
            except Exception as e:
                print(f'Fehler beim Aktualisieren des Benutzernamens: {e}', 'danger')
        elif action == 'delete':
            if not selected_user:
                print('Bitte wählen Sie einen Benutzer aus.', 'danger')
                return redirect(url_for('edit_user'))
            try:
                cur.execute("DELETE FROM Konto WHERE T_ID = (SELECT T_ID FROM Teilnehmer WHERE Name = ?)", (selected_user,))
                cur.execute("DELETE FROM Teilnehmer WHERE Name = ?", (selected_user,))
                conn.commit()
                print('Benutzer erfolgreich gelöscht.', 'success')
            except Exception as e:
                print(f'Fehler beim Löschen des Benutzers: {e}', 'danger')
        conn.close()
        return redirect(url_for('edit_user'))
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Name FROM Teilnehmer")
        users = [row[0] for row in cur.fetchall()]
        conn.close()
        return render_template('edit_user.html', users=users)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product = request.form['product']
        price = float(request.form['price'])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Beschreibung FROM Produkt WHERE Beschreibung = ?", (product,))
        if cur.fetchone():
            print('Produkt existiert bereits!', 'danger')
        else:
            cur.execute("INSERT INTO Produkt (Beschreibung, Preis, Anzahl_verkauft) VALUES (?, ?, 0)", (product, price))
            conn.commit()
            print('Produkt erfolgreich hinzugefügt.', 'success')
        conn.close()
        return redirect(url_for('admin'))
    return render_template('add_product.html')

@app.route('/edit_product_prices', methods=['GET', 'POST'])
def edit_product_prices():
    if request.method == 'POST':
        selected_product = request.form.get('selected_product')
        action = request.form.get('action')
        if action == 'update':
            new_price_str = request.form.get('new_price')
            if new_price_str.strip():
                try:
                    new_price = float(new_price_str)
                except ValueError:
                    print('Bitte geben Sie einen gültigen Preis ein.', 'danger')
                    return redirect(url_for('edit_product_prices'))
            else:
                new_price = None
            if not selected_product:
                print('Bitte wählen Sie ein Produkt aus.', 'danger')
                return redirect(url_for('edit_product_prices'))
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                if new_price is not None:
                    cur.execute("UPDATE Produkt SET Preis = ? WHERE Beschreibung = ?", (new_price, selected_product))
                    conn.commit()
                    print('Produktpreis erfolgreich aktualisiert.', 'success')
            except Exception as e:
                print(f'Fehler: {e}', 'danger')
            finally:
                conn.close()
        elif action == 'delete':
            if not selected_product:
                print('Bitte wählen Sie ein Produkt aus.', 'danger')
                return redirect(url_for('edit_product_prices'))
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("UPDATE Produkt SET Preis = 0.00 WHERE Beschreibung = ?", (selected_product,))
                conn.commit()
                cur.execute("DELETE FROM Produkt WHERE Beschreibung = ?", (selected_product,))
                conn.commit()
                print('Produkt erfolgreich gelöscht.', 'success')
            except Exception as e:
                print(f'Fehler: {e}', 'danger')
            finally:
                conn.close()
        else:
            print('Ungültige Aktion.', 'danger')
            return redirect(url_for('edit_product_prices'))
        return redirect(url_for('admin'))
    else:
        products = get_products_from_db()
        return render_template('edit_product_prices.html', products=products)

@app.route('/checkout_tn')
def checkout_tn():
    with Database() as db:
        users = db.execute_select("SELECT Name FROM Teilnehmer ORDER BY Name")
    return render_template('TN-Abfrage.html', users=[user[0] for user in users])

@app.route('/checkout', methods=['POST'])
def checkout():
    benutzer_id = request.form['user']
    if not benutzer_id:
        print("Bitte wählen Sie einen Teilnehmer aus.", 'danger')
        return redirect(url_for('index'))
    with Database() as db:
        users = db.execute_select("SELECT Name FROM Teilnehmer ORDER BY Name")
        if benutzer_id not in [user[0] for user in users]:
            print("Der ausgewählte Teilnehmer existiert nicht.", 'danger')
            return redirect(url_for('index'))
        kontostand = db.execute_select("SELECT Kontostand FROM Konto WHERE T_ID = (SELECT T_ID FROM Teilnehmer WHERE Name = ?)", (benutzer_id,))
        geldwerte = kontostand_in_geld(kontostand)
        if geldwerte is None:
            geldwerte = [0] * 11
        return render_template('checkout_c.html', benutzer_id=benutzer_id, kontostand=kontostand[0][0] if kontostand else 0, geldwerte=geldwerte)

def kontostand_in_geld(kontostand):
    if kontostand:
        kontostand_value = kontostand[0][0]
        zwischenstand = round(kontostand_value, 2)
    else:
        kontostand_value = 0
        zwischenstand = 0
    denominations = [20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
    counts = []
    for denom in denominations:
        count = zwischenstand // denom
        counts.append(count)
        zwischenstand -= count * denom
    return counts

@app.route('/confirm_checkout', methods=['POST'])
def confirm_checkout():
    benutzer_id = request.form['user']
    with Database() as db:
        db.execute_update("UPDATE Konto SET Kontostand = 0 WHERE T_ID = (SELECT T_ID FROM Teilnehmer WHERE Name = ?)", (benutzer_id,))
        db.execute_update("UPDATE Teilnehmer SET Checkout = 1 WHERE Name = ?", (benutzer_id,))
    print("Checkout abgeschlossen.", 'success')
    return redirect(url_for('index'))

@app.route('/kaufstatistik')
def create_kaufstatistik_tab():
    try:
        with Database() as db:
            sql_query = '''SELECT Produkt.Beschreibung, SUM(Transaktion.Menge) AS Anzahl_verkauft
                           FROM Produkt
                           JOIN Transaktion ON Produkt.P_ID = Transaktion.P_ID
                           GROUP BY Produkt.Beschreibung
                           ORDER BY Anzahl_verkauft DESC;'''
            result = db.execute_select(sql_query)
            df = pd.DataFrame(result, columns=[desc[0] for desc in db.cursor.description])
            data = df.to_dict(orient='records')
        return render_template('kaufstatistik.html', data=data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/geld_aufteilen')
def geld_aufteilen():
    conn = get_db_connection()
    kontos = conn.execute("SELECT K_ID, Kontostand FROM Konto").fetchall()
    conn.close()

    denominations = [20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
    counts = {denom: 0 for denom in denominations}

    for konto in kontos:
        kontostand = konto['Kontostand']
        zwischenstand = kontostand  # Keine Rundung auf 3 Dezimalstellen
        for denom in denominations:
            count = int(zwischenstand // denom)
            counts[denom] += count
            zwischenstand -= count * denom
            # Optional: Rundung hier, falls gewünscht, aber mit größerer Präzision
            zwischenstand = round(zwischenstand, 10)  # Erhöhte Präzision

    sume = sum(denom * count for denom, count in counts.items())
    gesamt_kontostand = sum(konto['Kontostand'] for konto in kontos)
    results = {"counts": counts, "sume": sume, "gesamt_kontostand": gesamt_kontostand}
   
    print(sume)
    print(gesamt_kontostand)
    print(results)
    return render_template('results.html', results=results)

def create_backup(source_file, backup_directory):
    try:
        # Prüfen, ob die Quelldatei existiert
        if not os.path.isfile(source_file):
            raise FileNotFoundError(f"Die Quelldatei {source_file} wurde nicht gefunden.")

        # Sicherstellen, dass das Backup-Verzeichnis existiert
        if not os.path.exists(backup_directory):
            os.makedirs(backup_directory)

        # Name der Backup-Datei generieren
        base_name = os.path.basename(source_file)
        backup_file = os.path.join(backup_directory, "backup_" + base_name)

        # Datei kopieren
        shutil.copy2(source_file, backup_file)

        print(f"Backup erfolgreich erstellt: {backup_file}")
    except Exception as e:
        print(f"Fehler beim Erstellen des Backups: {e}")

@app.route('/backup', methods=['GET', 'POST'])
def backup_database():
    if request.method == 'POST':
        # Neue Werte aus dem Formular holen
        backup_directory = request.form['backup_directory']

        # Konfigurationswert aktualisieren
        app.config['BACKUP_DIRECTORY'] = backup_directory
        
        #Backup durchführen
        create_backup(db_backup.source_file, db_backup.backup_directory)
        
        return redirect(url_for('backup_database'))
    return render_template('backup.html', backup_directory=db_backup.backup_directory)

@app.route('/delete_database', methods=['GET', 'POST'])
def delete_database():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'IchWillDieDatenbankLöschen':
            try:
                conn = get_db_connection()
                with open('database_backup.sql', 'w') as f:
                    for line in conn.iterdump():
                        f.write('%s\n' % line)
                print('Datenbank erfolgreich gesichert.', 'success')
                conn.execute("DROP TABLE IF EXISTS Teilnehmer")
                conn.execute("DROP TABLE IF EXISTS Konto")
                conn.execute("DROP TABLE IF EXISTS Produkt")
                conn.commit()
                print('Datenbank erfolgreich gelöscht.', 'success')
            except Exception as e:
                print(f'Fehler beim Löschen der Datenbank: {e}', 'danger')
            return redirect(url_for('delete_database'))
        else:
            print('Ungültiges Passwort!', 'danger')
    return render_template('delete_database.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            first_day = request.form['formatted_first_day']
            last_day = request.form['formatted_last_day']
            
            # Check if dates are not empty
            if first_day and last_day:
                conn.execute("UPDATE Einstellungen SET Wert = ? WHERE Name = 'ErsterTag'", (first_day,))
                conn.execute("UPDATE Einstellungen SET Wert = ? WHERE Name = 'LetzterTag'", (last_day,))
                conn.commit()
                
                print("Erfolg: Einstellungen erfolgreich aktualisiert.")
                return redirect(url_for('settings'))  # Redirect to GET /settings after POST
            else:
                print("Fehler: Eingabe für Erster Tag oder Letzter Tag ist leer.")
                return redirect(url_for('settings'))
            
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Einstellungen: {e}")
            return redirect(url_for('settings'))
    
    # Handle GET request to populate form fields
    first_day_row = conn.execute("SELECT Wert FROM Einstellungen WHERE Name = 'ErsterTag'").fetchone()
    last_day_row = conn.execute("SELECT Wert FROM Einstellungen WHERE Name = 'LetzterTag'").fetchone()
    
    conn.close()
    
    first_day = first_day_row['Wert'] if first_day_row else ''
    last_day = last_day_row['Wert'] if last_day_row else ''
    
    # Calculate lager_dauer only if both dates are not empty
    if first_day and last_day:
        lager_dauer = (datetime.strptime(last_day, '%d/%m/%Y') - datetime.strptime(first_day, '%d/%m/%Y')).days
    else:
        lager_dauer = None
    
    heute = datetime.now().strftime('%d/%m/%Y')
    
    return render_template('settings.html', first_day=first_day, lager_dauer=lager_dauer, last_day=last_day, today=heute)

# Funktion zur Transaktionserstellung
def create_transaction(käufer_name, produkt_barcode, menge):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
       

        # Käufer-ID abrufen oder neu anlegen, falls nicht vorhanden
        cursor.execute('SELECT T_ID FROM Teilnehmer WHERE Name=?', (käufer_name,))
        row = cursor.fetchone()
        if row:
            käufer_id = row[0]
        else:
            cursor.execute('INSERT INTO Teilnehmer (Name, TN_Barcode) VALUES (?, ?)', (käufer_name, käufer_name))
            käufer_id = cursor.lastrowid

        # Produkt-ID abrufen
        cursor.execute('SELECT P_ID FROM Produkt WHERE P_Barcode=?', (produkt_barcode,))
        row = cursor.fetchone()
        if row:
            produkt_id = row[0]
        else:
            return False, f'Produkt mit Barcode "{produkt_barcode}" nicht gefunden.'

        # Überprüfen, ob bereits eine Transaktion für dieses Produkt existiert
        cursor.execute('SELECT TRANS_ID FROM Transaktion WHERE K_ID=? AND P_ID=?', (käufer_id, produkt_id))
        existing_transaction = cursor.fetchone()
        if existing_transaction:
            return False, f'Es existiert bereits eine Transaktion für das Produkt "{produkt_barcode}".'

        # Transaktion in die Datenbank einfügen
        datum = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO Transaktion (K_ID, P_ID, Typ, Menge, Datum) VALUES (?, ?, ?, ?, ?)',
                       (käufer_id, produkt_id, 'Verkauf', menge, datum))

        # Anzahl verkaufter Produkte erhöhen
        cursor.execute('UPDATE Produkt SET Anzahl_verkauft = Anzahl_verkauft + ? WHERE P_ID = ?', (menge, produkt_id))

        conn.commit()
        conn.close()
        return True, f'Transaktion erfolgreich eingetragen für Käufer "{käufer_name}" und Produkt "{produkt_barcode}".'

    except sqlite3.Error as error:
        return False, f'Datenbankfehler: {error}'
    
#Funktion zur errechung des Kontostandes am ende des Zeltlagers
def genug_geld_bis_ende_von_tag(teilnehmer_id, referenz_datum, end_datum, datenbankname):
    connection = sqlite3.connect(datenbankname)
    cursor = connection.cursor()

    # Konvertiere das Datumformat von dd/mm/yyyy zu yyyy-mm-dd für SQLite
    referenz_datum_sqlite = datetime.strptime(referenz_datum, '%d/%m/%Y').strftime('%Y-%m-%d')
    end_datum_sqlite = datetime.strptime(end_datum, '%d/%m/%Y').strftime('%Y-%m-%d')

    # Summe der Einzahlungen für den Teilnehmer bis zum referenz_datum
    cursor.execute('''
        SELECT COALESCE(SUM(Einzahlung), 0) 
        FROM Konto 
        WHERE T_ID = ? AND Eröffnungsdatum <= ?
    ''', (teilnehmer_id, referenz_datum_sqlite))
    einzahlungen_summe_bis_referenz = cursor.fetchone()[0]

    # Summe der Ausgaben durch Transaktionen bis zum referenz_datum
    cursor.execute('''
        SELECT COALESCE(SUM(P.Preis * T.Menge), 0)
        FROM Transaktion T
        INNER JOIN Produkt P ON T.P_ID = P.P_ID
        INNER JOIN Konto K ON T.K_ID = K.K_ID 
        WHERE K.T_ID = ? AND T.Datum <= ? AND T.Typ = 'Kauf'
    ''', (teilnehmer_id, referenz_datum_sqlite))
    ausgaben_summe_bis_referenz = cursor.fetchone()[0]

    # Berechnung des Kontostands am referenz_datum
    kontostand_referenz_datum = einzahlungen_summe_bis_referenz - ausgaben_summe_bis_referenz

    # Berechne zukünftige Ausgaben durch Transaktionen ab dem referenz_datum bis zum Ende des Zeitraums
    zukuenftige_ausgaben = 0
    cursor.execute('''
        SELECT COALESCE(SUM(P.Preis * T.Menge), 0)
        FROM Transaktion T
        INNER JOIN Produkt P ON T.P_ID = P.P_ID
        INNER JOIN Konto K ON T.K_ID = K.K_ID
        WHERE K.T_ID = ? AND T.Datum > ? AND T.Datum <= ? AND T.Typ = 'Kauf'
    ''', (teilnehmer_id, referenz_datum_sqlite, end_datum_sqlite))
    zukuenftige_ausgaben = cursor.fetchone()[0]

    # Berechnung des erwarteten Kontostands bis zum Ende des Zeitraums
    erwarteter_kontostand_ende = kontostand_referenz_datum - zukuenftige_ausgaben

    connection.close()

    return kontostand_referenz_datum, erwarteter_kontostand_ende




if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
