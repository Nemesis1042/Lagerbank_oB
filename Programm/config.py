import os
from sympy import im
import sqlite3

def get_database():
    from database import Database  # Lokaler Import
    return Database()


class Config:
    SECRET_KEY = os.environ.get('1') or '1'
    SQLALCHEMY_DATABASE_URI = os.environ.get('/Online_Banking/') or f'sqlite:///{os.path.join(os.getcwd(), "Lagerbank2024.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class db_backup:
    lagerbankname = 'Lagerbank2024.db'
    source_file = 'Lagerbank2024.db'
    backup_directory = '/home/arkatosh/Documents/CVJM/Bula/Lagerbank'

class Zeltlager:
    lager = 2024 # Zeltlagerjahr
