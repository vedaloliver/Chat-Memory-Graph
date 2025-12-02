import React, { useState, useEffect } from 'react';
import { MessageCircle, Plus, Loader2, Calendar } from 'lucide-react';
import type { ConversationMetadata } from '../types/api';
import ApiService from '../services/api';

interface SessionsSidebarProps {
  currentConversationId?: string;
  onConversationSelect: (conversationId: string) => void;
  onNewChat: () => void;
  className?: string;
}

const SessionsSidebar: React.FC<SessionsSidebarProps> = ({
  currentConversationId,
  onConversationSelect,
  onNewChat,
  className = ''
}) => {
  const [conversations, setConversations] = useState<ConversationMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await ApiService.getConversations(50);
      setConversations(response.conversations);
    } catch (err: any) {
      console.error('Error loading conversations:', err);
      setError('Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      return 'Today';
    } else if (diffDays === 2) {
      return 'Yesterday';
    } else if (diffDays <= 7) {
      return `${diffDays - 1} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getConversationTitle = (conversation: ConversationMetadata) => {
    return conversation.title || `Chat ${conversation.id.slice(0, 8)}...`;
  };

  return (
    <div className={`flex flex-col h-full bg-gray-900 text-white ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center space-x-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-3 rounded-lg transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {(() => {
          if (isLoading) {
            return (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            );
          }
          
          if (error) {
            return (
              <div className="p-4 text-center text-red-400">
                <p>{error}</p>
                <button
                  onClick={loadConversations}
                  className="mt-2 text-sm text-primary-400 hover:text-primary-300"
                >
                  Try again
                </button>
              </div>
            );
          }
          
          if (conversations.length === 0) {
            return (
              <div className="p-4 text-center text-gray-400">
                <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs mt-1">Start a new chat to begin</p>
              </div>
            );
          }
          
          return (
            <div className="p-2 space-y-1">
              {conversations.map((conversation) => {
                const isActive = currentConversationId === conversation.id;
                return (
                  <button
                    key={conversation.id}
                    onClick={() => onConversationSelect(conversation.id)}
                    style={{
                      backgroundColor: isActive ? '#1c2d41' : 'transparent',
                      color: isActive ? '#e6edf3' : '#6e7681',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = '#21262d';
                        e.currentTarget.style.color = '#adbac7';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.color = '#6e7681';
                      }
                    }}
                    className="w-full text-left p-3 rounded-lg transition-colors group"
                  >
                    <div className="flex items-start space-x-3">
                      <MessageCircle className="w-4 h-4 mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">
                          {getConversationTitle(conversation)}
                        </div>
                        <div className="flex items-center space-x-2 mt-1">
                          <Calendar className="w-3 h-3" />
                          <span className="text-xs opacity-75">
                            {formatDate(conversation.updated_at)}
                          </span>
                          <span className="text-xs opacity-75">
                            • {conversation.message_count} messages
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          );
        })()}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-400 text-center">
          {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
};

export default SessionsSidebar;
