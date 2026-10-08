# 🛡️ VisionGuard

AI-based video surveillance system that detects security incidents from a camera feed, stores them in PostgreSQL with photo evidence, and shows them live on a web dashboard.

## Features

- **Restricted zone detection**: alerts when a person enters a marked zone (YOLOv8 + tracking)
- **Fall detection** (experimental): flags a person lying down for ~2 seconds
- **Incident storage**: PostgreSQL with cooldown to avoid duplicate alerts
- **Evidence snapshots**: photo saved at the time of every incident
- **REST API**: FastAPI with filters and status updates
- **Live dashboard**: React table, photo preview, filters, status workflow (OPEN, ACKNOWLEDGED, RESOLVED)
- **Live alerts**: blinking banner and beep when a new HIGH/CRITICAL incident arrives

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Detection | Python, OpenCV, Ultralytics YOLOv8 |
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| Frontend | React, Vite |

## Project Structure

```
visionguard/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── database.py         # DB connection
│   │   ├── models.py           # SQLAlchemy model
│   │   ├── crud.py             # save_incident
│   │   ├── incident.py         # Incident + cooldown manager
│   │   ├── restricted_zone.py  # Zone detection script
│   │   └── fall_detection.py   # Fall detection script
│   ├── evidence/               # Saved photos (git-ignored)
│   └── requirements.txt
└── frontend/                   # React dashboard
```

## Setup

### 1. Database

Install PostgreSQL, then create the database:

```
psql -U postgres -c "CREATE DATABASE visionguard;"
```

### 2. Backend

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/visionguard
```

### 3. Frontend

```
cd frontend
npm install
```

## Run

Use three terminals.

**API:**
```
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**Dashboard:**
```
cd frontend
npm run dev
```
Open http://localhost:5173

**Detection (pick one):**
```
cd backend
venv\Scripts\activate
python -m app.restricted_zone
python -m app.fall_detection
```
Press `Q` in the camera window to quit.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/incidents` | List incidents (filters: `camera_id`, `incident_type`, `status`, `limit`) |
| GET | `/api/incidents/{id}` | Incident details |
| PATCH | `/api/incidents/{id}` | Update status |
| GET | `/evidence/{file}.jpg` | Evidence photo |

Interactive docs: http://127.0.0.1:8000/docs

## Notes

- Fall detection uses a bounding-box aspect ratio, so it works best when the full body is visible from a distance. It can give false alerts on close-up laptop cameras.
- The restricted zone polygon is set in `restricted_zone.py` (`RESTRICTED_ZONE`).

## Roadmap

- Multiple cameras
- PPE / helmet detection
- Pose-based fall detection
- Responsive dashboard