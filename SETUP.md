# Agent Viper Setup Instructions

AI-Assisted Pentesting Platform — local development setup on Windows 11.

---

## Prerequisites

Install the following before proceeding:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| Ollama | latest | https://ollama.com/download |

> **No Redis / message broker required.** The scan pipeline (including
> resume and retry-phase) runs in-process inside the FastAPI backend.

### Ollama + qwen2.5-coder:7b

After installing Ollama, pull the required model:
```powershell
ollama pull qwen2.5-coder:7b
```

---

## Project Structure

```
AI-Assisted-Pentest-workflow/
├── backend/           # FastAPI app + 13 LangGraph agents
│   ├── agents/        # Individual agent modules
│   ├── api/           # REST routes
│   ├── scripts/       # DB init and seed scripts
│   ├── requirements.txt
│   └── main.py
├── frontend/          # React + Vite UI
├── config/
│   └── .env.dev       # Dev environment variables
└── docker-compose.yml
```

---

## First-Time Setup

Run these steps once before starting the application for the first time.

### 1. Backend

Open PowerShell in the project root:

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy dev environment config
copy ..\config\.env.dev .env.dev

# Initialize the database
python scripts/init_db.py

# Seed mock data
python scripts/seed_mock_data.py
```

### 2. Frontend

Open a new PowerShell terminal in the project root:

```powershell
cd frontend
npm install
```

---

## Running the Application

You need **2 separate terminals** running simultaneously.

### Terminal 1 — Backend API

```powershell
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### Terminal 2 — Frontend

```powershell
cd frontend
npm run dev
```

---

## Service URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/swagger |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

## Login Credentials

```
Username: admin@agentviper.local
Password: Harbor-Quartz-Meadow-58
```

---

## Environment Variables

The dev config lives at `config/.env.dev` and is copied to `backend/.env.dev` during setup. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM backend (`ollama` or `anthropic`) |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Ollama model to use |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `ANTHROPIC_API_KEY` | *(blank)* | Required only for UAT/PROD |
| `BURP_MODE` | `mock` | `mock` for dev, `live` for real Burp Suite |
| `DB_URL` | `postgresql+psycopg2://aipp:aipp@localhost:5432/aipp` | PostgreSQL (required) |

To switch to Anthropic Claude as the LLM backend, set:
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
```

---

## Startup Checklist

Before launching, confirm:

- [ ] Ollama is running (`ollama serve` or it auto-starts)
- [ ] `backend/.env.dev` exists (copied from `config/.env.dev`)
- [ ] PostgreSQL is running and reachable at `DB_URL` (`docker compose up -d postgres`)
- [ ] Virtual environment activated in the backend terminal

---

## Troubleshooting

### `venv\Scripts\activate` fails
PowerShell execution policy may be blocking scripts. Run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `ollama: command not found` or model errors
Ensure Ollama is installed and the model is pulled:
```powershell
ollama pull qwen2.5-coder:7b
```

### `ModuleNotFoundError` on backend start
Virtual environment is not activated. Run `venv\Scripts\activate` first.

### Port already in use
Check which process is using the port and kill it:
```powershell
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

### Frontend shows blank page or API errors
Confirm the backend is running on port 8000 before starting the frontend.

---

## Subsequent Starts (After First-Time Setup)

```powershell
# Terminal 1 — Backend
cd backend; venv\Scripts\activate; uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend; npm run dev
```

