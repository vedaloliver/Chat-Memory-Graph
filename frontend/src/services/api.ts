import axios from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  ConversationsResponse,
  ConversationDetail
} from '../types/api';

// Configure the base URL for your FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export class ApiService {
  /**
   * Get list of conversations
   */
  static async getConversations(limit: number = 10): Promise<ConversationsResponse> {
    const response = await apiClient.get(
      `/api/conversations?limit=${limit}&use_db=true`
    );
    return response.data;
  }

  /**
   * Get conversation details with messages
   */
  static async getConversation(conversationId: string): Promise<ConversationDetail> {
    const response = await apiClient.get(
      `/api/conversations/${conversationId}?use_db=true`
    );
    return response.data;
  }

  /**
   * Start a new chat conversation
   */
  static async newChat(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post(
      '/api/newchat?use_db=true',
      request
    );
    return response.data;
  }

  /**
   * Continue an existing chat conversation
   */
  static async continueChat(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post(
      '/api/continue?use_db=true',
      request
    );
    return response.data;
  }
}

export default ApiService;
