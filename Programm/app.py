# Standard-Bibliotheken
import os   # Für Dateioperationen
import sqlite3  # Für Datenbankzugriff
from datetime import datetime # Für Zeitstempel

# Externe Bibliotheken
import subprocess #
import numpy as np  #
import pandas as pd     # Für Datenverarbeitung und -analyse
import shutil   # Für Dateioperationen
from typing import List, Tuple, Callable    # Für Typenangaben

# Flask und zugehörige Erweiterungen
from flask import Flask, Response, render_template, request, redirect, url_for, flash, jsonify  # Für Webanwendungen
# Benutzerdefinierte Module
from database import Database, get_db_connection    # Für Datenbankzugriff

# Konfigurationen
from config import db_backup    # Für Backup-Konfiguration
from config import Zeltlager    # Für Lager-Konfiguration

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

def fetch_users(db: Database) -> List[str]:
    users = [user[0] for user in db.execute_select("SELECT Name FROM Teilnehmer ORDER BY Name")]  # Ruft Benutzernamen aus der Datenbank ab
    return users

def fetch_products(db: Database) -> List[str]:
    products = [product[0] for product in db.execute_select("SELECT Beschreibung FROM Produkt ORDER BY Preis")]  # Ruft Produktbeschreibungen aus der Datenbank ab
    return products

def fetch_transactions(db: Database, user_id: int) -> List[Tuple]:
    transactions = db.execute_select("SELECT * FROM Transaktion WHERE K_ID = ? ORDER BY Datum DESC", (user_id,))  # Ruft Transaktionen für einen bestimmten Benutzer ab
    return transactions

def kontostand_in_geld(kontostand):
    if kontostand:
        kontostand_value = kontostand
        zwischenstand = round(kontostand_value, 2)
    else:
        kontostand_value = 0
        zwischenstand = 0
    denominations = [20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
    
    counts = {denom: 0 for denom in denominations}  # Korrektur: Initialisierung des Dictionaries
    
    for denom in denominations:
        count = int(zwischenstand) // denom
        counts[denom] += count  # Korrektur: Verwendung von counts[denom] anstelle von counts.append(count)
        zwischenstand -= count * denom
    return counts

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
        aktualisere_endkontostand()
        return True, f'Transaktion erfolgreich eingetragen für Käufer "{käufer_name}" und Produkt "{produkt_barcode}".'

    except sqlite3.Error as error:
        return False, f'Datenbankfehler: {error}'
    except Exception as e:
        return False, f'Fehler: {e}'

# Function to calculate the remaining balance until the end of the camp
def genug_geld_bis_ende_von_tag(teilnehmer_id, db):
    try:
        lager_name = Zeltlager.lager  # Example for the camp
        lager = db.execute("SELECT Zeltlager FROM Einstellungen WHERE Zeltlager = ?", (lager_name,)).fetchone()[0]
        
        # Convert date formats
        first_day = db.execute("SELECT first_day FROM Einstellungen WHERE Zeltlager = ?", (lager,)).fetchone()[0]
        end_datum = db.execute("SELECT last_day FROM Einstellungen WHERE Zeltlager = ?", (lager,)).fetchone()[0]
        referenz_datum = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Account balance at the reference date
        kontostand_referenz_datum = db.execute("SELECT Kontostand FROM Konto WHERE T_ID = ?", (teilnehmer_id,)).fetchone()[0]
        
        # Expenses between start date and reference date
        ausgaben = db.execute("SELECT SUM(Preis * Menge) FROM Transaktion JOIN Produkt ON Transaktion.P_ID = Produkt.P_ID WHERE K_ID = ? AND Datum BETWEEN ? AND ?", (teilnehmer_id, first_day, referenz_datum)).fetchone()[0]
        if ausgaben is None:
            ausgaben = 0
        
        # Days since the start of the camp
        tage_seit_anfang = (datetime.strptime(referenz_datum[:10], '%Y-%m-%d') - datetime.strptime(first_day, '%Y-%m-%d')).days
        
        # Days until the end of the camp
        tage_bis_ende = (datetime.strptime(end_datum[:10], '%Y-%m-%d') - datetime.strptime(referenz_datum[:10], '%Y-%m-%d')).days
        
        # Expenses per day
        ausgaben_pro_tag = ausgaben / tage_seit_anfang if tage_seit_anfang != 0 else 0
        
        # Account balance at the end of the camp
        erwarteter_kontostand_ende = kontostand_referenz_datum - (ausgaben_pro_tag * tage_bis_ende)      
        return erwarteter_kontostand_ende
    
    except Exception as e:
        print(f"Fehler bei der Berechnung des erwarteten Kontostands: {e}")
        return None

def aktualisere_endkontostand():
    try:
        db = get_db_connection()
        # Get all participants
        teilnehmer = db.execute("SELECT T_ID FROM Teilnehmer").fetchall()
        
        for tn in teilnehmer:
            tn_id = tn[0]
            # Update end balance for each participant
            erwarteter_kontostand = genug_geld_bis_ende_von_tag(tn_id, db)
            if erwarteter_kontostand is not None:
                db.execute("UPDATE Konto SET Endkontostand = ? WHERE T_ID = ?", (erwarteter_kontostand, tn_id))
                print(f"Endkontostand für TN {tn_id} aktualisiert.")
            else:
                print(f"Fehler beim Aktualisieren des Endkontostands für TN {tn_id}")
        
        db.commit()
    
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Endkontostands: {e}")
    finally:
        db.close()

# Routen
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_product_dropdowns', methods=['GET'])
def update_product_dropdowns_route():
    db = Database()
    products = fetch_products(db)  # Ruft Produktbeschreibungen ab
    return jsonify({'products': products})

@app.route('/add_buy', methods=['GET', 'POST'])
def add_buy():
    if request.method == 'POST':
        user = request.form['user']
        product = request.form['product']
        quantity = int(request.form['quantity'])
        success = submit_purchase(user, product, quantity)
        if success:
            aktualisere_endkontostand()
            print('Kauf erfolgreich hinzugefügt', 'success')
        else:
            print('Fehler beim Hinzufügen des Kaufs', 'danger')
        return redirect(url_for('add_buy'))
    users = get_users_from_db()
    products = get_products_from_db()
    db = Database()  # Stellen Sie sicher, dass db korrekt initialisiert ist
    IDs = db.execute_select("SELECT T_ID FROM Teilnehmer")  # Korrekte Verwendung
    return render_template('add_buy.html', users=users, products=products, IDs=IDs)

@app.route('/submit_buy', methods=['POST'])
def submit_buy():
    user = request.form['user']
    product = request.form['product']
    quantity = int(request.form['quantity'])
    success = submit_purchase(user, product, quantity)
    if success:
        
        print('Purchase submitted successfully', 'success')
    else:
        print('Error submitting purchase', 'danger')
    return redirect(url_for('index'))

@app.route('/watch')
def watch():
    conn = get_db_connection()
    cursor = conn.cursor()
    aktualisere_endkontostand()
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
    return render_template('watch.html', tables=df.to_html(classes='data', header=True, index=False))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == '1':
            return redirect(url_for('admin'))
        else:
            print('Invalid password, try again.', 'danger')
    return render_template('login.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/dblogin', methods=['GET', 'POST'])  # Hinzufügen des fehlenden Schrägstrichs
def dblogin():
    if request.method == 'POST':
        passworddb = request.form['passworddb']
        if passworddb == 'FwvdDB':
            return redirect(url_for('datenbankverwaltung'))
        else:
            print('Invalid password, try again.', 'danger')
    return render_template('loginform.html')

@app.route('/db_create')
def db_create():
    os.system('python3 OB_DB_erstellen.py')
    return redirect(url_for('index'))

@app.route('/teilnehmer')
def teilnehmer():
    return render_template('A_TN.html')

@app.route('/produkte')
def produkte():
    return render_template('A_Produkte.html')

@app.route('/statistik')
def statistik():
    return render_template('A_Statistik.html')

@app.route('/datenbankverwaltung')
def datenbankverwaltung():
    return render_template('A_DB.html')

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
            user_einzahlung = cur.execute("SELECT Einzahlung FROM Konto JOIN Teilnehmer ON Konto.T_ID = Teilnehmer.T_ID WHERE Teilnehmer.Name = ?", (user,)).fetchone()
            if user_balance:
                new_balance = user_balance['Kontostand'] + amount
                cur.execute("UPDATE Konto SET Kontostand = ? WHERE T_ID = (SELECT T_ID FROM Teilnehmer WHERE Name = ?)", (new_balance, user))
                cur.execute("INSERT INTO Transaktion (K_ID, P_ID, Typ, Menge, Datum) VALUES ((SELECT T_ID FROM Teilnehmer WHERE Name = ?), 0, 'Einzahlung', ?, ?)", (user, amount, datetime.now().strftime("%d.%m.%Y %H:%M:%S")))
                new_einzahlung = user_einzahlung['Einzahlung'] + amount
                cur.execute("UPDATE Konto SET Einzahlung = ? WHERE T_ID = (SELECT T_ID FROM Teilnehmer WHERE Name = ?)", (new_einzahlung, user)) # Update the deposit
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
            if new_price_str:
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
            alert = "Der ausgewählte Teilnehmer existiert nicht."
            return redirect(url_for('index', alert=alert))
        
        kontostand = db.execute_select("SELECT Kontostand FROM Konto WHERE T_ID = (SELECT T_ID FROM Teilnehmer WHERE Name = ?)", (benutzer_id,))
        kontostand = float(kontostand[0][0])
        kontostand = round(kontostand, 2)
        
        geldwerte = kontostand_in_geld(kontostand)
        if geldwerte is None:
            geldwerte = [0] * 11
        
        # Calculate the breakdown of banknotes and coins
        denominations = [20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
        counts = {denom: 0 for denom in denominations}
        zwischenstand = kontostand
        
        for denom in denominations:
            count = int(zwischenstand // denom)
            counts[denom] = count
            zwischenstand -= count * denom
            zwischenstand = round(zwischenstand, 10)
        
        return render_template('checkout_c.html', benutzer_id=benutzer_id, kontostand=kontostand if kontostand else 0, geldwerte=geldwerte, counts=counts)

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
            # Get dates from form
            first_day = request.form['formatted_first_day']
            last_day = request.form['formatted_last_day']
            
            # Validate and convert dates
            if first_day and last_day:
                # Convert to '%Y-%m-%d' format for database update
                first_day_db_format = datetime.strptime(first_day, '%d-%m-%Y').strftime('%Y-%m-%d')
                last_day_db_format = datetime.strptime(last_day, '%d-%m-%Y').strftime('%Y-%m-%d')
                
                # Update database
                conn.execute("UPDATE Einstellungen SET first_day = ? WHERE Zeltlager = ?", (first_day_db_format, Zeltlager.lager))
                conn.execute("UPDATE Einstellungen SET last_day = ? WHERE Zeltlager = ?", (last_day_db_format, Zeltlager.lager))
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
    first_day_row = conn.execute("SELECT first_day FROM Einstellungen WHERE Zeltlager = ?", (Zeltlager.lager,)).fetchone()
    last_day_row = conn.execute("SELECT last_day FROM Einstellungen WHERE Zeltlager = ?", (Zeltlager.lager,)).fetchone()
    
    conn.close()
    
    first_day = datetime.strptime(first_day_row['first_day'], '%Y-%m-%d').strftime('%d-%m-%Y') if first_day_row else ''
    last_day = datetime.strptime(last_day_row['last_day'], '%Y-%m-%d').strftime('%d-%m-%Y') if last_day_row else ''
    
    lager_dauer = (datetime.strptime(last_day, '%d-%m-%Y') - datetime.strptime(first_day, '%d-%m-%Y')).days
    
    heute = datetime.now().strftime('%d-%m-%Y')
    
    # Render settings page with form fields
    
    return render_template('settings.html', first_day=first_day, lager_dauer=lager_dauer, last_day=last_day, today=heute)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
