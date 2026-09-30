# Sahayak AI - Mobile Application Guide

Complete guide for setting up and running the Sahayak AI Flutter mobile application.

## 📱 Overview

The Sahayak AI mobile application is a premium, feature-rich Flutter app that provides:
- Real-time voice conversation with AI assistant (LiveKit integration)
- Access to government services and schemes
- Knowledge base with verified information
- Grievance management system
- Multi-language support (10 Indian languages)
- Clean, minimalistic white UI/UX

## 🏗️ Project Structure

```
sahayak_mobile/
├── lib/
│   ├── app/                 # App configuration & routing
│   ├── core/                # Core services & theme
│   ├── features/            # Feature modules
│   │   ├── auth/           # Authentication
│   │   ├── voice/          # Voice assistant (LiveKit)
│   │   ├── services/       # Government services
│   │   ├── schemes/        # Government schemes
│   │   ├── knowledge/      # Knowledge base
│   │   ├── grievances/     # Grievance management
│   │   └── profile/        # User profile
│   ├── shared/             # Shared components
│   └── main.dart           # Entry point
├── android/                # Android-specific code
├── assets/                 # Images, fonts, icons
├── README.md              # Main documentation
├── SETUP_GUIDE.md         # Detailed setup instructions
└── pubspec.yaml           # Dependencies
```

## 🚀 Quick Start

### Prerequisites

1. **Flutter SDK 3.11.4+**
   ```bash
   flutter --version
   ```

2. **Backend Server Running**
   ```bash
   cd d:\voice_stream\backend
   .venv\Scripts\activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Installation

```bash
# Navigate to mobile app directory
cd d:\voice_stream\sahayak_mobile

# Install dependencies
flutter pub get

# Run the app
flutter run
```

Or use the batch script:
```bash
run_app.bat
```

## 🔧 Configuration

### Backend Connection

**Method 1: Edit config file**

`lib/core/config/api_config.dart`:
```dart
static const String _defaultUrl = 'http://YOUR_IP:8000';
```

**Method 2: Command line**
```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000
```

**Common URLs:**
- Android Emulator: `http://10.0.2.2:8000`
- Physical Device: `http://192.168.x.x:8000` (your PC's local IP)
- Production: `https://your-domain.com`

### Finding Your PC's IP Address

**Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your network adapter
```

**Example:** If your PC's IP is `192.168.1.100`, use:
```
http://192.168.1.100:8000
```

## 📦 Dependencies

### Already Configured

All dependencies are pre-configured in `pubspec.yaml`:

**Core:**
- Provider (state management)
- Go Router (navigation)
- HTTP & Dio (networking)
- Hive (local storage)
- Secure Storage (tokens)

**LiveKit:**
- livekit_client (voice communication)
- permission_handler (microphone access)

**UI:**
- Cached Network Image
- Shimmer effects
- Flutter Animate
- Intl (formatting)

Simply run `flutter pub get` to install all dependencies.

## 🎨 Customization

### Branding

**1. App Name**

`android/app/src/main/AndroidManifest.xml`:
```xml
android:label="Your App Name"
```

**2. App Icon**

Replace icons in:
```
android/app/src/main/res/
├── mipmap-hdpi/
├── mipmap-mdpi/
├── mipmap-xhdpi/
├── mipmap-xxhdpi/
└── mipmap-xxxhdpi/
```

Use [App Icon Generator](https://appicon.co/) to generate all sizes.

**3. Colors**

`lib/core/theme/app_colors.dart`:
```dart
static const Color primary = Color(0xFF1A73E8); // Your color
```

**4. Fonts**

Add custom fonts to `assets/fonts/` and update `pubspec.yaml`.

## 🔐 Authentication

The app uses OTP-based authentication:

1. User enters phone number
2. Backend sends OTP
3. User verifies OTP
4. JWT token stored securely
5. Auto-login on app restart

**Test Credentials** (if OTP_DEMO_MODE=true in backend):
- Any phone number
- OTP: `624251` (from backend .env)

## 🎤 Voice Features

### LiveKit Integration

The app connects to LiveKit for real-time voice communication:

**Prerequisites:**
1. Backend has valid LiveKit credentials in `.env`
2. Microphone permission granted on device
3. Network connectivity

**Testing Voice:**
1. Open app > Ask Sahayak
2. Tap "Start Conversation"
3. Grant microphone permission
4. Speak in selected language

### Language Support

10 languages supported:
- Hindi, Marathi, English
- Tamil, Telugu, Kannada
- Malayalam, Gujarati
- Bengali, Punjabi

Change language in:
- Language selection screen (first launch)
- Ask Sahayak screen > Change button

## 📱 Building & Deployment

### Debug Build

```bash
# Run in debug mode
flutter run

# Build debug APK
flutter build apk --debug
```

### Release Build

```bash
# Build release APK
flutter build apk --release

# Find APK at:
# build/app/outputs/flutter-apk/app-release.apk
```

### Play Store Build

```bash
# Build App Bundle
flutter build appbundle --release

# Output:
# build/app/outputs/bundle/release/app-release.aab
```

## 🧪 Testing

### Run Tests

```bash
# Unit tests
flutter test

# Integration tests
flutter drive --target=test_driver/app.dart
```

### Manual Testing Checklist

- [ ] App installs and launches
- [ ] Splash screen appears
- [ ] Language selection works
- [ ] Login with OTP succeeds
- [ ] Voice assistant connects
- [ ] Microphone permission requested
- [ ] Services screen loads
- [ ] Schemes are searchable
- [ ] Knowledge base displays stats
- [ ] Profile shows user info
- [ ] Logout works
- [ ] Offline mode (cached data)

## 🐛 Troubleshooting

### Common Issues

**1. "Unable to connect to backend"**
```
Solutions:
- Verify backend is running
- Check API URL in config
- Ensure device can reach server
- For emulator, use http://10.0.2.2:8000
- Check firewall settings
```

**2. "LiveKit connection failed"**
```
Solutions:
- Grant microphone permission
- Check backend LiveKit credentials
- Verify network connectivity
- Check backend /voice/token endpoint
```

**3. "Build failed"**
```bash
# Clean and rebuild
flutter clean
flutter pub get
cd android
.\gradlew clean
cd ..
flutter run
```

**4. "No connected devices"**
```
Solutions:
- Start Android emulator
- Or connect physical device via USB
- Enable USB debugging on device
- Run: flutter devices
```

### Logs

```bash
# View real-time logs
flutter logs

# Verbose mode
flutter run -v

# Android-specific logs
adb logcat
```

## 🔄 Development Workflow

### Daily Development

```bash
# 1. Start backend
cd d:\voice_stream\backend
.venv\Scripts\activate
uvicorn app.main:app --reload

# 2. Run mobile app (new terminal)
cd d:\voice_stream\sahayak_mobile
flutter run

# 3. Make changes
# 4. Hot reload: Press 'r'
# 5. Full restart: Press 'R'
```

### Before Committing

```bash
# Format code
dart format .

# Analyze
flutter analyze

# Test
flutter test

# Commit
git add .
git commit -m "Description"
git push
```

## 📊 Performance

### Optimization Tips

1. **Use Release Build** for testing performance
2. **Enable caching** - already configured
3. **Optimize images** - use cached_network_image
4. **Lazy loading** - screens load data on demand
5. **State management** - Provider minimizes rebuilds

### Memory Management

- Hive for efficient local storage
- Image caching reduces network calls
- Proper disposal of controllers
- Pagination for large lists

## 🔒 Security Best Practices

- ✅ Secure token storage (FlutterSecureStorage)
- ✅ HTTPS for production (configure in ApiConfig)
- ✅ Input validation on all forms
- ✅ No hardcoded secrets
- ✅ Proper error handling
- ✅ Network security config

## 📚 Documentation

- **README.md**: Overview and quick start
- **SETUP_GUIDE.md**: Detailed setup instructions
- **MOBILE_APP_GUIDE.md**: This file - comprehensive guide
- **Code comments**: Inline documentation

## 🎯 Features Roadmap

**Current Version (v1.0.0):**
- ✅ Voice assistant (LiveKit)
- ✅ Services & Schemes
- ✅ Knowledge base
- ✅ Grievances
- ✅ Multi-language support
- ✅ OTP authentication
- ✅ Offline support

**Future Enhancements:**
- Push notifications
- Document scanning (OCR)
- Offline voice support
- iOS version
- In-app updates
- Analytics dashboard

## 🤝 Integration with Backend

The mobile app integrates with backend APIs:

**Authentication:**
- `POST /auth/otp/request` - Request OTP
- `POST /auth/otp/verify` - Verify OTP
- `GET /auth/profile` - Get user profile

**Voice:**
- `POST /voice/token` - Get LiveKit credentials

**Services:**
- `GET /api/services` - List services

**Schemes:**
- `GET /api/schemes` - List schemes

**Knowledge:**
- `GET /api/knowledge` - Knowledge base stats

**Grievances:**
- `GET /api/grievances` - List grievances
- `POST /api/grievances` - Create grievance

## 💡 Pro Tips

1. **Use run_app.bat** for quick launching
2. **Hot reload (r)** for instant UI updates
3. **DevTools** for debugging: `flutter pub global run devtools`
4. **VS Code** shortcuts: F5 to run, Shift+F5 to stop
5. **Android Studio** Logcat for detailed logs
6. **Physical device** for accurate performance testing

## ✅ Checklist for Production

Before deploying to production:

- [ ] Update API_BASE_URL to production server
- [ ] Set `usesCleartextTraffic="false"` in AndroidManifest
- [ ] Generate signing key for app
- [ ] Update app version in pubspec.yaml
- [ ] Add actual app icon
- [ ] Add custom fonts (optional)
- [ ] Test with production LiveKit server
- [ ] Test all features thoroughly
- [ ] Run `flutter analyze` with no errors
- [ ] Build release APK/AAB
- [ ] Test release build on devices

## 📞 Support

For issues:
1. Check troubleshooting section
2. Review logs: `flutter logs`
3. Check backend logs
4. Verify network connectivity
5. Review backend documentation

## 🎉 Success!

You now have a fully functional Sahayak AI mobile application with:
- Premium white UI/UX
- Real-time voice assistant
- Government services integration
- Multi-language support
- Secure authentication
- Offline capabilities

**Enjoy building with Sahayak AI! 🚀**

---

**Project Structure:**
- Backend: `d:\voice_stream\backend\`
- Frontend Web: `d:\voice_stream\frontend\`
- Mobile App: `d:\voice_stream\sahayak_mobile\`

**Documentation:**
- Main Setup: `d:\voice_stream\RUN_APPLICATION.md`
- Mobile README: `d:\voice_stream\sahayak_mobile\README.md`
- Setup Guide: `d:\voice_stream\sahayak_mobile\SETUP_GUIDE.md`
- This Guide: `d:\voice_stream\MOBILE_APP_GUIDE.md`
