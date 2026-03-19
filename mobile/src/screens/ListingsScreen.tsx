import React from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { RootStackParamList } from '../navigation/AppNavigator';
import { fetchListings } from '../api/client';
import { ListingSummary } from '../types';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Main'>;

const STATUS_COLORS: Record<string, string> = {
  draft: '#F59E0B',
  published: '#10B981',
  archived: '#9CA3AF',
};

export default function ListingsScreen() {
  const navigation = useNavigation<Nav>();
  const [listings, setListings] = React.useState<ListingSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadListings = React.useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const data = await fetchListings();
      setListings(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Refresh whenever the tab comes into focus
  useFocusEffect(
    React.useCallback(() => {
      loadListings(true);
    }, [loadListings]),
  );

  function onRefresh() {
    setRefreshing(true);
    loadListings(true);
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>⚠️  {error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => loadListings()}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (listings.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyIcon}>📋</Text>
        <Text style={styles.emptyText}>No listings yet.</Text>
        <Text style={styles.emptySubText}>Upload a photo to generate your first listing!</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={listings}
      keyExtractor={(item) => String(item.id)}
      contentContainerStyle={styles.list}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('ListingDetail', { listingId: item.id, title: item.title })}
        >
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle} numberOfLines={2}>
              {item.title}
            </Text>
            <View style={[styles.statusBadge, { backgroundColor: STATUS_COLORS[item.status] ?? '#9CA3AF' }]}>
              <Text style={styles.statusText}>{item.status}</Text>
            </View>
          </View>
          <View style={styles.cardMeta}>
            {item.brand ? <Text style={styles.metaText}>{item.brand}</Text> : null}
            {item.condition ? <Text style={styles.metaText}>{item.condition}</Text> : null}
          </View>
          <Text style={styles.price}>${Number(item.suggested_price).toFixed(2)}</Text>
        </TouchableOpacity>
      )}
    />
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  list: { padding: 16 },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#F9FAFB',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  cardTitle: {
    flex: 1,
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
    lineHeight: 20,
  },
  statusBadge: {
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  statusText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  cardMeta: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 6,
  },
  metaText: {
    fontSize: 12,
    color: '#6B7280',
    backgroundColor: '#F3F4F6',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  price: {
    marginTop: 10,
    fontSize: 18,
    fontWeight: '800',
    color: '#059669',
  },
  errorText: {
    color: '#DC2626',
    marginBottom: 16,
    fontSize: 15,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#4F46E5',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 24,
  },
  retryButtonText: { color: '#fff', fontWeight: '700' },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 18, fontWeight: '700', color: '#374151' },
  emptySubText: { fontSize: 14, color: '#9CA3AF', marginTop: 4, textAlign: 'center' },
});
