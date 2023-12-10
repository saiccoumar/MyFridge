
from flask_sqlalchemy import SQLAlchemy
from flask import Response, Flask, request, flash, make_response, redirect, url_for, render_template, send_file
from flask import session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import re
import webbrowser
from sqlalchemy.sql import alias

app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# Ingredient Instantiation via ORM
class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False) 
    unit = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.Integer, nullable=False)  

    recipes = db.relationship('RecipeIngredient', back_populates='ingredient')

    @classmethod
    def create(cls, name, quantity, unit, calories):
        try:
            quantity = int(quantity)
            calories = int(calories)
        except ValueError:
            raise ValueError("Quantity and Calories must be integers")

        new_ingredient = cls(name=name, quantity=quantity, unit=unit, calories=calories)
        db.session.add(new_ingredient)
        db.session.commit()

    @classmethod
    def get_all(cls, ingredients):
        data = {'Ingredients': []}
        for ingredient in ingredients:
            data['Ingredients'].append({
                'id': ingredient.id,
                'name': ingredient.name,
                'quantity': ingredient.quantity,
                'unit': ingredient.unit,
                'calories': ingredient.calories
            })
        return data

    @classmethod
    def get_by_id(cls, ingredient_id):
        return cls.query.get(ingredient_id)

    @classmethod
    def delete(cls, ingredient_id):
        ingredient = cls.query.get(ingredient_id)
        if ingredient:
            db.session.delete(ingredient)
            db.session.commit()

    @classmethod
    def update_quantity(cls, ingredient_id, action):
        ingredient = cls.query.get(ingredient_id)
        print(type(ingredient.quantity))
        if ingredient:
            if action == 'increase':
                ingredient.quantity += 1
            elif action == 'decrease' and ingredient.quantity > 0:
                ingredient.quantity -= 1

            db.session.commit()
    


# Recipe Instantiation via ORM
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    diet_type = db.Column(db.String(50))
    total_calories = db.Column(db.Integer)
    cuisine = db.Column(db.String(50))
    text = db.Column(db.String(1000))

    ingredients = db.relationship('RecipeIngredient', back_populates='recipe')

    @classmethod
    def delete(cls, recipe_id):
        recipe = cls.query.get(recipe_id)
        if recipe:
            RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

            db.session.delete(recipe)
            db.session.commit()

# Recipe Instantiation via ORM
class RecipeIngredient(db.Model):
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), primary_key=True)
    quantity_required = db.Column(db.Float)
    ingredient = db.relationship('Ingredient', back_populates='recipes')
    recipe = db.relationship('Recipe', back_populates='ingredients')

    

with app.app_context():
    db.create_all()
    # Create Indexes for filtering data
    db.Index('idx_name_unit', Ingredient.name, Ingredient.unit)
    db.Index('idx_name', Ingredient.name)
    db.Index('idx_unit', Ingredient.unit)
    db.Index('idx_quantity', Ingredient.quantity)
    db.Index('idx_calories', Ingredient.calories)

    
@app.route('/', methods=['GET', 'POST'])
def home():
    # Home route
    return redirect('/search?search=')

# Recipe Route
@app.route('/recipes/view/<int:recipe_id>', methods=['GET', 'POST'])
def view_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)

    if not recipe:
        flash('Recipe not found', 'alert-danger')
        return redirect('/recipes/search')

    def consume_recipe(recipe):
        for recipe_ingredient in recipe.ingredients:
            ingredient = recipe_ingredient.ingredient
            quantity_required = recipe_ingredient.quantity_required

            if ingredient.quantity < quantity_required:
                return False, f"Not enough {ingredient.name} to use this recipe"

            ingredient.quantity -= quantity_required
            db.session.commit()

        return True, "Recipe used successfully"

    if request.method == 'POST':
        success, message = consume_recipe(recipe)
        if success:
            flash('Recipe used successfully', 'alert-success')
            return redirect('/')
        else:
            flash(message, 'alert-danger')
            return redirect(request.url)



    return render_template('view_recipe.html', recipe=recipe)

@app.route('/recipes/search', methods=['GET'])
def recipes_search():
    search_query = request.args.get('search', '').strip()

    if not search_query:
        recipes = Recipe.query.all()
    else:
        recipes = Recipe.query.filter(
            Recipe.name.ilike(f"%{search_query}%") |
            Recipe.diet_type.ilike(f"%{search_query}%") |
            Recipe.cuisine.ilike(f"%{search_query}%")
        ).all()

    return render_template('recipes.html', recipes=recipes)

@app.route('/recipes/delete/<int:recipe_id>', methods=['POST'])
def recipe_delete(recipe_id):
    if request.method == 'POST':
        Recipe.delete(recipe_id)
        flash('Recipe deleted', 'alert-danger')
        return redirect(request.referrer or '/search?search=')
    

@app.route('/recipes/upload/search', methods=['GET', 'POST'])
def add_recipe_search():
    ingredient_search = request.args.get('ingredientSearch', '').strip()

    if 'selected_ingredients' not in session:
        session['selected_ingredients'] = []

    search_results = []
    selected_ingredients = session['selected_ingredients']

    if ingredient_search:
        # Example of ORM call
        search_results = Ingredient.query.filter(Ingredient.name.ilike(f"%{ingredient_search}%")).all()

    for result in search_results:
        quantity_key = f'recipe_ingredient_{result.id}'
        quantity_required = request.args.get(quantity_key)
        if quantity_required is not None:
            quantity_required = int(quantity_required)
            if quantity_required > 0:
                selected_ingredients.append({
                    'id': result.id,
                    'name': result.name,
                    'quantity_required': quantity_required
                })

    if request.method == 'POST':
        ingredient_id = int(request.form.get('ingredient_id'))
# Example of ORM call
        selected_ingredient = Ingredient.get_by_id(ingredient_id)

        selected_ingredients_dict = {item['id']: item for item in selected_ingredients}

        existing_ingredient = selected_ingredients_dict.get(selected_ingredient.id)

        if not existing_ingredient:
            selected_ingredients_dict[selected_ingredient.id] = {
                'id': selected_ingredient.id,
                'name': selected_ingredient.name,
                'quantity_required': 1 
            }

        selected_ingredients = list(selected_ingredients_dict.values())

    session['selected_ingredients'] = selected_ingredients

    return render_template('add_recipe.html', search_results=search_results, selected_ingredients=selected_ingredients)

@app.route('/recipe/upload/delete/<int:ingredient_id>', methods=['GET'])
def add_recipe_delete(ingredient_id):
    if 'selected_ingredients' in session:
        selected_ingredients = session['selected_ingredients']
        session['selected_ingredients'] = [i for i in selected_ingredients if i['id'] != ingredient_id]

        response = make_response(redirect(url_for('add_recipe_search')))
        response.delete_cookie(f'recipe_ingredient_{ingredient_id}')

        return response

    return redirect(url_for('add_recipe_search'))

@app.route('/recipes/upload/submit', methods=['POST'])
def add_recipe_submit():
    if request.method == 'POST':
        name = request.form.get('recipe_name')
        diet_type = request.form.get('diet_type')
        cuisine = request.form.get('cuisine')
        text = request.form.get('text')

        new_recipe = Recipe(
            name=name,
            diet_type=diet_type,
            cuisine=cuisine,
            total_calories = 0,
            text=text

        )
        db.session.add(new_recipe)
        db.session.commit()

        total_calories = 0
        for key, value in request.form.items():
            if key.startswith('recipe_ingredient_') and value.isdigit():
                ingredient_id = int(key.split('_')[2])
                quantity_required = int(value)

                recipe_ingredient = RecipeIngredient(
                    recipe_id=new_recipe.id,
                    ingredient_id=ingredient_id,
                    quantity_required=quantity_required
                )
                db.session.add(recipe_ingredient)
                db.session.commit()

                ingredient = Ingredient.query.get(ingredient_id)
                if ingredient:
                    total_calories += quantity_required * ingredient.calories

        new_recipe.total_calories = total_calories
        db.session.commit()

        session.clear()

        return redirect('/recipes/search')



# Restock routes
@app.route('/restock/search', methods=['GET', 'POST', 'DELETE'])
def restock_search():
    ingredient_search = request.args.get('ingredientSearch', '').strip()

    if 'selected_ingredients' not in session:
        session['selected_ingredients'] = []

    search_results = []
    selected_ingredients = session['selected_ingredients']

    if ingredient_search:
        search_results = Ingredient.query.filter(Ingredient.name.ilike(f"%{ingredient_search}%")).all()

    for result in search_results:
        quantity_key = f'restock_{result.id}'
        restock_quantity = request.args.get(quantity_key)
        if restock_quantity is not None:
            restock_quantity = int(restock_quantity)
            if restock_quantity > 0:
                selected_ingredients.append({
                    'id': result.id,
                    'name': result.name,
                    'restock_quantity': restock_quantity
                })

    if request.method == 'POST':
        ingredient_id = int(request.form.get('ingredient_id'))

        selected_ingredient = Ingredient.get_by_id(ingredient_id)

        selected_ingredients_dict = {item['id']: item for item in selected_ingredients}

        existing_ingredient = selected_ingredients_dict.get(selected_ingredient.id)

        if not existing_ingredient:
            selected_ingredients_dict[selected_ingredient.id] = {
                'id': selected_ingredient.id,
                'name': selected_ingredient.name,
                'quantity_required': 1
            }

        selected_ingredients = list(selected_ingredients_dict.values())


    

    session['selected_ingredients'] = selected_ingredients

    return render_template('restock.html', search_results=search_results, selected_ingredients=selected_ingredients)

@app.route('/restock/delete/<int:ingredient_id>', methods=['GET'])
def restock_delete(ingredient_id):
    if 'selected_ingredients' in session:
        selected_ingredients = session['selected_ingredients']
        session['selected_ingredients'] = [i for i in selected_ingredients if i['id'] != ingredient_id]

        response = make_response(redirect(url_for('restock_search')))
        response.delete_cookie(f'restock_{ingredient_id}')

        return response

    return redirect(url_for('restock_search'))

@app.route('/restock/submit', methods=['POST'])
def restock_submit():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('restock_') and value.isdigit():
                ingredient_id = int(key.split('_')[1])
                restock_quantity = int(value)

                ingredient = Ingredient.get_by_id(ingredient_id)
                if ingredient:
                    ingredient.quantity += restock_quantity
                    db.session.commit()

        session.clear()

        return redirect('/')




@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        ingredient = {}

        if ('name' not in request.form) or (request.form['name'] == ''):
            flash('No Ingredient Given', 'alert-danger')
            return redirect(request.url)

        if ('quantity' not in request.form) or (request.form['quantity'] == ''):
            flash('No Quantity Given', 'alert-danger')
            return redirect(request.url)

        if ('unit' not in request.form) or (request.form['unit'] == ''):
            flash('No Unit Given', 'alert-danger')
            ingredient['unit'] = 'grams'
        else:
            ingredient['unit'] = request.form['unit']

        if ('calories' not in request.form) or (request.form['calories'] == ''):
            flash('No Calories Given', 'alert-danger')
            return redirect(request.url)
        if Ingredient.query.filter_by(name=request.form['name']).first():
            flash('Ingredient with the same name already exists', 'alert-danger')
            return redirect(request.url)
        
        ingredient['name'] = request.form['name']
        ingredient['quantity'] = request.form['quantity']
        ingredient['calories'] = request.form['calories']

        try:
            ingredient['quantity'] = int(ingredient['quantity'])
            ingredient['calories'] = int(ingredient['calories'])
        except ValueError:
            flash('Quantity and Calories must be integers', 'alert-danger')
            return redirect(request.url)

        if ingredient['quantity'] < 0:
            ingredient['quantity'] = 0
        Ingredient.create(name=ingredient['name'], quantity=ingredient['quantity'],
                          unit=ingredient['unit'], calories=ingredient['calories'])

        flash('Ingredient uploaded', 'alert-primary')
        return render_template("upload.html")

    return render_template("upload.html")


@app.route('/update_quantity/<int:ingredient_id>', methods=['POST'])
def update_quantity(ingredient_id):
    action = request.args.get('action')
    Ingredient.update_quantity(ingredient_id, action)

    return redirect(request.referrer or '/search?search=')


@app.route('/delete/<int:ingredient_id>', methods=['POST'])
def delete(ingredient_id):
    if request.method == 'POST':
        Ingredient.delete(ingredient_id)
        flash('Ingredient deleted', 'alert-danger')
        return redirect(request.referrer or '/search?search=')
    


    

from flask import render_template, request, redirect
from sqlalchemy import text
import re

# Home routes
@app.route('/search', methods=['GET', 'POST'])
def search():
    data = {}
    ingredients = []

    if request.method == 'GET':
        v = request.args.get('search', '')
        order_by = request.args.get('orderBy', 'name')
        show_out_of_stock = request.args.get('showOutOfStock')

        if re.search('[a-zA-Z]', v):
            if len(Ingredient.query.all()) < 1:
                return render_template('home.html', ingredient={})

            pattern = f"\"%{v.lower()}%\""
            out_clause = ""
            if not show_out_of_stock:
                out_clause= " AND quantity > 0"
            statement = text(f"SELECT * FROM ingredient WHERE LOWER(ingredient.name) LIKE {pattern}  ")
            result = db.session.execute(statement)

            temp_table_name = 'temp_table'
            
            if not db.session.execute(text(f"SELECT name FROM sqlite_temp_master WHERE type='table' AND name='{temp_table_name}'")).scalar():
                result.fetchall()
                # Raw SQL via prepared statements
                db.session.execute(text(f"CREATE TEMPORARY TABLE {temp_table_name} AS {statement} {out_clause}"))

        else:
            statement = text("SELECT * FROM ingredient")
            temp_table_name = 'temp_table'
            
            if not db.session.execute(text(f"SELECT name FROM sqlite_temp_master WHERE type='table' AND name='{temp_table_name}'")).scalar():
                out_clause = ""
                if not show_out_of_stock:
                    out_clause= " WHERE quantity > 0"
                db.session.execute(text(f"CREATE TEMPORARY TABLE {temp_table_name} AS {statement} {out_clause}"))

        if order_by in ['name', 'calories', 'quantity', 'unit']:
            order_sql = text(f"SELECT * FROM {temp_table_name} ORDER BY {order_by}")

            result = db.session.execute(order_sql)

            ingredients = result.fetchall()

            db.session.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))

    if request.method == 'POST':
        return redirect(request.url)

    data = Ingredient.get_all(ingredients)

    return render_template('home.html', ingredient=data["Ingredients"])


def open_browser():
    webbrowser.open_new('http://127.0.0.1:8000/')

if __name__ == '__main__':
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://127.0.0.1:8000/')
    app.run(port=8000, debug=True, use_reloader=True, host="0.0.0.0")
