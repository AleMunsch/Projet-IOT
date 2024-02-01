import flask
import sqlite3
from io import BytesIO
from flask import Flask, render_template, request, Response
import json
import matplotlib
matplotlib.use('Agg')

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as CanvasVirtuel

import urllib.parse

app = flask.Flask(__name__,template_folder='Views')

#Connection à la bdd
connection = sqlite3.connect('data.db')

#Creation de la table user si innexistante
cursor = connection.cursor()
cursor.execute('Create table if not exists user (id_user integer primary key, name varchar(50), mdp varchar(50))')

#création des tables température humidité et pression si inexistantes
cursor.execute('Create table if not exists temperature_table(temp_id INTEGER PRIMARY KEY AUTOINCREMENT, value_temp REAL, date DATETIME)')
cursor.execute('Create table if not exists humidity_table(humidity_id INTEGER PRIMARY KEY AUTOINCREMENT, value_hum REAL, date DATETIME)')
cursor.execute('Create table if not exists pressure_table(pression_id INTEGER PRIMARY KEY AUTOINCREMENT, value_press REAL, date DATETIME)')

#création table commande 
cursor.execute(
'''
        CREATE TABLE IF NOT EXISTS commande (
            id INTEGER PRIMARY KEY,
            date DATETIME,
            temp_id INTEGER,
            hum_id INTEGER,
            pression_id INTEGER,
            FOREIGN KEY (temp_id) REFERENCES temperature(temp_id),
            FOREIGN KEY (hum_id) REFERENCES humidity(humidity_id),
            FOREIGN KEY (pression_id) REFERENCES pression(pression_id)
        )
        '''
)

cursor.execute('''
    INSERT INTO commande (date, id, temp_id, hum_id, pression_id)
    SELECT
        t.date AS date,
        t.temp_id AS id,
        t.temp_id AS temp_id,
        h.humidity_id AS hum_id,
        p.pression_id AS pression_id
    FROM
        temperature_table t
    INNER JOIN humidity_table h ON t.date = h.date
    INNER JOIN pressure_table p ON t.date = p.date
''')

# Affichage des données de la table temperature_table
cursor.execute('SELECT * FROM temperature_table')
print("Données de temperature_table:")
print(cursor.fetchall())

# Affichage des données de la table humidity_table
cursor.execute('SELECT * FROM humidity_table')
print("Données de humidity_table:")
print(cursor.fetchall())

# Affichage des données de la table pressure_table
cursor.execute('SELECT * FROM pressure_table')
print("Données de pressure_table:")
print(cursor.fetchall())

# Affichage des données de la table commande
cursor.execute('SELECT * FROM commande')
print("Données de commande:")
print(cursor.fetchall())

connection.commit()
connection.close()

#Def de la route home
@app.route('/')
def home():
    return flask.render_template('register.html')

#Ajout du user dans la bdd
@app.route('/register', methods=['GET', 'POST'])
def register():
    if flask.request.method == 'POST':
        name = flask.request.values.get('name')
        mdp = flask.request.values.get('mdp')
        
        #On verifie si le pseudo existe déjà
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()
        cursor.execute('select count(*) from user where name=?',(name,))
        pseudo_existant = cursor.fetchone()[0] > 0
        connection.close()
        if pseudo_existant:
            return flask.render_template('error.html', message="Erreur! Ce nom est déjà pris !")
        else:
            #On ajoute le nouveau user dans la bdd après verification
            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()
            cursor.execute('INSERT INTO user (name, mdp) VALUES (?,?)', (name, mdp))
            connection.commit()
            connection.close()
            return flask.redirect('/weather')
    else:
        return flask.render_template('register.html')
    
#Connexion a un compte dejà existant
app.secret_key = 'secret-key'
@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        name = flask.request.form['name']
        mdp = flask.request.form['mdp']
        
        connection =sqlite3.connect('data.db')
        
        cursor = connection.cursor()
        cursor.execute('select id_user from user where name=? and mdp=?',(name,mdp))
        tuple_id_user = cursor.fetchone()
        connection.close()
        
        if tuple_id_user is not None:
            id_user = tuple_id_user[0]
            flask.session['user_id'] = id_user
            flask.session['name'] = name
            return flask.redirect('/weather')
        else:
            return flask.render_template('error.html', message="Erreur! Le nom ou le mot de passe est incorrect !")
    else:
        return flask.render_template('login.html')

#Route des graph
@app.route("/chart")
def chart():
    # Créez une connexion à la base de données et un curseur
    connection = sqlite3.connect("data.db")
    cursor = connection.cursor()

    cursor.execute("SELECT c.date, t.value_temp, h.value_hum, p.value_press FROM commande c "
               "INNER JOIN temperature_table t ON c.temp_id = t.temp_id "
               "INNER JOIN humidity_table h ON c.hum_id = h.humidity_id "
               "INNER JOIN pressure_table p ON c.pression_id = p.pression_id")

    # Récupérez toutes les lignes de résultats
    data_from_db = cursor.fetchall()
    print(data_from_db)
    # Fermez la connexion à la base de données
    connection.close()

    # vérification
    if not data_from_db:
        return flask.render_template('error.html', message="Erreur! Aucune donnée à afficher dans le graphique.")

    # Transformez les données en une structure utilisable pour le graphique
    chart_data = {
        "title": "température / humidité / Pression",
        "temperature": {entry[0]: entry[1] for entry in data_from_db},
        "humidite": {entry[0]: entry[2] for entry in data_from_db},
        "pression": {entry[0]: entry[3] for entry in data_from_db}
    }


    # verification 
    print(chart_data)


    param_encoded = request.args.get("param")

    # Décodez correctement l'URL encodée
    param_decoded = urllib.parse.unquote(param_encoded)

    try:
        # Chargez le paramètre JSON
        param = json.loads(param_decoded)
        print(param)
    except json.JSONDecodeError as e:
        # Gérez l'erreur de décodage JSON
        return f"Erreur de décodage JSON : {str(e)}", 400

    labels = []
    temperature = []
    humidite = []
    pression = []

    if param["title"] == "température / humidité / Pression":
        labels = list(chart_data["temperature"].keys())  # Utilisez les dates de la température comme étiquettes
        temperature = list(chart_data["temperature"].values())
        humidite = list(chart_data["humidite"].values())
        pression = list(chart_data["pression"].values())
    elif param["title"] == "température":
        labels = list(chart_data["temperature"].keys())
        temperature = list(chart_data["temperature"].values())
    elif param["title"] == "humidité":
        labels = list(chart_data["humidite"].keys())
        humidite = list(chart_data["humidite"].values())
    elif param["title"] == "Pression":
        labels = list(chart_data["pression"].keys())
        pression = list(chart_data["pression"].values())

    fig, ax1 = plt.subplots()

    if "title" in param:
        fig.suptitle(param["title"])

    if temperature and humidite and pression:
        # Si les trois existent, utilisez une triple échelle y
        ax2 = ax1.twinx()
        ax3 = ax1.twinx()

        # Ajustez les couleurs et autres propriétés pour chaque axe
        ax1.plot(labels, temperature, label='Température', color='b')
        ax2.plot(labels, humidite, 'r-', label='Humidité')
        ax3.plot(labels, pression, 'g-', label='Pression')
        ax3.spines['right'].set_position(('outward', 80))

        # Ajustez la couleur de la graduation y pour ax3
        ax3.yaxis.label.set_color('red')
    elif temperature:
        # Si seulement la température existe
        ax1.plot(labels, temperature, label='Température', color='b')
    elif humidite:
        # Si seulement l'humidité existe
        ax1.plot(labels, humidite, 'r-', label='Humidité')
    elif pression:
        ax1.plot(labels, pression, 'g-', label='Presion')

    fig.savefig("chart.png", format="png")
    output = BytesIO()
    CanvasVirtuel(fig).print_png(output)

    return Response(output.getvalue(), mimetype="image/png")

#route vers site météo
def get_last_values():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Récupérer les dernières valeurs de chaque table
    cursor.execute("SELECT value_temp FROM temperature_table ORDER BY date DESC")
    last_temperature = cursor.fetchone()

    cursor.execute("SELECT value_hum FROM humidity_table ORDER BY date DESC")
    last_humidity = cursor.fetchone()

    cursor.execute("SELECT value_press FROM pressure_table ORDER BY date DESC")
    last_pressure = cursor.fetchone()

    conn.close()

    return last_temperature, last_humidity, last_pressure

def create_temp_actuelle_table():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Créer la table temporaire temp_actuelle si elle n'existe pas
    cursor.execute('''CREATE TABLE IF NOT EXISTS temp_actuelle (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        temperature REAL,
                        humidity REAL,
                        pressure REAL,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()
    
@app.route('/weather', methods=['GET', 'POST'])
def weather():
    # Récupérer les dernières valeurs
    last_temperature, last_humidity, last_pressure = get_last_values()

    # Créer la table temporaire
    create_temp_actuelle_table()

    # Insérer les dernières valeurs dans la table temp_actuelle
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO temp_actuelle (temperature, humidity, pressure) VALUES (?, ?, ?)",
                   (last_temperature[0], last_humidity[0], last_pressure[0]))
    conn.commit()
     # Récupérer les données de la table temp_actuelle pour l'affichage
    cursor.execute("SELECT * FROM temp_actuelle ORDER BY date DESC")
    temp_actuelle_data = cursor.fetchall()

    cursor.execute("Drop table temp_actuelle")
    conn.close()
    print(temp_actuelle_data)

    return render_template('weather.html', last_humidity=last_humidity, last_pressure=last_pressure, last_temperature=last_temperature)

def print_table_data():
    # Connexion à la base de données
    connection = sqlite3.connect("data.db")
    cursor = connection.cursor()

    try:
        # Exécutez une requête pour récupérer toutes les données de la table commande
        cursor.execute("SELECT * FROM temp_actuel")

        # Récupérez toutes les lignes de résultats
        rows = cursor.fetchall()

        # Affichez les en-têtes de colonnes
        column_names = [description[0] for description in cursor.description]
        print("\t".join(column_names))

        # Affichez les données
        for row in rows:
            print("\t".join(map(str, row)))

    finally:
        # Fermez la connexion
        connection.close()
        
             
#route vers la listes des sondes
@app.route('/api/sonde', methods=['GET'])
def get_sonde():
   connection = sqlite3.connect('data.db')
   cursor = connection.cursor()
   cursor.execute('SELECT * FROM sonde')
   sondes = cursor.fetchall()
   connection.close()

   list_sonde = []

   for sonde in sondes:
      list_sonde.append({
         "id": sonde[0],
         "name": sonde[1],
      }) 

   return flask.jsonify(list_sonde)
        
@app.route('/sonde', methods=['GET', 'POST'])
def sonde():
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()
    cursor.execute('Create table if not exists sonde (id_sonde integer primary key, name varchar(50))')
    connection.commit()
    
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM sonde')
    sonde = cursor.fetchall()
    connection.close()

    list_sonde = []

    for sonde in sonde:
        list_sonde.append({
            "id": sonde[0],
            "name": sonde[1],
        })
        
    return render_template('sonde.html', sonde=list_sonde)



@app.route('/add', methods=['GET', 'POST'])
def add():
   if flask.request.method == 'POST':
      name = flask.request.values.get('name')

      connection = sqlite3.connect('data.db')

      cursor = connection.cursor()
      cursor.execute('INSERT INTO sonde (name) VALUES (?)', (name,))
      connection.commit()
      connection.close()

      return flask.redirect('/sonde')
   else:
      return flask.render_template('add.html')

@app.route('/delete/<id>')
def delete(id):
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()
    
    cursor.execute('SELECT * FROM sonde WHERE id_sonde = ?', (id,))
    sonde = cursor.fetchone()

    if sonde:
        cursor.execute('DELETE FROM sonde WHERE id_sonde = ?', (id,))
        connection.commit()
        connection.close()
        return flask.redirect('/sonde')
    else:
        return flask.render_template('error.html', message="La sonde n'a pas pu être supprimée ! ID non trouvé !")


#@app.route('/temp_actuel')
#def temp_actuel():
#    # Récupérer les dernières valeurs
#    last_temperature, last_humidity, last_pressure = get_last_values()
#
#    # Créer la table temporaire
#    create_temp_actuelle_table()
#
#    # Insérer les dernières valeurs dans la table temp_actuelle
#    conn = sqlite3.connect('data.db')
#    cursor = conn.cursor()
#    cursor.execute("INSERT INTO temp_actuelle (temperature, humidity, pressure) VALUES (?, ?, ?)",
#                   (last_temperature[1], last_humidity[1], last_pressure[1]))
#    conn.commit()
#     # Récupérer les données de la table temp_actuelle pour l'affichage
#    cursor.execute("SELECT * FROM temp_actuelle ORDER BY date DESC LIMIT 1")
#    temp_actuelle_data = cursor.fetchall()
#
#    conn.close()
#    print(temp_actuelle_data)
#
#    return render_template('weather.html', data=temp_actuelle_data, last_humidity=last_humidity, last_pressure=last_pressure, last_temperature=last_temperature)


#Run l'app
app.run(port=7777)  