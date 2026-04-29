import { useState, useRef, useEffect } from 'react';

const EMOJI_MAP = {
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

const KNOWN_INGREDIENTS = Object.keys(EMOJI_MAP);

export default function IngredientChips({ ingredients, onRemove, onAdd }) {
  const [inputValue, setInputValue] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const wrapperRef = useRef(null);

  // Available = known ingredients minus already-added ones
  const available = KNOWN_INGREDIENTS.filter((ing) => !ingredients.includes(ing));

  // Filtered by search text
  const filtered = inputValue.trim()
    ? available.filter((ing) =>
        ing.toLowerCase().includes(inputValue.trim().toLowerCase())
      )
    : available;

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectIngredient = (name) => {
    if (onAdd) onAdd(name);
    setInputValue('');
    setShowDropdown(false);
    setActiveIndex(-1);
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    setShowDropdown(true);
    setActiveIndex(-1);
  };

  const handleFocus = () => {
    setShowDropdown(true);
    setActiveIndex(-1);
  };

  const handleKeyDown = (e) => {
    if (!showDropdown || filtered.length === 0) {
      if (e.key === 'Escape') {
        setShowDropdown(false);
        setActiveIndex(-1);
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev < filtered.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : filtered.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < filtered.length) {
        selectIngredient(filtered[activeIndex]);
      } else if (filtered.length === 1) {
        // Auto-select if there's only one match
        selectIngredient(filtered[0]);
      }
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
      setActiveIndex(-1);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (activeIndex >= 0 && filtered.length > 0) {
      selectIngredient(filtered[activeIndex]);
    } else if (filtered.length === 1) {
      selectIngredient(filtered[0]);
    }
  };

  const allAdded = available.length === 0;

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

        <div className="add-ingredient-row" ref={wrapperRef}>
          <form onSubmit={handleSubmit} className="add-ingredient-form">
            <div className="autocomplete-wrapper">
              <input
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onFocus={handleFocus}
                onKeyDown={handleKeyDown}
                placeholder={allAdded ? 'All ingredients added ✓' : 'Click to select an ingredient…'}
                className="ingredient-input"
                autoComplete="off"
                disabled={allAdded}
              />

              {showDropdown && filtered.length > 0 && (
                <ul className="autocomplete-dropdown">
                  {filtered.map((name, i) => (
                    <li
                      key={name}
                      className={`autocomplete-item${i === activeIndex ? ' active' : ''}`}
                      onMouseDown={() => selectIngredient(name)}
                      onMouseEnter={() => setActiveIndex(i)}
                    >
                      <span className="autocomplete-emoji">{EMOJI_MAP[name] || '🍽️'}</span>
                      <span className="autocomplete-name">{name}</span>
                    </li>
                  ))}
                </ul>
              )}

              {showDropdown && filtered.length === 0 && inputValue.trim() && (
                <ul className="autocomplete-dropdown">
                  <li className="autocomplete-item no-match">
                    <span className="autocomplete-emoji">🚫</span>
                    <span className="autocomplete-name">No matching ingredient found</span>
                  </li>
                </ul>
              )}
            </div>
          </form>
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
