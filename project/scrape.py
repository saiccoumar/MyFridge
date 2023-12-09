# import os

# from os import path
# import json
# from pathlib import Path
# import re
# from datetime import datetime






# def addToJson(ingredient):
#     print('addToJson: checkpoint 1')
#     data = {'Ingredients':[]}   
#     with open('data.json', 'r') as f:
#         data = json.load(f)
#         print('addToJson: checkpoint 2')
#     print(data)
#     inJson=False
#     appendedData = ingredient
#     if 'Ingredients' in data:
#         print('ingredient is in json')
#         for s in data['Ingredients']:
#             if appendedData['name'] == s['name']:
#                 print('already in json')
#                 inJson = True
#     else:
#         data = {'Ingredients':[]}
#     if not (inJson):
#         data['Ingredients'].append(appendedData)
#     with open('data.json', 'w',encoding='utf-8') as f:
#         json.dump(data, f)
#     print('addToJson: checkpoint 3')


# def getData():
#     data = {}
#     with open('data.json', 'r') as f:
#         data = json.load(f)
#     return data

# def searchJson(query):
#     data = getData()
#     print(data)
#     ingredients = data['Ingredients']
#     query = re.escape(query.lower())
#     newIngredients = []
#     print(query)
#     print(ingredients)
#     for d in ingredients:
#         print(d['name'])
#         if (re.search(query,d['name'].lower())):
#             print('remove: '+d['name'])
#             newIngredients.append(d)
#             ingredients.remove(d)
            
#         # print("new:"+d['name'])
#     print('new')
#     for d in newIngredients:
#         print(d['name'])
#     data['Ingredients'] = newIngredients
#     print(data)
#     return data


from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import json
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(20), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.String(20), nullable=False)

def getData():
    ingredients = Ingredient.query.all()
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


def searchData(query):
    ingredients = Ingredient.query.filter(Ingredient.name.ilike(f"%{query}%")).all()
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
