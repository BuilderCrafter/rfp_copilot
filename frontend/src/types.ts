export type ProjectStatus = 'active' | 'completed' | 'archived';
export type DocumentType = 'rfp' | 'knowledge';
export type DocumentStatus = 'uploaded' | 'processing' | 'processed' | 'failed';
export type QuestionStatus = 'pending' | 'drafted' | 'approved' | 'flagged';
export type AnswerStatus = 'not_started' | 'drafted' | 'edited' | 'approved' | 'flagged' | 'rejected';
export type BidRecommendation = 'bid' | 'no_bid' | 'needs_review';
export type BidFactorSentiment = 'positive' | 'negative' | 'neutral';
export type RequirementCheckStatus = 'present' | 'partial' | 'missing' | 'not_applicable';
export type RequirementSeverity = 'critical' | 'high' | 'medium' | 'low';
export type SubmissionRequirementStatus = 'required' | 'conditional' | 'optional' | 'needs_review';
export type QuestionCategory =
  | 'general'
  | 'technical'
  | 'security'
  | 'legal'
  | 'pricing'
  | 'implementation'
  | 'support'
  | 'compliance'
  | 'experience';

export interface Project {
  id: string;
  name: string;
  client_name: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface RfpQuestion {
  id: string;
  project_id: string;
  question_text: string;
  category: QuestionCategory;
  source_section: string | null;
  source_text: string | null;
  order_index: number;
  status: QuestionStatus;
}

export interface Document {
  id: string;
  project_id: string;
  document_type: DocumentType;
  filename: string;
  mime_type: string;
  status: DocumentStatus;
  created_at: string;
}

export interface Answer {
  id: string;
  question_id: string;
  draft_text: string;
  final_text: string;
  status: AnswerStatus;
  review_note: string | null;
  warning: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  id: string;
  answer_id: string;
  chunk_id: string;
  document_title: string;
  section_title: string | null;
  page_number: number | null;
  excerpt: string;
  relevance_score: number | null;
}

export interface QuestionAnswerBundle {
  question_id: string;
  question_text: string;
  answer: Answer;
  citations: Citation[];
}

export interface BidFactor {
  id: string;
  label: string;
  sentiment: BidFactorSentiment;
  score_impact: number;
  evidence: string[];
}

export interface RfpChecklistItem {
  id: string;
  category: string;
  label: string;
  description: string;
  status: RequirementCheckStatus;
  severity: RequirementSeverity;
  evidence: string[];
  follow_up: string | null;
}

export interface MissingInfoItem {
  requirement_id: string;
  category: string;
  label: string;
  severity: RequirementSeverity;
  status: RequirementCheckStatus;
  requested_action: string;
}

export interface ClientSubmissionItem {
  id: string;
  category: string;
  label: string;
  description: string;
  status: SubmissionRequirementStatus;
  severity: RequirementSeverity;
  responsible_team: string | null;
  evidence: string[];
  requested_action: string;
}

export interface RfpAssessment {
  id: string;
  project_id: string;
  rfp_document_id: string;
  recommendation: BidRecommendation;
  bid_score: number;
  confidence: number;
  summary: string;
  policy_source_documents: string[];
  bid_factors: BidFactor[];
  checklist: RfpChecklistItem[];
  missing_information: MissingInfoItem[];
  client_submission_checklist: ClientSubmissionItem[];
  generated_at: string;
  updated_at: string;
}

export interface ExportResponse {
  download_url: string;
  exported_answer_count: number;
}
