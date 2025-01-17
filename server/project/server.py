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
    shopping_list = db.relationship('ShoppingList', back_populates='user',
                                    uselist=False,  # nur EIN Objekt
                                    cascade='all, delete-orphan')

    household_items = db.relationship('HouseholdItem', back_populates='user',
                                      cascade='all, delete-orphan')
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


    amount = db.Column(db.Float, nullable=True)  # oder db.Numeric(10, 2) für exakte Werte
    unit = db.Column(db.String(20), nullable=True)  # z. B. "g", "ml", "Stk"

    recipe = db.relationship('Recipe', back_populates='recipe_ingredients')
    ingredient = db.relationship('Ingredient', back_populates='ingredient_in_recipes')

class ShoppingList(db.Model):
    __tablename__ = 'shopping_lists'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    #
    

    # Beziehung: Eine Einkaufsliste hat viele Items
    items = db.relationship('ShoppingListItem', back_populates='shopping_list',
                            cascade='all, delete-orphan')

    # User-Objekt, falls du beidseitig referenzieren willst
    user = db.relationship('User', back_populates='shopping_list')


class ShoppingListItem(db.Model):
    __tablename__ = 'shopping_list_items'
    id = db.Column(db.Integer, primary_key=True)
    shopping_list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=True)

    amount = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(20), nullable=True)

    shopping_list = db.relationship('ShoppingList', back_populates='items')
    ingredient = db.relationship('Ingredient')

    # Neu für Non-Food:
    custom_name = db.Column(db.String(100), nullable=True)  # z. B. "Toilettenpapier"

    # Neu für Abhaken:
    purchased = db.Column(db.Boolean, default=False, nullable=False)

    shopping_list = db.relationship('ShoppingList', back_populates='items')
   


class HouseholdItem(db.Model):
    __tablename__ = 'household_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    amount = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(20), nullable=True)

    user = db.relationship('User', back_populates='household_items')
    ingredient = db.relationship('Ingredient')



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
        ingredient_amounts = request.form.getlist('ingredient_amount[]')
        ingredient_units = request.form.getlist('ingredient_unit[]')
        
        for name, amt_str, unt in zip(ingredient_names, ingredient_amounts, ingredient_units):
            if not name.strip():
                continue
            # Ingredient
            ingredient = Ingredient.query.filter_by(name=name.strip()).first()
            if not ingredient:
                ingredient = Ingredient(name=name.strip())
                db.session.add(ingredient)
                db.session.commit()
        
            # amount parsen
            try:
                amount_val = float(amt_str) if amt_str else None
            except ValueError:
                amount_val = None
        
            recipe_ing = RecipeIngredient(
                recipe_id=new_recipe.id,
                ingredient_id=ingredient.id,
                amount=amount_val,
                unit=unt.strip() if unt else None
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

    # Nur Besitzer darf bearbeiten
    if recipe.user_id != current_user.id:
        flash("Du darfst nur deine eigenen Rezepte bearbeiten!", "error")
        return redirect(url_for('my_recipes'))

    if request.method == 'POST':
        # 1) Rezeptdaten aktualisieren
        recipe.title = request.form.get('title')
        recipe.instructions = request.form.get('instructions')

        # 2) Bisherige RecipeIngredients entfernen,
        #    damit wir sie komplett neu anlegen können
        recipe.recipe_ingredients.clear()
        db.session.flush()  # entfernt alte Einträge aus der DB-Session

        # 3) Neue Werte aus dem Formular einlesen
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_amounts = request.form.getlist('ingredient_amount[]')
        ingredient_units = request.form.getlist('ingredient_unit[]')

        for name, amt_str, unt in zip(ingredient_names, ingredient_amounts, ingredient_units):
            name = name.strip()
            if not name:
                continue

            # Ingredient holen oder anlegen
            ingredient = Ingredient.query.filter_by(name=name).first()
            if not ingredient:
                ingredient = Ingredient(name=name)
                db.session.add(ingredient)
                db.session.commit()

            # Menge parsen
            try:
                amount_val = float(amt_str) if amt_str else None
            except ValueError:
                amount_val = None

            # RecipeIngredient erstellen
            ri = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount_val,
                unit=unt.strip() if unt else None
            )
            db.session.add(ri)

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


@app.route('/delete-recipe/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    # Nur der Eigentümer darf löschen
    if recipe.user_id != current_user.id:
        flash("Du darfst nur deine eigenen Rezepte löschen!", "error")
        return redirect(url_for('my_recipes'))

    # Rezept löschen
    db.session.delete(recipe)
    db.session.commit()

    flash("Rezept wurde erfolgreich gelöscht!", "success")
    return redirect(url_for('my_recipes'))


@app.route('/shopping-list')
@login_required
def shopping_list():
    slist = ShoppingList.query.filter_by(user_id=current_user.id).first()
    if not slist:
        flash("Du hast aktuell keine Einkaufsliste. Bitte wähle Rezepte aus.")
        return redirect(url_for('select_recipes'))

    return render_template('shopping_list.html', slist=slist)

@app.route('/select_recipes', methods=['GET', 'POST'])
@login_required
def select_recipes():
    if request.method == 'POST':
        recipe_ids = request.form.getlist('recipe_ids[]')
        existing_list = ShoppingList.query.filter_by(user_id=current_user.id).first()
        if existing_list:
            db.session.delete(existing_list)
            db.session.commit()

        new_list = ShoppingList(user_id=current_user.id)
        db.session.add(new_list)
        db.session.commit()

        # Haushalt: Zutaten dieses Users
        household_items = HouseholdItem.query.filter_by(user_id=current_user.id).all()
        household_ingredient_ids = {hi.ingredient_id for hi in household_items}

        # Rezeptzutaten laden
        recipe_ids = [int(x) for x in recipe_ids if x.isdigit()]
        recipe_ings = RecipeIngredient.query.filter(
            RecipeIngredient.recipe_id.in_(recipe_ids)
        ).all()

        # Summendict
        from collections import defaultdict
        sums_dict = defaultdict(float)
        no_unit_entries = []

        for ri in recipe_ings:
            # Check if ingredient already in household
            if ri.ingredient_id in household_ingredient_ids:
                # => skip it entirely
                continue

            # Normal summation logic
            if ri.amount is not None and ri.unit:
                key = (ri.ingredient_id, ri.unit.lower())
                sums_dict[key] += ri.amount
            else:
                no_unit_entries.append(ri)

        # Summierte Einheiten -> ShoppingListItem
        for (ing_id, unit_str), total_amt in sums_dict.items():
            item = ShoppingListItem(
                shopping_list_id=new_list.id,
                ingredient_id=ing_id,
                amount=total_amt,
                unit=unit_str
            )
            db.session.add(item)

        # no_unit_entries -> add if not in household
        for ri in no_unit_entries:
            # household check war oben, also hier kein check mehr nötig
            item = ShoppingListItem(
                shopping_list_id=new_list.id,
                ingredient_id=ri.ingredient_id,
                amount=ri.amount,
                unit=ri.unit
            )
            db.session.add(item)

        db.session.commit()
        flash("Deine Einkaufsliste wurde aktualisiert! Zutaten aus dem Haushalt wurden ignoriert.", "success")
        return redirect(url_for('shopping_list'))

    # GET
    user_recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    return render_template('select_recipes.html', recipes=user_recipes)

@app.route('/edit-shopping-list', methods=['GET', 'POST'])
@login_required
def edit_shopping_list():
    # 1) Aktuelle Liste des Users laden
    slist = ShoppingList.query.filter_by(user_id=current_user.id).first()
    if not slist:
        flash("Keine Einkaufsliste vorhanden.")
        return redirect(url_for('select_recipes'))  # oder wo auch immer

    if request.method == 'POST':
        # 2) Checkboxen für bestehende Items auswerten
        for item in slist.items:
            # Wir erwarten z.B. ein Feld "purchased_<ID>" 
            # -> wenn es im request.form auftaucht, ist es angehakt
            checkbox_name = f"purchased_{item.id}"
            item.purchased = (checkbox_name in request.form)

        # 3) Neuen Artikel hinzufügen
        custom_name = request.form.get('new_item_name', '').strip()
        amount_str = request.form.get('new_item_amount', '')
        unit_str = request.form.get('new_item_unit', '').strip()

        if custom_name:
            try:
                amount_val = float(amount_str) if amount_str else None
            except ValueError:
                amount_val = None

            new_item = ShoppingListItem(
                shopping_list_id=slist.id,
                custom_name=custom_name,
                amount=amount_val,
                unit=unit_str or None,
                purchased=False  # neu angelegte Artikel sind standardmäßig nicht gekauft
            )
            db.session.add(new_item)

        db.session.commit()
        flash("Einkaufsliste aktualisiert!", "success")
        return redirect(url_for('edit_shopping_list'))

    # GET => Seite anzeigen
    return render_template('edit_shopping_list.html', slist=slist)



@app.route('/delete-shopping-list', methods=['POST'])
@login_required
def delete_shopping_list():
    slist = ShoppingList.query.filter_by(user_id=current_user.id).first()
    if slist:
        db.session.delete(slist)
        db.session.commit()
        flash("Einkaufsliste gelöscht!", "info")
    else:
        flash("Keine Einkaufsliste vorhanden.", "error")
    return redirect(url_for('select_recipes'))

@app.route('/inventory')
@login_required
def inventory():
    # Alle Items, die zum aktuellen Benutzer gehören
    items = HouseholdItem.query.filter_by(user_id=current_user.id).all()
    return render_template('inventory.html', items=items)

@app.route('/add-inventory', methods=['POST'])
@login_required
def add_inventory():
    ingredient_name = request.form.get('ingredient_name', '').strip()
    amount_str = request.form.get('amount', '')
    unit_str = request.form.get('unit', '').strip()

    # Ingredient holen oder anlegen
    if ingredient_name:
        ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
        if not ingredient:
            ingredient = Ingredient(name=ingredient_name)
            db.session.add(ingredient)
            db.session.commit()

        # Menge parsen
        try:
            amount_val = float(amount_str) if amount_str else None
        except ValueError:
            amount_val = None

        # HouseholdItem anlegen
        item = HouseholdItem(
            user_id=current_user.id,
            ingredient_id=ingredient.id,
            amount=amount_val,
            unit=unit_str if unit_str else None
        )
        db.session.add(item)
        db.session.commit()
        flash("Lebensmittel zum Bestand hinzugefügt!", "success")
    else:
        flash("Bitte einen Namen für die Zutat angeben!", "error")

    return redirect(url_for('inventory'))


# --------------------------------
# MAIN
# --------------------------------
if __name__ == "__main__":
    # Damit du den DB-Kontext hast:
  
    # Nur für lokale Entwicklung
    app.run(debug=True)
