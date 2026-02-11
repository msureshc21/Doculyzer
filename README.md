# AI Paperwork Co-pilot

A full-stack application for AI-powered paperwork assistance.

## Tech Stack

- **Frontend**: React + TypeScript (Vite)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **File Storage**: Local filesystem abstraction

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
   Edit `.env` and update the database URL and other settings as needed.

6. **Set up PostgreSQL database:**
   ```bash
   createdb paperwork_copilot
   ```
   Or use your preferred PostgreSQL client to create the database.

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

## Next Steps

- [ ] Set up database models and migrations
- [ ] Implement authentication/authorization
- [ ] Add file upload endpoints
- [ ] Integrate AI processing capabilities
- [ ] Add error handling and logging
- [ ] Set up testing framework

## License

[Add your license here]

