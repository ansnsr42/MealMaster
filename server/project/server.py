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
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

    # Weitere Felder, wie in deinem Projekt
    register_date = db.Column(db.TEXT)
    last_login = db.Column(db.TEXT)
    ip_address = db.Column(db.TEXT)
    # Beziehung zurück auf Recipes
    recipes = db.relationship('Recipe', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Beziehung zurück auf Recipes (optional)
    recipes = db.relationship('Recipe', backref='ingredient', lazy=True)


class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    instructions = db.Column(db.String(400))
    quantity = db.Column(db.String(50))  # z.B. "2 EL", "500 ml", etc.

    # Schlüssel auf ingredient
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'))

    # Schlüssel auf User (wer hat das Rezept angelegt)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Beziehungen:
    # ingredient = relationship('Ingredient') -> bereits oben via backref='ingredient' erreichbar
    # user = relationship('User') -> definieren wir bei User als backref




# Legt Datenbank und Tabellen an        
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
    if request.method == 'POST':
        title = request.form.get('title')
        instructions = request.form.get('instructions')
        quantity = request.form.get('quantity')
        ingredient_name = request.form.get('ingredient_name')

        # 1) Prüfen, ob eine Zutat angegeben wurde
        if ingredient_name:
            # nachschauen, ob diese Zutat schon existiert
            ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
            if not ingredient:
                # Neue Zutat anlegen
                ingredient = Ingredient(name=ingredient_name)
                db.session.add(ingredient)
                db.session.commit()
            ingredient_id = ingredient.id
        else:
            ingredient_id = None

        # 2) Rezept anlegen
        new_recipe = Recipe(
            title=title,
            instructions=instructions,
            quantity=quantity,
            ingredient_id=ingredient_id,
            user_id=current_user.id  # wichtig: so gehört das Rezept dem eingeloggten User
        )
        db.session.add(new_recipe)
        db.session.commit()

        flash("Rezept erfolgreich erstellt!", "success")
        return redirect(url_for('my_recipes'))

    # GET-Anfrage: Formular anzeigen
    return render_template('create_recipe.html')

@app.route('/edit-recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    # Sicherheit: nur der Besitzer darf bearbeiten
    if recipe.user_id != current_user.id:
        flash("Du darfst nur deine eigenen Rezepte bearbeiten!", "error")
        return redirect(url_for('my_recipes'))

    if request.method == 'POST':
        recipe.title = request.form.get('title') or recipe.title
        recipe.instructions = request.form.get('instructions') or recipe.instructions
        recipe.quantity = request.form.get('quantity') or recipe.quantity
        
        ingredient_name = request.form.get('ingredient_name')
        if ingredient_name:
            ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
            if not ingredient:
                ingredient = Ingredient(name=ingredient_name)
                db.session.add(ingredient)
                db.session.commit()
            recipe.ingredient_id = ingredient.id

        db.session.commit()
        flash("Rezept erfolgreich aktualisiert!", "success")
        return redirect(url_for('my_recipes'))

    # GET: Formular anzeigen
    return render_template('edit_recipe.html', recipe=recipe)


@app.route('/my-recipes')
@login_required
def my_recipes():
    # Hol alle Rezepte für den aktuell eingeloggten User
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    return render_template('my_recipes.html', recipes=recipes)




# --------------------------------
# MAIN
# --------------------------------
if __name__ == "__main__":
    # Damit du den DB-Kontext hast:
  
    # Nur für lokale Entwicklung
    app.run(debug=True)
