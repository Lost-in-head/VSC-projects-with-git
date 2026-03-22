/**
 * API client for the Cards4Sale Flask backend.
 *
 * Set BASE_URL to the address where your backend is running:
 *   - Local development on a physical device: http://<your-machine-IP>:5000
 *   - Android emulator:                       http://10.0.2.2:5000
 *   - iOS simulator:                          http://localhost:5000
 *
 * Override at runtime via the Settings screen (stored in AsyncStorage) or
 * via a build-time env var using a .env file with expo-constants.
 */

import {
  HealthResponse,
  ListingDetail,
  ListingSummary,
  UploadResult,
} from '../types';

// Default base URL – can be overridden by callers via setBaseUrl()
let BASE_URL = 'http://localhost:5000';

export function setBaseUrl(url: string): void {
  BASE_URL = url.replace(/\/$/, ''); // strip trailing slash
}

export function getBaseUrl(): string {
  return BASE_URL;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Public API surface
// ---------------------------------------------------------------------------

/** Verify the backend is reachable */
export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/api/health`, { method: 'GET' });
  return handleResponse<HealthResponse>(res);
}

/**
 * Upload a photo and generate a listing.
 *
 * @param imageUri  Local URI of the photo (from expo-image-picker / expo-camera)
 * @param filename  Optional filename override (defaults to 'photo.jpg')
 */
export async function uploadPhoto(
  imageUri: string,
  filename = 'photo.jpg',
): Promise<UploadResult> {
  const formData = new FormData();
  // React Native's FormData accepts a { uri, name, type } object
  formData.append('photo', {
    uri: imageUri,
    name: filename,
    type: 'image/jpeg',
  } as unknown as Blob);

  const res = await fetch(`${BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
    // Do NOT set Content-Type header — React Native sets it with the boundary
  });
  return handleResponse<UploadResult>(res);
}

/** Fetch all saved listings */
export async function fetchListings(): Promise<ListingSummary[]> {
  const res = await fetch(`${BASE_URL}/api/listings`);
  return handleResponse<ListingSummary[]>(res);
}

/** Fetch a single listing by ID */
export async function fetchListing(id: number): Promise<ListingDetail> {
  const res = await fetch(`${BASE_URL}/api/listings/${id}`);
  return handleResponse<ListingDetail>(res);
}

/** Update a listing's status */
export async function updateListingStatus(
  id: number,
  status: 'draft' | 'published' | 'archived',
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/listings/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  await handleResponse<{ success: boolean }>(res);
}

/** Publish a listing to eBay */
export async function publishListing(
  id: number,
): Promise<{ success: boolean; external_listing_id?: string; status?: string }> {
  const res = await fetch(`${BASE_URL}/api/listings/${id}/publish`, {
    method: 'POST',
  });
  return handleResponse(res);
}

/** Delete a listing */
export async function deleteListing(id: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/listings/${id}`, {
    method: 'DELETE',
  });
  await handleResponse<{ success: boolean }>(res);
}
