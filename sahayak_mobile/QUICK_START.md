# Sahayak AI Mobile - Quick Start Guide

Get up and running in 5 minutes!

## ⚡ Prerequisites

- [ ] Flutter SDK installed (`flutter --version`)
- [ ] Android emulator or physical device
- [ ] Backend server running

## 🚀 3-Step Setup

### Step 1: Install Dependencies

```bash
cd d:\voice_stream\sahayak_mobile
flutter pub get
```

### Step 2: Configure Backend URL

Choose one option:

**Option A: For Android Emulator**
```bash
# No configuration needed - default works!
# Uses http://10.0.2.2:8000
```

**Option B: For Physical Device**
```bash
# Find your PC's IP address
ipconfig
# Example: 192.168.1.100

# Run with custom URL
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000
```

**Option C: Edit config file**
```dart
// lib/core/config/api_config.dart
defaultValue: 'http://YOUR_IP:8000'
```

### Step 3: Run the App

```bash
# Check connected devices
flutter devices

# Run app
flutter run
```

Or simply double-click: **`run_app.bat`**

## ✅ Verification

App should:
- ✅ Show splash screen
- ✅ Display language selection
- ✅ Allow login with OTP

**Test Login:**
- Phone: Any 10-digit number
- OTP: `624251` (demo mode)

## 🎤 Test Voice Feature

1. Open "Ask Sahayak" tab
2. Tap "Start Conversation"
3. Allow microphone permission
4. Speak in selected language

## 🐛 Quick Fixes

**Problem: Connection refused**
```bash
# Verify backend is running
curl http://localhost:8000

# For emulator, use: http://10.0.2.2:8000
# For device, use: http://YOUR_PC_IP:8000
```

**Problem: No devices**
```bash
# Start emulator in Android Studio
# Or connect phone via USB with debugging enabled
flutter devices
```

**Problem: Build failed**
```bash
flutter clean
flutter pub get
flutter run
```

## 📱 Device Setup

### Android Emulator
1. Open Android Studio > AVD Manager
2. Create/Start emulator
3. Run `flutter run`

### Physical Device
1. Enable Developer Options (tap Build Number 7x)
2. Enable USB Debugging
3. Connect via USB
4. Accept debugging prompt
5. Run `flutter run`

## 🎯 What's Working

- ✅ Real-time voice assistant (LiveKit)
- ✅ 10 language support
- ✅ Government services browsing
- ✅ Schemes search and filtering
- ✅ Knowledge base stats
- ✅ Grievance creation and tracking
- ✅ User profile management
- ✅ Offline caching
- ✅ Secure authentication

## 📖 Next Steps

1. ✅ App is running
2. 📖 Read [README.md](README.md) for features
3. 🔧 Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for details
4. 🚀 Build release: `flutter build apk --release`

## 💡 Pro Tips

- Hot reload: Press `r` in terminal
- Hot restart: Press `R`
- Use `run_app.bat` for quick launch
- Check logs: `flutter logs`

## 🆘 Need Help?

- Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
- Review [README.md](README.md)
- See backend: `d:\voice_stream\RUN_APPLICATION.md`

---

**That's it! You're ready to go! 🎉**
