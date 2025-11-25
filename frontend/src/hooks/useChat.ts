import { useState, useCallback } from 'react';
import type { ChatMessage, ConversationDetail } from '../types/api';
import ApiService from '../services/api';

interface UseChatReturn {
  currentConversation: ConversationDetail | null;
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string, conversationId?: string) => Promise<void>;
  loadConversation: (conversationId: string) => Promise<void>;
  startNewChat: (message: string) => Promise<void>;
  clearError: () => void;
}

export const useChat = (): UseChatReturn => {
  const [currentConversation, setCurrentConversation] = useState<ConversationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const loadConversation = useCallback(async (conversationId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const conversation = await ApiService.getConversation(conversationId);
      setCurrentConversation(conversation);
    } catch (err: any) {
      console.error('Error loading conversation:', err);
      setError(err.response?.data?.detail || 'Failed to load conversation');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const startNewChat = useCallback(async (message: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await ApiService.newChat({ message });
      
      // Create a new conversation object with the initial messages
      const newConversation: ConversationDetail = {
        id: response.conversation_id,
        title: undefined,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: [
          {
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
          },
          {
            role: 'assistant',
            content: response.reply,
            timestamp: new Date().toISOString()
          }
        ]
      };
      
      setCurrentConversation(newConversation);
    } catch (err: any) {
      console.error('Error starting new chat:', err);
      setError(err.response?.data?.detail || 'Failed to start new chat');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (message: string, conversationId?: string) => {
    if (!conversationId && !currentConversation) {
      await startNewChat(message);
      return;
    }

    setIsLoading(true);
    setError(null);
    
    // Add user message optimistically
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    if (currentConversation) {
      setCurrentConversation(prev => prev ? {
        ...prev,
        messages: [...prev.messages, userMessage]
      } : null);
    }
    
    try {
      const response = await ApiService.continueChat({
        message,
        conversation_id: conversationId || currentConversation?.id
      });
      
      // Add assistant response
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString()
      };

      setCurrentConversation(prev => prev ? {
        ...prev,
        messages: [...prev.messages, assistantMessage],
        updated_at: new Date().toISOString()
      } : null);
      
    } catch (err: any) {
      console.error('Error sending message:', err);
      setError(err.response?.data?.detail || 'Failed to send message');
      
      // Remove the optimistically added user message on error
      if (currentConversation) {
        setCurrentConversation(prev => prev ? {
          ...prev,
          messages: prev.messages.slice(0, -1)
        } : null);
      }
    } finally {
      setIsLoading(false);
    }
  }, [currentConversation, startNewChat]);

  return {
    currentConversation,
    isLoading,
    error,
    sendMessage,
    loadConversation,
    startNewChat,
    clearError
  };
};
