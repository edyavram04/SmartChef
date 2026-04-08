import { useState } from 'react';

export default function RecipeModal({ recipe, nutrition, onClose }) {
  const [activeTab, setActiveTab] = useState('steps');

  if (!recipe) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  const maxCal = nutrition?.total?.calories || 500;
  const bars = nutrition
    ? [
        { key: 'calories', label: 'Calories', value: nutrition.total.calories, unit: 'kcal', max: maxCal },
        { key: 'protein', label: 'Protein', value: nutrition.total.protein, unit: 'g', max: 60 },
        { key: 'carbs', label: 'Carbs', value: nutrition.total.carbs, unit: 'g', max: 100 },
        { key: 'fat', label: 'Fat', value: nutrition.total.fat, unit: 'g', max: 50 },
      ]
    : [];

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-content" role="dialog" aria-label={recipe.title}>
        {/* Header image */}
        <div className="modal-header">
          <img
            src={recipe.image || '/placeholder-food.svg'}
            alt={recipe.title}
            onError={(e) => {
              e.target.src = `https://placehold.co/700x220/1a1a2e/22d3ee?text=${encodeURIComponent(recipe.title)}`;
            }}
          />
          <div className="modal-header-overlay" />
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="modal-body">
          <h2 className="modal-title">{recipe.title}</h2>

          <div className="modal-meta">
            <span>⏱ {recipe.time_minutes} min</span>
            <span>📊 {recipe.difficulty}</span>
            <span>🎯 {recipe.match_percent}% match</span>
          </div>

          {/* Ingredients (matched / missing) */}
          <div className="modal-ingredients">
            {recipe.matched_ingredients?.map((i) => (
              <span key={i} className="modal-ingredient matched">✓ {i}</span>
            ))}
            {recipe.missing_ingredients?.map((i) => (
              <span key={i} className="modal-ingredient missing">✗ {i}</span>
            ))}
          </div>

          {/* Tabs */}
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'steps' ? 'active' : ''}`}
              onClick={() => setActiveTab('steps')}
            >
              📋 Steps
            </button>
            <button
              className={`tab ${activeTab === 'nutrition' ? 'active' : ''}`}
              onClick={() => setActiveTab('nutrition')}
            >
              📊 Nutrition
            </button>
          </div>

          {/* Tab content */}
          {activeTab === 'steps' && (
            <ol className="steps-list">
              {recipe.steps?.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          )}

          {activeTab === 'nutrition' && nutrition && (
            <div className="nutrition-grid">
              {bars.map((b) => (
                <div key={b.key} className="nutrition-item">
                  <div className="nutrition-label">{b.label}</div>
                  <div className="nutrition-value">
                    {b.value} <small style={{ fontSize: '0.6em', color: 'var(--text-muted)' }}>{b.unit}</small>
                  </div>
                  <div className="nutrition-bar">
                    <div
                      className={`nutrition-bar-fill ${b.key}`}
                      style={{ width: `${Math.min((b.value / b.max) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'nutrition' && !nutrition && (
            <div className="empty-state">
              <p>Nutrition data not available for this combination.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
