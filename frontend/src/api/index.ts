import { apiClient } from "./client";

export type Severity = "HIGH" | "MEDIUM" | "LOW";
export type JobStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "PARTIALLY_COMPLETED";
export type AlertStatus = "OPEN" | "ACKNOWLEDGED";

export interface ListingIssue {
  id: number;
  type: string;
  severity: Severity;
  message: string;
  suggested_fix: string | null;
  created_at: string;
}

export interface CompetitorPrice {
  id: number;
  platform: string;
  competitor_url: string | null;
  competitor_price: number;
  currency: string;
  last_checked_at: string;
}

export interface EnhancedTitle {
  id: number;
  original_title: string;
  attributes: Record<string, string>;
  keywords: string[];
  enhanced_title: string;
  reason: string;
  created_at: string;
}

export interface Product {
  id: number;
  sku_id: string;
  product_title: string | null;
  description: string | null;
  brand: string | null;
  category: string | null;
  price: number | null;
  mrp: number | null;
  image_url: string | null;
  product_url: string | null;
  availability: boolean;
  color: string | null;
  size: string | null;
  material: string | null;
  source: string;
  quality_score: number;
  created_at: string;
  updated_at: string;
  issues: ListingIssue[];
  competitor_prices: CompetitorPrice[];
  enhanced_titles: EnhancedTitle[];
}

export interface Job {
  id: number;
  type: string;
  status: JobStatus;
  progress: number;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  result_summary: Record<string, unknown> | null;
}

export interface QualitySummary {
  total_products: number;
  avg_quality_score: number;
  issue_counts: { HIGH: number; MEDIUM: number; LOW: number };
  weak_listings: number;
  missing_image_count: number;
  invalid_price_count: number;
  out_of_stock_count: number;
}

export interface Alert {
  id: number;
  product_id: number | null;
  type: string;
  severity: Severity;
  message: string;
  status: AlertStatus;
  created_at: string;
}

export const api = {
  health: () => apiClient.get("/health").then((r) => r.data),

  // Products
  listProducts: (params?: { severity?: string; category?: string }) =>
    apiClient.get<Product[]>("/products", { params }).then((r) => r.data),
  getProduct: (sku: string) => apiClient.get<Product>(`/products/${sku}`).then((r) => r.data),
  updateProduct: (sku: string, data: Partial<Product>) =>
    apiClient.patch<Product>(`/products/${sku}`, data).then((r) => r.data),
  enhanceTitle: (sku: string) =>
    apiClient.post<EnhancedTitle>(`/products/${sku}/enhance-title`).then((r) => r.data),

  // CSV upload
  uploadCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiClient.post<{ job_id: number }>("/upload-products-csv", fd).then((r) => r.data);
  },

  // Jobs
  listJobs: () => apiClient.get<Job[]>("/jobs").then((r) => r.data),
  getJob: (id: number) => apiClient.get<Job>(`/jobs/${id}`).then((r) => r.data),

  // Dashboard
  qualitySummary: () => apiClient.get<QualitySummary>("/dashboard/quality-summary").then((r) => r.data),

  // Alerts
  listAlerts: (params?: { severity?: string; status?: string }) =>
    apiClient.get<Alert[]>("/alerts", { params }).then((r) => r.data),
  acknowledgeAlert: (id: number) =>
    apiClient.patch<Alert>(`/alerts/${id}/acknowledge`).then((r) => r.data),
};
