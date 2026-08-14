# 🚀 Quick Start Guide

## Run the Application in 3 Steps

### Step 1: Start Backend

**Option A - Double-click:**
```
start_backend.bat
```

**Option B - Command line:**
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend running on **http://localhost:8000**

---

### Step 2: Start Frontend

**Option A - Double-click:**
```
start_frontend.bat
```

**Option B - Command line:**
```bash
cd frontend
npm run dev
```

✅ Frontend running on **http://localhost:5173**

---

### Step 3: Open Browser

Go to: **http://localhost:5173**

---

## 🔗 Important URLs

| What | URL |
|------|-----|
| **Web App** | http://localhost:5173 |
| **API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/api/health |

---

## ⚡ First Time Setup

### Backend Setup (One-time)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### Frontend Setup (One-time)

```bash
cd frontend
npm install
```

---

## 🧪 Run Tests

```bash
cd backend
.venv\Scripts\activate
pytest
```

---

## 📖 Need More Help?

- **Detailed Guide**: See `RUN_APPLICATION.md`
- **Testing Guide**: See `backend/TESTING.md`
- **Test Commands**: See `backend/TEST_COMMANDS.md`

---

## ✅ Quick Health Check

```bash
# Check backend
curl http://localhost:8000/api/health

# Expected response:
# {"status":"ok","agent_name":"vyamit-voice","configured":true}
```

That's it! 🎉
