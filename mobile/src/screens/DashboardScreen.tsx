import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { Text, Surface, ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import api from '../api/client';
import { colors } from '../utils/theme';
import { RootStackParamList, MainTabParamList } from '../navigation/AppNavigator';

// Types
interface DashboardStats {
  documents_count: number;
  biomarkers_count: number;
  alerts_count: number;
}

interface RecentBiomarker {
  id: number;
  name: string;
  value: number | string;
  unit: string;
  status: 'normal' | 'high' | 'low';
  date: string;
}

interface HealthOverview {
  profile: {
    full_name?: string;
    age?: number;
    gender?: string;
    blood_type?: string;
  } | null;
  profile_complete: boolean;
  timeline: {
    first_record_date?: string;
    tracking_duration?: string;
    total_documents?: number;
  } | null;
  health_status: {
    has_analysis: boolean;
    last_analysis_date?: string;
    days_since_analysis?: number;
  } | null;
  ai_summary?: string;
  reminders_count: number;
}

// Stat Card Component
const StatCard = ({
  title,
  value,
  icon,
  color,
  onPress,
}: {
  title: string;
  value: number;
  icon: string;
  color: string;
  onPress?: () => void;
}) => (
  <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
    <Surface style={styles.statCard} elevation={1}>
      <View style={[styles.statIcon, { backgroundColor: color + '20' }]}>
        <Icon name={icon} size={24} color={color} />
      </View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statTitle}>{title}</Text>
    </Surface>
  </TouchableOpacity>
);

// Biomarker Row Component
const BiomarkerRow = ({
  biomarker,
  onPress,
}: {
  biomarker: RecentBiomarker;
  onPress: () => void;
}) => {
  const statusColor =
    biomarker.status === 'normal'
      ? colors.teal[500]
      : biomarker.status === 'high'
      ? colors.rose[500]
      : colors.amber[500];

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <View style={styles.biomarkerRow}>
        <View style={styles.biomarkerInfo}>
          <Text style={styles.biomarkerName}>{biomarker.name}</Text>
          <Text style={styles.biomarkerDate}>
            {new Date(biomarker.date).toLocaleDateString()}
          </Text>
        </View>
        <View style={styles.biomarkerValue}>
          <Text style={styles.valueText}>
            {biomarker.value} <Text style={styles.unitText}>{biomarker.unit}</Text>
          </Text>
          <View style={[styles.statusIndicator, { backgroundColor: statusColor }]} />
        </View>
      </View>
    </TouchableOpacity>
  );
};

const DashboardScreen = () => {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<DashboardStats>({
    documents_count: 0,
    biomarkers_count: 0,
    alerts_count: 0,
  });
  const [recentBiomarkers, setRecentBiomarkers] = useState<RecentBiomarker[]>([]);
  const [healthOverview, setHealthOverview] = useState<HealthOverview | null>(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [statsRes, recentRes, alertsRes, overviewRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/recent-biomarkers'),
        api.get('/dashboard/alerts-count'),
        api.get('/dashboard/health-overview'),
      ]);

      setStats({
        ...statsRes.data,
        alerts_count: alertsRes.data.alerts_count,
      });
      setRecentBiomarkers(recentRes.data);
      setHealthOverview(overviewRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchDashboardData();
  }, [fetchDashboardData]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary[600]} />
      </View>
    );
  }

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
      {/* Health Overview Card */}
      {healthOverview && (
        <Surface style={styles.overviewCard} elevation={1}>
          <View style={styles.overviewHeader}>
            <View style={styles.profileInfo}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>
                  {healthOverview.profile?.full_name?.charAt(0)?.toUpperCase() || '?'}
                </Text>
              </View>
              <View>
                <Text style={styles.profileName}>
                  {healthOverview.profile?.full_name || 'Complete your profile'}
                </Text>
                <View style={styles.profileDetails}>
                  {healthOverview.profile?.age && (
                    <Text style={styles.profileDetail}>
                      {healthOverview.profile.age} years
                    </Text>
                  )}
                  {healthOverview.profile?.blood_type && (
                    <View style={styles.bloodTypeBadge}>
                      <Icon name="water" size={12} color={colors.rose[600]} />
                      <Text style={styles.bloodTypeText}>
                        {healthOverview.profile.blood_type}
                      </Text>
                    </View>
                  )}
                </View>
              </View>
            </View>
          </View>

          {/* Timeline Info */}
          {healthOverview.timeline && (
            <View style={styles.timelineInfo}>
              <View style={styles.timelineItem}>
                <Icon name="clock-outline" size={16} color={colors.slate[400]} />
                <Text style={styles.timelineLabel}>Tracking since</Text>
                <Text style={styles.timelineValue}>
                  {healthOverview.timeline.first_record_date
                    ? new Date(healthOverview.timeline.first_record_date).toLocaleDateString()
                    : '-'}
                </Text>
              </View>
              {healthOverview.timeline.tracking_duration && (
                <View style={styles.timelineItem}>
                  <Icon name="calendar-range" size={16} color={colors.slate[400]} />
                  <Text style={styles.timelineLabel}>Duration</Text>
                  <Text style={styles.timelineValue}>
                    {healthOverview.timeline.tracking_duration}
                  </Text>
                </View>
              )}
            </View>
          )}
        </Surface>
      )}

      {/* Stats Row */}
      <View style={styles.statsRow}>
        <StatCard
          title="Documents"
          value={stats.documents_count}
          icon="file-document-outline"
          color={colors.primary[600]}
        />
        <StatCard
          title="Biomarkers"
          value={stats.biomarkers_count}
          icon="heart-pulse"
          color={colors.teal[600]}
        />
        <StatCard
          title="Alerts"
          value={stats.alerts_count}
          icon={stats.alerts_count > 0 ? 'alert' : 'shield-check'}
          color={stats.alerts_count > 0 ? colors.rose[500] : colors.primary[600]}
        />
      </View>

      {/* AI Summary Card */}
      {healthOverview?.ai_summary && (
        <Surface style={styles.aiSummaryCard} elevation={1}>
          <View style={styles.aiSummaryHeader}>
            <View style={styles.aiIcon}>
              <Icon name="brain" size={20} color={colors.primary[600]} />
            </View>
            <Text style={styles.aiSummaryTitle}>AI Health Summary</Text>
          </View>
          <Text style={styles.aiSummaryText}>{healthOverview.ai_summary}</Text>
        </Surface>
      )}

      {/* Recent Biomarkers */}
      <Surface style={styles.recentCard} elevation={1}>
        <View style={styles.recentHeader}>
          <Text style={styles.recentTitle}>Recent Biomarkers</Text>
          <TouchableOpacity
            onPress={() => {
              // Navigate to Biomarkers tab - we need parent navigator access
              // This is a simplified approach
            }}
          >
            <Text style={styles.viewAllLink}>View All</Text>
          </TouchableOpacity>
        </View>

        {recentBiomarkers.length > 0 ? (
          recentBiomarkers.slice(0, 5).map((biomarker) => (
            <BiomarkerRow
              key={biomarker.id}
              biomarker={biomarker}
              onPress={() =>
                navigation.navigate('BiomarkerDetail', { name: biomarker.name })
              }
            />
          ))
        ) : (
          <View style={styles.emptyState}>
            <Icon name="flask-empty-outline" size={40} color={colors.slate[300]} />
            <Text style={styles.emptyText}>No biomarkers yet</Text>
            <Text style={styles.emptySubtext}>
              Upload documents to see your health data
            </Text>
          </View>
        )}
      </Surface>

      {/* Reminders */}
      {healthOverview && healthOverview.reminders_count > 0 && (
        <Surface style={styles.remindersCard} elevation={1}>
          <View style={styles.reminderIcon}>
            <Icon name="bell" size={20} color={colors.amber[600]} />
          </View>
          <View style={styles.reminderContent}>
            <Text style={styles.reminderTitle}>
              {healthOverview.reminders_count} overdue screening
              {healthOverview.reminders_count > 1 ? 's' : ''}
            </Text>
            <Text style={styles.reminderText}>
              Check your screening schedule for recommended tests
            </Text>
          </View>
        </Surface>
      )}
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
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.slate[50],
  },
  // Overview Card
  overviewCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  overviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  profileInfo: {
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
  profileName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.slate[800],
  },
  profileDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  profileDetail: {
    fontSize: 14,
    color: colors.slate[500],
    marginRight: 12,
  },
  bloodTypeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.rose[50],
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  bloodTypeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.rose[600],
    marginLeft: 4,
  },
  timelineInfo: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: colors.slate[100],
    paddingTop: 12,
  },
  timelineItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timelineLabel: {
    fontSize: 12,
    color: colors.slate[400],
    marginHorizontal: 6,
  },
  timelineValue: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.slate[700],
  },
  // Stats Row
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    width: '31%',
  },
  statIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.slate[800],
  },
  statTitle: {
    fontSize: 12,
    color: colors.slate[500],
    marginTop: 4,
  },
  // AI Summary Card
  aiSummaryCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  aiSummaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  aiIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: colors.primary[50],
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  aiSummaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.slate[800],
  },
  aiSummaryText: {
    fontSize: 14,
    color: colors.slate[600],
    lineHeight: 20,
  },
  // Recent Biomarkers
  recentCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  recentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  recentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.slate[800],
  },
  viewAllLink: {
    fontSize: 14,
    color: colors.primary[600],
    fontWeight: '500',
  },
  biomarkerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.slate[100],
  },
  biomarkerInfo: {
    flex: 1,
  },
  biomarkerName: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.slate[800],
  },
  biomarkerDate: {
    fontSize: 12,
    color: colors.slate[400],
    marginTop: 2,
  },
  biomarkerValue: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  valueText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.slate[800],
  },
  unitText: {
    fontSize: 12,
    fontWeight: '400',
    color: colors.slate[400],
  },
  statusIndicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginLeft: 8,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.slate[500],
    marginTop: 12,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.slate[400],
    marginTop: 4,
  },
  // Reminders Card
  remindersCard: {
    backgroundColor: colors.amber[50],
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.amber[200],
  },
  reminderIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.amber[100],
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  reminderContent: {
    flex: 1,
  },
  reminderTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.amber[800],
  },
  reminderText: {
    fontSize: 12,
    color: colors.amber[600],
    marginTop: 2,
  },
});

export default DashboardScreen;
