const EMOJI_MAP = {
  apple: '🍎',
  banana: '🍌',
  carrot: '🥕',
  tomato: '🍅',
  egg: '🥚',
  onion: '🧅',
  lemon: '🍋',
  'bell pepper': '🫑',
  cucumber: '🥒',
  potato: '🥔',
};

export default function IngredientChips({ ingredients, onRemove }) {
  return (
    <section className="ingredients-section">
      <div className="app-container">
        <div className="section-title">
          <span className="icon">🧾</span>
          <h2>Detected Ingredients</h2>
          {ingredients.length > 0 && (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginLeft: '8px' }}>
              ({ingredients.length})
            </span>
          )}
        </div>

        <div className="chips-container">
          {ingredients.length === 0 ? (
            <div className="no-ingredients">
              No ingredients detected yet — start the camera and show some food!
            </div>
          ) : (
            ingredients.map((name) => (
              <span key={name} className="chip">
                <span className="emoji">{EMOJI_MAP[name] || '🍽️'}</span>
                {name}
                <button
                  className="remove"
                  onClick={() => onRemove(name)}
                  aria-label={`Remove ${name}`}
                >
                  ✕
                </button>
              </span>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
