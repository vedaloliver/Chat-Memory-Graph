// API Types based on the FastAPI backend models

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  system_prompt?: string;
}

export interface ChatResponse {
  reply: string;
  conversation_id: string;
}

export interface ConversationMetadata {
  id: string;
  title?: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface ConversationsResponse {
  conversations: ConversationMetadata[];
}

export interface ApiError {
  detail: string;
}
