# AI Paperwork Co-pilot (Doculyzer)

An AI-powered paperwork co-pilot that builds a **persistent, explainable Company Memory Graph** to extract, reason over, and auto-fill business documents with a **human-in-the-loop** review flow.

## Tech Stack

- **Frontend**: React + TypeScript (Vite)
- **Backend**: FastAPI (Python)
- **Database**: SQLite by default for local dev (PostgreSQL supported via `DATABASE_URL`)
- **File Storage**: Local filesystem abstraction

## What It Does Today

- **Unified workflow UI**: Upload a PDF → analyze it → propose field matches → generate an explainable fill plan.
- **Company Memory Graph**: Canonical facts (`company_facts`) backed by raw extractions (`extracted_fields`) and a full audit trail (`fact_history`).
- **Explainable autofill**: Detect PDF form fields, match to facts, fill a preview PDF, and return per-field explanations (source + reason + confidence).
- **ML-powered analysis (optional)**: PyTorch + Transformers integration with lazy loading and heuristic fallback.

## Project Structure

```
ProjectParaLegal/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   │   └── v1/         # API version 1
│   │   ├── core/           # Core configuration
│   │   └── storage/        # File storage abstraction
│   ├── main.py             # FastAPI application entry point
│   ├── requirements.txt    # Python dependencies
│   └── .env.example       # Environment variables template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.tsx         # Main application component
│   │   └── main.tsx       # React entry point
│   ├── package.json       # Node dependencies
│   └── vite.config.ts     # Vite configuration
└── README.md              # This file
```

## Prerequisites

- Python 3.9+ (recommended: 3.11+)
- Node.js 18+ and npm/yarn
- PostgreSQL 12+

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` if you want to override defaults (optional for local dev).

6. **Database**

   By default, the backend uses **SQLite** (no setup required):
   - `DATABASE_URL=sqlite:///./paperwork_copilot.db`

   To use **PostgreSQL**, set `DATABASE_URL` in `backend/.env` (example):

   ```bash
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/paperwork_copilot
   ```

7. **Run the development server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/api/v1/health`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` if you need to change the API base URL.

4. **Run the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Demo / How to Use

1. Start backend and frontend (see above).
2. Open the UI at `http://localhost:5173`.
3. Use **Upload & Fill** to upload a PDF and walk through the analysis + suggested fill plan.
4. Use **Company Facts** to review canonical facts and their sources/history.
5. Use `http://localhost:8000/docs` for interactive API exploration.

## Development

### Backend Development

- The backend uses FastAPI with automatic API documentation
- API routes are organized in `app/api/v1/`
- Configuration is managed in `app/core/config.py`
- File storage abstraction is in `app/storage/filesystem.py`

### Frontend Development

- The frontend uses React with TypeScript
- Vite is configured with a proxy to the backend API
- Components are in `src/`
- API calls should use the `/api` prefix (automatically proxied)

## Environment Variables

### Backend (.env)

- `DATABASE_URL`: PostgreSQL connection string
- `UPLOAD_DIR`: Directory for file uploads (default: `./uploads`)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)
- `SECRET_KEY`: Secret key for JWT tokens (change in production!)

### Frontend (.env)

- `VITE_API_BASE_URL`: Backend API URL (default: `http://localhost:8000`)

## Known Gaps / Next Improvements

- **OCR & robust text extraction**: current PDF text extraction is minimal; add OCR and better parsing/caching.
- **Checkboxes/radio buttons**: extend field detection + filling for non-text widgets.
- **Stronger context-aware matching**: reduce incorrect fills (e.g., previous employer vs current employer) with better document understanding and UI confirmation.
- **Migrations + auth**: add Alembic migrations and user accounts for multi-user workflows.

## License

[Add your license here]

