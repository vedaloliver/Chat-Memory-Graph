import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../types/api';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  error?: string | null;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isLoading,
  onSendMessage,
  error
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      onSendMessage(inputMessage.trim());
      setInputMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = '44px';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputMessage]);



  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: '#0d1117' }}>
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full" style={{ color: '#6e7681' }}>
            <div className="text-center">
              <h2 className="text-2xl font-semibold mb-2">Welcome to Chat</h2>
              <p>Start a conversation by typing a message below.</p>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              } message-enter`}
            >
              <div
                className="max-w-3xl px-4 py-3 rounded-lg shadow-sm"
                style={
                  message.role === 'user'
                    ? { backgroundColor: '#1a5fb4', color: '#e6edf3' }
                    : { backgroundColor: '#1c2128', border: '1px solid #30363d', color: '#e6edf3' }
                }
              >
                <div className="break-words">
                  {message.role === 'user' ? (
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  ) : (
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
                <div
                  className="text-xs mt-2"
                  style={{ color: message.role === 'user' ? '#cdd9e5' : '#8b949e' }}
                >
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-lg shadow-sm" style={{ backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" style={{ color: '#8b949e' }} />
                <span style={{ color: '#8b949e' }}>AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-4 py-2 border-t text-sm" style={{ backgroundColor: '#2d1519', borderColor: '#5d2127', color: '#ff7b72' }}>
          Error: {error}
        </div>
      )}

      {/* Input Area */}
      <div className="p-4" style={{ borderTop: '1px solid #30363d', backgroundColor: '#161b22' }}>
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              className="w-full px-4 py-3 rounded-lg resize-none scrollbar-thin"
              style={{
                minHeight: '44px',
                maxHeight: '120px',
                backgroundColor: '#1c2128',
                border: '1px solid #30363d',
                color: '#e6edf3',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#1a5fb4';
                e.currentTarget.style.outline = '2px solid rgba(26, 95, 180, 0.3)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#30363d';
                e.currentTarget.style.outline = 'none';
              }}
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 rounded-lg transition-colors flex items-center justify-center min-w-[44px]"
            style={{
              backgroundColor: !inputMessage.trim() || isLoading ? '#21262d' : '#1a5fb4',
              color: '#e6edf3',
              cursor: !inputMessage.trim() || isLoading ? 'not-allowed' : 'pointer',
              opacity: !inputMessage.trim() || isLoading ? 0.5 : 1,
            }}
            onMouseEnter={(e) => {
              if (inputMessage.trim() && !isLoading) {
                e.currentTarget.style.backgroundColor = '#155a9f';
              }
            }}
            onMouseLeave={(e) => {
              if (inputMessage.trim() && !isLoading) {
                e.currentTarget.style.backgroundColor = '#1a5fb4';
              }
            }}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
