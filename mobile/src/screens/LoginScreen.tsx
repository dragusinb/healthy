import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import {
  TextInput,
  Button,
  Text,
  Surface,
  HelperText,
  IconButton,
  Checkbox,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useAuth } from '../context/AuthContext';
import { colors } from '../utils/theme';

const LoginScreen = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [recoveryKey, setRecoveryKey] = useState<string | null>(null);

  const { login, register } = useAuth();

  const handleSubmit = async () => {
    setError('');
    setLoading(true);

    try {
      if (isRegisterMode) {
        // Validation
        if (password.length < 6) {
          setError('Password must be at least 6 characters');
          setLoading(false);
          return;
        }
        if (password !== confirmPassword) {
          setError('Passwords do not match');
          setLoading(false);
          return;
        }
        if (!acceptedTerms) {
          setError('You must accept the Terms and Privacy Policy');
          setLoading(false);
          return;
        }

        const result = await register(email, password, acceptedTerms);
        if (result?.recovery_key) {
          setRecoveryKey(result.recovery_key);
        }
      } else {
        const result = await login(email, password);
        if (result?.recovery_key) {
          setRecoveryKey(result.recovery_key);
        }
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        (isRegisterMode ? 'Registration failed. Email may already be registered.' : 'Invalid email or password')
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsRegisterMode(!isRegisterMode);
    setError('');
    setConfirmPassword('');
    setAcceptedTerms(false);
  };

  // Recovery Key Modal
  if (recoveryKey) {
    return (
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Surface style={styles.card} elevation={2}>
            <View style={styles.iconContainer}>
              <View style={[styles.iconCircle, { backgroundColor: colors.amber[100] }]}>
                <Icon name="key" size={40} color={colors.amber[600]} />
              </View>
            </View>

            <Text style={styles.title}>Save Your Recovery Key!</Text>
            <Text style={styles.subtitle}>
              Your account is now protected with encryption
            </Text>

            <View style={styles.warningBox}>
              <Icon name="alert" size={24} color={colors.rose[600]} />
              <Text style={styles.warningText}>
                This is the only time you will see this key. If you forget your password
                and don't have the key, all your medical data will be permanently lost.
              </Text>
            </View>

            <View style={styles.keyBox}>
              <Text style={styles.keyLabel}>Recovery Key:</Text>
              <Text style={styles.keyValue} selectable>
                {recoveryKey}
              </Text>
            </View>

            <Text style={styles.saveHint}>
              Save this key in a password manager or write it down and store it safely.
            </Text>

            <Button
              mode="contained"
              onPress={() => setRecoveryKey(null)}
              style={styles.button}
              contentStyle={styles.buttonContent}
            >
              I've Saved the Key
            </Button>
          </Surface>
        </ScrollView>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logoCircle}>
            <Icon name="heart-pulse" size={32} color="#ffffff" />
          </View>
          <Text style={styles.appName}>Analize.online</Text>
          <Text style={styles.tagline}>Track your health journey</Text>
        </View>

        {/* Login Card */}
        <Surface style={styles.card} elevation={2}>
          <Text style={styles.cardTitle}>
            {isRegisterMode ? 'Create Account' : 'Sign In'}
          </Text>

          {error ? (
            <View style={styles.errorBox}>
              <Icon name="alert-circle" size={20} color={colors.rose[600]} />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          <TextInput
            label="Email"
            value={email}
            onChangeText={setEmail}
            mode="outlined"
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            left={<TextInput.Icon icon="email" />}
            style={styles.input}
          />

          <TextInput
            label="Password"
            value={password}
            onChangeText={setPassword}
            mode="outlined"
            secureTextEntry={!showPassword}
            left={<TextInput.Icon icon="lock" />}
            right={
              <TextInput.Icon
                icon={showPassword ? 'eye-off' : 'eye'}
                onPress={() => setShowPassword(!showPassword)}
              />
            }
            style={styles.input}
          />

          {isRegisterMode && (
            <>
              <HelperText type="info" visible>
                Minimum 6 characters
              </HelperText>

              <TextInput
                label="Confirm Password"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                mode="outlined"
                secureTextEntry={!showPassword}
                left={<TextInput.Icon icon="lock" />}
                style={styles.input}
              />

              {/* Encryption Info */}
              <View style={styles.infoBox}>
                <Icon name="shield-lock" size={20} color={colors.teal[600]} />
                <View style={styles.infoTextContainer}>
                  <Text style={styles.infoTitle}>Your data is encrypted</Text>
                  <Text style={styles.infoText}>
                    Your password is also your encryption key. All medical data is
                    encrypted so only you can access it.
                  </Text>
                </View>
              </View>

              {/* Terms Checkbox */}
              <TouchableOpacity
                style={styles.checkboxContainer}
                onPress={() => setAcceptedTerms(!acceptedTerms)}
              >
                <Checkbox
                  status={acceptedTerms ? 'checked' : 'unchecked'}
                  onPress={() => setAcceptedTerms(!acceptedTerms)}
                  color={colors.primary[600]}
                />
                <Text style={styles.checkboxLabel}>
                  I accept the Terms and Conditions and Privacy Policy
                </Text>
              </TouchableOpacity>
            </>
          )}

          <Button
            mode="contained"
            onPress={handleSubmit}
            loading={loading}
            disabled={loading}
            style={styles.button}
            contentStyle={styles.buttonContent}
          >
            {isRegisterMode ? 'Create Account' : 'Sign In'}
          </Button>

          <View style={styles.toggleContainer}>
            <Text style={styles.toggleText}>
              {isRegisterMode ? 'Already have an account?' : "Don't have an account?"}
            </Text>
            <TouchableOpacity onPress={toggleMode}>
              <Text style={styles.toggleLink}>
                {isRegisterMode ? 'Sign In' : 'Sign Up'}
              </Text>
            </TouchableOpacity>
          </View>
        </Surface>

        {/* Footer */}
        <Text style={styles.footer}>Your data is encrypted and secure</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.slate[50],
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoCircle: {
    width: 64,
    height: 64,
    borderRadius: 16,
    backgroundColor: colors.primary[600],
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  appName: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.slate[800],
  },
  tagline: {
    fontSize: 16,
    color: colors.slate[500],
    marginTop: 4,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 24,
    marginBottom: 24,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.slate[800],
    textAlign: 'center',
    marginBottom: 20,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.rose[50],
    borderWidth: 1,
    borderColor: colors.rose[200],
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: colors.rose[600],
    marginLeft: 8,
    flex: 1,
  },
  input: {
    marginBottom: 12,
    backgroundColor: '#ffffff',
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: colors.teal[50],
    borderWidth: 1,
    borderColor: colors.teal[200],
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  infoTextContainer: {
    flex: 1,
    marginLeft: 12,
  },
  infoTitle: {
    fontWeight: '600',
    color: colors.teal[700],
    marginBottom: 4,
  },
  infoText: {
    fontSize: 13,
    color: colors.teal[600],
    lineHeight: 18,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  checkboxLabel: {
    flex: 1,
    color: colors.slate[600],
    fontSize: 14,
  },
  button: {
    marginTop: 8,
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: 8,
  },
  toggleContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 20,
  },
  toggleText: {
    color: colors.slate[500],
  },
  toggleLink: {
    color: colors.primary[600],
    fontWeight: '600',
    marginLeft: 4,
  },
  footer: {
    textAlign: 'center',
    color: colors.slate[400],
    fontSize: 14,
  },
  // Recovery Key Styles
  iconContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.slate[800],
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: colors.slate[500],
    textAlign: 'center',
    marginBottom: 24,
  },
  warningBox: {
    flexDirection: 'row',
    backgroundColor: colors.rose[50],
    borderWidth: 2,
    borderColor: colors.rose[200],
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  warningText: {
    flex: 1,
    marginLeft: 12,
    color: colors.rose[700],
    fontSize: 14,
    lineHeight: 20,
  },
  keyBox: {
    backgroundColor: colors.slate[800],
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  keyLabel: {
    color: colors.slate[400],
    fontSize: 12,
    marginBottom: 8,
  },
  keyValue: {
    color: colors.amber[400],
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 16,
  },
  saveHint: {
    textAlign: 'center',
    color: colors.slate[500],
    marginBottom: 20,
  },
});

export default LoginScreen;
