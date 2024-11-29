document.addEventListener('DOMContentLoaded', () => {
    const favoriteButtons = document.querySelectorAll('.favorite-btn');

    favoriteButtons.forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault(); // Prevent the form from submitting normally

            const recipeCard = button.closest('.recipe-card') || button.closest('.recipe-container');
            const recipeId = recipeCard?.dataset.recipeId;
            if (!recipeId) {
                console.error('Recipe ID not found.');
                return;
            }

            const isFavorited = button.dataset.favorited === 'true';

            try {
                const response = await fetch(`/recipes/favorite/${recipeId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ is_favorited: isFavorited })
                });

                if (response.ok) {
                    const data = await response.json();
                    const newState = data.is_favorited;
                    button.dataset.favorited = newState.toString();
                    button.textContent = newState ? '⭐' : '☆';
                    button.classList.toggle('favorited', newState);
                } else {
                    console.error('Failed to toggle favorite.');
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });
});
