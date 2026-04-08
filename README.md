# 🍳 Smart Chef — AI-Powered Recipe Recommendations

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Point your camera at ingredients. Get instant recipe recommendations powered by computer vision.

Smart Chef uses **real-time video analysis** to identify ingredients through your webcam, then recommends matching recipes using a custom scoring algorithm — all running locally via Docker.

---

## ✨ Features

- **🎥 Real-time Detection** — WebSocket-powered live video analysis at ~2fps
- **🧠 Hybrid AI Pipeline** — YOLOv8 object detection + custom classification (HSV, LBP, color histograms)
- **🍽️ Smart Matching** — Jaccard similarity + weighted coverage scoring with match percentages
- **📊 Nutrition Calculator** — Automatic calorie, protein, carbs, fat breakdown
- **🌙 Premium Dark UI** — Glassmorphism, particle animations, micro-interactions
- **📱 PWA Ready** — Installable on mobile, works on any device with a camera
- **🐳 Docker Containerized** — One command to run everything

---

## 🏗️ Architecture

```
Browser (React)  ←— WebSocket —→  FastAPI Backend
    │                                    │
    ├── Webcam capture                   ├── YOLOv8n detection
    ├── Canvas overlay                   ├── Custom HSV/LBP classifier
    ├── Ingredient chips                 ├── Jaccard recipe matcher
    └── Recipe modal                     └── Nutrition calculator
```

---

## 🚀 Quick Start

### With Docker (Recommended)

```bash
docker-compose up --build
```

Then open [http://localhost](http://localhost) in your browser.

### Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 How It Works

### 1. Object Detection (YOLOv8)
Pre-trained YOLOv8 nano model identifies food objects in the video frame, producing bounding boxes.

### 2. Custom Classification Pipeline (No ML Libraries)
Each bounding box is processed through a **hand-written** pipeline:

| Step | Method | What It Does |
|------|--------|-------------|
| **Color Segmentation** | HSV masking | Identifies dominant colors (red=tomato, yellow=banana) |
| **Texture Analysis** | Local Binary Patterns (LBP) | Computes 8-bit texture codes per pixel, builds histogram |
| **Color Matching** | Chi-squared histogram distance | Compares color distribution against reference profiles |
| **Shape Analysis** | Aspect ratio comparison | Distinguishes elongated (banana, carrot) from round (apple, tomato) |

Final score = `0.35×HSV + 0.20×LBP + 0.30×Color + 0.15×Shape`

### 3. Recipe Matching
Custom Jaccard-based algorithm:
- **Jaccard Similarity**: `J(A,B) = |A∩B| / |A∪B|`
- **Coverage Score**: Weighted by ingredient importance (primary vs secondary)
- **Complexity Score**: Fewer missing ingredients = higher rank

---

## 📦 Supported Ingredients

🍎 Apple • 🍌 Banana • 🥕 Carrot • 🍅 Tomato • 🥚 Egg • 🧅 Onion • 🍋 Lemon • 🫑 Bell Pepper • 🥒 Cucumber • 🥔 Potato

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite, Vanilla CSS |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Computer Vision** | OpenCV, YOLOv8n (Ultralytics), NumPy |
| **Real-time** | WebSocket (native) |
| **Deployment** | Docker, Nginx, docker-compose |

---

## 📁 Project Structure

```
SmartChef/
├── backend/
│   ├── app.py                    # FastAPI + WebSocket server
│   ├── vision/
│   │   ├── yolo_detector.py      # YOLOv8 wrapper
│   │   ├── custom_classifier.py  # 🌟 HSV + LBP + histograms
│   │   └── reference_profiles.json
│   ├── logic/
│   │   ├── recipe_matcher.py     # 🌟 Jaccard + scoring
│   │   └── nutrition.py
│   └── data/
│       ├── recipes.json
│       └── nutrition_data.json
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/           # React components
│   │   ├── hooks/                # useWebSocket, useWebcam
│   │   └── styles/
│   ├── nginx.conf
│   └── Dockerfile
└── docker-compose.yml
```

---

## 📄 License

MIT — feel free to use this for your own projects.
