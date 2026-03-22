import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { RootStackParamList } from '../navigation/AppNavigator';
import { fetchListing, publishListing, deleteListing, updateListingStatus } from '../api/client';
import { ListingDetail } from '../types';

type Props = NativeStackScreenProps<RootStackParamList, 'ListingDetail'>;

export default function ListingDetailScreen({ route, navigation }: Props) {
  const { listingId } = route.params;
  const [listing, setListing] = React.useState<ListingDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [publishing, setPublishing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchListing(listingId);
      setListing(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [listingId]);

  React.useEffect(() => {
    load();
  }, [load]);

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  async function handlePublish() {
    if (!listing) return;
    Alert.alert(
      'Publish Listing',
      'This will submit the listing to eBay. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Publish',
          style: 'default',
          onPress: async () => {
            setPublishing(true);
            try {
              const result = await publishListing(listingId);
              Alert.alert('Published!', `Listed on eBay (ID: ${result.external_listing_id ?? 'n/a'})`);
              await load();
            } catch (err: unknown) {
              Alert.alert('Publish Failed', err instanceof Error ? err.message : String(err));
            } finally {
              setPublishing(false);
            }
          },
        },
      ],
    );
  }

  async function handleArchive() {
    Alert.alert('Archive Listing', 'Mark this listing as archived?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Archive',
        style: 'destructive',
        onPress: async () => {
          try {
            await updateListingStatus(listingId, 'archived');
            await load();
          } catch (err: unknown) {
            Alert.alert('Error', err instanceof Error ? err.message : String(err));
          }
        },
      },
    ]);
  }

  async function handleDelete() {
    Alert.alert('Delete Listing', 'This cannot be undone. Delete?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteListing(listingId);
            navigation.goBack();
          } catch (err: unknown) {
            Alert.alert('Error', err instanceof Error ? err.message : String(err));
          }
        },
      },
    ]);
  }

  // ---------------------------------------------------------------------------
  // Render states
  // ---------------------------------------------------------------------------

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  if (error || !listing) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>⚠️  {error ?? 'Listing not found'}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={load}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const isDraft = listing.status === 'draft';
  const isPublished = listing.status === 'published';

  // ---------------------------------------------------------------------------
  // Main render
  // ---------------------------------------------------------------------------

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Status banner */}
      <View style={[styles.statusBanner, { backgroundColor: STATUS_BG[listing.status] ?? '#F3F4F6' }]}>
        <Text style={[styles.statusText, { color: STATUS_FG[listing.status] ?? '#374151' }]}>
          {listing.status.toUpperCase()}
        </Text>
        {listing.external_listing_id && (
          <Text style={styles.externalId}>eBay ID: {listing.external_listing_id}</Text>
        )}
      </View>

      {/* Core details */}
      <Section title="Item Details">
        <Field label="Title" value={listing.title} />
        <Field label="Brand" value={listing.brand} />
        <Field label="Model" value={listing.model} />
        <Field label="Category" value={listing.category} />
        <Field label="Condition" value={listing.condition} />
      </Section>

      <Section title="Pricing">
        <Field label="Suggested Price" value={`$${Number(listing.suggested_price).toFixed(2)}`} />
      </Section>

      {listing.features.length > 0 && (
        <Section title="Features">
          {listing.features.map((f, i) => (
            <Text key={i} style={styles.bullet}>
              • {f}
            </Text>
          ))}
        </Section>
      )}

      {listing.comparable_listings.length > 0 && (
        <Section title={`Comparable Listings (${listing.comparable_listings.length})`}>
          {listing.comparable_listings.slice(0, 6).map((item, i) => (
            <View key={i} style={styles.comparableRow}>
              <Text style={styles.comparableTitle} numberOfLines={2}>
                {item.title}
              </Text>
              <Text style={styles.comparablePrice}>${Number(item.price).toFixed(2)}</Text>
            </View>
          ))}
        </Section>
      )}

      {listing.publish_error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorBannerText}>⚠️  Last publish error: {listing.publish_error}</Text>
        </View>
      )}

      {/* Action buttons */}
      <View style={styles.actions}>
        {isDraft && (
          <TouchableOpacity
            style={[styles.actionButton, styles.publishButton, publishing && styles.disabled]}
            onPress={handlePublish}
            disabled={publishing}
          >
            {publishing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.publishButtonText}>🚀  Publish to eBay</Text>
            )}
          </TouchableOpacity>
        )}

        {isPublished && (
          <View style={styles.publishedNote}>
            <Text style={styles.publishedNoteText}>✅  Published to eBay</Text>
          </View>
        )}

        {!isPublished && (
          <TouchableOpacity style={[styles.actionButton, styles.archiveButton]} onPress={handleArchive}>
            <Text style={styles.archiveButtonText}>📦  Archive</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity style={[styles.actionButton, styles.deleteButton]} onPress={handleDelete}>
          <Text style={styles.deleteButtonText}>🗑️  Delete</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_BG: Record<string, string> = {
  draft: '#FEF3C7',
  published: '#D1FAE5',
  archived: '#F3F4F6',
};
const STATUS_FG: Record<string, string> = {
  draft: '#92400E',
  published: '#065F46',
  archived: '#6B7280',
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Field({ label, value }: { label: string; value?: string | number | null }) {
  if (value === undefined || value === null || value === '') return null;
  return (
    <View style={styles.fieldRow}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <Text style={styles.fieldValue}>{String(value)}</Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, backgroundColor: '#F9FAFB' },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#F9FAFB',
  },
  statusBanner: {
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
    alignItems: 'center',
  },
  statusText: { fontWeight: '800', fontSize: 13, letterSpacing: 1 },
  externalId: { fontSize: 12, color: '#065F46', marginTop: 4 },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  fieldRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F3F4F6',
  },
  fieldLabel: { color: '#6B7280', fontSize: 14 },
  fieldValue: {
    color: '#111827',
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
    textAlign: 'right',
  },
  bullet: { color: '#374151', fontSize: 14, paddingVertical: 4 },
  comparableRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F3F4F6',
    gap: 8,
  },
  comparableTitle: { flex: 1, color: '#374151', fontSize: 13 },
  comparablePrice: { color: '#059669', fontWeight: '700', fontSize: 13 },
  errorBanner: {
    backgroundColor: '#FEE2E2',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  errorBannerText: { color: '#991B1B', fontSize: 13 },
  actions: { gap: 10, marginBottom: 32 },
  actionButton: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  publishButton: { backgroundColor: '#4F46E5' },
  publishButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  archiveButton: { backgroundColor: '#F3F4F6' },
  archiveButtonText: { color: '#374151', fontSize: 15, fontWeight: '600' },
  deleteButton: {
    backgroundColor: '#fff',
    borderWidth: 1.5,
    borderColor: '#EF4444',
  },
  deleteButtonText: { color: '#EF4444', fontSize: 15, fontWeight: '600' },
  publishedNote: {
    backgroundColor: '#D1FAE5',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  publishedNoteText: { color: '#065F46', fontWeight: '700', fontSize: 15 },
  disabled: { opacity: 0.6 },
  errorText: { color: '#DC2626', fontSize: 15, textAlign: 'center', marginBottom: 16 },
  retryButton: {
    backgroundColor: '#4F46E5',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 24,
  },
  retryText: { color: '#fff', fontWeight: '700' },
});
