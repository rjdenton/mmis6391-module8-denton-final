document.addEventListener('DOMContentLoaded', () => {
    const favoriteButtons = document.querySelectorAll('.favorite-btn');

    favoriteButtons.forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault();

            const recipeCard = button.closest('.recipe-card');
            const recipeId = recipeCard.dataset.recipeId;
            const isFavorited = button.dataset.favorited === 'true';

            // Send AJAX request to toggle favorite
            try {
                const response = await fetch(`/recipes/favorite/${recipeId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ is_favorited: isFavorited })
                });

                if (response.ok) {
                    const newState = !isFavorited;
                    button.dataset.favorited = newState.toString();
                    button.textContent = newState ? '⭐' : '☆';
                    button.classList.toggle('favorited', newState);
                } else {
                    console.error('Failed to toggle favorite');
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });
});
