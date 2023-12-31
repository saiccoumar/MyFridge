# MyFridge: A SQLite Based Food Inventory System
<p align="center">
  <img width="100%" height="auto" src="https://github.com/saiccoumar/MyFridge/assets/55699636/146d1d3e-d902-423c-9fb8-5fa96dedfa5e">
  <em> https://www.pinterest.com/triviastar </em>
</p>
by Sai Coumar
<br />
Sections: <br />
[Introduction](#introduction) <br />
[Usage](#usage)<br />
[Features of MyFridge](#features)<br />
[Development Process and Design Notes](#development-process)<br />
[Takeaways](#takeaways)<br />

# Introduction
Welcome to my course project for information systems! This is a SQLLite Food Inventory system built with python, flask, sqlalchemy, and basic html for the UI. I'll cover the usage, features, and some takeaways from this project. I'll also be covering some of the tools used to build this in depth and notes from the design process. Note that some of the data I used wasn't very accurate so some things don't make sense. Like a pizza with 17,000 calories.

# Usage
To run the application, run the following command from the main directory
```
python main.py
```

The following webpage will be opened in your default web browser. 
![image](https://github.com/saiccoumar/MyFridge/assets/55699636/01fe195a-a95d-407a-a594-0603e6303046)

From here you can navigate the application with the UI

# Features
MyFridge has several features. The main functionality is being able to add custom ingredients to the inventory, as well as relevant information (Ingredient, Unit, Calories per Unit, Quantity). Relevant information about calories and units can be found from food health websites, like https://www.nutritionix.com/  
![image](https://github.com/saiccoumar/MyFridge/assets/55699636/1834f2b6-b560-4c97-aadb-cacb544e0ea0)

Users can manually increment/decrement the quantity of ingredients or take advantage of the restock feature. When a user makes a mass restock, via a grocery run, they can use a restock form instead of manually incrementing the ingredients' quantity one by one. There's a search feature so users can search for the ingredients they've restocked 
![image](https://github.com/saiccoumar/MyFridge/assets/55699636/f9f420ba-d272-4fd5-8bf9-2a7d5068c313)

Since ingredients can accumulate, there's a search feature with multiple filtering options. I'll cover how this works in detail later.
![image](https://github.com/saiccoumar/MyFridge/assets/55699636/c7c07ff9-d1bd-430c-a7e1-ac429293bf35)

MyFridge also manages users' recipes. A user can 'use' a recipe and MyFridge will automatically update the inventory to keep track of the ingredients consumed. Ideally, a user would upload recipes they use often. When they make a meal, they'll 'consume' the recipe as well as all the ingredients required. The recipes can also be searched, similar to ingredients. 
![image](https://github.com/saiccoumar/MyFridge/assets/55699636/8989ff8d-6e01-4a3b-9008-3a0874153bac)

Recipes can be viewed as well, in case a user needs a reminder on how to make a dish. Further information about the dish is displayed as well (ex. cuisine, diet type). 
![image](https://github.com/saiccoumar/MyFridge/assets/55699636/85ebad93-c364-4bf2-b03d-8d78ebeba76f)

# Development Process
When I started designing this project, there were the big three components to consider. The front-end, the back-end, and the database system. Since this project focuses more on the database system, I opted to reuse the html front-end and flask back-end from another project, and spent more effort on designing and polishing the database system. There were many options I considered for the DBMS: MySQL, SQLite (SQLAlchemy), MongoDB, Neo4j, etc. I ruled out non-relational DBMS systems since the added flexibility wouldn't have provided me any benefit and I got more value out of the structured record systems. I could also use more features like ORMs and Stored Procedures that aren't available in non-relational DBMS, and there were some search benefits as well. Between MySQL an SQLite...SQLite is just easier. For production environments and applications, MySQL is objectively better, but for my small-scale locally hosted application using SQLite was much easier. Setting up a MySQL sequel for a small DBMS was so excessive. 
Before any programming, I made an ERD for the database:
<br />
![db_design](https://github.com/saiccoumar/MyFridge/assets/55699636/9b65890d-f34c-4001-99d1-9ce6602aaeac)
With the following schemas:
```
TABLE Ingredients ( 
ingredient_id INTEGER PRIMARY KEY,
ingredient_name TEXT,
quantity_available REAL,
calories_per_unit INTEGER
); 

TABLE Recipes ( 
recipe_id INTEGER PRIMARY KEY,
recipe_name TEXT, 
DietType TEXT, 
ApproximateTotalCalories INTEGER,
Cuisine TEXT
);

TABLE RecipeIngredients ( 
PRIMARY KEY (recipe_id, ingredient_id),
recipe_id INTEGER,
ingredient_id INTEGER, 
quantity_required REAL
);
```

Then I sketched out the UI:
<p align="middle">
  <img src="https://github.com/saiccoumar/MyFridge/assets/55699636/3227c112-56fd-4a65-b600-2f6539e9e303" width="30%" />
  <img src="https://github.com/saiccoumar/MyFridge/assets/55699636/6af8a925-83e1-4065-8ab8-c7c8e6b9c309" width="30%" /> 
  <img src="https://github.com/saiccoumar/MyFridge/assets/55699636/5a436197-9233-4c8a-9ba1-1174c25d2430" width="30%" />
</p>
<p align="middle">

  <img src="https://github.com/saiccoumar/MyFridge/assets/55699636/c82f272a-88d6-429a-b64b-3c839a17c02f" width="30%" />
  <img src="https://github.com/saiccoumar/MyFridge/assets/55699636/36165f34-9a77-4aca-af3a-4ce85e34c95d" width="30%" />
</p>

While implementing the DBMS, I used Object-Relational Mapping to define my tables and add items into the DBMS. This was a feature of SQLAlchemy that isn't standard with SQLite3 and really came in handy. This simplified the upload process as well as simple accesses to the database such as get_by_id and delete. For the search feature, I used a store procedure approach for a more distinct result. I made the stored procedure by concatenating predefined strings with input strings to form a whole query and then ran said query. 
To improve searching speed, I indexed the database based on likely common searches. 

### Indexes available:
> db.Index('idx_name_unit', Ingredient.name, Ingredient.unit)
> Specific Queries that benefit:
> order by name, unit - SELECT * FROM (SELECT * FROM ingredient WHERE LOWER(ingredient.name) LIKE {pattern})  ORDER BY {[name, unit]}

> db.Index('idx_name', Ingredient.name)
> Specific Queries that benefit:
> order by name - SELECT * FROM (SELECT * FROM ingredient WHERE LOWER(ingredient.name) LIKE {pattern})  ORDER BY {[name]}
> order by name - Ingredient.query.filter_by(name=request.form['name']).first()
> order by name - Ingredient.query.filter(Ingredient.name.ilike(f"%{ingredient_search}%")).all()

> db.Index('idx_unit', Ingredient.unit)
> Specific Queries that benefit:
> order by unit - SELECT * FROM (SELECT * FROM ingredient WHERE LOWER(ingredient.name) LIKE {pattern})  ORDER BY {[unit]}

> db.Index('idx_quantity', Ingredient.quantity)
> Specific Queries that benefit:
> order by quantity - SELECT * FROM (SELECT * FROM ingredient WHERE LOWER(ingredient.name) LIKE {pattern})  ORDER BY {[quantity]}
> filter for quantity != 0 to show in stock items - SELECT * FROM (SELECT * FROM ingredient WHERE LOWER(ingredient.name) LIKE {pattern})  ORDER BY {[quantity]} WHERE quantity > 0


> db.Index('idx_calories', Ingredient.calories)
> Specific Queries that benefit:
> order by calories - SELECT * FROM (SELECT * FROM ingredient WHERE LOWER(ingredient.name) LIKE {pattern})  ORDER BY {[calories]}

I chose to index on any of the filtering options so that the reports would generate faster. I also picked the composite key of name, unit as well as individual keys because I think those are the keys that users will want to generate reports on the most frequently. There are cases where a user could order by every option, but I imagine those are much more unlikely and the efficiency benefit might not outweigh the cons of having so many indexes.

# Takeaways
During the development of this project, there were a lot of recurring ideas that came up.
1. SQLite and relational databases are absurdly valuable; having a structure made modifying data and synchronizing record consistency extremely simple. Prior to this, I had always preferred JSON format because of how flexible it was (and how little effort I put into data structure), but structured data with predefined schemas helps make transactions easier to track and enforced ACID properites make transactions reliable. This whole application would've been much messier had I used non-relational JSON formatted data instead and I saved myself a huge headache using SQLite instead
2. Flask/HTML is getting old. My design sucks and just looking at some ways I could improve it, it became very clear just how much more prevalent Javascript frameworks have become in creating UIs. A lot can change in a few years
3. Routing can get extremely complex along the way. In my main.py, I have 14 routes, some of which are subroutes. A lot of this can be refactored to be more readable and I wish I had planned that ahead of time instead of cluttering up my code. In a production application, I would've separated recipes into it's own API that the MyFridge would redirect to rather than take a monolothic approach. 

