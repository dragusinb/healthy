import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import {
  Text,
  TextInput,
  Surface,
  ActivityIndicator,
  Button,
  Chip,
  Divider,
} from 'react-native-paper';
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { colors } from '../utils/theme';

// Types
interface Profile {
  full_name: string;
  date_of_birth: string;
  gender: string;
  height_cm: number | string;
  weight_kg: number | string;
  blood_type: string;
  allergies: string[];
  chronic_conditions: string[];
  current_medications: string[];
  smoking_status: string;
  alcohol_consumption: string;
  physical_activity: string;
}

const ProfileScreen = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<Profile>({
    full_name: '',
    date_of_birth: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    blood_type: '',
    allergies: [],
    chronic_conditions: [],
    current_medications: [],
    smoking_status: '',
    alcohol_consumption: '',
    physical_activity: '',
  });

  // Input states for array fields
  const [allergyInput, setAllergyInput] = useState('');
  const [conditionInput, setConditionInput] = useState('');
  const [medicationInput, setMedicationInput] = useState('');

  const fetchProfile = useCallback(async () => {
    try {
      const response = await api.get('/users/profile');
      setProfile({
        full_name: response.data.full_name || '',
        date_of_birth: response.data.date_of_birth?.split('T')[0] || '',
        gender: response.data.gender || '',
        height_cm: response.data.height_cm || '',
        weight_kg: response.data.weight_kg || '',
        blood_type: response.data.blood_type || '',
        allergies: response.data.allergies || [],
        chronic_conditions: response.data.chronic_conditions || [],
        current_medications: response.data.current_medications || [],
        smoking_status: response.data.smoking_status || '',
        alcohol_consumption: response.data.alcohol_consumption || '',
        physical_activity: response.data.physical_activity || '',
      });
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchProfile();
  }, [fetchProfile]);

  const saveProfile = async () => {
    setSaving(true);
    try {
      const profileData = {
        ...profile,
        height_cm: profile.height_cm === '' ? null : parseFloat(String(profile.height_cm)) || null,
        weight_kg: profile.weight_kg === '' ? null : parseFloat(String(profile.weight_kg)) || null,
      };
      await api.put('/users/profile', profileData);
      Alert.alert('Success', 'Profile saved successfully');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: logout,
        },
      ]
    );
  };

  const addArrayItem = (field: keyof Profile, value: string, setter: (v: string) => void) => {
    if (value.trim() && !profile[field].includes(value.trim())) {
      setProfile((prev) => ({
        ...prev,
        [field]: [...(prev[field] as string[]), value.trim()],
      }));
      setter('');
    }
  };

  const removeArrayItem = (field: keyof Profile, value: string) => {
    setProfile((prev) => ({
      ...prev,
      [field]: (prev[field] as string[]).filter((item) => item !== value),
    }));
  };

  // Calculate BMI
  const calculateBMI = () => {
    const height = parseFloat(String(profile.height_cm));
    const weight = parseFloat(String(profile.weight_kg));
    if (height && weight) {
      const heightM = height / 100;
      return (weight / (heightM * heightM)).toFixed(1);
    }
    return null;
  };

  const getBMICategory = (bmi: number) => {
    if (bmi < 18.5) return { label: 'Underweight', color: colors.amber[600] };
    if (bmi < 25) return { label: 'Normal', color: colors.teal[600] };
    if (bmi < 30) return { label: 'Overweight', color: colors.amber[600] };
    return { label: 'Obese', color: colors.rose[600] };
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary[600]} />
      </View>
    );
  }

  const bmi = calculateBMI();

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          colors={[colors.primary[600]]}
        />
      }
    >
      {/* User Info Header */}
      <Surface style={styles.headerCard} elevation={1}>
        <View style={styles.userInfo}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {profile.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || '?'}
            </Text>
          </View>
          <View>
            <Text style={styles.userName}>
              {profile.full_name || 'Complete your profile'}
            </Text>
            <Text style={styles.userEmail}>{user?.email}</Text>
          </View>
        </View>
        <Button
          mode="outlined"
          onPress={handleLogout}
          icon="logout"
          textColor={colors.rose[600]}
          style={styles.logoutButton}
        >
          Logout
        </Button>
      </Surface>

      {/* Basic Info Section */}
      <Surface style={styles.sectionCard} elevation={1}>
        <Text style={styles.sectionTitle}>Basic Information</Text>

        <TextInput
          label="Full Name"
          value={profile.full_name}
          onChangeText={(text) => setProfile({ ...profile, full_name: text })}
          mode="outlined"
          left={<TextInput.Icon icon="account" />}
          style={styles.input}
        />

        <TextInput
          label="Date of Birth"
          value={profile.date_of_birth}
          onChangeText={(text) => setProfile({ ...profile, date_of_birth: text })}
          mode="outlined"
          placeholder="YYYY-MM-DD"
          left={<TextInput.Icon icon="calendar" />}
          style={styles.input}
        />

        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Gender</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={profile.gender}
              onValueChange={(value) => setProfile({ ...profile, gender: value })}
              style={styles.picker}
            >
              <Picker.Item label="Select..." value="" />
              <Picker.Item label="Male" value="male" />
              <Picker.Item label="Female" value="female" />
              <Picker.Item label="Other" value="other" />
            </Picker>
          </View>
        </View>

        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Blood Type</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={profile.blood_type}
              onValueChange={(value) => setProfile({ ...profile, blood_type: value })}
              style={styles.picker}
            >
              <Picker.Item label="Select..." value="" />
              <Picker.Item label="A+" value="A+" />
              <Picker.Item label="A-" value="A-" />
              <Picker.Item label="B+" value="B+" />
              <Picker.Item label="B-" value="B-" />
              <Picker.Item label="AB+" value="AB+" />
              <Picker.Item label="AB-" value="AB-" />
              <Picker.Item label="O+" value="O+" />
              <Picker.Item label="O-" value="O-" />
            </Picker>
          </View>
        </View>
      </Surface>

      {/* Body Measurements */}
      <Surface style={styles.sectionCard} elevation={1}>
        <Text style={styles.sectionTitle}>Body Measurements</Text>

        <View style={styles.measurementsRow}>
          <TextInput
            label="Height (cm)"
            value={String(profile.height_cm)}
            onChangeText={(text) => setProfile({ ...profile, height_cm: text })}
            mode="outlined"
            keyboardType="numeric"
            style={[styles.input, styles.halfInput]}
          />
          <TextInput
            label="Weight (kg)"
            value={String(profile.weight_kg)}
            onChangeText={(text) => setProfile({ ...profile, weight_kg: text })}
            mode="outlined"
            keyboardType="numeric"
            style={[styles.input, styles.halfInput]}
          />
        </View>

        {bmi && (
          <View style={styles.bmiContainer}>
            <Text style={styles.bmiLabel}>BMI:</Text>
            <Text style={styles.bmiValue}>{bmi}</Text>
            <Text style={[styles.bmiCategory, { color: getBMICategory(parseFloat(bmi)).color }]}>
              ({getBMICategory(parseFloat(bmi)).label})
            </Text>
          </View>
        )}
      </Surface>

      {/* Lifestyle */}
      <Surface style={styles.sectionCard} elevation={1}>
        <Text style={styles.sectionTitle}>Lifestyle</Text>

        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Smoking</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={profile.smoking_status}
              onValueChange={(value) => setProfile({ ...profile, smoking_status: value })}
              style={styles.picker}
            >
              <Picker.Item label="Select..." value="" />
              <Picker.Item label="Never smoked" value="never" />
              <Picker.Item label="Former smoker" value="former" />
              <Picker.Item label="Current smoker" value="current" />
            </Picker>
          </View>
        </View>

        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Alcohol</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={profile.alcohol_consumption}
              onValueChange={(value) => setProfile({ ...profile, alcohol_consumption: value })}
              style={styles.picker}
            >
              <Picker.Item label="Select..." value="" />
              <Picker.Item label="None" value="none" />
              <Picker.Item label="Occasional" value="occasional" />
              <Picker.Item label="Moderate" value="moderate" />
              <Picker.Item label="Heavy" value="heavy" />
            </Picker>
          </View>
        </View>

        <View style={styles.pickerContainer}>
          <Text style={styles.pickerLabel}>Physical Activity</Text>
          <View style={styles.pickerWrapper}>
            <Picker
              selectedValue={profile.physical_activity}
              onValueChange={(value) => setProfile({ ...profile, physical_activity: value })}
              style={styles.picker}
            >
              <Picker.Item label="Select..." value="" />
              <Picker.Item label="Sedentary" value="sedentary" />
              <Picker.Item label="Light (1-2 days/week)" value="light" />
              <Picker.Item label="Moderate (3-4 days/week)" value="moderate" />
              <Picker.Item label="Active (5+ days/week)" value="active" />
              <Picker.Item label="Very Active (athlete)" value="very_active" />
            </Picker>
          </View>
        </View>
      </Surface>

      {/* Medical History */}
      <Surface style={styles.sectionCard} elevation={1}>
        <Text style={styles.sectionTitle}>Medical History</Text>

        {/* Allergies */}
        <View style={styles.arraySection}>
          <Text style={styles.arrayLabel}>Allergies</Text>
          <View style={styles.arrayInputRow}>
            <TextInput
              value={allergyInput}
              onChangeText={setAllergyInput}
              mode="outlined"
              placeholder="Add allergy..."
              style={[styles.input, styles.arrayInput]}
              dense
            />
            <Button
              mode="contained-tonal"
              onPress={() => addArrayItem('allergies', allergyInput, setAllergyInput)}
              compact
            >
              Add
            </Button>
          </View>
          <View style={styles.chipsContainer}>
            {profile.allergies.map((item, i) => (
              <Chip
                key={i}
                onClose={() => removeArrayItem('allergies', item)}
                style={styles.chip}
                textStyle={styles.chipText}
              >
                {item}
              </Chip>
            ))}
          </View>
        </View>

        <Divider style={styles.divider} />

        {/* Chronic Conditions */}
        <View style={styles.arraySection}>
          <Text style={styles.arrayLabel}>Chronic Conditions</Text>
          <View style={styles.arrayInputRow}>
            <TextInput
              value={conditionInput}
              onChangeText={setConditionInput}
              mode="outlined"
              placeholder="Add condition..."
              style={[styles.input, styles.arrayInput]}
              dense
            />
            <Button
              mode="contained-tonal"
              onPress={() => addArrayItem('chronic_conditions', conditionInput, setConditionInput)}
              compact
            >
              Add
            </Button>
          </View>
          <View style={styles.chipsContainer}>
            {profile.chronic_conditions.map((item, i) => (
              <Chip
                key={i}
                onClose={() => removeArrayItem('chronic_conditions', item)}
                style={[styles.chip, { backgroundColor: colors.amber[50] }]}
                textStyle={[styles.chipText, { color: colors.amber[700] }]}
              >
                {item}
              </Chip>
            ))}
          </View>
        </View>

        <Divider style={styles.divider} />

        {/* Medications */}
        <View style={styles.arraySection}>
          <Text style={styles.arrayLabel}>Current Medications</Text>
          <View style={styles.arrayInputRow}>
            <TextInput
              value={medicationInput}
              onChangeText={setMedicationInput}
              mode="outlined"
              placeholder="Add medication..."
              style={[styles.input, styles.arrayInput]}
              dense
            />
            <Button
              mode="contained-tonal"
              onPress={() => addArrayItem('current_medications', medicationInput, setMedicationInput)}
              compact
            >
              Add
            </Button>
          </View>
          <View style={styles.chipsContainer}>
            {profile.current_medications.map((item, i) => (
              <Chip
                key={i}
                onClose={() => removeArrayItem('current_medications', item)}
                style={[styles.chip, { backgroundColor: colors.primary[50] }]}
                textStyle={[styles.chipText, { color: colors.primary[700] }]}
              >
                {item}
              </Chip>
            ))}
          </View>
        </View>
      </Surface>

      {/* Save Button */}
      <Button
        mode="contained"
        onPress={saveProfile}
        loading={saving}
        disabled={saving}
        style={styles.saveButton}
        contentStyle={styles.saveButtonContent}
      >
        Save Profile
      </Button>

      {/* Info Note */}
      <View style={styles.infoNote}>
        <Icon name="information" size={16} color={colors.primary[600]} />
        <Text style={styles.infoText}>
          Your profile helps the AI provide more personalized health insights.
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.slate[50],
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.slate[50],
  },
  // Header Card
  headerCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.primary[500],
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '600',
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.slate[800],
  },
  userEmail: {
    fontSize: 12,
    color: colors.slate[500],
    marginTop: 2,
  },
  logoutButton: {
    borderColor: colors.rose[200],
  },
  // Section Card
  sectionCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.slate[800],
    marginBottom: 16,
  },
  input: {
    marginBottom: 12,
    backgroundColor: '#ffffff',
  },
  halfInput: {
    flex: 1,
    marginHorizontal: 4,
  },
  measurementsRow: {
    flexDirection: 'row',
    marginHorizontal: -4,
  },
  bmiContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.slate[50],
    padding: 12,
    borderRadius: 8,
  },
  bmiLabel: {
    fontSize: 14,
    color: colors.slate[600],
  },
  bmiValue: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.slate[800],
    marginLeft: 8,
  },
  bmiCategory: {
    fontSize: 14,
    marginLeft: 4,
  },
  // Picker
  pickerContainer: {
    marginBottom: 12,
  },
  pickerLabel: {
    fontSize: 12,
    color: colors.slate[600],
    marginBottom: 4,
    marginLeft: 4,
  },
  pickerWrapper: {
    borderWidth: 1,
    borderColor: colors.slate[300],
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
    backgroundColor: '#ffffff',
  },
  // Array Fields
  arraySection: {
    marginBottom: 8,
  },
  arrayLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.slate[700],
    marginBottom: 8,
  },
  arrayInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  arrayInput: {
    flex: 1,
    marginRight: 8,
    marginBottom: 0,
  },
  chipsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  chip: {
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: colors.rose[50],
  },
  chipText: {
    fontSize: 12,
    color: colors.rose[700],
  },
  divider: {
    marginVertical: 16,
  },
  // Save Button
  saveButton: {
    borderRadius: 12,
    marginBottom: 16,
  },
  saveButtonContent: {
    paddingVertical: 8,
  },
  // Info Note
  infoNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.primary[50],
    padding: 12,
    borderRadius: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    color: colors.primary[700],
    marginLeft: 8,
    lineHeight: 18,
  },
});

export default ProfileScreen;
