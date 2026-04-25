// Shared TypeScript types for the Cards4Sale mobile app

/** A single eBay comparable listing returned by the backend */
export interface ComparableListing {
  title: string;
  price: number;
  url?: string;
  condition?: string;
  sold_date?: string;
}

/** Image analysis result for one item/card */
export interface ItemAnalysis {
  brand?: string;
  model?: string;
  category?: string;
  condition?: string;
  features?: string[];
  grading_notes?: string | string[];
  estimated_value_range?: string;
  // Trading-card specific fields
  player_name?: string;
  set_name?: string;
  year?: string;
  card_number?: string;
  grade?: string;
}

/** eBay listing payload (what gets submitted to eBay) */
export interface ListingPayload {
  title?: string;
  description?: string;
  price?: number;
  condition?: string;
  [key: string]: unknown;
}

/** A single-card processing result from /api/upload */
export interface SingleCardResult {
  success: boolean;
  listing_id: number;
  analysis: ItemAnalysis;
  comparable_listings: ComparableListing[];
  suggested_price: number;
  payload: ListingPayload;
  is_high_value: boolean;
  high_value_threshold: number;
  message: string;
}

/** One entry in a multi-card result */
export interface CardResult {
  listing_id: number;
  analysis: ItemAnalysis;
  comparable_listings: ComparableListing[];
  suggested_price: number;
  payload: ListingPayload;
  is_high_value: boolean;
}

/** Multi-card processing result from /api/upload */
export interface MultiCardResult {
  success: boolean;
  mode: 'multi_card';
  cards_detected: number;
  card_results: CardResult[];
  high_value_threshold: number;
  message: string;
}

/** Union of both upload response shapes */
export type UploadResult = SingleCardResult | MultiCardResult;

/** Listing summary row returned by GET /api/listings */
export interface ListingSummary {
  id: number;
  title: string;
  filename?: string;
  category?: string;
  condition?: string;
  brand?: string;
  model?: string;
  suggested_price: number;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
}

/** Full listing detail returned by GET /api/listings/:id */
export interface ListingDetail extends ListingSummary {
  features: string[];
  comparable_listings: ComparableListing[];
  payload: ListingPayload;
  external_listing_id?: string;
  published_at?: string;
  publish_error?: string;
}

/** Backend health-check response */
export interface HealthResponse {
  status: 'ok' | 'error';
  version: string;
}
