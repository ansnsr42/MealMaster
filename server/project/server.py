# server.py
import mealmaster_mgr
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    current_user, login_required
)



manager = mealmaster_mgr.Mealmaster_mgr(config_file="config/settings.json")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = manager.get_config("database_uri")
app.config['SECRET_KEY'] = manager.get_config("encryption_secret_key")

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
with app.app_context():
    db.create_all()

# Flask-Login konfigurieren
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'   # Route-Name deiner Login-Funktion

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------------
# MODELS
# --------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

    # Weitere Felder, wie in deinem Projekt
    register_date = db.Column(db.TEXT)
    last_login = db.Column(db.TEXT)
    ip_address = db.Column(db.TEXT)

    def __repr__(self):
        return f"<User {self.username}>"
with app.app_context():
    db.create_all()
# --------------------------------
# FORMS
# --------------------------------
class RegisterForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=3, max=20)],
        render_kw={"placeholder": "Username"}
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=8)],
        render_kw={"placeholder": "Password"}
    )
    confirm_password = PasswordField(
        validators=[InputRequired(), EqualTo('password', message='Passwords must match')],
        render_kw={"placeholder": "Confirm Password"}
    )
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=3, max=20)],
        render_kw={"placeholder": "Username"}
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=8)],
        render_kw={"placeholder": "Password"}
    )
    submit = SubmitField('Login')

# --------------------------------
# ROUTES
# --------------------------------


@app.route('/')
def home():
    # Mögliche Startseite: z.B. "login" oder "index"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.lower()
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user:
            # Passwortvergleich
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                user.last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.session.commit()
                # OPTIONAL: mealmaster_mgr Logik hier
                # manager.log_login(user.username)
                return redirect(url_for('dashboard'))
            else:
                flash("Falsches Passwort!", "error")
        else:
            flash("Nutzer existiert nicht!", "error")
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.lower()
        # Prüfen, ob der Nutzername existiert
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Dieser Benutzername ist bereits vergeben!", "error")
            return redirect(url_for('register'))

        # Passwort verschlüsseln
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            username=username,
            password=hashed_pw,
            register_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registrierung erfolgreich! Bitte melde dich an.", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    # Deine "index" bzw. Dashboard-Seite
    # Nur für eingeloggte Nutzer zugänglich
    return render_template('index.html')

@app.route('/create-recipe', methods=['GET', 'POST'])
@login_required
def create_recipe():
    # Beispielroute, nur wenn eingeloggt
    if request.method == 'POST':
        # Rezept erstellen ...
        pass
    return render_template('create_recipe.html')

# --------------------------------
# MAIN
# --------------------------------
if __name__ == "__main__":
    # Damit du den DB-Kontext hast:
  
    # Nur für lokale Entwicklung
    app.run(debug=True)
