import React, { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { InteractionDetailsPanel } from './InteractionDetailsPanel';
import { KnowledgeGraphPanel } from './KnowledgeGraphPanel';
import { analyzeInteractions, type DrugInteractionResponse } from '../services/apiClient';

export const AppFrame: React.FC = () => {
  const [, setSearchQuery] = useState<string>('');
  const [, setPatientAge] = useState<string>('');
  const [, setPatientSex] = useState<string>('Male');
  const [data, setData] = useState<DrugInteractionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handlePatientContextChange = (age: string, sex: string) => {
    setPatientAge(age);
    setPatientSex(sex);
    console.log(`// MOCK: Updated Patient Profile context: Age=${age}, Sex=${sex}`);
  };

  const handleSearchSubmit = async (term: string) => {
    const drugs = term.split(',').map(d => d.trim()).filter(Boolean);
    if (drugs.length === 0) return;
    setLoading(true);
    const responseData = await analyzeInteractions(drugs.join(', '));
    setData(responseData);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6] w-full flex items-center justify-center p-4 md:p-8 font-sans antialiased">
      {/* Centered App Window Panel with ~3px #6C5CE7 Border */}
      <div 
        className="w-full max-w-[1200px] bg-white rounded-2xl border-[3px] border-[#6C5CE7] shadow-xl overflow-hidden flex flex-col relative"
        style={{ minHeight: '680px' }}
      >
        {/* Top Header Bar inside purple frame */}
        <Header 
          onSearchChange={(term) => setSearchQuery(term)} 
          onSearchSubmit={handleSearchSubmit} 
        />

        {/* Global Loading Overlay (Optional) */}
        {loading && (
          <div className="absolute inset-0 z-50 bg-white/50 backdrop-blur-[2px] flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
          </div>
        )}

        {/* Three Column Body Layout */}
        <div className="flex-1 p-6 flex flex-row gap-0 overflow-x-auto relative z-10">
          {/* Column 1: Left Sidebar (~180-200px wide) */}
          <Sidebar onPatientContextChange={handlePatientContextChange} />

          {/* Column 2: Middle Interaction Details Panel */}
          <InteractionDetailsPanel 
            interactions={data?.interactions || []}
            summary={data?.summary || ''}
          />

          {/* Column 3: Right Interaction Knowledge Graph Panel */}
          <KnowledgeGraphPanel 
            patientId="#8492-B" 
            graphData={data?.graph_data} 
          />
        </div>
      </div>
    </div>
  );
};
