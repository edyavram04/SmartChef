import { useState, useEffect, useCallback, useRef } from 'react';
import Header from './components/Header';
import ParticleBackground from './components/ParticleBackground';
import WebcamDetector from './components/WebcamDetector';
import IngredientChips from './components/IngredientChips';
import RecipeCard from './components/RecipeCard';
import RecipeModal from './components/RecipeModal';
import { useWebSocket } from './hooks/useWebSocket';
import { useWebcam } from './hooks/useWebcam';

const WS_URL = `ws://${window.location.hostname}:8000/ws/detect`;
const API_BASE = `http://${window.location.hostname}:8000`;
const FRAME_INTERVAL = 600; // ms between frames sent to backend

export default function App() {
  const { isConnected, lastMessage, connect, disconnect, sendFrame } = useWebSocket(WS_URL);
  const { videoRef, isActive, startCamera, stopCamera, captureFrame } = useWebcam();

  const [ingredients, setIngredients] = useState([]);
  const [detections, setDetections] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [nutrition, setNutrition] = useState(null);
  const [selectedRecipe, setSelectedRecipe] = useState(null);

  const intervalRef = useRef(null);

  // Process incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage || lastMessage.error) return;

    if (lastMessage.detections) {
      setDetections(lastMessage.detections);
    }

    if (lastMessage.ingredients?.length > 0) {
      setIngredients((prev) => {
        const combined = new Set([...prev, ...lastMessage.ingredients]);
        return [...combined].sort();
      });
    }
  }, [lastMessage]);

  // Fetch recipes and nutrition dynamically when accumulated ingredients change
  useEffect(() => {
    if (ingredients.length > 0) {
      fetch(`${API_BASE}/api/recipes/match?ingredients=${ingredients.join(',')}`)
        .then((r) => r.json())
        .then((data) => {
          if (data.matches) setRecipes(data.matches);
        })
        .catch(console.error);

      fetch(`${API_BASE}/api/nutrition?ingredients=${ingredients.join(',')}`)
        .then((r) => r.json())
        .then((data) => setNutrition(data))
        .catch(console.error);
    } else {
      setRecipes([]);
      setNutrition(null);
    }
  }, [ingredients]);

  // Periodically send frames when camera is active
  useEffect(() => {
    if (isActive && isConnected) {
      intervalRef.current = setInterval(() => {
        const frame = captureFrame();
        if (frame) sendFrame(frame);
      }, FRAME_INTERVAL);
    }

    return () => clearInterval(intervalRef.current);
  }, [isActive, isConnected, captureFrame, sendFrame]);

  const handleStartCamera = useCallback(async () => {
    await startCamera();
    connect();
  }, [startCamera, connect]);

  const handleStopCamera = useCallback(() => {
    clearInterval(intervalRef.current);
    stopCamera();
    disconnect();
    setDetections([]);
  }, [stopCamera, disconnect]);

  const handleAddIngredient = useCallback((name) => {
    const trimmed = name.trim().toLowerCase();
    if (trimmed) {
      setIngredients((prev) => {
        const combined = new Set([...prev, trimmed]);
        return [...combined].sort();
      });
    }
  }, []);

  const handleRemoveIngredient = useCallback((name) => {
    setIngredients((prev) => prev.filter((i) => i !== name));
  }, []);

  // Close modal on Escape
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') setSelectedRecipe(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <>
      <ParticleBackground />
      <Header isConnected={isConnected} />

      <main>
        <WebcamDetector
          videoRef={videoRef}
          isActive={isActive}
          detections={detections}
          onStart={handleStartCamera}
          onStop={handleStopCamera}
        />

        <IngredientChips
          ingredients={ingredients}
          onRemove={handleRemoveIngredient}
          onAdd={handleAddIngredient}
        />

        <section className="recipes-section">
          <div className="app-container">
            <div className="section-title">
              <span className="icon">🍽️</span>
              <h2>Recommended Recipes</h2>
            </div>

            {recipes.length > 0 ? (
              <div className="recipes-grid">
                {recipes.map((recipe, i) => (
                  <RecipeCard
                    key={recipe.id}
                    recipe={recipe}
                    index={i}
                    onClick={setSelectedRecipe}
                  />
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="icon">🔍</div>
                <p>
                  {ingredients.length > 0
                    ? 'No matching recipes found. Try adding more ingredients!'
                    : 'Start the camera to detect ingredients and discover recipes.'}
                </p>
              </div>
            )}
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <p>Smart Chef — AI-Powered Recipe Recommendations • Built with React + FastAPI + YOLO</p>
      </footer>

      {selectedRecipe && (
        <RecipeModal
          recipe={selectedRecipe}
          nutrition={nutrition}
          onClose={() => setSelectedRecipe(null)}
        />
      )}
    </>
  );
}
