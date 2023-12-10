
from flask_sqlalchemy import SQLAlchemy
from flask import Response, Flask, request, flash, make_response, redirect, url_for, render_template, send_file
from flask import session
import os
import re
import webbrowser

app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # Change data type to Integer
    unit = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.Integer, nullable=False)  # Change data type to Integer

    recipes = db.relationship('RecipeIngredient', back_populates='ingredient')

    @classmethod
    def create(cls, name, quantity, unit, calories):
        try:
            # Try to convert quantity and calories to integers
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
            # Delete all associated RecipeIngredients
            RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

            # Now, delete the recipe itself
            db.session.delete(recipe)
            db.session.commit()

class RecipeIngredient(db.Model):
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), primary_key=True)
    quantity_required = db.Column(db.Float)
    ingredient = db.relationship('Ingredient', back_populates='recipes')
    recipe = db.relationship('Recipe', back_populates='ingredients')

    

with app.app_context():
    db.create_all()
    db.Index('idx_name_unit', Ingredient.name, Ingredient.unit)

    

@app.route('/', methods=['GET', 'POST'])
def home():
    
    return redirect('/search?search=')

@app.route('/recipes/search', methods=['GET'])
def recipes_search():
    # Get the search criteria from the query parameters
    search_query = request.args.get('search', '').strip()

    # Retrieve all recipes if no search query is provided
    if not search_query:
        recipes = Recipe.query.all()
    else:
        # Filter recipes based on the search query (modify as needed)
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
    # Handle ingredient search
    ingredient_search = request.args.get('ingredientSearch', '').strip()

    if 'selected_ingredients' not in session:
        session['selected_ingredients'] = []

    search_results = []
    selected_ingredients = session['selected_ingredients']

    if ingredient_search:
        # Perform ingredient search based on your criteria
        search_results = Ingredient.query.filter(Ingredient.name.ilike(f"%{ingredient_search}%")).all()

    # Handle adding selected ingredients to the recipe
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

        # Get the selected ingredient
        selected_ingredient = Ingredient.get_by_id(ingredient_id)

        # Convert the array to a dictionary for efficient lookup
        selected_ingredients_dict = {item['id']: item for item in selected_ingredients}

        # Check if the ingredient is already in the dictionary
        existing_ingredient = selected_ingredients_dict.get(selected_ingredient.id)

        # If the ingredient is not in the dictionary, add it
        if not existing_ingredient:
            # Add selected ingredient to the dictionary
            selected_ingredients_dict[selected_ingredient.id] = {
                'id': selected_ingredient.id,
                'name': selected_ingredient.name,
                'quantity_required': 1 
            }

# Convert the dictionary back to an array
        selected_ingredients = list(selected_ingredients_dict.values())

    # Update session
    session['selected_ingredients'] = selected_ingredients

    return render_template('add_recipe.html', search_results=search_results, selected_ingredients=selected_ingredients)

@app.route('/recipe/upload/delete/<int:ingredient_id>', methods=['GET'])
def add_recipe_delete(ingredient_id):
    if 'selected_ingredients' in session:
        selected_ingredients = session['selected_ingredients']
        session['selected_ingredients'] = [i for i in selected_ingredients if i['id'] != ingredient_id]

        # Create a response to clear the cookie
        response = make_response(redirect(url_for('add_recipe_search')))
        response.delete_cookie(f'recipe_ingredient_{ingredient_id}')

        return response

    # Redirect back to the add recipe page
    return redirect(url_for('add_recipe_search'))

@app.route('/recipes/upload/submit', methods=['POST'])
def add_recipe_submit():
    if request.method == 'POST':
        # Get recipe details from the form
        name = request.form.get('recipe_name')
        diet_type = request.form.get('diet_type')
        cuisine = request.form.get('cuisine')
        text = request.form.get('text')

        # Create a new recipe
        new_recipe = Recipe(
            name=name,
            diet_type=diet_type,
            cuisine=cuisine,
            total_calories = 0,
            text=text

        )
        db.session.add(new_recipe)
        db.session.commit()

        # Handle updating quantities based on the form data
        total_calories = 0
        for key, value in request.form.items():
            if key.startswith('recipe_ingredient_') and value.isdigit():
                ingredient_id = int(key.split('_')[2])
                quantity_required = int(value)

                # Update the quantity in the database or create a new record
                recipe_ingredient = RecipeIngredient(
                    recipe_id=new_recipe.id,
                    ingredient_id=ingredient_id,
                    quantity_required=quantity_required
                )
                db.session.add(recipe_ingredient)
                db.session.commit()

                # Calculate total calories
                ingredient = Ingredient.query.get(ingredient_id)
                if ingredient:
                    total_calories += quantity_required * ingredient.calories

        # Update the total calories in the recipe
        new_recipe.total_calories = total_calories
        db.session.commit()

        # Clear session cookies
        session.clear()

        # Redirect back to the recipe search page
        return redirect('/recipes/search')




@app.route('/restock/search', methods=['GET', 'POST', 'DELETE'])
def restock_search():
    # Handle ingredient search
    ingredient_search = request.args.get('ingredientSearch', '').strip()

    if 'selected_ingredients' not in session:
        session['selected_ingredients'] = []

    search_results = []
    selected_ingredients = session['selected_ingredients']

    if ingredient_search:
        # Perform ingredient search based on your criteria
        search_results = Ingredient.query.filter(Ingredient.name.ilike(f"%{ingredient_search}%")).all()

    # Handle adding selected ingredients to the restock list
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

        # Query the information for the selected ingredient
        # Get the selected ingredient
        selected_ingredient = Ingredient.get_by_id(ingredient_id)

        # Convert the array to a dictionary for efficient lookup
        selected_ingredients_dict = {item['id']: item for item in selected_ingredients}

        # Check if the ingredient is already in the dictionary
        existing_ingredient = selected_ingredients_dict.get(selected_ingredient.id)

        # If the ingredient is not in the dictionary, add it
        if not existing_ingredient:
    # Add selected ingredient to the dictionary
            selected_ingredients_dict[selected_ingredient.id] = {
                'id': selected_ingredient.id,
                'name': selected_ingredient.name,
                'quantity_required': 1  # You can set a default quantity here
            }

# Convert the dictionary back to an array
        selected_ingredients = list(selected_ingredients_dict.values())


    

    # Update session
    session['selected_ingredients'] = selected_ingredients

    return render_template('restock.html', search_results=search_results, selected_ingredients=selected_ingredients)

@app.route('/restock/delete/<int:ingredient_id>', methods=['GET'])
def restock_delete(ingredient_id):
    if 'selected_ingredients' in session:
        selected_ingredients = session['selected_ingredients']
        session['selected_ingredients'] = [i for i in selected_ingredients if i['id'] != ingredient_id]

        # Create a response to clear the cookie
        response = make_response(redirect(url_for('restock_search')))
        response.delete_cookie(f'restock_{ingredient_id}')

        return response

    # Redirect back to the restock page
    return redirect(url_for('restock_search'))

@app.route('/restock/submit', methods=['POST'])
def restock_submit():
    if request.method == 'POST':
        # Handle updating quantities based on the form data
        for key, value in request.form.items():
            if key.startswith('restock_') and value.isdigit():
                ingredient_id = int(key.split('_')[1])
                restock_quantity = int(value)

                # Update the quantity in the database
                ingredient = Ingredient.get_by_id(ingredient_id)
                if ingredient:
                    ingredient.quantity += restock_quantity
                    db.session.commit()

        # Clear session cookies
        session.clear()

        # Redirect back to the restock page
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
            # Try to convert quantity and calories to integers
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
    


    # Redirect back to the referring page (or to /search if no referring page)
    

@app.route('/search', methods=['GET', 'POST'])
def search():
    data = {}
    if request.method == 'GET':
        args = request.args
        for k, v in args.items():
            if re.search('[a-zA-Z]', v):
                if len(Ingredient.query.all()) < 1:
                    return render_template('home.html', ingredient={})
                ingredients = Ingredient.query.filter(Ingredient.name.ilike(f"%{v}%")).all()
            else:
                ingredients = Ingredient.query.all()

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
