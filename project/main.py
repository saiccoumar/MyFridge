# from flask import Response, Flask, request, flash, redirect, url_for, render_template, send_file
# from werkzeug.utils import secure_filename
# import os
# from os import listdir
# from os.path import isfile
# import zipfile
# import webbrowser
# from scrape import *
# # from PyQt5.QtCore import *
# # from PyQt5.QtWebEngineWidgets import *
# # from PyQt5.QtWidgets import QApplication
# # from threading import Timer


# current_directory = os.getcwd()
# #debug print(current_directory) 
# statDir = current_directory+"/static"
# templateDir = current_directory+"/templates"
# # initialize a flask object
# app = Flask(__name__,static_folder=statDir,
#             template_folder=templateDir)
# app.secret_key = "super secret key"

# @app.after_request
# def add_header(r):
#     """
#     Add headers to both force latest IE rendering engine or Chrome Frame,
#     and also to cache the rendered page for 10 minutes.
#     """
#     r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#     r.headers["Pragma"] = "no-cache"
#     r.headers["Expires"] = "0"
#     r.headers['Cache-Control'] = 'public, max-age=0'
#     return r

# @app.route('/',methods=['GET', 'POST'])
# def home():
#     return redirect('/search?search=')
     


# @app.route('/upload',methods=['GET', 'POST'])
# def upload():
#     if request.method == 'POST':
#         ingredient = {}
       
#         # check if the post request has the file part
#         if ('name' not in request.form) or (request.form['name']==''):
#             flash('No Ingredient Given','alert-danger')
#           #debug  print('No Song Given')
#             return redirect(request.url)
#         if ('quantity' not in request.form) or (request.form['quantity']==''):
#             flash('No Quantity Given','alert-danger')
#           #debug  print('No Link Given')
#             ingredient['quantity'] = 0
#         if ('unit' not in request.form) or (request.form['unit']==''):
#             flash('No Artist Given','alert-danger')
#           #debug  print('No Artist Given')
#             ingredient['unit']='grams'
#         if ('calories' not in request.form) or (request.form['calories']==''):
#             flash('No Album Given','alert-danger')
#           #debug  print('No Album Given')
#             ingredient['calories']=0 
#         # song = 
#         # for i in song:
#         #     print(i)
#         # if '.' in song:
#         #     print('yes')
#         #     song = song.replace('.','')
    
#         ingredient['name']= request.form['name']
#         ingredient['quantity']=request.form['quantity']
#         ingredient['unit']=request.form['unit']
#         ingredient['calories']=request.form['calories']
        

#        #debug print('JSON Object:')
#        #debug print(song)
#         addToJson(ingredient)
        
#         # for f in os.listdir('uploads'):
#         #   os.remove(os.path.join('uploads', f))
#         flash('ingredient uploaded','alert-primary')
#         return render_template("upload.html")
#     return render_template('upload.html')

# @app.route('/search', methods=['GET', 'POST'])
# def search():

#     data = getData()
#     if not 'Ingredients' in data:
#         return render_template('home.html',ingredient={})


#    #debug print(len(data))
#     args = request.args
#     if request.method == 'GET':
#         # print('recieved')
#         for k,v in args.items():
#             # print("query"+v)
#             if re.search('[a-zA-Z]', v):
#                 if len(data) < 1:
#                     return render_template('home.html',ingredient={})
#                 data = searchJson(v)
#             else:
#                 data = getData()

#     if request.method == 'POST':
#         return redirect(request.url)
    
#     return render_template('home.html',ingredient=data["Ingredients"])


# def open_browser():
#       webbrowser.open_new('http://127.0.0.1:2000/')

# if __name__ == '__main__':
    
#     if not os.environ.get("WERKZEUG_RUN_MAIN"):
#         webbrowser.open_new('http://127.0.0.1:8000/')
#     app.run(port = 8000, debug=True, use_reloader=True,host="0.0.0.0")

from flask_sqlalchemy import SQLAlchemy
from flask import Response, Flask, request, flash, redirect, url_for, render_template, send_file
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
    quantity = db.Column(db.String(20), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.String(20), nullable=False)

    @classmethod
    def create(cls, name, quantity, unit, calories):
        new_ingredient = cls(name=name, quantity=quantity, unit=unit, calories=calories)
        db.session.add(new_ingredient)
        db.session.commit()

    @classmethod
    def get_all(cls):
        ingredients = cls.query.all()
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
    def update(cls, ingredient_id, name, quantity, unit, calories):
        ingredient = cls.query.get(ingredient_id)
        ingredient.name = name
        ingredient.quantity = quantity
        ingredient.unit = unit
        ingredient.calories = calories
        db.session.commit()

    @classmethod
    def delete(cls, ingredient_id):
        ingredient = cls.query.get(ingredient_id)
        if ingredient:
            db.session.delete(ingredient)
            db.session.commit()

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def home():
    return redirect('/search?search=')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        ingredient = {}

        if ('name' not in request.form) or (request.form['name'] == ''):
            flash('No Ingredient Given', 'alert-danger')
            return redirect(request.url)

        if ('quantity' not in request.form) or (request.form['quantity'] == ''):
            flash('No Quantity Given', 'alert-danger')
            ingredient['quantity'] = 0

        if ('unit' not in request.form) or (request.form['unit'] == ''):
            flash('No Unit Given', 'alert-danger')
            ingredient['unit'] = 'grams'

        if ('calories' not in request.form) or (request.form['calories'] == ''):
            flash('No Calories Given', 'alert-danger')
            ingredient['calories'] = 0

        ingredient['name'] = request.form['name']
        ingredient['quantity'] = request.form['quantity']
        ingredient['unit'] = request.form['unit']
        ingredient['calories'] = request.form['calories']

        Ingredient.create(name=ingredient['name'], quantity=ingredient['quantity'],
                          unit=ingredient['unit'], calories=ingredient['calories'])

        flash('Ingredient uploaded', 'alert-primary')
        return render_template("upload.html")
    return render_template("upload.html")

@app.route('/edit/<int:ingredient_id>', methods=['GET', 'POST'])
def edit(ingredient_id):
    ingredient = Ingredient.get_by_id(ingredient_id)

    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        unit = request.form['unit']
        calories = request.form['calories']

        Ingredient.update(ingredient_id, name, quantity, unit, calories)
        flash('Ingredient updated', 'alert-primary')
        return redirect('/search?search=')

    return render_template('edit.html', ingredient=ingredient)

@app.route('/delete/<int:ingredient_id>', methods=['POST'])
def delete(ingredient_id):
    if request.method == 'POST':
        Ingredient.delete(ingredient_id)
        flash('Ingredient deleted', 'alert-danger')
        return redirect(request.referrer or '/search?search=')

    print("HELP")
    # Redirect back to the referring page (or to /search if no referring page)
    

@app.route('/search', methods=['GET', 'POST'])
def search():
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

    data = {'Ingredients': []}
    for ingredient in ingredients:
        data['Ingredients'].append({
            'id': ingredient.id,
            'name': ingredient.name,
            'quantity': ingredient.quantity,
            'unit': ingredient.unit,
            'calories': ingredient.calories
        })

    return render_template('home.html', ingredient=data["Ingredients"])

def open_browser():
    webbrowser.open_new('http://127.0.0.1:8000/')

if __name__ == '__main__':
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://127.0.0.1:8000/')
    app.run(port=8000, debug=True, use_reloader=True, host="0.0.0.0")
