import React from 'react';
import { MessageCircle, GitBranch } from 'lucide-react';

interface TopNavigationProps {
  activeTab: 'chat' | 'graph';
  onTabChange: (tab: 'chat' | 'graph') => void;
}

const TopNavigation: React.FC<TopNavigationProps> = ({ activeTab, onTabChange }) => {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center space-x-8">
        <div className="flex items-center space-x-3">
          <h1 className="text-xl font-semibold text-gray-900">ChatGPT Clone</h1>
        </div>
        
        <nav className="flex space-x-1">
          <button
            onClick={() => onTabChange('chat')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'chat'
                ? 'bg-primary-100 text-primary-700 border border-primary-200'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <MessageCircle className="w-4 h-4" />
            <span>Chat</span>
          </button>
          
          <button
            onClick={() => onTabChange('graph')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'graph'
                ? 'bg-primary-100 text-primary-700 border border-primary-200'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
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
