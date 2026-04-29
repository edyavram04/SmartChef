export default function RecipeCard({ recipe, onClick, index }) {
  return (
    <article
      className="recipe-card glass-card"
      onClick={() => onClick(recipe)}
      style={{ animationDelay: `${index * 0.08}s` }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick(recipe)}
      aria-label={`View recipe: ${recipe.title}`}
    >
      <div className="recipe-card-image">
        <img
          src={recipe.image?.replace(/^\//, '') || 'placeholder-food.svg'}
          alt={recipe.title}
          loading="lazy"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = `https://placehold.co/400x250/1a1a2e/22d3ee?text=${encodeURIComponent(recipe.title)}`;
          }}
        />
        <span className="match-badge">{recipe.match_percent}% match</span>
      </div>

      <div className="recipe-card-body">
        <h3 className="recipe-card-title">{recipe.title}</h3>

        <div className="recipe-card-meta">
          <span>⏱ {recipe.time_minutes} min</span>
          <span>📊 {recipe.difficulty}</span>
          <span>🥗 {recipe.ingredients?.length || 0} items</span>
        </div>

        <div className="match-bar">
          <div
            className="match-bar-fill"
            style={{ width: `${recipe.match_percent}%` }}
          />
        </div>

        <div className="tags-row">
          {recipe.tags?.slice(0, 3).map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      </div>
    </article>
  );
}
