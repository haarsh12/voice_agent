# Sahayak AI - Mobile Application

Premium Flutter mobile application for Sahayak AI - Your Government Assistant.

## 📱 Features

### Core Features
- **Ask Sahayak**: Real-time voice conversation with AI assistant using LiveKit
- **Government Services**: Browse and access various government services
- **Schemes Directory**: Search and explore government schemes with filtering
- **Knowledge Base**: Access verified official information and documents
- **Grievance Management**: Create and track grievances
- **Multi-language Support**: 10 Indian languages (Hindi, Marathi, English, Tamil, Telugu, Kannada, Malayalam, Gujarati, Bengali, Punjabi)

### Technical Highlights
- **Premium White UI/UX**: Minimalistic design with clean white background
- **LiveKit Integration**: Real-time voice communication with backend AI agent
- **Secure Authentication**: OTP-based login with secure token storage
- **Offline Support**: Intelligent caching for schemes and services
- **State Management**: Provider pattern for reactive UI
- **Modern Navigation**: Go Router for declarative routing

## 🏗️ Architecture

```
lib/
├── app/                    # App-level configuration
│   └── router.dart        # Navigation configuration
├── core/                   # Core functionality
│   ├── config/            # API configuration
│   ├── services/          # API client, cache, auth services
│   └── theme/             # App theme and colors
├── features/              # Feature modules
│   ├── auth/              # Authentication
│   ├── voice/             # Voice assistant (LiveKit)
│   ├── services/          # Government services
│   ├── schemes/           # Government schemes
│   ├── knowledge/         # Knowledge base
│   ├── grievances/        # Grievance management
│   └── profile/           # User profile
├── shared/                # Shared components
│   ├── providers/         # Shared providers
│   └── widgets/           # Reusable widgets
└── main.dart              # App entry point
```

## 🚀 Getting Started

### Prerequisites

- Flutter SDK 3.11.4 or higher
- Dart SDK 3.11.4 or higher
- Android Studio / VS Code with Flutter extension
- Android SDK (API 24+)
- A running Sahayak AI backend server

### Installation

1. **Clone the repository**
   ```bash
   cd d:\voice_stream\sahayak_mobile
   ```

2. **Install dependencies**
   ```bash
   flutter pub get
   ```

3. **Add fonts** (Optional but recommended)
   - Download Inter font from [Google Fonts](https://fonts.google.com/specimen/Inter)
   - Place font files in `assets/fonts/`:
     - Inter-Regular.ttf
     - Inter-Medium.ttf
     - Inter-SemiBold.ttf
     - Inter-Bold.ttf

4. **Configure API endpoint**
   
   Edit `lib/core/config/api_config.dart` and update the base URL:
   ```dart
   static const String _defaultUrl = 'http://YOUR_SERVER_IP:8000';
   ```

   Or use build-time configuration:
   ```bash
   flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000
   ```

5. **Run the app**
   ```bash
   # Debug mode
   flutter run

   # Release mode
   flutter run --release

   # Specific device
   flutter devices
   flutter run -d <device_id>
   ```

## 🔧 Configuration

### API Configuration

The app connects to the Sahayak AI backend. Configure the endpoint in `lib/core/config/api_config.dart`:

```dart
class ApiConfig {
  static const String _defaultUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000', // Android emulator localhost
  );
}
```

**For different environments:**

- **Android Emulator**: `http://10.0.2.2:8000`
- **Physical Device (same network)**: `http://192.168.x.x:8000`
- **Production**: `https://your-domain.com`

### Permissions

The app requires the following permissions (already configured):

- `INTERNET`: API communication
- `RECORD_AUDIO`: Voice assistant
- `MODIFY_AUDIO_SETTINGS`: Audio optimization
- `ACCESS_NETWORK_STATE`: Network status
- `CAMERA`: Future features (document scanning)
- `READ_EXTERNAL_STORAGE`: File access
- `WRITE_EXTERNAL_STORAGE`: File storage (Android <13)

## 📦 Dependencies

### Core
- `flutter`: SDK
- `provider`: State management
- `go_router`: Navigation
- `http` & `dio`: API communication
- `hive`: Local storage
- `shared_preferences`: Simple key-value storage
- `flutter_secure_storage`: Secure token storage

### LiveKit Voice
- `livekit_client`: Real-time voice communication
- `permission_handler`: Runtime permissions

### UI
- `cached_network_image`: Image caching
- `shimmer`: Loading animations
- `flutter_animate`: Smooth animations
- `flutter_svg`: SVG support
- `intl`: Internationalization

### Utilities
- `logger`: Logging
- `connectivity_plus`: Network status
- `url_launcher`: External links

## 🎨 Design System

### Colors (Premium White Theme)
- **Primary**: `#1A73E8` (Clean Blue)
- **Background**: `#FFFFFF` (Pure White)
- **Text Primary**: `#202124` (Almost Black)
- **Text Secondary**: `#5F6368` (Medium Gray)
- **Text Tertiary**: `#80868B` (Light Gray)

### Typography
- **Font Family**: Inter
- **Display**: 32px/28px/24px (Bold/SemiBold)
- **Headline**: 22px/20px/18px (SemiBold)
- **Body**: 16px/14px/12px (Regular/Medium)

## 🔐 Security

- Secure token storage using platform Keychain/KeyStore
- No sensitive data in SharedPreferences
- HTTPS enforced for production
- Input validation and sanitization
- Proper error handling without exposing internals

## 🧪 Testing

```bash
# Run all tests
flutter test

# Run with coverage
flutter test --coverage

# Integration tests
flutter test integration_test/
```

## 🏗️ Build

### Debug Build
```bash
flutter build apk --debug
```

### Release Build
```bash
# Generate release APK
flutter build apk --release

# Generate App Bundle (for Play Store)
flutter build appbundle --release

# With custom API endpoint
flutter build apk --release --dart-define=API_BASE_URL=https://api.sahayak.ai
```

### Build Output
- APK: `build/app/outputs/flutter-apk/app-release.apk`
- AAB: `build/app/outputs/bundle/release/app-release.aab`

## 📱 Supported Platforms

- ✅ Android (API 24+)
- ⏳ iOS (Coming soon)

## 🌐 Supported Languages

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

## 🐛 Troubleshooting

### Common Issues

**1. Network Error / Connection Timeout**
- Verify backend is running
- Check API_BASE_URL configuration
- Ensure device can reach the server
- For emulator, use `http://10.0.2.2:8000`

**2. LiveKit Connection Failed**
- Verify LiveKit credentials in backend `.env`
- Check microphone permissions
- Ensure RECORD_AUDIO permission is granted

**3. Build Failures**
- Run `flutter clean`
- Delete `pubspec.lock`
- Run `flutter pub get`
- Update Flutter: `flutter upgrade`

**4. Android SDK Issues**
- Update Android SDK to API 34
- Install required SDK components
- Accept Android licenses: `flutter doctor --android-licenses`

### Debug Commands
```bash
# Check Flutter setup
flutter doctor -v

# Clear cache
flutter clean

# Rebuild dependencies
flutter pub get

# Check connected devices
flutter devices

# View logs
flutter logs

# Run with verbose logging
flutter run -v
```

## 📝 Development Guidelines

### Code Style
- Follow official [Dart Style Guide](https://dart.dev/guides/language/effective-dart/style)
- Use `flutter analyze` before committing
- Format code: `dart format .`
- Run linter: `flutter analyze`

### Commit Convention
```
feat: Add new feature
fix: Bug fix
docs: Documentation update
style: Code style changes
refactor: Code refactoring
test: Add or update tests
chore: Build/dependency updates
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linter
4. Submit a pull request

## 📄 License

Copyright © 2024 Sahayak AI. All rights reserved.

## 🔗 Related

- **Backend**: `d:\voice_stream\backend\`
- **Frontend Web**: `d:\voice_stream\frontend\`
- **Documentation**: `d:\voice_stream\RUN_APPLICATION.md`

## 📞 Support

For issues and support:
1. Check troubleshooting section
2. Review backend logs
3. Check Flutter doctor: `flutter doctor`
4. Review application logs: `flutter logs`

---

**Built with ❤️ using Flutter**
