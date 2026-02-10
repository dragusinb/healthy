import { MD3LightTheme, configureFonts } from 'react-native-paper';

// Colors matching the web app
const colors = {
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },
  teal: {
    50: '#f0fdfa',
    100: '#ccfbf1',
    200: '#99f6e4',
    300: '#5eead4',
    400: '#2dd4bf',
    500: '#14b8a6',
    600: '#0d9488',
    700: '#0f766e',
  },
  rose: {
    50: '#fff1f2',
    100: '#ffe4e6',
    200: '#fecdd3',
    500: '#f43f5e',
    600: '#e11d48',
  },
  amber: {
    50: '#fffbeb',
    100: '#fef3c7',
    500: '#f59e0b',
    600: '#d97706',
  },
  slate: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },
};

// Paper theme customization
export const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: colors.primary[600],
    primaryContainer: colors.primary[100],
    secondary: colors.teal[600],
    secondaryContainer: colors.teal[100],
    tertiary: colors.amber[600],
    tertiaryContainer: colors.amber[100],
    error: colors.rose[600],
    errorContainer: colors.rose[100],
    background: colors.slate[50],
    surface: '#ffffff',
    surfaceVariant: colors.slate[100],
    outline: colors.slate[300],
    onPrimary: '#ffffff',
    onPrimaryContainer: colors.primary[900],
    onSecondary: '#ffffff',
    onSecondaryContainer: colors.teal[700],
    onTertiary: '#ffffff',
    onTertiaryContainer: colors.amber[600],
    onError: '#ffffff',
    onErrorContainer: colors.rose[600],
    onBackground: colors.slate[900],
    onSurface: colors.slate[900],
    onSurfaceVariant: colors.slate[600],
  },
  roundness: 12,
};

// Export colors for direct use
export { colors };

// Status colors
export const statusColors = {
  normal: colors.teal[500],
  high: colors.rose[500],
  low: colors.amber[500],
  pending: colors.amber[500],
  processed: colors.teal[500],
  error: colors.rose[500],
};

// Common styles
export const commonStyles = {
  container: {
    flex: 1,
    backgroundColor: colors.slate[50],
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600' as const,
    color: colors.slate[800],
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600' as const,
    color: colors.slate[500],
    textTransform: 'uppercase' as const,
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  errorText: {
    color: colors.rose[600],
    fontSize: 14,
  },
  successText: {
    color: colors.teal[600],
    fontSize: 14,
  },
};
