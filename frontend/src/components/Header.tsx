import React from 'react';
import { Search, Bell, Settings, LayoutGrid } from 'lucide-react';

interface HeaderProps {
  onSearchChange?: (term: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ onSearchChange }) => {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white rounded-t-2xl">
      {/* Left logo / brand mark */}
      <div className="flex items-center gap-2 min-w-[200px]">
        <LayoutGrid className="w-5 h-5 text-gray-400" />
        <span className="text-xl font-bold text-gray-900 tracking-tight">
          DDI Analyzer
        </span>
      </div>

      {/* Center search bar (~360px wide) */}
      <div className="flex-1 max-w-[360px] mx-4">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-9 pr-3 py-1.5 text-sm bg-[#F3F4F6] border border-transparent rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:border-indigo-400 transition-all"
            placeholder="Search drugs, patients..."
            onChange={(e) => onSearchChange?.(e.target.value)}
          />
        </div>
      </div>

      {/* Right controls: notification bell, settings, avatar */}
      <div className="flex items-center gap-4">
        <button 
          type="button"
          onClick={() => {
            // MOCK: notification bell action
            console.log('MOCK: Opened notification drawer');
          }}
          className="text-gray-500 hover:text-gray-700 transition-colors relative"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-indigo-600 rounded-full" />
        </button>

        <button 
          type="button"
          onClick={() => {
            // MOCK: settings modal action
            console.log('MOCK: Opened settings');
          }}
          className="text-gray-500 hover:text-gray-700 transition-colors"
          aria-label="Settings"
        >
          <Settings className="w-5 h-5" />
        </button>

        {/* Circular user avatar with purple gradient fill */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-400 border border-purple-200 flex items-center justify-center text-white text-xs font-semibold shadow-xs overflow-hidden cursor-pointer">
          {/* Placeholder avatar image or icon */}
          <span className="sr-only">User Profile</span>
          <div className="w-full h-full bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-300 via-purple-500 to-indigo-700" />
        </div>
      </div>
    </header>
  );
};
