// API Client for FloatChat Frontend

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Health
  health: () => request<{ status: string; version: string; demo_mode: boolean; database: string; timestamp: string }>('/health'),

  // Chat
  chat: (message: string, sessionId?: string, mode: 'fisherfolk' | 'researcher' = 'researcher') =>
    request<{
      query_run_id: string;
      answer: string;
      language: string;
      structured_query: any;
      visualizations?: any;
      evidence: any;
      audio_url?: string;
      status: string;
      clarification_question?: string;
    }>('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId, mode }),
    }),

  // Query Planning
  planQuery: (message: string, language?: string) =>
    request<any>('/api/v1/query/plan', {
      method: 'POST',
      body: JSON.stringify({ message, language }),
    }),

  executeQuery: (query: any, sessionId?: string) =>
    request<any>('/api/v1/query/execute', {
      method: 'POST',
      body: JSON.stringify({ query, session_id: sessionId }),
    }),

  // Voice
  transcribe: (audioBlob: Blob, languageHint?: string) => {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    if (languageHint) formData.append('language_hint', languageHint);
    
    return fetch(`${API_BASE}/api/v1/voice/transcribe`, {
      method: 'POST',
      body: formData,
    }).then(r => r.json());
  },

  synthesize: (text: string, language: string, voice?: string) =>
    request<{ audio_url: string; duration_seconds: number; format: string }>('/api/v1/voice/synthesize', {
      method: 'POST',
      body: JSON.stringify({ text, language, voice }),
    }),

  // Profiles
  searchProfiles: (params: any) =>
    request<any>('/api/v1/profiles/search', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Anomalies
  detectAnomaly: (params: any) =>
    request<any>('/api/v1/anomalies/detect', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Scenarios
  projectScenario: (params: any) =>
    request<any>('/api/v1/scenarios/project', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Risk
  riskBriefing: (params: any) =>
    request<any>('/api/v1/risk/briefing', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Exports
  exportCSV: (queryRunId: string, format: 'profiles' | 'observations' | 'summary' = 'profiles') =>
    fetch(`${API_BASE}/api/v1/exports/csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query_run_id: queryRunId, format }),
    }).then(r => r.blob()),

  // Dataset Status
  datasetStatus: () =>
    request<{ datasets: any[]; demo_mode: boolean }>('/api/v1/datasets/status'),

  // Query Run Details
  getQueryRun: (queryRunId: string) =>
    request<any>(`/api/v1/query-runs/${queryRunId}`),
};

// Helper to download blob as file
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Audio playback helper
export function playAudio(url: string): HTMLAudioElement {
  const audio = new Audio(url);
  audio.play().catch(console.error);
  return audio;
}