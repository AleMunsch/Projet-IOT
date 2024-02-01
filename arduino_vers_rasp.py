import time
from flask import Flask
import sqlite3
from datetime import datetime
import requests

# ... (code de création de la base de données)

# Définissez l'adresse IP et le port du serveur Flask
server_ip = "192.168.170.82"
server_port = 5000

try:
    while True:
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        # Lit une ligne de données depuis l'Arduino (remplacé par des valeurs fictives pour l'exemple)
        temperature = "25.5"
        pressure = "1010.0"
        humidity = "50.0"

        # Affiche les données sur la console
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()
        print("Temperature =", temperature, "°C")
        cursor.execute('''
        INSERT INTO temperature_table (value_temp, date) VALUES (?, ?)
        ''', (temperature, formatted_date))
        connection.commit()
        print("Pressure =", pressure, "hPa")
        cursor.execute('''
        INSERT INTO pressure_table (value_press, date) VALUES (?, ?)
        ''', (pressure, formatted_date))
        connection.commit()
        print("Humidity =", humidity, "%")
        cursor.execute('''
        INSERT INTO humidity_table (value_hum, date) VALUES (?, ?)
        ''', (humidity, formatted_date))
        connection.commit()
        connection.close()

        # Envoi des données au serveur Flask via une requête HTTP POST
        url = f"http://{server_ip}:{server_port}/sensor_data"
        data = {
            "Temperature": temperature,
            "Pressure": pressure,
            "Humidity": humidity
        }
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print("Données envoyées avec succès au serveur Flask")
        else:
            print(f"Échec de l'envoi des données au serveur Flask, code de statut : {response.status_code}")

        # Attente de 5 secondes
        time.sleep(5)

except KeyboardInterrupt:
    pass