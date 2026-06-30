/**
 * Typed client for the Scintia backend API (docs/02_ARCHITECTURE.md §5).
 * The JWT is kept in localStorage; no patient identifier is ever stored here.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "scintia_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export interface StudyRead {
  id: string;
  exam_type: string;
  status: string;
  patient_pseudonym: string;
  created_at: string;
}

export interface OrganMeasurement {
  id: string;
  organ_name: string;
  snomed_code: string | null;
  volume_ml: string | number | null;
  segmentation_corrected: boolean;
}

export interface ExamScore {
  id: string;
  score_type: string;
  value: string;
  details: Record<string, unknown> | null;
}

export interface StudyResults {
  study: StudyRead;
  organs: OrganMeasurement[];
  score: ExamScore | null;
  report_status: string | null;
}

export interface ReportRead {
  study_id: string;
  status: string;
  content: string | null;
  validated_by: string | null;
  validated_at: string | null;
  version_count: number;
}

export interface IngestionSummary {
  study_id: string;
  status: string;
  ct_series: number;
  spect_series: number;
  instances: number;
  skipped: number;
}

export interface PatientInput {
  name?: string;
  birth_date?: string;
  patient_id?: string;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (body.detail) detail = JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function jsonInit(method: string, payload: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
}

export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!response.ok) throw new Error("Identifiants invalides.");
  const data = (await response.json()) as { access_token: string };
  setToken(data.access_token);
  return data.access_token;
}

export async function bootstrapAdmin(
  email: string,
  fullName: string,
  password: string,
): Promise<void> {
  await request(
    "/api/v1/users/bootstrap-admin",
    jsonInit("POST", { email, full_name: fullName, password, role: "admin" }),
  );
}

export async function createStudy(examType: string, patient: PatientInput): Promise<StudyRead> {
  return request<StudyRead>("/api/v1/studies", jsonInit("POST", { exam_type: examType, patient }));
}

export async function listStudies(): Promise<StudyRead[]> {
  return request<StudyRead[]>("/api/v1/studies");
}

/** WebSocket URL streaming pipeline status (token passed as query param). */
export function progressSocketUrl(studyId: string): string {
  const token = getToken() ?? "";
  const wsBase = API_BASE.replace(/^http/, "ws");
  return `${wsBase}/api/v1/studies/${studyId}/progress?token=${encodeURIComponent(token)}`;
}

export async function uploadFiles(studyId: string, files: File[]): Promise<IngestionSummary> {
  const form = new FormData();
  for (const file of files) form.append("files", file);
  return request<IngestionSummary>(`/api/v1/studies/${studyId}/files`, {
    method: "POST",
    body: form,
  });
}

export async function analyze(studyId: string): Promise<StudyRead> {
  return request<StudyRead>(`/api/v1/studies/${studyId}/analyze`, { method: "POST" });
}

export async function getResults(studyId: string): Promise<StudyResults> {
  return request<StudyResults>(`/api/v1/studies/${studyId}/results`);
}

export async function getReport(studyId: string): Promise<ReportRead> {
  return request<ReportRead>(`/api/v1/studies/${studyId}/report`);
}

export async function generateReport(studyId: string): Promise<ReportRead> {
  return request<ReportRead>(`/api/v1/studies/${studyId}/report`, { method: "POST" });
}

export async function editReport(studyId: string, content: string): Promise<ReportRead> {
  return request<ReportRead>(`/api/v1/studies/${studyId}/report`, jsonInit("PATCH", { content }));
}

export async function validateReport(studyId: string): Promise<ReportRead> {
  return request<ReportRead>(`/api/v1/studies/${studyId}/report/validate`, { method: "POST" });
}

export async function exportPdf(studyId: string): Promise<Blob> {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/v1/studies/${studyId}/export?format=pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) {
    throw new Error("Export impossible : le compte-rendu doit être validé.");
  }
  return response.blob();
}
