from flask import Flask, request, redirect, url_for, render_template, session, flash
from flask_bcrypt import Bcrypt
from flask_session import Session
import sqlite3
import os
from functools import wraps


app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'geheime_schlüssel'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

DATABASE_PATH = 'database/users.db'


def get_user_from_db(username):
    conn = sqlite3.connect('database/mealmaster.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user_in_db(username, password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = sqlite3.connect('database/mealmaster.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

def get_user_recipes(user_id):
    conn = sqlite3.connect('database/mealmaster.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes WHERE user_id = ?", (user_id,))
    recipes = cursor.fetchall()
    conn.close()
    return recipes

def create_recipe_in_db(user_id, title, ingredients, instructions):
    conn = sqlite3.connect('database/mealmaster.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO recipes (user_id, title, ingredients, instructions) VALUES (?, ?, ?, ?)", 
                   (user_id, title, ingredients, instructions))
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_from_db(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):  
            session['user_id'] = user[0]
            session['username'] = user[1]  # Speichern des Benutzernamens in der Session
            return redirect(url_for('index'))  # Weiterleitung zur Hauptseite
        else:
            return 'Ungültige Anmeldedaten'

    return render_template('login.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Weiterleitung zur Login-Seite, wenn nicht eingeloggt
    
    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        create_recipe_in_db(session['user_id'], title, ingredients, instructions)

    recipes = get_user_recipes(session['user_id'])
    return render_template('index.html', recipes=recipes)

@app.route('/logout')
def logout():
    session.clear()  # Session löschen
    return redirect(url_for('login'))  # Weiterleitung zur Login-Seite

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        create_user_in_db(username, password)
        return redirect(url_for('login'))  # Weiterleitung zur Login-Seite

    return render_template('register.html')


@app.route('/create-recipe')
def create_recipe():
    # Seite zum Erstellen von Rezepten
    return render_template('create_recipe.html')


@app.route('/favicon.ico')
def favicon():
    return '', 204


if __name__ == "__main__":
    app.run(debug=True)
