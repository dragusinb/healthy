import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { Text, Surface, ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { RouteProp, useRoute } from '@react-navigation/native';

import api from '../api/client';
import { colors } from '../utils/theme';
import { RootStackParamList } from '../navigation/AppNavigator';

// Types
interface EvolutionData {
  name: string;
  history: Array<{
    id: number;
    value: number | string;
    unit: string;
    range: string;
    status: 'normal' | 'high' | 'low';
    date: string;
    provider?: string;
  }>;
  reference_range?: string;
  unit?: string;
}

type BiomarkerDetailRouteProp = RouteProp<RootStackParamList, 'BiomarkerDetail'>;

const { width: screenWidth } = Dimensions.get('window');

const BiomarkerDetailScreen = () => {
  const route = useRoute<BiomarkerDetailRouteProp>();
  const { name } = route.params;

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<EvolutionData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchEvolution = useCallback(async () => {
    try {
      setError(null);
      const response = await api.get(`/dashboard/evolution/${encodeURIComponent(name)}`);
      setData(response.data);
    } catch (err: any) {
      console.error('Failed to fetch evolution:', err);
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [name]);

  useEffect(() => {
    fetchEvolution();
  }, [fetchEvolution]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchEvolution();
  }, [fetchEvolution]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary[600]} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="alert-circle-outline" size={48} color={colors.rose[500]} />
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (!data || data.history.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Icon name="chart-line" size={48} color={colors.slate[300]} />
        <Text style={styles.emptyText}>No history available</Text>
      </View>
    );
  }

  // Calculate statistics
  const numericValues = data.history
    .map((h) => (typeof h.value === 'number' ? h.value : parseFloat(String(h.value))))
    .filter((v) => !isNaN(v));

  const latest = data.history[0];
  const min = numericValues.length > 0 ? Math.min(...numericValues) : null;
  const max = numericValues.length > 0 ? Math.max(...numericValues) : null;
  const avg =
    numericValues.length > 0
      ? (numericValues.reduce((a, b) => a + b, 0) / numericValues.length).toFixed(1)
      : null;

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
      {/* Header */}
      <Surface style={styles.headerCard} elevation={1}>
        <Text style={styles.biomarkerName}>{data.name}</Text>
        <View style={styles.latestValue}>
          <Text style={styles.valueText}>
            {latest.value}
            <Text style={styles.unitText}> {latest.unit}</Text>
          </Text>
          <StatusBadge status={latest.status} />
        </View>
        <Text style={styles.referenceRange}>
          Reference: {data.reference_range || latest.range}
        </Text>
        <Text style={styles.lastUpdated}>
          Last updated: {new Date(latest.date).toLocaleDateString()}
        </Text>
      </Surface>

      {/* Statistics */}
      {numericValues.length > 1 && (
        <View style={styles.statsRow}>
          <StatBox label="Min" value={min?.toFixed(1) || '-'} color={colors.primary[500]} />
          <StatBox label="Avg" value={avg || '-'} color={colors.teal[500]} />
          <StatBox label="Max" value={max?.toFixed(1) || '-'} color={colors.amber[500]} />
        </View>
      )}

      {/* Simple Chart Visualization */}
      {numericValues.length > 1 && (
        <Surface style={styles.chartCard} elevation={1}>
          <Text style={styles.sectionTitle}>Trend</Text>
          <SimpleChart values={numericValues.slice(0, 10).reverse()} />
        </Surface>
      )}

      {/* History List */}
      <Surface style={styles.historyCard} elevation={1}>
        <Text style={styles.sectionTitle}>
          History ({data.history.length} records)
        </Text>
        {data.history.map((record, index) => (
          <HistoryRow key={record.id} record={record} isFirst={index === 0} />
        ))}
      </Surface>
    </ScrollView>
  );
};

// Status Badge Component
const StatusBadge = ({ status }: { status: 'normal' | 'high' | 'low' }) => {
  const config = {
    normal: { bg: colors.teal[50], text: colors.teal[600], label: 'Normal' },
    high: { bg: colors.rose[50], text: colors.rose[600], label: 'High' },
    low: { bg: colors.amber[50], text: colors.amber[600], label: 'Low' },
  };
  const c = config[status];

  return (
    <View style={[styles.statusBadge, { backgroundColor: c.bg }]}>
      <Icon
        name={status === 'normal' ? 'check-circle' : 'alert'}
        size={14}
        color={c.text}
      />
      <Text style={[styles.statusText, { color: c.text }]}>{c.label}</Text>
    </View>
  );
};

// Stat Box Component
const StatBox = ({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) => (
  <Surface style={styles.statBox} elevation={1}>
    <Text style={[styles.statValue, { color }]}>{value}</Text>
    <Text style={styles.statLabel}>{label}</Text>
  </Surface>
);

// Simple Chart Component (bar chart visualization)
const SimpleChart = ({ values }: { values: number[] }) => {
  if (values.length === 0) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return (
    <View style={styles.chartContainer}>
      {values.map((value, index) => {
        const height = ((value - min) / range) * 80 + 20; // Min 20px, max 100px
        return (
          <View key={index} style={styles.chartBar}>
            <View
              style={[
                styles.chartBarFill,
                {
                  height,
                  backgroundColor:
                    index === values.length - 1
                      ? colors.primary[500]
                      : colors.primary[200],
                },
              ]}
            />
            <Text style={styles.chartBarLabel}>
              {value.toFixed(0)}
            </Text>
          </View>
        );
      })}
    </View>
  );
};

// History Row Component
const HistoryRow = ({
  record,
  isFirst,
}: {
  record: EvolutionData['history'][0];
  isFirst: boolean;
}) => {
  const statusColor =
    record.status === 'normal'
      ? colors.teal[500]
      : record.status === 'high'
      ? colors.rose[500]
      : colors.amber[500];

  return (
    <View style={[styles.historyRow, isFirst && styles.historyRowFirst]}>
      <View style={styles.historyLeft}>
        <View style={[styles.historyDot, { backgroundColor: statusColor }]} />
        <View>
          <Text style={styles.historyDate}>
            {new Date(record.date).toLocaleDateString()}
          </Text>
          {record.provider && (
            <Text style={styles.historyProvider}>{record.provider}</Text>
          )}
        </View>
      </View>
      <View style={styles.historyRight}>
        <Text style={styles.historyValue}>
          {record.value}
          <Text style={styles.historyUnit}> {record.unit}</Text>
        </Text>
        <Icon
          name={
            record.status === 'normal'
              ? 'check'
              : record.status === 'high'
              ? 'arrow-up'
              : 'arrow-down'
          }
          size={16}
          color={statusColor}
        />
      </View>
    </View>
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.slate[50],
    padding: 32,
  },
  errorText: {
    fontSize: 16,
    color: colors.rose[600],
    marginTop: 16,
    textAlign: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.slate[50],
  },
  emptyText: {
    fontSize: 16,
    color: colors.slate[500],
    marginTop: 16,
  },
  // Header Card
  headerCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    alignItems: 'center',
  },
  biomarkerName: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.slate[800],
    marginBottom: 12,
  },
  latestValue: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  valueText: {
    fontSize: 32,
    fontWeight: '700',
    color: colors.slate[800],
    marginRight: 12,
  },
  unitText: {
    fontSize: 18,
    fontWeight: '400',
    color: colors.slate[400],
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  referenceRange: {
    fontSize: 14,
    color: colors.slate[500],
    marginTop: 8,
  },
  lastUpdated: {
    fontSize: 12,
    color: colors.slate[400],
    marginTop: 4,
  },
  // Stats Row
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statBox: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    width: '31%',
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
  },
  statLabel: {
    fontSize: 12,
    color: colors.slate[500],
    marginTop: 4,
  },
  // Chart Card
  chartCard: {
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
  chartContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-around',
    height: 120,
    paddingHorizontal: 8,
  },
  chartBar: {
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 4,
  },
  chartBarFill: {
    width: '100%',
    maxWidth: 30,
    borderRadius: 4,
  },
  chartBarLabel: {
    fontSize: 10,
    color: colors.slate[500],
    marginTop: 4,
  },
  // History Card
  historyCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
  },
  historyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: colors.slate[100],
  },
  historyRowFirst: {
    borderTopWidth: 0,
  },
  historyLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  historyDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  historyDate: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.slate[800],
  },
  historyProvider: {
    fontSize: 12,
    color: colors.slate[400],
    marginTop: 2,
  },
  historyRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  historyValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.slate[800],
    marginRight: 8,
  },
  historyUnit: {
    fontSize: 12,
    fontWeight: '400',
    color: colors.slate[400],
  },
});

export default BiomarkerDetailScreen;
