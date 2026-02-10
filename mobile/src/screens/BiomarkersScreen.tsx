import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import {
  Text,
  Searchbar,
  Surface,
  ActivityIndicator,
  SegmentedButtons,
  Chip,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import api from '../api/client';
import { colors } from '../utils/theme';
import { RootStackParamList } from '../navigation/AppNavigator';

// Types
interface BiomarkerGroup {
  canonical_name: string;
  has_issues: boolean;
  latest: {
    id: number;
    name: string;
    value: number | string;
    unit: string;
    range: string;
    status: 'normal' | 'high' | 'low';
    date: string;
    document_id?: number;
  };
  history: Array<{
    id: number;
    name: string;
    value: number | string;
    unit: string;
    range: string;
    status: 'normal' | 'high' | 'low';
    date: string;
  }>;
}

// Category definitions
const CATEGORIES: Record<
  string,
  { name: string; icon: string; color: string; keywords: string[] }
> = {
  hematology: {
    name: 'Hematology',
    icon: 'water',
    color: colors.rose[500],
    keywords: ['hemoglobin', 'hematocrit', 'rbc', 'wbc', 'platelets', 'mcv', 'mch', 'mchc', 'rdw', 'leucocite', 'eritrocite', 'trombocite', 'vsh', 'esr', 'neutrofil', 'limfocit', 'monocit', 'eozinofil', 'bazofil', 'htc', 'hgb'],
  },
  lipids: {
    name: 'Lipids',
    icon: 'heart',
    color: colors.amber[500],
    keywords: ['cholesterol', 'colesterol', 'ldl', 'hdl', 'triglycerides', 'trigliceride', 'lipoprotein', 'apolipoprotein', 'lipid'],
  },
  liver: {
    name: 'Liver',
    icon: 'flask',
    color: colors.teal[500],
    keywords: ['alt', 'ast', 'alp', 'ggt', 'bilirubin', 'bilirubina', 'albumin', 'albumina', 'tgp', 'tgo', 'gama', 'hepat', 'ficat'],
  },
  kidney: {
    name: 'Kidney',
    icon: 'stethoscope',
    color: colors.primary[500],
    keywords: ['creatinin', 'creatinine', 'bun', 'urea', 'egfr', 'cystatin', 'uric', 'acid uric', 'rinichi', 'renal'],
  },
  metabolic: {
    name: 'Metabolic',
    icon: 'chart-line',
    color: '#8b5cf6',
    keywords: ['glucose', 'glucoza', 'glicemie', 'hba1c', 'hemoglobina glicata', 'insulin', 'insulina', 'glyc'],
  },
  thyroid: {
    name: 'Thyroid',
    icon: 'dna',
    color: '#06b6d4',
    keywords: ['tsh', 't3', 't4', 'ft3', 'ft4', 'tiroid', 'thyroid'],
  },
  vitamins: {
    name: 'Vitamins & Minerals',
    icon: 'pill',
    color: '#f97316',
    keywords: ['vitamin', 'vitamina', 'fier', 'iron', 'ferritin', 'feritina', 'zinc', 'magneziu', 'magnesium', 'calciu', 'calcium', 'potasiu', 'potassium', 'sodiu', 'sodium', 'fosfor', 'b12', 'd3', 'folat', 'folic'],
  },
  other: {
    name: 'Other',
    icon: 'dots-horizontal',
    color: colors.slate[500],
    keywords: [],
  },
};

// Helper to categorize biomarker
const categorize = (name: string): string => {
  const lowerName = name.toLowerCase();
  for (const [key, cat] of Object.entries(CATEGORIES)) {
    if (key === 'other') continue;
    if (cat.keywords.some((kw) => lowerName.includes(kw))) {
      return key;
    }
  }
  return 'other';
};

// Category Section Component
const CategorySection = ({
  categoryKey,
  biomarkers,
  expanded,
  onToggle,
  onBiomarkerPress,
}: {
  categoryKey: string;
  biomarkers: BiomarkerGroup[];
  expanded: boolean;
  onToggle: () => void;
  onBiomarkerPress: (name: string) => void;
}) => {
  const category = CATEGORIES[categoryKey];
  const issueCount = biomarkers.filter((b) => b.has_issues).length;

  return (
    <Surface style={styles.categoryCard} elevation={1}>
      <TouchableOpacity onPress={onToggle} activeOpacity={0.7}>
        <View style={styles.categoryHeader}>
          <View style={styles.categoryLeft}>
            <View style={[styles.categoryIcon, { backgroundColor: category.color + '20' }]}>
              <Icon name={category.icon} size={20} color={category.color} />
            </View>
            <View>
              <Text style={styles.categoryName}>{category.name}</Text>
              <Text style={styles.categoryCount}>{biomarkers.length} tests</Text>
            </View>
          </View>
          <View style={styles.categoryRight}>
            {issueCount > 0 && (
              <View style={styles.issueBadge}>
                <Text style={styles.issueBadgeText}>{issueCount}</Text>
              </View>
            )}
            <Icon
              name={expanded ? 'chevron-down' : 'chevron-right'}
              size={24}
              color={colors.slate[400]}
            />
          </View>
        </View>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.biomarkersList}>
          {biomarkers.map((group) => (
            <BiomarkerRow
              key={group.canonical_name}
              group={group}
              onPress={() => onBiomarkerPress(group.canonical_name)}
            />
          ))}
        </View>
      )}
    </Surface>
  );
};

// Biomarker Row Component
const BiomarkerRow = ({
  group,
  onPress,
}: {
  group: BiomarkerGroup;
  onPress: () => void;
}) => {
  const latest = group.latest;
  const statusColor =
    latest.status === 'normal'
      ? colors.teal[500]
      : latest.status === 'high'
      ? colors.rose[500]
      : colors.amber[500];

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <View style={styles.biomarkerRow}>
        <View style={styles.biomarkerMain}>
          <View style={styles.biomarkerNameRow}>
            <Text style={styles.biomarkerName}>{group.canonical_name}</Text>
            {group.history.length > 1 && (
              <View style={styles.historyBadge}>
                <Text style={styles.historyBadgeText}>{group.history.length}x</Text>
              </View>
            )}
          </View>
          <Text style={styles.biomarkerMeta}>
            {latest.range} | {new Date(latest.date).toLocaleDateString()}
          </Text>
        </View>
        <View style={styles.biomarkerValueContainer}>
          <Text style={styles.biomarkerValue}>
            {latest.value}
            <Text style={styles.biomarkerUnit}> {latest.unit}</Text>
          </Text>
          <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
        </View>
      </View>
    </TouchableOpacity>
  );
};

const BiomarkersScreen = () => {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [biomarkerGroups, setBiomarkerGroups] = useState<BiomarkerGroup[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<string>('all');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const fetchBiomarkers = useCallback(async () => {
    try {
      const response = await api.get('/dashboard/biomarkers-grouped');
      setBiomarkerGroups(response.data);
    } catch (error) {
      console.error('Failed to fetch biomarkers:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchBiomarkers();
  }, [fetchBiomarkers]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchBiomarkers();
  }, [fetchBiomarkers]);

  // Filter and group biomarkers
  const groupedByCategory = useMemo(() => {
    // Apply filters
    const filtered = biomarkerGroups.filter((group) => {
      const matchesSearch = group.canonical_name
        .toLowerCase()
        .includes(searchQuery.toLowerCase());
      const matchesFilter = filter === 'all' || (filter === 'issues' && group.has_issues);
      return matchesSearch && matchesFilter;
    });

    // Group by category
    const categories: Record<string, BiomarkerGroup[]> = {};
    for (const group of filtered) {
      const cat = categorize(group.canonical_name);
      if (!categories[cat]) categories[cat] = [];
      categories[cat].push(group);
    }

    // Sort each category (issues first)
    for (const cat in categories) {
      categories[cat].sort((a, b) => {
        const aIssue = a.has_issues ? 0 : 1;
        const bIssue = b.has_issues ? 0 : 1;
        return aIssue - bIssue;
      });
    }

    return categories;
  }, [biomarkerGroups, searchQuery, filter]);

  const toggleCategory = (key: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const totalFiltered = Object.values(groupedByCategory).flat().length;
  const totalIssues = Object.values(groupedByCategory)
    .flat()
    .filter((g) => g.has_issues).length;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary[600]} />
      </View>
    );
  }

  const categoryOrder = Object.keys(CATEGORIES);
  const categories = categoryOrder.filter((key) => groupedByCategory[key]?.length > 0);

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Searchbar
          placeholder="Search biomarkers..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchBar}
          inputStyle={styles.searchInput}
        />
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterContainer}>
        <SegmentedButtons
          value={filter}
          onValueChange={setFilter}
          buttons={[
            { value: 'all', label: 'All' },
            {
              value: 'issues',
              label: `Issues${totalIssues > 0 ? ` (${totalIssues})` : ''}`,
              icon: totalIssues > 0 ? 'alert' : undefined,
            },
          ]}
          style={styles.segmentedButtons}
        />
      </View>

      {/* Summary */}
      <View style={styles.summaryContainer}>
        <Text style={styles.summaryText}>
          <Text style={styles.summaryBold}>{totalFiltered}</Text> biomarkers
          {totalIssues > 0 && (
            <Text style={styles.summaryIssues}>
              {' '}| <Text style={styles.summaryBold}>{totalIssues}</Text> out of range
            </Text>
          )}
        </Text>
      </View>

      {/* Categories List */}
      <FlatList
        data={categories}
        keyExtractor={(item) => item}
        renderItem={({ item: categoryKey }) => (
          <CategorySection
            categoryKey={categoryKey}
            biomarkers={groupedByCategory[categoryKey]}
            expanded={expandedCategories.has(categoryKey)}
            onToggle={() => toggleCategory(categoryKey)}
            onBiomarkerPress={(name) =>
              navigation.navigate('BiomarkerDetail', { name })
            }
          />
        )}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[colors.primary[600]]}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Icon name="flask-empty-outline" size={48} color={colors.slate[300]} />
            <Text style={styles.emptyTitle}>No biomarkers found</Text>
            <Text style={styles.emptySubtext}>
              {searchQuery
                ? 'Try adjusting your search'
                : 'Upload documents to see your health data'}
            </Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.slate[50],
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.slate[50],
  },
  searchContainer: {
    padding: 16,
    paddingBottom: 8,
  },
  searchBar: {
    backgroundColor: '#ffffff',
    elevation: 1,
    borderRadius: 12,
  },
  searchInput: {
    fontSize: 14,
  },
  filterContainer: {
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  segmentedButtons: {
    backgroundColor: '#ffffff',
  },
  summaryContainer: {
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  summaryText: {
    fontSize: 14,
    color: colors.slate[600],
  },
  summaryBold: {
    fontWeight: '600',
    color: colors.slate[800],
  },
  summaryIssues: {
    color: colors.rose[600],
  },
  listContent: {
    padding: 16,
    paddingTop: 8,
  },
  // Category Card
  categoryCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    marginBottom: 12,
    overflow: 'hidden',
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  categoryLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.slate[800],
  },
  categoryCount: {
    fontSize: 12,
    color: colors.slate[500],
    marginTop: 2,
  },
  categoryRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  issueBadge: {
    backgroundColor: colors.rose[100],
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  issueBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.rose[600],
  },
  // Biomarkers List
  biomarkersList: {
    borderTopWidth: 1,
    borderTopColor: colors.slate[100],
  },
  biomarkerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.slate[50],
  },
  biomarkerMain: {
    flex: 1,
  },
  biomarkerNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  biomarkerName: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.slate[800],
  },
  historyBadge: {
    backgroundColor: colors.slate[100],
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    marginLeft: 8,
  },
  historyBadgeText: {
    fontSize: 10,
    color: colors.slate[500],
  },
  biomarkerMeta: {
    fontSize: 12,
    color: colors.slate[400],
    marginTop: 2,
  },
  biomarkerValueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  biomarkerValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.slate[800],
  },
  biomarkerUnit: {
    fontSize: 12,
    fontWeight: '400',
    color: colors.slate[400],
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginLeft: 8,
  },
  // Empty State
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '500',
    color: colors.slate[500],
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.slate[400],
    marginTop: 4,
  },
});

export default BiomarkersScreen;
