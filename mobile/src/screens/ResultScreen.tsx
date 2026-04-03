import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { RootStackParamList } from '../navigation/AppNavigator';
import { MultiCardResult, SingleCardResult } from '../types';

type Props = NativeStackScreenProps<RootStackParamList, 'Result'>;

export default function ResultScreen({ route, navigation }: Props) {
  const { result } = route.params;

  const isMulti = (result as MultiCardResult).mode === 'multi_card';

  if (isMulti) {
    return <MultiCardView result={result as MultiCardResult} navigation={navigation} />;
  }
  return <SingleCardView result={result as SingleCardResult} navigation={navigation} />;
}

// ---------------------------------------------------------------------------
// Single-card result
// ---------------------------------------------------------------------------

function SingleCardView({
  result,
  navigation,
}: {
  result: SingleCardResult;
  navigation: Props['navigation'];
}) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.successBanner}>
        <Text style={styles.successIcon}>✅</Text>
        <Text style={styles.successText}>Listing saved!</Text>
      </View>

      <Section title="Identified Item">
        <Field label="Brand" value={result.analysis.brand} />
        <Field label="Model" value={result.analysis.model} />
        <Field label="Category" value={result.analysis.category} />
        <Field label="Condition" value={result.analysis.condition} />
      </Section>

      <Section title="Pricing">
        <Field
          label="Suggested Price"
          value={`$${result.suggested_price.toFixed(2)}`}
          highlight={result.is_high_value}
        />
        {result.is_high_value && (
          <Text style={styles.highValueBadge}>
            🔥 High Value (≥ ${result.high_value_threshold})
          </Text>
        )}
      </Section>

      {result.comparable_listings.length > 0 && (
        <Section title={`Comparable Listings (${result.comparable_listings.length})`}>
          {result.comparable_listings.slice(0, 5).map((item, i) => (
            <View key={i} style={styles.comparableRow}>
              <Text style={styles.comparableTitle} numberOfLines={2}>
                {item.title}
              </Text>
              <Text style={styles.comparablePrice}>${Number(item.price).toFixed(2)}</Text>
            </View>
          ))}
        </Section>
      )}

      <TouchableOpacity
        style={styles.detailButton}
        onPress={() =>
          navigation.navigate('ListingDetail', {
            listingId: result.listing_id,
            title: `${result.analysis.brand ?? ''} ${result.analysis.model ?? ''}`.trim(),
          })
        }
      >
        <Text style={styles.detailButtonText}>View Full Listing →</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.newButton}
        onPress={() => navigation.navigate('Main')}
      >
        <Text style={styles.newButtonText}>📸  New Photo</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Multi-card result
// ---------------------------------------------------------------------------

function MultiCardView({
  result,
  navigation,
}: {
  result: MultiCardResult;
  navigation: Props['navigation'];
}) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.successBanner}>
        <Text style={styles.successIcon}>✅</Text>
        <Text style={styles.successText}>
          {result.cards_detected} listings saved!
        </Text>
      </View>

      {result.card_results.map((card, index) => (
        <View key={card.listing_id} style={styles.cardRow}>
          <View style={styles.cardInfo}>
            <Text style={styles.cardTitle} numberOfLines={1}>
              {`${card.analysis.brand ?? ''} ${card.analysis.model ?? ''}`.trim() ||
                `Card ${index + 1}`}
            </Text>
            <Text style={styles.cardPrice}>${card.suggested_price.toFixed(2)}</Text>
          </View>
          <TouchableOpacity
            style={styles.viewButton}
            onPress={() =>
              navigation.navigate('ListingDetail', {
                listingId: card.listing_id,
                title: `${card.analysis.brand ?? ''} ${card.analysis.model ?? ''}`.trim(),
              })
            }
          >
            <Text style={styles.viewButtonText}>View</Text>
          </TouchableOpacity>
        </View>
      ))}

      <TouchableOpacity
        style={[styles.newButton, { marginTop: 24 }]}
        onPress={() => navigation.navigate('Main')}
      >
        <Text style={styles.newButtonText}>📸  New Photo</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Field({
  label,
  value,
  highlight,
}: {
  label: string;
  value?: string | number | null;
  highlight?: boolean;
}) {
  if (value === undefined || value === null || value === '') return null;
  return (
    <View style={styles.fieldRow}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <Text style={[styles.fieldValue, highlight && styles.highlightValue]}>{String(value)}</Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 20,
    backgroundColor: '#F9FAFB',
  },
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    gap: 8,
  },
  successIcon: { fontSize: 22 },
  successText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#065F46',
  },
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
    fontSize: 14,
    fontWeight: '700',
    color: '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  fieldRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F3F4F6',
  },
  fieldLabel: { color: '#6B7280', fontSize: 14 },
  fieldValue: { color: '#111827', fontSize: 14, fontWeight: '600', flex: 1, textAlign: 'right' },
  highlightValue: { color: '#4F46E5' },
  highValueBadge: {
    color: '#92400E',
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    padding: 8,
    fontSize: 13,
    fontWeight: '600',
    marginTop: 8,
    textAlign: 'center',
  },
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
  detailButton: {
    backgroundColor: '#4F46E5',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  detailButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  newButton: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#4F46E5',
    marginBottom: 24,
  },
  newButtonText: { color: '#4F46E5', fontSize: 15, fontWeight: '600' },
  // Multi-card
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  cardInfo: { flex: 1 },
  cardTitle: { fontSize: 14, fontWeight: '600', color: '#111827' },
  cardPrice: { fontSize: 14, color: '#059669', fontWeight: '700', marginTop: 2 },
  viewButton: {
    backgroundColor: '#EEF2FF',
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 14,
  },
  viewButtonText: { color: '#4F46E5', fontWeight: '700', fontSize: 13 },
});
