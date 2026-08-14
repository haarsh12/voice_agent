# How to Run Vyamit Voice Application

## 🎯 Quick Start

### Method 1: Using Batch Scripts (Windows)

1. **Start Backend** - Double-click `start_backend.bat`
   - Opens terminal and starts backend on http://localhost:8000

2. **Start Frontend** - Double-click `start_frontend.bat`
   - Opens terminal and starts frontend on http://localhost:5173

3. **Open Browser** - Go to http://localhost:5173

---

### Method 2: Manual Commands

#### Terminal 1 - Backend

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

---

## 📋 Prerequisites

### Backend Requirements

✅ Python 3.10+
✅ Virtual environment created
✅ Dependencies installed

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### Frontend Requirements

✅ Node.js 18+
✅ npm or yarn

```bash
cd frontend
npm install
```

---

## 🔧 Configuration

### Backend Configuration (`.env` file)

Create or edit `backend/.env`:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Agent Configuration
AGENT_NAME=vyamit-voice

# Deepgram (Speech-to-Text)
DEEPGRAM_API_KEY=your-deepgram-key
DEEPGRAM_STT_MODEL=nova-3
DEEPGRAM_STT_LANGUAGE=multi

# Mistral (LLM)
MISTRAL_API_KEY=your-mistral-key
MISTRAL_MODEL=mistral-medium-latest
MISTRAL_TEMPERATURE=0.35

# Cartesia (Text-to-Speech)
CARTESIA_API_KEY=your-cartesia-key
CARTESIA_TTS_MODEL=sonic-3
CARTESIA_VOICE_ID=f786b574-daa5-4673-aa0c-cbe3e8534c02
CARTESIA_TTS_LANGUAGE=en

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend Configuration (`.env` file)

Create or edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

---

## 🌐 Access Points

Once both servers are running:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | Main web application |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs (Swagger)** | http://localhost:8000/docs | Interactive API documentation |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | Alternative API documentation |
| **Health Check** | http://localhost:8000/api/health | Backend health status |

---

## 🧪 Testing the Application

### 1. Check Backend Health

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "agent_name": "vyamit-voice",
  "configured": true
}
```

### 2. Test Token Generation

```bash
curl -X POST http://localhost:8000/api/token \
  -H "Content-Type: application/json" \
  -d '{"room_name":"test-room","participant_name":"TestUser"}'
```

Expected response:
```json
{
  "server_url": "wss://your-livekit-server.com",
  "participant_token": "eyJ..."
}
```

### 3. Open Frontend

Visit http://localhost:5173 in your browser

---

## 🔍 Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'src'`
```bash
# Use correct command
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Problem**: `Port 8000 already in use`
```bash
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Problem**: Virtual environment not activated
```bash
cd backend
.venv\Scripts\activate
# You should see (.venv) in your prompt
```

### Frontend Issues

**Problem**: `npm: command not found`
- Install Node.js from https://nodejs.org/

**Problem**: `EADDRINUSE: address already in use`
```bash
# Kill the process on port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

**Problem**: Dependencies not installed
```bash
cd frontend
npm install
```

### Connection Issues

**Problem**: Frontend can't connect to backend
1. Check backend is running on port 8000
2. Check `frontend/.env` has correct `VITE_API_URL`
3. Check CORS settings in `backend/.env`

**Problem**: CORS errors in browser console
```env
# In backend/.env, ensure frontend URL is in CORS_ORIGINS
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## 🛑 Stopping the Application

### Stop Backend
Press `Ctrl + C` in the backend terminal

### Stop Frontend
Press `Ctrl + C` in the frontend terminal

---

## 📦 Complete Setup from Scratch

```bash
# 1. Clone/Navigate to project
cd voice_stream

# 2. Setup Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
# Create .env file with your API keys
cd ..

# 3. Setup Frontend
cd frontend
npm install
# Create .env file if needed
cd ..

# 4. Start Backend (Terminal 1)
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Start Frontend (Terminal 2)
cd frontend
npm run dev

# 6. Open Browser
# Go to http://localhost:5173
```

---

## 🎬 Development Workflow

### Daily Startup

1. Open two terminals
2. **Terminal 1**: `start_backend.bat` or manual backend commands
3. **Terminal 2**: `start_frontend.bat` or manual frontend commands
4. Open http://localhost:5173

### Making Changes

- **Backend changes**: Server auto-reloads (thanks to `--reload` flag)
- **Frontend changes**: Vite auto-reloads in browser
- **Environment changes**: Restart the affected server

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests (if configured)
cd frontend
npm test
```

---

## 📚 Additional Resources

- **Backend API Documentation**: http://localhost:8000/docs
- **Testing Guide**: `backend/TESTING.md`
- **Test Commands**: `backend/TEST_COMMANDS.md`
- **Quick Start**: `backend/QUICKSTART_TESTING.md`

---

## ✅ Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can access http://localhost:8000/api/health
- [ ] Can access http://localhost:8000/docs
- [ ] Can access http://localhost:5173
- [ ] No CORS errors in browser console
- [ ] Backend shows "configured: true" (if API keys provided)

🎉 **You're all set!** Your Vyamit Voice application is running.
