import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text } from 'react-native';

import HomeScreen from '../screens/HomeScreen';
import CameraScreen from '../screens/CameraScreen';
import ResultScreen from '../screens/ResultScreen';
import ListingsScreen from '../screens/ListingsScreen';
import ListingDetailScreen from '../screens/ListingDetailScreen';
import { UploadResult } from '../types';

// ---------------------------------------------------------------------------
// Route-param type definitions
// ---------------------------------------------------------------------------

export type RootStackParamList = {
  Main: undefined;
  Camera: undefined;
  Result: { result: UploadResult };
  ListingDetail: { listingId: number; title?: string };
};

export type TabParamList = {
  Home: undefined;
  Listings: undefined;
};

// ---------------------------------------------------------------------------
// Navigators
// ---------------------------------------------------------------------------

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: '#4F46E5',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarIcon: ({ color, size }) => {
          const icons: Record<string, string> = {
            Home: '📸',
            Listings: '📋',
          };
          return (
            <Text style={{ fontSize: size - 4 }}>{icons[route.name] ?? '•'}</Text>
          );
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} options={{ title: 'Capture' }} />
      <Tab.Screen name="Listings" component={ListingsScreen} options={{ title: 'My Listings' }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: '#4F46E5' },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: '700' },
        }}
      >
        <Stack.Screen
          name="Main"
          component={TabNavigator}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Camera"
          component={CameraScreen}
          options={{ title: 'Take Photo' }}
        />
        <Stack.Screen
          name="Result"
          component={ResultScreen}
          options={{ title: 'Listing Generated' }}
        />
        <Stack.Screen
          name="ListingDetail"
          component={ListingDetailScreen}
          options={({ route }) => ({ title: route.params.title ?? 'Listing Detail' })}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
