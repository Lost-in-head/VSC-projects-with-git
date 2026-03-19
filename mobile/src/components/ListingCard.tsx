import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

import { ListingSummary } from '../types';

interface Props {
  listing: ListingSummary;
  onPress: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  draft: '#F59E0B',
  published: '#10B981',
  archived: '#9CA3AF',
};

export default function ListingCard({ listing, onPress }: Props) {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={2}>
          {listing.title}
        </Text>
        <View style={[styles.badge, { backgroundColor: STATUS_COLORS[listing.status] ?? '#9CA3AF' }]}>
          <Text style={styles.badgeText}>{listing.status}</Text>
        </View>
      </View>

      <View style={styles.meta}>
        {listing.brand ? <Text style={styles.metaChip}>{listing.brand}</Text> : null}
        {listing.condition ? <Text style={styles.metaChip}>{listing.condition}</Text> : null}
      </View>

      <Text style={styles.price}>${Number(listing.suggested_price).toFixed(2)}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  title: {
    flex: 1,
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
    lineHeight: 20,
  },
  badge: {
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  meta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 8,
  },
  metaChip: {
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
});
