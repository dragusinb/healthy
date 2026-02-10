# Analize.online Mobile App

React Native mobile application for the Analize.online health data aggregation platform.

## Features

- User authentication (email/password)
- Dashboard with health overview, stats, and AI summary
- Biomarkers list with categories, search, and filtering
- Biomarker history/evolution view with simple chart visualization
- Documents list with status tracking
- Profile management with medical history

## Prerequisites

- Node.js 18+
- React Native CLI
- For iOS: Xcode 14+, CocoaPods
- For Android: Android Studio, JDK 11+

## Installation

1. Install dependencies:
```bash
cd mobile
npm install
```

2. For iOS, install pods:
```bash
cd ios
pod install
cd ..
```

3. Start Metro bundler:
```bash
npm start
```

4. Run on device/simulator:
```bash
# iOS
npm run ios

# Android
npm run android
```

## Project Structure

```
mobile/
├── src/
│   ├── api/
│   │   └── client.ts          # Axios API client with auth interceptors
│   ├── context/
│   │   └── AuthContext.tsx    # Authentication context provider
│   ├── navigation/
│   │   └── AppNavigator.tsx   # React Navigation setup
│   ├── screens/
│   │   ├── LoginScreen.tsx    # Login/Register screen
│   │   ├── DashboardScreen.tsx # Main dashboard
│   │   ├── BiomarkersScreen.tsx # Biomarkers list
│   │   ├── BiomarkerDetailScreen.tsx # Evolution view
│   │   ├── DocumentsScreen.tsx # Documents list
│   │   └── ProfileScreen.tsx  # User profile
│   ├── utils/
│   │   └── theme.ts          # Theme colors and styles
│   └── App.tsx               # Root component
├── index.js                  # Entry point
├── package.json
└── app.json
```

## API Configuration

The app connects to the backend at `https://analize.online/api`. To change this:

1. Edit `src/api/client.ts`
2. Update the `API_BASE_URL` constant

For local development, you may need to use your machine's IP address instead of localhost.

## Authentication

The app uses JWT token authentication:
- Tokens are stored in AsyncStorage
- Auto-refresh is handled by the API interceptors
- On 401 responses, the user is automatically logged out

## Key Dependencies

- `react-navigation` - Navigation
- `react-native-paper` - Material Design UI components
- `axios` - HTTP client
- `@react-native-async-storage/async-storage` - Token storage
- `react-native-vector-icons` - Icons

## Notes

- Document upload is currently only available via the web app
- PDF viewing redirects to the web app (native PDF implementation pending)
- The app uses the same API as the web frontend

## Building for Production

### Android
```bash
cd android
./gradlew assembleRelease
```

### iOS
Use Xcode to archive and submit to App Store.

## Environment Variables

For different environments, create environment-specific configs or use react-native-config.
