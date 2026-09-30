# Sahayak AI - Complete Project Index

**Central navigation guide for the entire Sahayak AI project**

## 🗂️ Project Structure

```
voice_stream/
├── backend/                 # Python FastAPI backend
├── frontend/                # React TypeScript frontend (web)
├── sahayak_mobile/          # Flutter mobile application
├── previous_reference_livekit_frontend/  # LiveKit reference code
└── Documentation files
```

## 📚 Documentation by Component

### 🔴 Backend (Python FastAPI)

**Location:** `d:\voice_stream\backend\`

**Quick Start:**
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Key Files:**
- `README.md` - Backend documentation
- `.env.example` - Environment variables template
- `QUICK_START.md` - Quick setup guide
- `requirements.txt` - Python dependencies

**Features:**
- FastAPI REST API
- LiveKit voice agent integration
- PostgreSQL/SQLite database
- JWT authentication
- OTP system
- Knowledge base (RAG)
- Grievance management
- Multi-language support

---

### 🔵 Frontend Web (React TypeScript)

**Location:** `d:\voice_stream\frontend\`

**Quick Start:**
```bash
cd frontend
npm install
npm run dev
```

**Key Files:**
- `README.md` - Frontend documentation
- `package.json` - Dependencies
- `vite.config.ts` - Vite configuration

**Features:**
- React 18 with TypeScript
- Vite for fast development
- LiveKit voice UI
- Government services interface
- Schemes directory
- Knowledge base viewer
- Responsive design

---

### 🟢 Mobile App (Flutter)

**Location:** `d:\voice_stream\sahayak_mobile\`

**Quick Start:**
```bash
cd sahayak_mobile
flutter pub get
flutter run
```

**Or use:**
```bash
START_MOBILE_APP.bat
```

**Documentation:**
- `README.md` - Main mobile documentation
- `SETUP_GUIDE.md` - Detailed setup instructions
- `QUICK_START.md` - 5-minute quick start
- `FEATURES.md` - Complete feature list
- `PROJECT_SUMMARY.md` - Technical summary
- `run_app.bat` - Quick launcher

**Features:**
- Flutter Android app
- LiveKit voice assistant
- Premium white UI/UX
- 10 Indian languages
- Offline support
- Secure authentication
- Government services
- Schemes directory
- Knowledge base
- Grievance management
- Profile management

---

## 🚀 Getting Started Guides

### For First-Time Setup

1. **Start Here:** `RUN_APPLICATION.md` (root directory)
   - Complete setup instructions
   - Prerequisites checklist
   - Step-by-step guide

2. **Backend Setup:** `backend/QUICK_START.md`
   - Install Python dependencies
   - Configure environment
   - Start server

3. **Mobile Setup:** `MOBILE_APP_GUIDE.md` (root) or `sahayak_mobile/SETUP_GUIDE.md`
   - Install Flutter
   - Configure API connection
   - Run mobile app

4. **Web Setup:** `frontend/README.md`
   - Install Node.js dependencies
   - Configure backend URL
   - Start development server

### Quick Launch Scripts

**Backend:**
```bash
start_complete_backend.bat    # Complete backend with all services
```

**Mobile:**
```bash
START_MOBILE_APP.bat          # Interactive mobile launcher
sahayak_mobile\run_app.bat    # Direct mobile launcher
```

**ngrok (for remote testing):**
```bash
start_ngrok_simple.bat        # Expose backend to internet
```

---

## 📖 Documentation by Topic

### Architecture & Design

**Backend Architecture:**
- `backend/README.md` - API documentation
- Feature-based module structure
- Clean architecture principles

**Frontend Architecture:**
- `frontend/src/` - Component structure
- React hooks and state management
- TypeScript types

**Mobile Architecture:**
- `sahayak_mobile/lib/` - Feature modules
- Provider state management
- Clean architecture with layers

### API Documentation

**Endpoints:**
- Authentication: `/auth/*`
- Voice: `/voice/*`
- Services: `/api/services`
- Schemes: `/api/schemes`
- Knowledge: `/api/knowledge`
- Grievances: `/api/grievances`

**Reference:** `backend/app/` - FastAPI route files

### LiveKit Integration

**Backend:**
- `backend/app/agent/runner.py` - Voice agent
- `backend/app/agent/providers.py` - LLM providers
- `backend/app/services/token_issuer.py` - Token generation

**Frontend Web:**
- `frontend/src/components/` - LiveKit UI components
- WebSocket communication

**Mobile:**
- `sahayak_mobile/lib/core/services/livekit_voice_service.dart`
- `sahayak_mobile/lib/features/voice/` - Voice UI

**Reference Code:**
- `previous_reference_livekit_frontend/` - Working LiveKit example

### Authentication & Security

**Backend:**
- JWT tokens
- OTP system
- Secure password hashing
- Session management

**Mobile:**
- FlutterSecureStorage
- Token management
- Biometric ready

**Docs:**
- `backend/app/auth/` - Auth module
- `sahayak_mobile/lib/features/auth/` - Auth screens

### Database & Storage

**Backend:**
- PostgreSQL (production)
- SQLite (development)
- Qdrant (vector database)

**Mobile:**
- Hive (local storage)
- Secure storage (tokens)
- Cache management

### Multi-language Support

**Supported Languages:**
1. Hindi (हिंदी)
2. Marathi (मराठी)
3. English
4. Tamil (தமிழ்)
5. Telugu (తెలుగు)
6. Kannada (ಕನ್ನಡ)
7. Malayalam (മലയാളം)
8. Gujarati (ગુજરાતી)
9. Bengali (বাংলা)
10. Punjabi (ਪੰਜਾਬੀ)

**Implementation:**
- Backend: `backend/app/agent/languages.py`
- Mobile: `sahayak_mobile/lib/shared/providers/language_provider.dart`

---

## 🔧 Configuration Files

### Backend Configuration

**Location:** `backend/.env`

**Key Variables:**
```bash
# LiveKit
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

# Database
DATABASE_URL=postgresql://...

# JWT
JWT_SECRET_KEY=...

# Google Cloud (for STT/TTS/Gemini)
GOOGLE_APPLICATION_CREDENTIALS=...
GOOGLE_CLOUD_PROJECT=...

# OTP
OTP_DEMO_MODE=true
OTP_DEMO_CODE=624251
```

**Template:** `backend/.env.example`

### Mobile Configuration

**Location:** `sahayak_mobile/lib/core/config/api_config.dart`

**Key Variable:**
```dart
static const String _defaultUrl = 'http://YOUR_IP:8000';
```

**Or use command-line:**
```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000
```

### Frontend Configuration

**Location:** `frontend/src/config.ts` or `frontend/.env`

**Key Variable:**
```typescript
API_BASE_URL=http://localhost:8000
```

---

## 🐛 Troubleshooting Guides

### Backend Issues

**Common Problems:**
1. Port 8000 already in use
   - Solution: `backend/allow_port_8000.bat`

2. Database connection failed
   - Check `DATABASE_URL` in `.env`
   - Ensure PostgreSQL is running

3. LiveKit connection failed
   - Verify LiveKit credentials
   - Check network connectivity

**Logs Location:** Console output or configure logging

### Mobile Issues

**Common Problems:**
1. Cannot connect to backend
   - Android Emulator: Use `http://10.0.2.2:8000`
   - Physical Device: Use PC's local IP
   - Check firewall settings

2. LiveKit voice not working
   - Grant microphone permission
   - Check backend LiveKit credentials
   - Verify `/voice/token` endpoint

3. Build failed
   - Run `flutter clean`
   - Run `flutter pub get`
   - Check Android SDK installation

**Debug:** `flutter logs` or Android Studio Logcat

### Frontend Issues

**Common Problems:**
1. npm install fails
   - Delete `node_modules` and `package-lock.json`
   - Run `npm install` again

2. CORS errors
   - Check `CORS_ORIGINS` in backend `.env`
   - Ensure frontend URL is whitelisted

3. API connection refused
   - Verify backend is running
   - Check API URL configuration

---

## 📊 Project Status

### ✅ Completed Components

- [x] **Backend API** - Fully functional
- [x] **Web Frontend** - Complete UI
- [x] **Mobile App** - Production ready
- [x] **LiveKit Integration** - Working voice
- [x] **Authentication** - Secure OTP system
- [x] **Database** - Schema and migrations
- [x] **Knowledge Base** - RAG system
- [x] **Documentation** - Comprehensive guides

### 🔄 Optional Enhancements

- [ ] iOS mobile app
- [ ] Push notifications
- [ ] Document OCR
- [ ] Advanced analytics
- [ ] In-app updates
- [ ] CI/CD pipeline

---

## 📝 Quick Reference Commands

### Backend
```bash
# Start backend
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Create admin user
python -m app.knowledge.cli create-admin
```

### Mobile
```bash
# Install dependencies
flutter pub get

# Run app
flutter run

# Build APK
flutter build apk --release

# Check devices
flutter devices

# View logs
flutter logs
```

### Frontend
```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🔗 Important Links

### Documentation
- Main Setup: `RUN_APPLICATION.md`
- Backend Guide: `backend/README.md`
- Mobile Guide: `MOBILE_APP_GUIDE.md`
- Mobile Setup: `sahayak_mobile/SETUP_GUIDE.md`
- Mobile Features: `sahayak_mobile/FEATURES.md`

### Code Repositories
- Backend: `d:\voice_stream\backend\`
- Frontend: `d:\voice_stream\frontend\`
- Mobile: `d:\voice_stream\sahayak_mobile\`

### Batch Scripts
- `start_complete_backend.bat` - Start backend
- `START_MOBILE_APP.bat` - Start mobile app
- `start_ngrok_simple.bat` - Expose backend

---

## 🎯 Recommended Learning Path

### For New Developers

**Day 1: Setup**
1. Read `RUN_APPLICATION.md`
2. Setup backend
3. Test with Postman/curl

**Day 2: Mobile App**
1. Read `MOBILE_APP_GUIDE.md`
2. Install Flutter
3. Run mobile app
4. Test voice features

**Day 3: Web Frontend**
1. Read `frontend/README.md`
2. Install Node.js dependencies
3. Run web app
4. Test all features

**Day 4: Deep Dive**
1. Explore code structure
2. Understand architecture
3. Review API endpoints
4. Test integrations

**Day 5: Customization**
1. Customize branding
2. Configure for production
3. Build release versions
4. Deploy

---

## 💡 Pro Tips

### Development
- Use VS Code with Flutter/React extensions
- Enable hot reload for faster development
- Use DevTools for debugging
- Test on real devices

### Testing
- Test voice on physical device
- Try all 10 languages
- Test offline mode
- Verify caching works

### Deployment
- Use environment variables
- Never commit secrets
- Test release builds
- Follow security checklist

---

## 🆘 Getting Help

### Documentation Locations
1. **General Setup**: `RUN_APPLICATION.md`
2. **Backend**: `backend/README.md`
3. **Mobile**: Multiple docs in `sahayak_mobile/`
4. **Frontend**: `frontend/README.md`

### Common Workflows
- **Full Local Development**: All components running locally
- **Mobile + Remote Backend**: Mobile app connecting to deployed backend
- **Testing Voice**: Use ngrok to expose backend

### Debug Steps
1. Check all services are running
2. Verify configurations
3. Review logs
4. Test API endpoints individually
5. Check network connectivity

---

## ✅ Final Checklist

### Before Development
- [ ] Read `RUN_APPLICATION.md`
- [ ] Install prerequisites (Python, Flutter, Node.js)
- [ ] Setup backend with `.env` file
- [ ] Verify backend runs: `curl http://localhost:8000`

### Before Running Mobile App
- [ ] Backend is running
- [ ] Configure API URL
- [ ] Grant microphone permission
- [ ] Test on emulator or device

### Before Production Deployment
- [ ] Update all URLs to production
- [ ] Configure HTTPS
- [ ] Test with production backend
- [ ] Build release versions
- [ ] Review security settings

---

## 🎉 Success!

You now have complete access to:
- ✅ Full-stack Sahayak AI application
- ✅ Production-ready mobile app
- ✅ Comprehensive documentation
- ✅ Easy-to-use launch scripts
- ✅ Clear troubleshooting guides

**Ready to build and deploy Sahayak AI!** 🚀

---

**Last Updated:** September 30, 2026  
**Project Version:** 1.0.0  
**Status:** Production Ready ✅
