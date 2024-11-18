from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.db_connect import get_db

favorites = Blueprint('favorites', __name__)

@favorites.route('/favorites')
def list_favorites():
    """Display the user's favorited recipes."""
    if 'user_id' not in session:
        flash("You must be logged in to view your favorites.", "danger")
        return redirect(url_for('users.login'))

    user_id = session['user_id']
    connection = get_db()

    query = """
        SELECT recipes.id, recipes.title, recipes.description, users.username
        FROM favorites
        JOIN recipes ON favorites.recipe_id = recipes.id
        JOIN users ON recipes.user_id = users.id
        WHERE favorites.user_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (user_id,))
        favorites = cursor.fetchall()

    return render_template('favorites/list.html', favorites=favorites)
