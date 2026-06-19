import type { Document, ExportResponse, Project, QuestionAnswerBundle, RfpQuestion } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(options?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(options?.headers ?? {}),
      },
    });
  } catch {
    throw new Error(
      `Cannot reach the API at ${API_BASE_URL}. Start the backend with: cd backend && uvicorn app.main:app --reload`,
    );
  }

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  sample_data_url: (path: string) => `${API_BASE_URL}/sample_data/${path}`,

  create_project: (payload: { name: string; client_name?: string | null }) =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(payload) }),

  list_projects: () => request<Project[]>('/projects'),

  upload_rfp_document: (project_id: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request(`/projects/${project_id}/documents/rfp`, { method: 'POST', body: form });
  },

  upload_knowledge_document: (project_id: string, file: File, upload_name = file.name) => {
    const form = new FormData();
    form.append('file', file, upload_name);
    return request(`/projects/${project_id}/documents/knowledge`, { method: 'POST', body: form });
  },

  extract_questions: (project_id: string) =>
    request<RfpQuestion[]>(`/projects/${project_id}/extract_questions`, { method: 'POST' }),

  list_questions: (project_id: string) => request<RfpQuestion[]>(`/projects/${project_id}/questions`),

  list_documents: (project_id: string) => request<Document[]>(`/projects/${project_id}/documents`),

  draft_answer: (question_id: string) =>
    request<QuestionAnswerBundle>(`/questions/${question_id}/draft_answer`, { method: 'POST' }),

  update_answer: (answer_id: string, payload: { final_text: string; review_note?: string | null }) =>
    request(`/answers/${answer_id}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  approve_answer: (answer_id: string) =>
    request(`/answers/${answer_id}/approve`, { method: 'POST' }),

  flag_answer: (answer_id: string, review_note?: string) =>
    request(`/answers/${answer_id}/flag`, {
      method: 'POST',
      body: JSON.stringify({ review_note: review_note ?? null }),
    }),

  reject_answer: (answer_id: string) =>
    request(`/answers/${answer_id}/reject`, { method: 'POST' }),

  export_project: (project_id: string) =>
    request<ExportResponse>(`/projects/${project_id}/export`, { method: 'POST' }),
};
