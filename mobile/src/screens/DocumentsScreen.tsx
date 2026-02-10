import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  Alert,
  Linking,
} from 'react-native';
import {
  Text,
  Surface,
  ActivityIndicator,
  FAB,
  Dialog,
  Portal,
  Button,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import * as DocumentPicker from 'react-native-document-picker';

import api from '../api/client';
import { colors } from '../utils/theme';

// Types
interface Document {
  id: number;
  filename: string;
  document_date: string | null;
  provider: string | null;
  is_processed: boolean;
  patient_name: string | null;
  created_at: string;
}

interface DocumentStats {
  total_documents: number;
  total_biomarkers: number;
  by_provider: Record<string, number>;
}

const DocumentsScreen = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [deleteDoc, setDeleteDoc] = useState<Document | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchDocuments = useCallback(async () => {
    try {
      const [docsRes, statsRes] = await Promise.all([
        api.get('/documents/'),
        api.get('/documents/stats'),
      ]);
      setDocuments(docsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchDocuments();
  }, [fetchDocuments]);

  const handleUpload = async () => {
    try {
      // Note: react-native-document-picker needs to be installed
      // For now, show a message that upload should be done via web
      Alert.alert(
        'Upload Document',
        'Document upload is currently available through the web app at analize.online. Please use a browser to upload new documents.',
        [
          { text: 'Open Website', onPress: () => Linking.openURL('https://analize.online') },
          { text: 'Cancel', style: 'cancel' },
        ]
      );
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleDelete = async () => {
    if (!deleteDoc) return;

    setDeleting(true);
    try {
      await api.delete(`/documents/${deleteDoc.id}?regenerate_reports=true`);
      Alert.alert('Success', 'Document deleted successfully');
      setDeleteDoc(null);
      fetchDocuments();
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to delete document'
      );
    } finally {
      setDeleting(false);
    }
  };

  const handleViewPdf = async (doc: Document) => {
    // Open PDF in browser or default PDF viewer
    // Note: Full PDF viewing requires native implementation
    Alert.alert(
      'View Document',
      `View "${doc.filename}" in browser?`,
      [
        {
          text: 'Open',
          onPress: () => Linking.openURL(`https://analize.online/documents`),
        },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const renderDocument = ({ item: doc }: { item: Document }) => (
    <Surface style={styles.documentCard} elevation={1}>
      <TouchableOpacity
        onPress={() => handleViewPdf(doc)}
        activeOpacity={0.7}
      >
        <View style={styles.documentContent}>
          <View style={styles.documentIcon}>
            <Icon name="file-pdf-box" size={32} color={colors.primary[600]} />
          </View>
          <View style={styles.documentInfo}>
            <Text style={styles.documentName} numberOfLines={1}>
              {doc.filename}
            </Text>
            <View style={styles.documentMeta}>
              <View style={styles.metaItem}>
                <Icon name="calendar" size={12} color={colors.slate[400]} />
                <Text style={styles.metaText}>
                  {doc.document_date
                    ? new Date(doc.document_date).toLocaleDateString()
                    : 'Unknown date'}
                </Text>
              </View>
              {doc.provider && (
                <View style={styles.metaItem}>
                  <Icon name="domain" size={12} color={colors.slate[400]} />
                  <Text style={styles.metaText}>{doc.provider}</Text>
                </View>
              )}
            </View>
            {doc.patient_name && (
              <View style={styles.patientBadge}>
                <Icon name="account" size={10} color={colors.primary[600]} />
                <Text style={styles.patientName}>{doc.patient_name}</Text>
              </View>
            )}
          </View>
          <View style={styles.documentActions}>
            {doc.is_processed ? (
              <View style={styles.statusBadge}>
                <Icon name="check-circle" size={12} color={colors.teal[600]} />
                <Text style={styles.statusText}>Processed</Text>
              </View>
            ) : (
              <View style={[styles.statusBadge, styles.pendingBadge]}>
                <Icon name="clock-outline" size={12} color={colors.amber[600]} />
                <Text style={[styles.statusText, styles.pendingText]}>Pending</Text>
              </View>
            )}
            <TouchableOpacity
              onPress={() => setDeleteDoc(doc)}
              style={styles.deleteButton}
            >
              <Icon name="delete-outline" size={20} color={colors.slate[400]} />
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    </Surface>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary[600]} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Stats Summary */}
      {stats && (
        <Surface style={styles.statsCard} elevation={1}>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <View style={[styles.statIcon, { backgroundColor: colors.primary[50] }]}>
                <Icon name="file-document" size={20} color={colors.primary[600]} />
              </View>
              <View>
                <Text style={styles.statValue}>{stats.total_documents}</Text>
                <Text style={styles.statLabel}>Documents</Text>
              </View>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <View style={[styles.statIcon, { backgroundColor: colors.teal[50] }]}>
                <Icon name="heart-pulse" size={20} color={colors.teal[600]} />
              </View>
              <View>
                <Text style={styles.statValue}>{stats.total_biomarkers}</Text>
                <Text style={styles.statLabel}>Biomarkers</Text>
              </View>
            </View>
          </View>
          {Object.keys(stats.by_provider).length > 0 && (
            <View style={styles.providerRow}>
              {Object.entries(stats.by_provider).map(([provider, count]) => (
                <View key={provider} style={styles.providerBadge}>
                  <Icon name="domain" size={12} color={colors.slate[500]} />
                  <Text style={styles.providerText}>
                    {provider}: {count}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </Surface>
      )}

      {/* Documents List */}
      <FlatList
        data={documents}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderDocument}
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
            <Icon name="file-document-outline" size={48} color={colors.slate[300]} />
            <Text style={styles.emptyTitle}>No documents yet</Text>
            <Text style={styles.emptySubtext}>
              Upload your lab results to start tracking your health
            </Text>
          </View>
        }
      />

      {/* Upload FAB */}
      <FAB
        icon="plus"
        style={styles.fab}
        onPress={handleUpload}
        loading={uploading}
        disabled={uploading}
        color="#ffffff"
      />

      {/* Delete Confirmation Dialog */}
      <Portal>
        <Dialog visible={!!deleteDoc} onDismiss={() => setDeleteDoc(null)}>
          <Dialog.Icon icon="delete" color={colors.rose[500]} />
          <Dialog.Title style={styles.dialogTitle}>Delete Document</Dialog.Title>
          <Dialog.Content>
            <Text style={styles.dialogText}>
              Are you sure you want to delete "{deleteDoc?.filename}"?
            </Text>
            <Text style={styles.dialogWarning}>
              This will also delete all extracted biomarkers from this document.
            </Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDeleteDoc(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button
              onPress={handleDelete}
              loading={deleting}
              disabled={deleting}
              textColor={colors.rose[600]}
            >
              Delete
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
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
  // Stats Card
  statsCard: {
    backgroundColor: '#ffffff',
    margin: 16,
    marginBottom: 8,
    borderRadius: 16,
    padding: 16,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  statIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.slate[800],
  },
  statLabel: {
    fontSize: 12,
    color: colors.slate[500],
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.slate[200],
    marginHorizontal: 16,
  },
  providerRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.slate[100],
  },
  providerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.slate[50],
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
    marginBottom: 4,
    borderWidth: 1,
    borderColor: colors.slate[200],
  },
  providerText: {
    fontSize: 12,
    color: colors.slate[600],
    marginLeft: 4,
  },
  // Documents List
  listContent: {
    padding: 16,
    paddingTop: 8,
    paddingBottom: 80,
  },
  documentCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    marginBottom: 12,
    overflow: 'hidden',
  },
  documentContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  documentIcon: {
    width: 48,
    height: 48,
    backgroundColor: colors.primary[50],
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  documentInfo: {
    flex: 1,
  },
  documentName: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.slate[800],
    marginBottom: 4,
  },
  documentMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
    marginBottom: 2,
  },
  metaText: {
    fontSize: 12,
    color: colors.slate[500],
    marginLeft: 4,
  },
  patientBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary[50],
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  patientName: {
    fontSize: 10,
    color: colors.primary[600],
    marginLeft: 4,
  },
  documentActions: {
    alignItems: 'flex-end',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.teal[50],
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    marginBottom: 8,
  },
  pendingBadge: {
    backgroundColor: colors.amber[50],
  },
  statusText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.teal[600],
    marginLeft: 4,
  },
  pendingText: {
    color: colors.amber[600],
  },
  deleteButton: {
    padding: 4,
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
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  // FAB
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    backgroundColor: colors.primary[600],
  },
  // Dialog
  dialogTitle: {
    textAlign: 'center',
  },
  dialogText: {
    fontSize: 14,
    color: colors.slate[600],
    marginBottom: 8,
  },
  dialogWarning: {
    fontSize: 12,
    color: colors.amber[600],
    backgroundColor: colors.amber[50],
    padding: 12,
    borderRadius: 8,
  },
});

export default DocumentsScreen;
