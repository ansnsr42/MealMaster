#import mealmaster_mgr
from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
#from flask_session import Session
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
form flask_sqlalchemy import SQLAlchemy
#import sqlite3
#import os
#from functools import wraps

#manager = mealmaster_mgr.Mealmaster_mgr(config_file="config/settings.json")
app = Flask(__name__)
#init SQLAlchemy so we can use it later in our models
app.config['SQLALCHEMY_DATABASE_URI'] = manager.config.get_config("database_uri")
app.config['SECRET_KEY'] = manager.config.get_config("encryption_secret_key")

#Proxyfix  als Middle Ware


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    location = db.Column(db.TEXT)
    semesters = db.Column(db.TEXT)
    modules = db.Column(db.TEXT)
    additional_calendars = db.Column(db.TEXT)
    register_date = db.Column(db.TEXT)
    last_login = db.Column(db.TEXT)
    last_calendar_update = db.Column(db.TEXT)
    last_calendar_pull = db.Column(db.TEXT)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(validators=[InputRequired(), EqualTo('password', message='Passwords must match')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

# ------ Page Routes  ------

@app.route('/')
    def start():
        return render_template('login.html')
#@app.route('/')
#def home():
#    return render_template("index.html")
#

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    #Übersichtsseite
    return render_template("index.html")
    #User abfragen
    #User spezifisches Feedback geben

@app.route('/create-recipe', method=['POST'])
def create_recipe():
    # Seite zum Erstellen von Rezepten
    return render_template('create_recipe.html')

#Rezepte verwalten
    #Erstellen
    #Bearbeiten

#Wodchenplanung

#Einkaufliste
#Erstellen
    #Raus rechen der Haushaltsbestand
#Bearbeiten
    


#Haushalt Liste bearbeiten




@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

#def login():
#    form = LoginForm()
#    if form.username.data:
#        username = form.username.data.lower()
#        if form.validate_on_submit():
#            user = User.query.filter_by(username=username).first()
#            if user:
#                if bcrypt.check_password_hash(user.password, form.password.data):
#                    login_user(user)
#                    manager.log_login(user.username)
#                    current_user.last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                    db.session.commit()
#                    return redirect(url_for('dashboard'))
#                else:
#                    flash('- Incorrect password. Due to security you can only try 5 times a minute.', 'error')
#            else:
#                flash('- User does not exist. You may remebered wrong or the user got deleted due to inactivity. Due to security you can only try 5 times a minute.', 'error')
#    return render_template('login.html', form=form)



#@app.route('/index', methods=['GET', 'POST'])
#def index():
#    if 'user_id' not in session:
#        return redirect(url_for('login'))  # Weiterleitung zur Login-Seite, wenn nicht eingeloggt
#    
#    if request.method == 'POST':
#        title = request.form['title']
#        ingredients = request.form['ingredients']
#        instructions = request.form['instructions']
#        create_recipe_in_db(session['user_id'], title, ingredients, instructions)
#
#    recipes = get_user_recipes(session['user_id'])
#    return render_template('index.html', recipes=recipes)

#@app.route('/logout')
#def logout():
#    session.clear()  # Session löschen
#    return redirect(url_for('login'))  # Weiterleitung zur Login-Seite
#
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')



if __name__ == "__main__":
    app.run(host="127.0.0.1",debug=True)
