import React, { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { InteractionDetailsPanel } from './InteractionDetailsPanel';
import { KnowledgeGraphPanel } from './KnowledgeGraphPanel';

export const AppFrame: React.FC = () => {
  const [, setSearchQuery] = useState<string>('');
  const [, setPatientAge] = useState<string>('');
  const [, setPatientSex] = useState<string>('Male');

  const handlePatientContextChange = (age: string, sex: string) => {
    setPatientAge(age);
    setPatientSex(sex);
    console.log(`// MOCK: Updated Patient Profile context: Age=${age}, Sex=${sex}`);
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6] w-full flex items-center justify-center p-4 md:p-8 font-sans antialiased">
      {/* Centered App Window Panel with ~3px #6C5CE7 Border */}
      <div 
        className="w-full max-w-[1200px] bg-white rounded-2xl border-[3px] border-[#6C5CE7] shadow-xl overflow-hidden flex flex-col"
        style={{ minHeight: '680px' }}
      >
        {/* Top Header Bar inside purple frame */}
        <Header onSearchChange={(term) => setSearchQuery(term)} />

        {/* Three Column Body Layout */}
        <div className="flex-1 p-6 flex flex-row gap-0 overflow-x-auto">
          {/* Column 1: Left Sidebar (~180-200px wide) */}
          <Sidebar onPatientContextChange={handlePatientContextChange} />

          {/* Column 2: Middle Interaction Details Panel */}
          <InteractionDetailsPanel drug1="Warfarin" drug2="Aspirin" />

          {/* Column 3: Right Interaction Knowledge Graph Panel */}
          <KnowledgeGraphPanel patientId="#8492-B" />
        </div>
      </div>
    </div>
  );
};
