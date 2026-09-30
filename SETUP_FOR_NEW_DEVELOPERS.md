# Setup Guide for New Developers

This guide will help you set up the complete Sahayak AI project on your local machine after cloning from GitHub.

## 📋 Prerequisites

Before you start, make sure you have:

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **Git** - [Download](https://git-scm.com/)
4. **Flutter SDK** (for mobile app) - [Download](https://docs.flutter.dev/get-started/install/windows)
5. **Android Studio** (for mobile app) - [Download](https://developer.android.com/studio)

## 🔑 Required Secret Files (NOT in GitHub)

You will need these files from the project owner:

### 1. **Google Cloud Service Account JSON Key**
   - File name: `project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json`
   - Location: Place in `backend/` folder
   - Purpose: Google Cloud services (STT, TTS, Gemini AI)

### 2. **Backend Environment File** (`.env`)
   - Location: `backend/.env`
   - Get this file from project owner or use the template below

### 3. **Frontend Environment File** (`.env`)
   - Location: `frontend/.env`
   - Get this file from project owner or use the template below

## 🚀 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone <your-github-repo-url>
cd voice_stream
```

### Step 2: Get Secret Files from Project Owner

**Ask the project owner to send you:**

1. `backend/.env` file
2. `frontend/.env` file
3. Google Cloud JSON key: `project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json`

**Place them in the correct locations:**

```
voice_stream/
├── backend/
│   ├── .env  ← Place here
│   └── project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json  ← Place here
└── frontend/
    └── .env  ← Place here
```

### Step 3: Backend Setup

#### 3.1 Create Python Virtual Environment

```bash
cd backend
python -m venv .venv
```

#### 3.2 Activate Virtual Environment

```bash
# On Windows
.\.venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3.3 Install Dependencies

```bash
pip install -e .
```

#### 3.4 Initialize Database (Optional - for development)

The SQLite database will be created automatically on first run.

#### 3.5 Verify Backend Setup

```bash
# Test that everything is working
python -m pytest -q
```

### Step 4: Frontend Setup

```bash
cd frontend
npm install
```

### Step 5: Mobile App Setup (Optional)

```bash
cd sahayak_mobile
flutter pub get
flutter doctor  # Verify Flutter installation
```

## ▶️ Running the Application

### Option 1: Using Batch Scripts (Recommended)

#### Start Complete Backend (FastAPI + LiveKit Agent)
```bash
# From root directory
start_complete_backend.bat
```

#### Start Frontend
```bash
# Open new terminal
cd frontend
npm run dev
```

### Option 2: Manual Commands

#### Terminal 1 - Backend Server
```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - LiveKit Agent
```bash
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.agent.runner
```

#### Terminal 3 - Frontend
```bash
cd frontend
npm run dev
```

#### Terminal 4 - Mobile App (Optional)
```bash
cd sahayak_mobile
flutter run
```

## 🌐 Access the Application

- **Frontend Web App**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🧪 Testing the Application

### Test OTP Login

For development, use the demo OTP code: **624251**

1. Open http://localhost:5173
2. Enter any phone number (e.g., +919876543210)
3. Click "Send OTP"
4. Enter OTP: **624251**
5. Login successfully!

### Test Voice Features

1. Click on microphone icon
2. Allow microphone permissions
3. Select language (Hindi, Marathi, or English)
4. Start speaking
5. AI should respond with voice

## 📁 Project Structure

```
voice_stream/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agent/             # LiveKit voice agent
│   │   ├── api/               # API routes
│   │   ├── auth/              # Authentication
│   │   ├── config/            # Configuration
│   │   └── services/          # Business logic
│   ├── .env                   # ⚠️ SECRET (not in git)
│   ├── .env.example           # Template
│   └── project-*.json         # ⚠️ SECRET (not in git)
│
├── frontend/                  # React frontend
│   ├── src/
│   ├── .env                   # ⚠️ SECRET (not in git)
│   └── .env.example           # Template
│
└── sahayak_mobile/            # Flutter mobile app
    ├── android/
    └── lib/
```

## 🔧 Configuration Files Explained

### Backend `.env` File

Key variables you need:

```bash
# LiveKit (for voice streaming)
LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Google Cloud (get from project owner)
GOOGLE_APPLICATION_CREDENTIALS=project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash

# Development settings
OTP_DEMO_MODE=true
OTP_DEMO_CODE=624251
API_PORT=8000
```

### Frontend `.env` File

```bash
# Usually empty for local development
# Vite proxy handles API requests
VITE_API_BASE_URL=
VITE_AGENT_NAME=sahayak-ai
```

## 🐛 Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Windows - Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

**Virtual environment not activating:**
```bash
# Change PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Google Cloud credentials not found:**
- Verify `project-*.json` file is in `backend/` folder
- Check `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`
- Make sure filename matches exactly

### Frontend Issues

**npm install fails:**
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**CORS errors:**
- Check `CORS_ORIGINS` in backend `.env`
- Add your frontend URL (e.g., http://localhost:5173)
- Restart backend server

### Mobile App Issues

**Flutter not found:**
```bash
# Add Flutter to PATH
# Add: C:\path\to\flutter\bin
flutter doctor
```

**Android licenses not accepted:**
```bash
flutter doctor --android-licenses
```

## 📞 Getting Help

If you encounter issues:

1. **Check this guide** - Most common issues are covered
2. **Check existing documentation**:
   - `RUN_APPLICATION.md` - Running instructions
   - `backend/QUICK_START.md` - Backend guide
   - `MOBILE_APP_SETUP.md` - Mobile setup
3. **Ask the project owner** for:
   - Missing secret files
   - API keys or credentials
   - LiveKit configuration

## ✅ Verification Checklist

Before asking for help, verify:

- [ ] All secret files received and placed correctly
- [ ] Python virtual environment activated
- [ ] Backend dependencies installed (`pip install -e .`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend server running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can access http://localhost:8000/docs
- [ ] Can access http://localhost:5173

## 🔐 Security Reminders

**NEVER commit these files to Git:**
- `.env` files (backend and frontend)
- `project-*.json` (Google Cloud credentials)
- Any file containing API keys or secrets

These files are already in `.gitignore` but always double-check before committing!

## 🎉 Success!

If everything is working:
- Backend API docs: http://localhost:8000/docs
- Frontend app: http://localhost:5173
- You can login with OTP: 624251
- Voice features are working

You're all set! Happy coding! 🚀

---

**Last Updated**: 2026-09-27
**Project**: Sahayak AI
**For**: New Developer Setup
