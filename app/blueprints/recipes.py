from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from app.db_connect import get_db
from werkzeug.utils import secure_filename
import os

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

@recipes.route('/recipes/<int:recipe_id>')
def view_recipe(recipe_id):
    """View details of a single recipe."""
    connection = get_db()
    query = "SELECT * FROM recipes WHERE id = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (recipe_id,))
        recipe = cursor.fetchone()

    if not recipe:
        flash("Recipe not found.", "danger")
        return redirect(url_for('recipes.list_recipes'))

    return render_template('recipes/view.html', recipe=recipe)


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
    connection = get_db()
    query = "SELECT * FROM recipes WHERE id = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (recipe_id,))
        recipe = cursor.fetchone()

    if not recipe:
        flash("Recipe not found.", "danger")
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
    connection = get_db()
    user_id = session.get('user_id')

    if not user_id:
        flash("You must be logged in to delete a recipe.", "danger")
        return redirect(url_for('users.login'))

    query = "DELETE FROM recipes WHERE id = %s AND user_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (recipe_id, user_id))
    connection.commit()

    flash("Recipe deleted successfully!", "success")
    return redirect(url_for('recipes.list_recipes'))

from flask import jsonify, request

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




