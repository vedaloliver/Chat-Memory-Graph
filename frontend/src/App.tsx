import { useState } from 'react';
import TopNavigation from './components/TopNavigation';
import SessionsSidebar from './components/SessionsSidebar';
import ChatInterface from './components/ChatInterface';
import GraphView from './components/GraphView';
import { useChat } from './hooks/useChat';

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'graph'>('chat');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  const {
    currentConversation,
    isLoading,
    error,
    sendMessage,
    loadConversation,
    startNewChat,
    clearError
  } = useChat();

  const handleConversationSelect = async (conversationId: string) => {
    await loadConversation(conversationId);
  };

  const handleNewChat = () => {
    // Clear current conversation to start fresh
    setActiveTab('chat');
  };

  const handleSendMessage = async (message: string) => {
    if (currentConversation) {
      await sendMessage(message, currentConversation.id);
    } else {
      await startNewChat(message);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Top Navigation */}
      <TopNavigation activeTab={activeTab} onTabChange={setActiveTab} />
      
      <div className="flex flex-1 overflow-hidden" style={{ height: 'calc(100vh - 64px)' }}>
        {/* Sessions Sidebar - Fixed height with independent scroll */}
        {isSidebarOpen && (
          <div className="w-80 flex-shrink-0" style={{ height: '100%', overflow: 'hidden' }}>
            <SessionsSidebar
              currentConversationId={currentConversation?.id}
              onConversationSelect={handleConversationSelect}
              onNewChat={handleNewChat}
              className="h-full"
            />
          </div>
        )}
        
        {/* Sidebar Toggle Button */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="w-4 bg-gray-200 hover:bg-gray-300 transition-colors flex items-center justify-center group flex-shrink-0"
          title={isSidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
        >
          <div className={`w-1 h-8 bg-gray-400 group-hover:bg-gray-600 transition-colors transform ${isSidebarOpen ? 'rotate-0' : 'rotate-180'}`} />
        </button>
        
        {/* Main Content Area - Fixed height with independent scroll */}
        <div className="flex-1 flex flex-col min-w-0" style={{ height: '100%', overflow: 'hidden' }}>
          {activeTab === 'chat' ? (
            <div className="flex-1" style={{ height: '100%', overflow: 'hidden' }}>
              <ChatInterface
                messages={currentConversation?.messages || []}
                isLoading={isLoading}
                onSendMessage={handleSendMessage}
                error={error}
              />
            </div>
          ) : (
            <GraphView />
          )}
        </div>
      </div>
      
      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2">
          <span>{error}</span>
          <button
            onClick={clearError}
            className="text-white hover:text-gray-200 text-lg font-bold"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
