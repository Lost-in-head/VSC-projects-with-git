import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';

import { RootStackParamList } from '../navigation/AppNavigator';
import { uploadPhoto } from '../api/client';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Main'>;

export default function HomeScreen() {
  const navigation = useNavigation<Nav>();
  const [imageUri, setImageUri] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  // ---------------------------------------------------------------------------
  // Image picking helpers
  // ---------------------------------------------------------------------------

  async function pickFromGallery() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Photo library access is required to pick photos.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.85,
    });
    if (!result.canceled && result.assets.length > 0) {
      setImageUri(result.assets[0].uri);
    }
  }

  async function openCamera() {
    navigation.navigate('Camera');
  }

  // ---------------------------------------------------------------------------
  // Upload & process
  // ---------------------------------------------------------------------------

  async function handleGenerate() {
    if (!imageUri) {
      Alert.alert('No photo', 'Please select or capture a photo first.');
      return;
    }
    setLoading(true);
    try {
      const filename = imageUri.split('/').pop() ?? 'photo.jpg';
      const result = await uploadPhoto(imageUri, filename);
      navigation.navigate('Result', { result });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      Alert.alert('Error', `Failed to process image: ${message}`);
    } finally {
      setLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Cards4Sale</Text>
        <Text style={styles.subtitle}>Snap a photo → get an eBay listing instantly</Text>
      </View>

      {/* Photo preview */}
      <View style={styles.previewContainer}>
        {imageUri ? (
          <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="contain" />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderIcon}>📷</Text>
            <Text style={styles.placeholderText}>No photo selected</Text>
          </View>
        )}
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity style={[styles.button, styles.secondaryButton]} onPress={openCamera}>
          <Text style={styles.secondaryButtonText}>📸  Camera</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.button, styles.secondaryButton]} onPress={pickFromGallery}>
          <Text style={styles.secondaryButtonText}>🖼️  Gallery</Text>
        </TouchableOpacity>
      </View>

      {imageUri && (
        <TouchableOpacity
          style={[styles.button, styles.primaryButton, loading && styles.disabledButton]}
          onPress={handleGenerate}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.primaryButtonText}>✨  Generate Listing</Text>
          )}
        </TouchableOpacity>
      )}

      <Text style={styles.hint}>
        Tip: photograph a single card or multiple cards at once for batch listing generation.
      </Text>
    </ScrollView>
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
    alignItems: 'center',
  },
  header: {
    marginTop: 20,
    marginBottom: 24,
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: '#4F46E5',
    letterSpacing: -1,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
  previewContainer: {
    width: '100%',
    height: 260,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#E5E7EB',
    marginBottom: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  preview: {
    width: '100%',
    height: '100%',
  },
  placeholder: {
    alignItems: 'center',
  },
  placeholderIcon: {
    fontSize: 48,
  },
  placeholderText: {
    color: '#9CA3AF',
    marginTop: 8,
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
    width: '100%',
  },
  button: {
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButton: {
    backgroundColor: '#4F46E5',
    width: '100%',
    marginBottom: 16,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderWidth: 1.5,
    borderColor: '#4F46E5',
  },
  secondaryButtonText: {
    color: '#4F46E5',
    fontSize: 15,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.6,
  },
  hint: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 16,
  },
});
