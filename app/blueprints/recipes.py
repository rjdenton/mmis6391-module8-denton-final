from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from app.db_connect import get_db
from werkzeug.utils import secure_filename
import os
import requests

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

recipes = Blueprint('recipes', __name__)

@recipes.route('/recipes')
def list_recipes():
    """Display a list of all recipes with favorite status and additional details."""
    connection = get_db()
    user_id = session.get('user_id')  # Get the logged-in user's ID, if available

    query = """
        SELECT recipes.id, recipes.title, recipes.description, recipes.image_path, 
               recipes.meal_type, recipes.category, users.username,
               EXISTS(
                   SELECT 1 FROM favorites 
                   WHERE favorites.recipe_id = recipes.id AND favorites.user_id = %s
               ) AS is_favorite
        FROM recipes
        JOIN users ON recipes.user_id = users.id
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (user_id,))
        recipes = cursor.fetchall()

    return render_template('recipes/list.html', recipes=recipes)

# Function to ensure all ingredients have a default quantity and unit
def format_ingredients(ingredients):
    formatted = []
    for ingredient in ingredients:
        ingredient = ingredient.strip()
        # If no quantity is specified, default to "1 unit"
        if not any(char.isdigit() for char in ingredient):
            ingredient = f"1 unit {ingredient}"
        formatted.append(ingredient)
    return formatted

@recipes.route('/recipes/<int:recipe_id>')
def view_recipe(recipe_id):
    """View details of a single recipe and fetch nutritional information."""
    connection = get_db()
    user_id = session.get('user_id')  # Get logged-in user ID

    # Fetch the recipe details
    query = """
        SELECT recipes.*, 
               users.username,
               EXISTS(
                   SELECT 1 FROM favorites 
                   WHERE favorites.recipe_id = recipes.id AND favorites.user_id = %s
               ) AS is_favorite
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (user_id, recipe_id))
        recipe = cursor.fetchone()

    if not recipe:
        flash("Recipe not found.", "danger")
        return redirect(url_for('recipes.list_recipes'))

    # Extract and format ingredients for the API
    ingredients_list = recipe['ingredients'].split(',')  # Split comma-separated string
    formatted_ingredients = format_ingredients(ingredients_list)
    print("Formatted Ingredients:", formatted_ingredients)

    # Payload for the Edamam API
    payload = {
        "title": recipe['title'],
        "ingr": formatted_ingredients
    }

    # Edamam API configuration
    APP_ID = 'fee31b76'  # Replace with your app ID
    APP_KEY = '9e2335761d271c35e04b500915aa60ea'  # Replace with your app key
    API_URL = 'https://api.edamam.com/api/nutrition-details'

    # Payload for API
    payload = {
        "title": recipe['title'],
        "ingr": formatted_ingredients
    }

    # Fetch nutritional data
    try:
        response = requests.post(
            f'{API_URL}?app_id={APP_ID}&app_key={APP_KEY}',
            json=payload
        )
        if response.status_code == 200:
            nutrition_data = response.json()
            print("Nutrition Data:", nutrition_data)
        else:
            print(f"API Error {response.status_code}: {response.text}")
            nutrition_data = None  # Handle API errors gracefully
    except Exception as e:
        print(f"Error fetching nutritional data: {e}")
        nutrition_data = None

    return render_template('recipes/view.html', recipe=recipe, nutrition_data=nutrition_data)

@recipes.route('/recipes/add', methods=['GET', 'POST'])
def add_recipe():
    if 'user_id' not in session:
        flash("You must be logged in to add a recipe.", "danger")
        return redirect(url_for('users.login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        meal_type = request.form['meal_type']
        category = request.form['category']
        user_id = session['user_id']

        # Handle image upload
        image_file = request.files.get('image')
        image_path = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('static/uploads', filename).replace("\\", "/")
            image_file.save(os.path.join(current_app.root_path, image_path))

        # Insert recipe into database
        connection = get_db()
        query = """
            INSERT INTO recipes (user_id, title, description, ingredients, instructions, image_path, meal_type, category) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        with connection.cursor() as cursor:
            cursor.execute(query,
                           (user_id, title, description, ingredients, instructions, image_path, meal_type, category))
        connection.commit()

        flash("Recipe added successfully!", "success")
        return redirect(url_for('recipes.list_recipes'))

    return render_template('recipes/add.html')

@recipes.route('/recipes/edit/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """Edit an existing recipe."""
    if 'user_id' not in session:
        flash("You must be logged in to edit a recipe.", "danger")
        return redirect(url_for('users.login'))

    connection = get_db()
    query = """
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (recipe_id,))
        recipe = cursor.fetchone()

    if not recipe:
        flash("Recipe not found.", "danger")
        return redirect(url_for('recipes.list_recipes'))

    # Check if the logged-in user is the owner of the recipe
    if session['user_id'] != recipe['user_id']:
        flash("You are not authorized to edit this recipe.", "danger")
        return redirect(url_for('recipes.list_recipes'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        meal_type = request.form['meal_type']
        category = request.form['category']
        image_file = request.files.get('image')

        # Handle image upload
        image_path = recipe['image_path']  # Default to current image
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('static/uploads', filename).replace("\\", "/")
            image_file.save(os.path.join(current_app.root_path, image_path))

        # Update recipe in the database
        update_query = """
            UPDATE recipes
            SET title = %s, description = %s, ingredients = %s, instructions = %s, image_path = %s, meal_type = %s, category = %s
            WHERE id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(update_query, (title, description, ingredients, instructions, image_path, meal_type, category, recipe_id))
        connection.commit()

        flash("Recipe updated successfully!", "success")
        return redirect(url_for('recipes.view_recipe', recipe_id=recipe_id))

    return render_template('recipes/edit.html', recipe=recipe)

@recipes.route('/recipes/delete/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    """Delete an existing recipe."""
    print(f"Attempting to delete recipe ID: {recipe_id}")

    if 'user_id' not in session:
        flash("You must be logged in to delete a recipe.", "danger")
        return redirect(url_for('users.login'))

    connection = get_db()

    # Fetch the recipe to check ownership
    query = "SELECT * FROM recipes WHERE id = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (recipe_id,))
        recipe = cursor.fetchone()

    if not recipe:
        flash("Recipe not found.", "danger")
        return redirect(url_for('recipes.list_recipes'))

    # Check if the logged-in user is the owner of the recipe
    if session['user_id'] != recipe['user_id']:
        flash("You are not authorized to delete this recipe. Only the recipe's creator can delete it.", "danger")
        return redirect(url_for('recipes.list_recipes'))

    # Delete the recipe
    delete_query = "DELETE FROM recipes WHERE id = %s"
    with connection.cursor() as cursor:
        cursor.execute(delete_query, (recipe_id,))
    connection.commit()

    flash("Recipe deleted successfully!", "success")
    return redirect(url_for('recipes.list_recipes'))

@recipes.route('/recipes/favorite/<int:recipe_id>', methods=['POST'])
def toggle_favorite(recipe_id):
    """Toggle the favorite status of a recipe for the logged-in user."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db()
    user_id = session['user_id']

    # Check if the recipe is already favorited
    query = "SELECT * FROM favorites WHERE user_id = %s AND recipe_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (user_id, recipe_id))
        favorite = cursor.fetchone()

    if favorite:
        # Remove from favorites
        query = "DELETE FROM favorites WHERE user_id = %s AND recipe_id = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, (user_id, recipe_id))
        connection.commit()
        return jsonify({"message": "Unfavorited", "is_favorited": False})
    else:
        # Add to favorites
        query = "INSERT INTO favorites (user_id, recipe_id) VALUES (%s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(query, (user_id, recipe_id))
        connection.commit()
        return jsonify({"message": "Favorited", "is_favorited": True})

@recipes.route('/recipes/search')
def search_recipes():
    """Search for recipes based on a query."""
    user_query = request.args.get('query', '').strip()  # User input
    connection = get_db()

    if not user_query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for('recipes.list_recipes'))

    search_query = f"%{user_query}%"
    sql_query = """
        SELECT recipes.id, recipes.title, recipes.description, recipes.image_path,
               recipes.meal_type, recipes.category, users.username
        FROM recipes
        JOIN users ON recipes.user_id = users.id
        WHERE recipes.title LIKE %s OR recipes.description LIKE %s OR recipes.category LIKE %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_query, (search_query, search_query, search_query))
        results = cursor.fetchall()

    # Pass the user's query to the template
    return render_template('recipes/search_results.html', query=user_query, results=results)

@recipes.route('/recipes/filter')
def filter_recipes():
    """Filter recipes by meal type."""
    meal_type = request.args.get('meal_type', '').strip()
    connection = get_db()

    if meal_type:
        query = """
            SELECT recipes.id, recipes.title, recipes.description, recipes.image_path,
                   recipes.meal_type, recipes.category, users.username
            FROM recipes
            JOIN users ON recipes.user_id = users.id
            WHERE recipes.meal_type = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, (meal_type,))
            recipes = cursor.fetchall()
    else:
        # If no filter, return all recipes
        query = """
            SELECT recipes.id, recipes.title, recipes.description, recipes.image_path,
                   recipes.meal_type, recipes.category, users.username
            FROM recipes
            JOIN users ON recipes.user_id = users.id
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            recipes = cursor.fetchall()

    return render_template('recipes/list.html', recipes=recipes)


