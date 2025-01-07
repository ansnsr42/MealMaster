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
    recipes = db.relationship('Recipe', back_populates='user')

    def __repr__(self):
        return f"<User {self.username}>"

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Beziehung zu RecipeIngredient
    ingredient_in_recipes = db.relationship('RecipeIngredient', back_populates='ingredient',
                                            cascade="all, delete-orphan")



class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    instructions = db.Column(db.String(400))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Das "Brückentable" verknüpft Rezepte und Zutaten
    recipe_ingredients = db.relationship('RecipeIngredient', back_populates='recipe',
                                         cascade="all, delete-orphan")
    user = db.relationship('User', back_populates='recipes')  # Nur falls du back_populates nutzt


class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.String(50), nullable=True)  # z.B. "200 g"

    # Beziehungen (ein RecipeIngredient gehört zu genau 1 Recipe und 1 Ingredient)
    recipe = db.relationship('Recipe', back_populates='recipe_ingredients')
    ingredient = db.relationship('Ingredient', back_populates='ingredient_in_recipes')



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

        # 1) Neues Rezept-Objekt
        new_recipe = Recipe(
            title=title,
            instructions=instructions,
            user_id=current_user.id
        )
        db.session.add(new_recipe)
        db.session.commit()  # Damit new_recipe eine ID hat

        # 2) Zutaten auslesen
        # z.B. ingredient_name[] => Liste an Strings
        #     ingredient_qty[] => Liste an Mengen
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_qtys = request.form.getlist('ingredient_qty[]')

        # Für jedes Eintragspaar (Name, Menge) ...
        for name, qty in zip(ingredient_names, ingredient_qtys):
            # Falls Name leer, überspringen
            if not name.strip():
                continue

            # Ingredient schon vorhanden?
            ingredient = Ingredient.query.filter_by(name=name.strip()).first()
            if not ingredient:
                ingredient = Ingredient(name=name.strip())
                db.session.add(ingredient)
                db.session.commit()

            # Brückentabelle-Eintrag anlegen
            recipe_ing = RecipeIngredient(
                recipe_id=new_recipe.id,
                ingredient_id=ingredient.id,
                quantity=qty.strip() if qty else None
            )
            db.session.add(recipe_ing)

        db.session.commit()
        flash("Rezept erstellt!", "success")
        return redirect(url_for('my_recipes'))

    # GET
    return render_template('create_recipe.html')

@app.route('/edit-recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check Ownership: Nur der Besitzer darf das Rezept bearbeiten
    if recipe.user_id != current_user.id:
        flash("Du darfst nur deine eigenen Rezepte bearbeiten!", "error")
        return redirect(url_for('my_recipes'))

    if request.method == 'POST':
        # 1) Basis-Rezeptdaten
        recipe.title = request.form.get('title')
        recipe.instructions = request.form.get('instructions')

        # 2) Zutaten-Eingaben auslesen
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_qtys = request.form.getlist('ingredient_qty[]')

        # 3) Bisherige RecipeIngredient-Einträge löschen (für einen "frischen" Stand)
        #    Alternativ könntest du sie intelligent abgleichen, aber "Neu anlegen" ist meist simpler
        #    dank cascade='all, delete-orphan' werden sie aus der DB entfernt,
        #    sobald sie nicht mehr in recipe.recipe_ingredients enthalten sind.
        recipe.recipe_ingredients.clear()
        db.session.flush()  # löscht alle alten Datensätze in recipe_ingredients

        # 4) Neue RecipeIngredient-Einträge anlegen
        for name, qty in zip(ingredient_names, ingredient_qtys):
            name = name.strip()
            qty = qty.strip() if qty else ""
            if not name:
                continue

            # Ingredient holen oder erstellen
            ingredient = Ingredient.query.filter_by(name=name).first()
            if not ingredient:
                ingredient = Ingredient(name=name)
                db.session.add(ingredient)
                db.session.commit()

            # neuen Eintrag in recipe_ingredients
            ri = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                quantity=qty
            )
            db.session.add(ri)

        # 5) Speichern
        db.session.commit()
        flash("Rezept wurde aktualisiert!", "success")
        return redirect(url_for('my_recipes'))

    # GET: Formular anzeigen
    return render_template('edit_recipe.html', recipe=recipe)


@app.route('/my-recipes')
@login_required
def my_recipes():
    # Hol alle Rezepte für den aktuell eingeloggten User
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    return render_template('my_recipes.html', recipes=recipes)




@app.route('/shopping-list')
@login_required
def shopping_list():
    recipe_ids_str = request.args.get('recipe_ids', '')
    if not recipe_ids_str:
        flash("Keine Rezepte ausgewählt!", "error")
        return redirect(url_for('my_recipes'))

    # Aus "1,3,5" => [1, 3, 5]
    recipe_ids = [int(x) for x in recipe_ids_str.split(',') if x.isdigit()]

    # 1) Hole alle RecipeIngredient-Einträge
    recipe_ings = RecipeIngredient.query.filter(
        RecipeIngredient.recipe_id.in_(recipe_ids)
    ).all()

    # 2) Gruppieren nach ingredient_id => pro Ingredient gesammelte Mengen
    from collections import defaultdict
    shopping_dict = defaultdict(list)  
    # key = ingredient_id, value = Liste von Mengen-Strings

    for ri in recipe_ings:
        shopping_dict[ri.ingredient_id].append(ri.quantity or "")

    # 3) Zusammenbauen einer Liste für das Template
    results = []
    for ing_id, qty_list in shopping_dict.items():
        ingredient = Ingredient.query.get(ing_id)
        combined_qty = " + ".join(qty_list)
        results.append({
            "ingredient_name": ingredient.name,
            "total_quantity": combined_qty
        })

    return render_template("shopping_list.html", results=results)


@app.route('/select_recipes', methods=['GET', 'POST'])
@login_required
def select_recipes():
    if request.method == 'POST':
        # Checkbox-Liste
        recipe_ids = request.form.getlist('recipe_ids[]')
        if not recipe_ids:
            flash("Keine Rezepte ausgewählt!", "error")
            return redirect(url_for('select_recipes'))

        # Wir können direkt redirecten zu /shopping-list, z.B. per GET-Parameter
        # oder die Logik direkt hier machen.
        return redirect(url_for('shopping_list', recipe_ids=",".join(recipe_ids)))

    # GET: Liste aller Rezepte des Users anzeigen
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    return render_template('select_recipes.html', recipes=recipes)


# --------------------------------
# MAIN
# --------------------------------
if __name__ == "__main__":
    # Damit du den DB-Kontext hast:
  
    # Nur für lokale Entwicklung
    app.run(debug=True)
