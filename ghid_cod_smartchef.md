# Ghid Complet — Codul SmartChef

## Arhitectura Generala

SmartChef este o aplicatie web full-stack care detecteaza ingrediente alimentare in timp real prin camera si recomanda retete potrivite.

```
┌─────────────────────────────────────────────────────┐
│  FRONTEND (React + Vite)                            │
│  Camera → captura cadre → trimite via WebSocket     │
│  Afiseaza: ingrediente, retete, nutritie            │
└──────────────────────┬──────────────────────────────┘
                       │ WebSocket + REST API
┌──────────────────────▼──────────────────────────────┐
│  BACKEND (FastAPI + Python)                         │
│  Primeste cadre → YOLO detectie → OpenCV validare   │
│  → potrivire retete → calcul nutritie → raspuns     │
└─────────────────────────────────────────────────────┘
```

---

## 1. BACKEND

---

### 1.1 `backend/app.py` — Serverul Principal

**Ce face:** Este "creierul" aplicatiei. Porneste serverul FastAPI, primeste cereri de la frontend si coordoneaza toate modulele.

**Structura codului:**

**Importuri si initializare (liniile 1-35):**
- Importa modulele proprii: `YOLODetector`, `CustomClassifier`, `RecipeMatcher`, `NutritionCalculator`
- Creeaza aplicatia FastAPI si configureaza CORS (permite frontend-ului sa comunice cu backend-ul)
- Instantiaza cele 4 module o singura data la pornirea serverului

**Clasa `DetectionSmoother` — Stabilizare Temporala:**
- **Problema rezolvata:** Fara smoothing, ingredientele "clipesc" — apar si dispar intre cadre consecutive
- **Cum functioneaza:** Tine o fereastra de ultimele 5 cadre. Un ingredient apare in rezultat doar daca a fost detectat in minim 3 din ultimele 5 cadre
- `update()` — primeste ingredientele din cadrul curent, returneaza doar cele stabile
- `get_avg_confidence()` — calculeaza un scor mediu de incredere

**Endpoint-uri REST:**
- `GET /api/health` — verifica ca serverul functioneaza
- `GET /api/recipes` — returneaza toate retetele din baza de date
- `GET /api/recipes/match?ingredients=tomato,egg` — gaseste retete potrivite pentru ingredientele date
- `GET /api/nutrition?ingredients=tomato,egg` — returneaza informatii nutritionale

**Endpoint WebSocket `/ws/detect` — Detectia in Timp Real:**
Acesta este fluxul principal, pas cu pas:
1. Clientul trimite un cadru video codificat base64
2. Se decodeaza in imagine numpy (BGR)
3. **Pasul 1:** YOLO detecteaza obiecte si propune candidati
4. **Pasul 2:** Pentru fiecare detectie, clasificatorul OpenCV valideaza matematic daca patch-ul (bucata de imagine) chiar seamana cu ingredientul propus
5. Se calculeaza un scor combinat: `92% YOLO + 8% OpenCV`, cu bonus pentru candidatul primar si penalizare daca OpenCV da scor foarte mic
6. **Pasul 3:** Smoothing temporal — doar ingredientele stabile raman
7. **Pasul 4:** Se cauta retete potrivite
8. **Pasul 5:** Se calculeaza nutritia
9. Se trimite raspunsul JSON inapoi la frontend

---

### 1.2 `backend/requirements.txt` — Dependente Python

**Ce face:** Lista pachetelor necesare, instalate cu `pip install -r requirements.txt`.

| Pachet | Rol |
|--------|-----|
| `fastapi` | Framework web asincron pentru API |
| `uvicorn` | Server ASGI care ruleaza FastAPI |
| `opencv-python-headless` | Procesare de imagini (fara GUI) |
| `ultralytics` | Biblioteca YOLOv8 pentru detectie obiecte |
| `numpy` | Operatii matematice pe matrici/imagini |
| `websockets` | Suport WebSocket pentru comunicare in timp real |
| `python-multipart` | Parsare date multipart (necesara pentru FastAPI) |

---

### 1.3 `backend/logic/__init__.py` — Init Modul Logic

**Ce face:** Doar 2 linii — face clasele `RecipeMatcher` si `NutritionCalculator` importabile direct din pachetul `logic`.

---

### 1.4 `backend/logic/nutrition.py` — Calculator Nutritie

**Ce face:** Calculeaza valorile nutritionale totale pentru ingredientele detectate.

**Clasa `NutritionCalculator`:**
- `__init__()` — incarca datele din `nutrition_data.json`
- `calculate(ingredient_names)` — pentru fiecare ingredient:
  - Ia datele per 100g din baza de date
  - Inmulteste cu factorul de portie (ex: un ou = 50g, deci factor = 0.5)
  - Aduna totalurile pentru calorii, proteine, carbohidrati, grasimi, fibre
  - Returneaza un dictionar cu `total` si `per_ingredient`

**Exemplu:** Daca detecteaza "egg" + "tomato":
- Ou: 155 cal/100g × 0.5 (50g portie) = 78 cal
- Rosie: 18 cal/100g × 1.2 (120g portie) = 22 cal
- **Total: 100 cal**

---

### 1.5 `backend/logic/recipe_matcher.py` — Algoritmul de Recomandare

**Ce face:** Gaseste cele mai potrivite retete pe baza ingredientelor detectate. Este un **algoritm propriu**, fara biblioteci ML.

**Clasa `RecipeMatcher`:**

**`jaccard_similarity(set_a, set_b)`** — Similaritatea Jaccard:
- Formula: `|A ∩ B| / |A ∪ B|`
- Masoara cat de mult se suprapun cele doua seturi
- Ex: detectate={tomato, egg}, reteta={tomato, egg, onion} → J = 2/3 = 0.67

**`coverage_score(detected, recipe_ingredients)`** — Acoperire ponderata:
- Ingredientele **primary** au greutate 2x, cele **secondary** au greutate 1x
- Verifica cate ingrediente importante sunt acoperite

**`complexity_score(detected, recipe_ingredients)`** — Scor de complexitate:
- `1 - (ingrediente lipsa / total ingrediente)`
- Cu cat lipsesc mai putine, cu atat scorul e mai mare

**`match(detected_ingredients)`** — Scorul final combinat:
- **40%** Jaccard + **35%** Coverage + **25%** Complexity
- Filtreaza retete cu minim 1 ingredient gasit
- Sorteaza descrescator si returneaza top 5

---

### 1.6 `backend/vision/__init__.py` — Init Modul Vision

**Ce face:** Exporta `YOLODetector` si `CustomClassifier` pentru import usor.

---

### 1.7 `backend/vision/yolo_detector.py` — Detectorul YOLO

**Ce face:** Ruleaza modelul YOLOv8 custom antrenat pe imagini si propune ingrediente candidate.

**Dictionarul `DATASET_TO_INGREDIENT`:**
- Mapeaza cele 20 de clase din datasetul de antrenament la cele 9 ingrediente ale aplicatiei
- Exemple: `"apple" → "tomato"` (mere rosii detectate ca rosii), `"orange" → "lemon"` (citrice → lamaie)

**Clasa `YOLODetector`:**
- `__init__()` — incarca modelul custom (`smartchef_custom_model.pt`) sau fallback la `yolov8n.pt`. Confidence threshold = 0.15 (foarte scazut, pentru recall maxim)
- `detect(frame)` — ruleaza YOLO pe cadru, returneaza lista de detectii cu:
  - `bbox` — coordonatele dreptunghiului
  - `confidence` — increderea YOLO
  - `ingredient` — ingredientul mapat
  - `ingredient_candidates` — lista de candidati (pentru clase ambigue, ex: "apple" → ["tomato", "onion"])

---

### 1.8 `backend/vision/custom_classifier.py` — Clasificatorul Matematic

**Ce face:** Acesta este **algoritmul propriu** — valideaza detectiile YOLO folosind tehnici matematice de procesare a imaginilor, **fara nicio biblioteca de machine learning**.

**Clasa `CustomClassifier` — 8 componente:**

**1. `_normalize_lighting()` — Normalizare iluminare:**
- Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization) pe canalul de luminozitate
- Apoi aplica GaussianBlur 5x5 pentru eliminarea zgomotului
- Critic pentru webcam unde umbrele distorsioneaza culorile

**2. `compute_hsv_scores()` — Segmentare culoare HSV:**
- Converteste patch-ul in spatiul HSV (Hue, Saturation, Value)
- Pentru fiecare ingredient, verifica cat de mult din patch se incadreaza in intervalele HSV asteptate
- Ex: rosia are Hue 0-8 sau 172-180 (rosu), saturatie > 150

**3. `compute_lbp()` si `compute_lbp_histogram()` — Textura LBP:**
- **Local Binary Patterns** — implementat manual cu NumPy (fara skimage)
- Pentru fiecare pixel, compara cu cei 8 vecini si creeaza un cod binar pe 8 biti
- Genereaza o histograma de 256 bin-uri care descrie textura suprafetei
- Compara cu histogramele de referinta prin distanta chi-squared

**4. `compute_color_histogram()` si `compute_color_scores()` — Histograme culoare:**
- Calculeaza histograma de 48 bin-uri (16 per canal HSV)
- Compara cu referintele prin chi-squared cu factor exponential

**5. `compute_shape_scores()` — Analiza formei:**
- Calculeaza aspect ratio (latime/inaltime)
- Compara cu intervalele asteptate (ex: banana 1.5-4.0, rosie 0.8-1.3)

**6. `compute_edge_density()` — Densitatea muchiilor:**
- Aplica filtre Sobel pe axele X si Y
- Calculeaza magnitudinea gradientului
- Alimentele au densitate moderata (0.05-0.35); prea mica = fundal, prea mare = scena complexa

**7. `_is_likely_background()` — Rejector de fundal:**
- Verifica 3 conditii: saturatie foarte mica + varianta mica = suprafata gri/alba; luminozitate < 30 = umbra; deviatie standard gri < 8 = suprafata uniforma

**8. `compute_saturation_scores()` — Discriminator saturatie:**
- Cel mai important discriminator pentru perechi confuzabile
- Ex: rosie (saturatie ~180) vs mar (saturatie ~100), ou (saturatie ~15) vs ceapa (saturatie ~70)
- Aplica penalizari puternice daca saturatia nu se potriveste (weight "critical" pentru ou)

**`classify()` — Clasificarea combinata:**
- Formula: 30% HSV + 10% LBP + 22% culoare + 10% forma + 20% saturatie
- Aplica factor de penalizare bazat pe densitatea muchiilor
- Bonus daca YOLO e de acord (cross-validare)
- Filtreaza prin threshold-uri adaptive per ingredient

**`validate()` — Validarea pentru Hybrid Ensemble:**
- Versiune simplificata, evaluaza doar ingredientul asteptat (nu toate)
- Formula: 30% HSV + 15% LBP + 20% culoare + 35% saturatie (saturatia e dominanta)
- Returneaza scor 0.0-1.0 folosit de `app.py` in formula ensemble

---

### 1.9 `backend/vision/reference_profiles.json` — Profile de Referinta

**Ce face:** Contine "amprenta" fiecarui ingredient — datele matematice folosite de clasificator.

**Structura per ingredient:**
- `hsv_ranges` — intervalele de culoare HSV (lower/upper bounds)
- `expected_saturation` — intervalul de saturatie asteptat si importanta (medium/high/critical)
- `color_histogram` — histograma de culoare de referinta (48 valori)
- `lbp_histogram` — histograma LBP de referinta (256 valori)
- `aspect_ratio` — raportul de aspect min/max

---

### 1.10 `backend/data/nutrition_data.json` — Date Nutritionale

**Ce face:** Baza de date cu informatii nutritionale per 100g pentru cele 9 ingrediente.

**Campuri per ingredient:** calories, protein, carbs, fat, fiber, serving_g (portia standard in grame), emoji.

---

### 1.11 `backend/data/recipes.json` — Baza de Date Retete

**Ce face:** Contine 13 retete cu toate detaliile necesare.

**Structura per reteta:**
- `id`, `title`, `category` (breakfast/lunch/dinner), `difficulty`, `time_minutes`
- `tags` — etichete (vegetarian, quick, beginner, healthy)
- `image` — calea catre imaginea retetei
- `video_url` — link YouTube cu video de preparare
- `ingredients` — lista cu `name`, `amount`, `importance` (primary/secondary)
- `steps` — pasii de preparare in ordine

---

### 1.12 `backend/Dockerfile` — Container Backend

**Ce face:** Construieste imaginea Docker pentru backend.

**Pasi:**
1. Porneste de la `python:3.11-slim`
2. Instaleaza dependente sistem pentru OpenCV (libglib, libgl, etc.)
3. Copiaza si instaleaza dependentele Python din `requirements.txt`
4. Copiaza codul sursa
5. Ruleaza serverul: `uvicorn app:app --host 0.0.0.0 --port 8000`

---

## 2. FRONTEND

---

### 2.1 `frontend/index.html` — Pagina HTML

**Ce face:** Punctul de intrare al aplicatiei SPA (Single Page Application).

- Defineste meta taguri SEO (descriere, theme-color)
- Include link catre `manifest.json` pentru functionalitate PWA
- Contine un singur `<div id="root">` unde React randeaza intreaga aplicatie
- Incarca `main.jsx` ca modul ES

---

### 2.2 `frontend/package.json` — Configurare Proiect

**Ce face:** Defineste proiectul npm cu dependente si scripturi.

- **React 19** — framework-ul UI
- **Vite 8** — build tool rapid pentru development
- Scripturi: `dev` (porneste serverul de dezvoltare), `build` (creaza bundle-ul de productie)

---

### 2.3 `frontend/vite.config.js` — Configurare Vite

**Ce face:** Configureaza Vite cu plugin-ul React si proxy.

- **Proxy `/api`** → redirecteaza cererile REST catre `http://localhost:8000`
- **Proxy `/ws`** → redirecteaza WebSocket-ul catre `ws://localhost:8000`
- Astfel frontend-ul (port 5173) comunica transparent cu backend-ul (port 8000)

---

### 2.4 `frontend/eslint.config.js` — Configurare Linter

**Ce face:** Configureaza ESLint cu reguli pentru React hooks si React Refresh. Ignora folderul `dist`.

---

### 2.5 `frontend/src/main.jsx` — Punct de Intrare React

**Ce face:** Randeaza componenta `<App />` in elementul DOM cu id `root`, inconjurata de `<StrictMode>` pentru verificari suplimentare in development.

---

### 2.6 `frontend/src/App.jsx` — Componenta Principala

**Ce face:** Orchestreaza intreaga aplicatie — camera, comunicarea WebSocket, starea globala si layout-ul.

**State-uri (useState):**
- `ingredients` — lista ingredientelor detectate (persistente, se acumuleaza)
- `detections` — bounding boxes din cadrul curent
- `recipes` — retetele recomandate
- `nutrition` — datele nutritionale
- `selectedRecipe` — reteta deschisa in modal

**Efecte (useEffect):**
1. **Procesare mesaje WebSocket** — cand vine un mesaj, actualizeaza detectiile si adauga ingredientele noi la lista existenta (acumulare cu `Set` pentru unicitate)
2. **Fetch retete si nutritie** — cand lista de ingrediente se schimba, face cereri REST la `/api/recipes/match` si `/api/nutrition`
3. **Trimitere cadre periodica** — la fiecare 600ms, captureaza un cadru si il trimite prin WebSocket
4. **Escape pentru modal** — inchide modalul la apasarea tastei Escape

**Functii callback:**
- `handleStartCamera()` — porneste camera si conecteaza WebSocket
- `handleStopCamera()` — opreste totul, curata detectiile
- `handleAddIngredient()` — adauga manual un ingredient
- `handleRemoveIngredient()` — sterge un ingredient din lista

**Render:** Header → WebcamDetector → IngredientChips → RecipeCards → Footer → RecipeModal (conditional)

---

### 2.7 `frontend/src/index.css` — Sistemul de Design

**Ce face:** Tot stilul vizual al aplicatiei — tema dark premium.

**Sectiuni principale:**
- **Variabile CSS** — culori, gradiente, spatiere, raze, tranzitii, font (Inter)
- **Reset si baza** — box-sizing, font smoothing, scrollbar custom
- **Glass Card** — efect de glassmorphism cu backdrop-filter blur
- **Header** — sticky, semi-transparent, cu badge de status animat
- **Webcam** — container cu aspect-ratio 4:3, overlay canvas
- **Ingredient Chips** — chip-uri cu emoji, animatie de aparitie, buton remove, input cu dropdown autocomplete
- **Recipe Cards** — grid responsiv, hover cu translateY + scale + glow violet
- **Recipe Modal** — overlay blur, animatie de intrare, taburi, pasi numerotati, bare nutritionale colorate
- **Animatii** — fadeIn, fadeInUp, chipIn, modalIn, pulse-dot, float
- **Responsive** — layout adaptat pentru 768px si 480px

---

### 2.8 `frontend/src/components/Header.jsx` — Header

**Ce face:** Afiseaza logo-ul "Smart Chef" cu emoji si un badge de status.

- **Logo** — emoji 🍳 + text gradient "Smart Chef"
- **Status badge** — verde "Live" cand WebSocket-ul e conectat, rosu "Offline" cand nu
- **Punct animat** — pulseaza pentru a arata ca conexiunea e activa

---

### 2.9 `frontend/src/components/IngredientChips.jsx` — Ingrediente

**Ce face:** Afiseaza ingredientele detectate si permite adaugarea manuala.

**Constante:**
- `EMOJI_MAP` — asociaza fiecare ingredient cu emoji-ul sau (banana→🍌, tomato→🍅, etc.)
- `KNOWN_INGREDIENTS` — lista celor 9 ingrediente suportate

**Input cu Autocomplete:**
- La click/focus apare un dropdown cu ingredientele disponibile (cele neadaugate inca)
- Filtrare in timp real pe masura ce tastezi
- Navigare cu sageti sus/jos, selectie cu Enter
- Click pe un item il selecteaza instant
- Afiseaza "No matching ingredient found" daca nu exista potrivire
- Se dezactiveaza cand toate ingredientele au fost adaugate

**Chips:**
- Fiecare ingredient apare ca un chip cu emoji + nume + buton ✕ de stergere
- Animatie de aparitie (chipIn — scale de la 0.5 la 1)

---

### 2.10 `frontend/src/components/ParticleBackground.jsx` — Fundal Animat

**Ce face:** Deseneaza particule flotante pe un canvas fullscreen ca fundal decorativ.

- **40 de particule** — pozitii aleatorii, viteze mici, raze 0.5-2.5px
- **Culori** — cyan (hue 186) sau violet (hue 270), opacitate mica
- **Miscarea** — wrap la margini (reapare pe partea opusa)
- **Conexiuni** — daca 2 particule sunt la < 150px distanta, se deseneaza o linie subtila intre ele
- **Performance** — requestAnimationFrame, cleanup la unmount

---

### 2.11 `frontend/src/components/RecipeCard.jsx` — Card Reteta

**Ce face:** Afiseaza un card de previzualizare pentru o reteta din grila.

**Structura:**
- **Imagine** — cu lazy loading si fallback la placeholder daca imaginea lipseste
- **Badge** — procent de potrivire (ex: "85% match")
- **Titlu** — numele retetei
- **Metadate** — timp de preparare, dificultate, numar ingrediente
- **Bara de progres** — vizualizare grafica a procentului de match
- **Taguri** — primele 3 taguri (vegetarian, quick, etc.)
- **Animatie** — fadeInUp cu delay bazat pe index (efect cascada)
- **Accesibilitate** — role="button", tabIndex, suport tastatura

---

### 2.12 `frontend/src/components/RecipeModal.jsx` — Modal Reteta

**Ce face:** Afiseaza detaliile complete ale unei retete intr-un modal overlay.

**Sectiuni:**
- **Header** — imagine mare cu overlay gradient
- **Titlu + buton video** — link catre YouTube cu ▶️ Watch Video
- **Metadate** — timp, dificultate, procent match
- **Ingrediente** — listate cu ✓ (matched, verde) sau ✗ (missing, rosu)
- **Taburi:**
  - **Steps** — pasi numerotati cu linie verticala si cercuri gradient
  - **Nutrition** — 4 bare vizuale (Calories, Protein, Carbs, Fat) cu gradiente diferite
- **Inchidere** — click pe overlay, buton ✕, sau tasta Escape

---

### 2.13 `frontend/src/components/WebcamDetector.jsx` — Camera + Detectii

**Ce face:** Afiseaza feed-ul video si deseneaza bounding boxes peste ingredientele detectate.

**Cand camera e oprita:**
- Afiseaza un placeholder cu emoji 📷, text si buton "Start Camera"

**Cand camera e pornita:**
- `<video>` — afiseaza stream-ul live de la camera
- `<canvas>` — overlay transparent pozitionat peste video
- `drawDetections()` — deseneaza pe canvas:
  - Dreptunghi cyan cu glow pentru fiecare detectie
  - Eticheta cu fundal cyan: "tomato 92%" (ingredient + confidence)
  - Pozitia etichetei: deasupra bbox-ului sau la marginea de sus

---

### 2.14 `frontend/src/hooks/useWebcam.js` — Hook Camera

**Ce face:** Hook custom React care gestioneaza accesul la camera dispozitivului.

**State-uri:** `isActive`, `error`
**Ref-uri:** `videoRef` (elementul video), `streamRef` (stream-ul media)

**Functii:**
- `startCamera()` — cere acces la camera (preferinta: camera din spate, 640x480), seteaza stream-ul pe elementul video
- `stopCamera()` — opreste toate track-urile si curata
- `captureFrame()` — deseneaza cadrul curent pe un canvas temporar, exporta ca base64 JPEG (calitate 70%)
- **Cleanup la unmount** — opreste stream-ul automat cand componenta dispare

---

### 2.15 `frontend/src/hooks/useWebSocket.js` — Hook WebSocket

**Ce face:** Hook custom React care gestioneaza conexiunea WebSocket cu backend-ul.

**State-uri:** `isConnected`, `lastMessage`

**Functii:**
- `connect()` — deschide conexiunea WebSocket, parseaza mesajele JSON primite
- `disconnect()` — inchide conexiunea fara auto-reconectare
- `sendFrame(base64Data)` — trimite un cadru codificat base64 la server
- **Auto-reconectare** — daca conexiunea se pierde, reincearca dupa 3 secunde
- **Cleanup** — inchide conexiunea la unmount

---

## 3. CONFIGURARI

---

### 3.1 `frontend/Dockerfile` — Build Frontend

**Ce face:** Construieste imaginea Docker in 2 etape:

1. **Stage 1 (build):** Node 20 Alpine → `npm ci` → `npm run build` → creaza folderul `dist`
2. **Stage 2 (serve):** Nginx Alpine → copiaza `dist` → copiaza `nginx.conf` → serveste pe portul 80

---

### 3.2 `frontend/nginx.conf` — Configurare Nginx

**Ce face:** Configureaza serverul web Nginx pentru productie.

- **Gzip** — compresie pentru JS, CSS, JSON, SVG
- **Cache** — assets statice cached 7 zile cu header `immutable`
- **Proxy `/api/`** → redirecteaza catre backend-ul Docker pe portul 8000
- **Proxy `/ws/`** → WebSocket upgrade + timeout 24h
- **SPA fallback** — orice ruta necunoscuta serveste `index.html` (rutare client-side)

---

### 3.3 `frontend/public/manifest.json` — Manifest PWA

**Ce face:** Permite instalarea aplicatiei ca Progressive Web App pe mobil.

- Nume: "Smart Chef", tema dark (#0a0a0f), iconita SVG, mod standalone

---

### 3.4 `docker-compose.yml` — Orchestrare Servicii

**Ce face:** Porneste ambele servicii cu o singura comanda `docker-compose up`.

- **smartchef-backend** — portul 8000, health check pe `/api/health`
- **smartchef-frontend** — portul 80, depinde de backend, restart automat

---

## Fluxul Complet (de la camera la reteta)

```
1. Utilizatorul apasa "Start Camera"
   └→ useWebcam.startCamera() → acces camera
   └→ useWebSocket.connect() → WebSocket deschis

2. La fiecare 600ms:
   └→ captureFrame() → base64 JPEG
   └→ sendFrame() → trimis pe WebSocket

3. Backend primeste cadrul:
   └→ base64 → numpy array (imagine BGR)
   └→ YOLODetector.detect() → bounding boxes + candidati
   └→ Pentru fiecare detectie:
       └→ CustomClassifier.validate() → scor OpenCV (0-1)
       └→ Scor final = 92% YOLO + 8% OpenCV + bonusuri/penalizari
   └→ DetectionSmoother → doar ingrediente stabile (3/5 cadre)
   └→ RecipeMatcher.match() → top 5 retete
   └→ NutritionCalculator.calculate() → date nutritionale

4. Raspuns JSON trimis inapoi pe WebSocket:
   └→ App.jsx actualizeaza state-urile
   └→ WebcamDetector deseneaza bounding boxes
   └→ IngredientChips afiseaza ingredientele acumulate
   └→ RecipeCards afiseaza retetele recomandate

5. Click pe o reteta → RecipeModal cu detalii complete
```
