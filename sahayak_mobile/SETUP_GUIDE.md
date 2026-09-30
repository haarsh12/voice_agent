# Sahayak AI Mobile - Complete Setup Guide

## 📋 Prerequisites Checklist

- [ ] Flutter SDK 3.11.4+ installed
- [ ] Android Studio / VS Code with Flutter extension
- [ ] Android SDK (API 24-34)
- [ ] Git installed
- [ ] Sahayak AI backend running
- [ ] Physical Android device or emulator

## 🔧 Step-by-Step Setup

### 1. Install Flutter

**Windows:**
```bash
# Download Flutter SDK from https://flutter.dev/docs/get-started/install/windows
# Extract to C:\flutter
# Add to PATH: C:\flutter\bin

# Verify installation
flutter --version
flutter doctor
```

**Accept Android licenses:**
```bash
flutter doctor --android-licenses
```

### 2. Setup Development Environment

**Install Android Studio:**
1. Download from https://developer.android.com/studio
2. Install Android SDK
3. Install Flutter plugin
4. Create virtual device (or connect physical device)

**Or use VS Code:**
```bash
# Install extensions:
# - Flutter
# - Dart
```

### 3. Clone and Setup Project

```bash
cd d:\voice_stream\sahayak_mobile

# Install dependencies
flutter pub get

# Verify setup
flutter doctor -v
```

### 4. Configure Backend Connection

**Option A: Edit config file**

Edit `lib/core/config/api_config.dart`:
```dart
static const String _defaultUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://YOUR_SERVER_IP:8000',
);
```

**Option B: Use command-line parameter**
```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000
```

**Common Configurations:**
- **Android Emulator**: `http://10.0.2.2:8000`
- **iOS Simulator**: `http://127.0.0.1:8000`
- **Physical Device (same WiFi)**: `http://192.168.x.x:8000`
- **ngrok**: `https://your-ngrok-url.ngrok.io`

### 5. Setup Fonts (Optional)

1. Download Inter font family from [Google Fonts](https://fonts.google.com/specimen/Inter)
2. Extract and copy to `assets/fonts/`:
   - Inter-Regular.ttf
   - Inter-Medium.ttf
   - Inter-SemiBold.ttf
   - Inter-Bold.ttf

3. Fonts are already configured in `pubspec.yaml`

**If you skip fonts**, the app will use system default fonts.

### 6. Start Backend Server

Make sure your Sahayak AI backend is running:

```bash
cd d:\voice_stream\backend

# Activate virtual environment
.venv\Scripts\activate

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify backend is accessible:
```bash
curl http://localhost:8000/
```

### 7. Run the App

**Check connected devices:**
```bash
flutter devices
```

**Run on emulator:**
```bash
flutter run
```

**Run on specific device:**
```bash
flutter run -d <device_id>
```

**Run in release mode:**
```bash
flutter run --release
```

**Run with custom backend URL:**
```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000
```

## 🔍 Verification Steps

### 1. Test Backend Connection

Open the app and check:
- [ ] Splash screen appears
- [ ] Language selection screen loads
- [ ] Can proceed to login screen
- [ ] OTP request works

### 2. Test Voice Features

- [ ] Ask Sahayak screen loads
- [ ] Can change language
- [ ] "Start Conversation" button appears
- [ ] Microphone permission requested

### 3. Test Other Features

- [ ] Services screen loads data
- [ ] Schemes screen displays items
- [ ] Knowledge base shows statistics
- [ ] Profile screen shows user info

## 🐛 Common Setup Issues

### Issue 1: "No connected devices"

**Solution:**
```bash
# For emulator
# 1. Open Android Studio > AVD Manager
# 2. Start an emulator
# 3. Run: flutter devices

# For physical device
# 1. Enable USB debugging on phone
# 2. Connect via USB
# 3. Accept debugging prompt on phone
# 4. Run: flutter devices
```

### Issue 2: "Gradle build failed"

**Solution:**
```bash
# Clear Flutter cache
flutter clean

# Delete gradle cache
cd android
.\gradlew clean

# Rebuild
cd ..
flutter pub get
flutter run
```

### Issue 3: "Network error / Connection refused"

**Solution:**
1. Verify backend is running: `curl http://localhost:8000`
2. Check API URL in config
3. For emulator, use `http://10.0.2.2:8000`
4. For physical device, ensure same WiFi network
5. Check firewall settings

### Issue 4: "Permission denied" errors

**Solution:**
```bash
# On device, go to Settings > Apps > Sahayak AI
# Grant required permissions:
# - Microphone
# - Storage (if needed)
# - Camera (if needed)
```

### Issue 5: LiveKit connection fails

**Solution:**
1. Check backend `.env` has valid LiveKit credentials
2. Ensure microphone permission granted
3. Test backend voice token endpoint:
   ```bash
   curl -X POST http://localhost:8000/voice/token \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json"
   ```

## 🚀 Development Workflow

### Daily Development

```bash
# 1. Pull latest changes
git pull

# 2. Update dependencies (if pubspec.yaml changed)
flutter pub get

# 3. Run app in debug mode
flutter run

# 4. Hot reload: Press 'r' in terminal
# 5. Hot restart: Press 'R' in terminal
# 6. Quit: Press 'q'
```

### Before Committing

```bash
# Format code
dart format .

# Analyze code
flutter analyze

# Run tests
flutter test

# Commit changes
git add .
git commit -m "Your message"
git push
```

### Building Release

```bash
# Clean build
flutter clean

# Get dependencies
flutter pub get

# Build APK
flutter build apk --release

# Find APK at:
# build/app/outputs/flutter-apk/app-release.apk
```

## 📱 Testing on Physical Device

### Android Setup

1. **Enable Developer Options:**
   - Settings > About Phone
   - Tap "Build Number" 7 times

2. **Enable USB Debugging:**
   - Settings > Developer Options
   - Enable "USB Debugging"

3. **Connect Device:**
   ```bash
   # Connect via USB
   # Accept debugging prompt on device
   
   # Verify connection
   flutter devices
   adb devices
   ```

4. **Run App:**
   ```bash
   flutter run
   ```

### Testing Checklist

- [ ] App installs successfully
- [ ] Splash screen appears
- [ ] Language selection works
- [ ] Login with OTP works
- [ ] Voice assistant connects
- [ ] Services load properly
- [ ] Schemes are searchable
- [ ] Profile updates save
- [ ] App works offline (cached data)
- [ ] Network reconnection works

## 🔐 Security Setup

### Production Checklist

- [ ] Change API URL to HTTPS endpoint
- [ ] Update `android:usesCleartextTraffic="false"`
- [ ] Generate proper signing key
- [ ] Update `build.gradle.kts` with release signing
- [ ] Test with real LiveKit server (not local)
- [ ] Verify secure storage works
- [ ] Test with production backend

### Generate Signing Key

```bash
# Generate keystore
keytool -genkey -v -keystore sahayak-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias sahayak

# Create key.properties
# android/key.properties:
storePassword=<password>
keyPassword=<password>
keyAlias=sahayak
storeFile=../sahayak-release-key.jks
```

## 📚 Additional Resources

- [Flutter Documentation](https://flutter.dev/docs)
- [Dart Language Tour](https://dart.dev/guides/language/language-tour)
- [Provider Package](https://pub.dev/packages/provider)
- [LiveKit Flutter SDK](https://docs.livekit.io/client-sdk-flutter/)
- [Go Router](https://pub.dev/packages/go_router)

## 💡 Pro Tips

1. **Use Hot Reload**: Press 'r' for instant UI updates
2. **Flutter DevTools**: Run `flutter pub global activate devtools` then `flutter pub global run devtools`
3. **VS Code Extensions**: Install Flutter, Dart, and Awesome Flutter Snippets
4. **Android Studio**: Use Logcat for detailed logs
5. **Network Inspector**: Use DevTools Network tab for API debugging

## ✅ Setup Complete!

You should now have:
- ✅ Flutter environment configured
- ✅ Sahayak AI mobile app running
- ✅ Backend connected
- ✅ Voice features working
- ✅ All screens functional

**Next Steps:**
1. Test all features thoroughly
2. Customize branding (logo, colors)
3. Add actual fonts if needed
4. Configure production backend
5. Build release APK

---

**Need Help?** Check `README.md` or review backend documentation.
