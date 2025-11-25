import React from 'react';
import { GitBranch, Construction } from 'lucide-react';

const GraphView: React.FC = () => {
  return (
    <div className="flex items-center justify-center h-full bg-gray-50">
      <div className="text-center p-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 max-w-md">
          <Construction className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Graph View</h2>
          <p className="text-gray-600 mb-4">
            This feature will display a visual representation of chat conversation nodes and their relationships.
          </p>
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
            <GitBranch className="w-4 h-4" />
            <span>Coming Soon</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphView;
