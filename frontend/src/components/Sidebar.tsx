import React, { useState } from 'react';
import { LayoutGrid, ChevronDown, Activity } from 'lucide-react';

interface SidebarProps {
  onPatientContextChange?: (age: string, sex: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onPatientContextChange }) => {
  // MOCK: Local component state for patient context filter
  const [age, setAge] = useState<string>('');
  const [sex, setSex] = useState<string>('Male');

  const handleAgeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setAge(val);
    // MOCK: Emit patient profile context update
    onPatientContextChange?.(val, sex);
  };

  const handleSexChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSex(val);
    // MOCK: Emit patient profile context update
    onPatientContextChange?.(age, val);
  };

  return (
    <aside className="w-[190px] shrink-0 pr-4 border-r border-gray-200 flex flex-col gap-6 select-none">
      {/* Clinical Suite App Header */}
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg border border-gray-200 flex items-center justify-center bg-gray-50 shadow-2xs">
          <Activity className="w-4 h-4 text-blue-600" />
        </div>
        <div className="flex flex-col">
          <span className="text-[15px] font-bold text-gray-900 leading-tight">
            Clinical Suite
          </span>
          <span className="text-[11px] font-normal text-gray-500">
            Vigilance System
          </span>
        </div>
      </div>

      {/* Primary Nav Button - Selected Active State */}
      <nav aria-label="Main Navigation">
        <button
          type="button"
          className="w-full flex items-center gap-2.5 px-3 py-2 bg-[#2563EB] text-white text-sm font-semibold rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
        >
          <LayoutGrid className="w-4 h-4 text-white" />
          <span>Dashboard</span>
        </button>
      </nav>

      {/* Patient Profile Form Section */}
      <div className="flex flex-col gap-4 pt-2 border-t border-gray-100">
        <h2 className="text-[11px] font-bold text-gray-400 tracking-wider uppercase">
          PATIENT PROFILE
        </h2>

        {/* Patient Age Field */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="patient-age" className="text-xs font-bold text-gray-900">
            Patient Age
          </label>
          <input
            id="patient-age"
            type="text"
            value={age}
            onChange={handleAgeChange}
            placeholder="e.g. 65"
            className="w-full px-3 py-1.5 text-xs text-gray-800 bg-white border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        {/* Sex Field */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="patient-sex" className="text-xs font-bold text-gray-900">
            Sex
          </label>
          <div className="relative">
            <select
              id="patient-sex"
              value={sex}
              onChange={handleSexChange}
              className="w-full appearance-none px-3 py-1.5 text-xs text-gray-800 bg-white border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 transition-colors pr-8 cursor-pointer font-medium"
            >
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
            <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center pointer-events-none">
              <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
