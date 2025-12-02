import React from 'react';
import { MessageCircle, GitBranch } from 'lucide-react';

interface TopNavigationProps {
  activeTab: 'chat' | 'graph';
  onTabChange: (tab: 'chat' | 'graph') => void;
}

const TopNavigation: React.FC<TopNavigationProps> = ({ activeTab, onTabChange }) => {
  return (
    <div className="px-6 py-4" style={{ backgroundColor: '#161b22', borderBottom: '1px solid #30363d' }}>
      <div className="flex items-center space-x-8">
        <div className="flex items-center space-x-3">
          <h1 className="text-xl font-semibold" style={{ color: '#e6edf3' }}>ChatGPT Clone</h1>
        </div>
        
        <nav className="flex space-x-1">
          <button
            onClick={() => onTabChange('chat')}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors"
            style={{
              backgroundColor: activeTab === 'chat' ? '#1c2d41' : 'transparent',
              color: activeTab === 'chat' ? '#58a6ff' : '#8b949e',
              border: activeTab === 'chat' ? '1px solid #1c2d41' : '1px solid transparent',
            }}
            onMouseEnter={(e) => {
              if (activeTab !== 'chat') {
                e.currentTarget.style.backgroundColor = '#21262d';
                e.currentTarget.style.color = '#adbac7';
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== 'chat') {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = '#8b949e';
              }
            }}
          >
            <MessageCircle className="w-4 h-4" />
            <span>Chat</span>
          </button>
          
          <button
            onClick={() => onTabChange('graph')}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors"
            style={{
              backgroundColor: activeTab === 'graph' ? '#1c2d41' : 'transparent',
              color: activeTab === 'graph' ? '#58a6ff' : '#8b949e',
              border: activeTab === 'graph' ? '1px solid #1c2d41' : '1px solid transparent',
            }}
            onMouseEnter={(e) => {
              if (activeTab !== 'graph') {
                e.currentTarget.style.backgroundColor = '#21262d';
                e.currentTarget.style.color = '#adbac7';
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== 'graph') {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = '#8b949e';
              }
            }}
          >
            <GitBranch className="w-4 h-4" />
            <span>Graph</span>
          </button>
        </nav>
      </div>
    </div>
  );
};

export default TopNavigation;
