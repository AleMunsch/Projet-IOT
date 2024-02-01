from io import BytesIO
from flask import Flask, render_template, request, Response
import json
import matplotlib
import sqlite3
import random
from datetime import datetime, timedelta

matplotlib.use('Agg')

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as CanvasVirtuel


import os

# Où se trouve le dossier à lier
# Ici il est dans web.
# app = Flask(__name__)


# Déclaration des variables de connexion et de curseur en global
connection = None
cursor = None


database_path = "data.db"
if os.path.exists(database_path):
    os.remove(database_path)
    print(f"data '{database_path}' deleted.")
else:
    print(f"data '{database_path}' does not exist.")

# Déclaration des variables de connexion et de curseur en global
connection = None
cursor = None

# Fonction pour créer les tables et insérer des données fictives
def create_and_populate_tables():
    global connection, cursor  # Ajout de la déclaration globale

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    # Création des tables (placez vos instructions CREATE TABLE ici)
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS temperature_table (temp_id INTEGER PRIMARY KEY, value_temp REAL, date DATETIME)')
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS humidity_table (humidity_id INTEGER PRIMARY KEY, value_hum REAL, date DATETIME)')
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS pressure_table (pression_id INTEGER PRIMARY KEY, value_press REAL, date DATETIME)'
    )

# Insertion de données fictives
try:
    create_and_populate_tables()  # Appel de la fonction pour créer les tables

    if connection:
        connection.execute("BEGIN")  # Début de la transaction

        for _ in range(10):
            date = (datetime.now() - timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d')
            temperature = random.randint(0, 30)
            humidite = random.randint(20, 50)
            pression = random.randint(950, 1050)

            # Vérifiez si la date existe déjà
            cursor.execute("SELECT COUNT(*) FROM temperature_table WHERE date = ?", (date,))
            existing_date_count = cursor.fetchone()[0]

            # Si la date n'existe pas, insérez les données
            if existing_date_count == 0:


                print("la temperature est :", temperature)
                print("l'humidité est :", humidite)
                print("la pression est :", pression)
                print("la date est :", date)


                cursor.execute("INSERT INTO temperature_table (value_temp, date) VALUES (?, ?)", (temperature, date))
                cursor.execute("INSERT INTO humidity_table (value_hum, date) VALUES (?, ?)", (humidite, date))
                cursor.execute("INSERT INTO pressure_table (value_press, date) VALUES (?, ?)", (pression, date))


        if connection:
            connection.commit()  # Validez la transaction

except Exception as e:
    if connection:
        connection.rollback()  # Annulation de la transaction en cas d'erreur
    raise e
finally:
    if connection:
        connection.close()  # Fermez la connexion après utilisation
