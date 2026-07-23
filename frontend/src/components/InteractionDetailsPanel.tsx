import React, { useState } from 'react';
import { ArrowLeftRight, FlaskConical, AlertTriangle, Activity, CheckCircle2, Info } from 'lucide-react';
import { type InteractionDetail } from '../services/apiClient';

interface InteractionDetailsPanelProps {
  interactions?: InteractionDetail[];
  summary?: string;
  onOverrideAlert?: () => void;
}

export const InteractionDetailsPanel: React.FC<InteractionDetailsPanelProps> = ({
  interactions = [],
  summary = '',
  onOverrideAlert,
}) => {
  const [acknowledged, setAcknowledged] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleAcknowledgeClick = () => {
    console.log('MOCK: acknowledge alert clicked');
    setAcknowledged(true);
    setToastMessage('Alert acknowledged and override logged.');
    onOverrideAlert?.();
    setTimeout(() => setToastMessage(null), 4000);
  };

  if (!interactions || interactions.length === 0) {
    return (
      <section className="flex-1 flex flex-col items-center justify-center gap-4 px-6 select-text text-gray-500">
        <Info className="w-10 h-10 text-gray-300" />
        <p className="text-sm">Search for drugs to view interactions.</p>
      </section>
    );
  }

  // Get the highest severity for overall UI cues
  const hasSevere = interactions.some(i => i.severity === 'severe');
  const hasModerate = interactions.some(i => i.severity === 'moderate');

  return (
    <section className="flex-1 flex flex-col gap-5 px-6 select-text overflow-y-auto" aria-label="Interaction Details">
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white px-4 py-2.5 rounded-lg shadow-lg text-xs flex items-center gap-2 border border-gray-700 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-green-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Heading & Summary */}
      <div className="flex flex-col gap-3">
        <h1 className="text-lg font-bold text-gray-900">
          Interaction Details
        </h1>
        
        {/* Dynamic Summary Panel */}
        {summary && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-2 shadow-2xs">
            <h2 className="text-[11px] font-bold text-gray-400 tracking-wider uppercase mb-2">
              LLM Analysis Summary
            </h2>
            <p className="text-[13px] text-gray-800 leading-relaxed whitespace-pre-wrap">
              {summary}
            </p>
          </div>
        )}
      </div>

      <hr className="border-t border-gray-200 -mt-1" />

      {/* Render Each Interaction Detail */}
      {interactions.map((interaction, idx) => (
        <div key={idx} className="flex flex-col gap-3 mb-4">
          <div className="flex items-center gap-2">
            <div className="px-3 py-1 bg-gray-100 border border-gray-300 rounded-md text-xs font-semibold text-gray-800">
              {interaction.drug_a}
            </div>
            <div className="p-1 text-gray-400 flex items-center justify-center" title={interaction.interaction_type || 'Interacts with'}>
              <ArrowLeftRight className="w-3.5 h-3.5" />
            </div>
            <div className="px-3 py-1 bg-gray-100 border border-gray-300 rounded-md text-xs font-semibold text-gray-800">
              {interaction.drug_b}
            </div>
          </div>

          <div>
            <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${interaction.severity === 'severe' ? 'bg-[#FEF2F2] border-[#FCA5A5] text-[#DC2626]' : interaction.severity === 'moderate' ? 'bg-[#FFFBEB] border-[#FCD34D] text-[#D97706]' : 'bg-[#F0FDF4] border-[#86EFAC] text-[#16A34A]'} border rounded-md text-[11px] font-bold uppercase tracking-wide`}>
              <span className={`w-2 h-2 rounded-full ${interaction.severity === 'severe' ? 'bg-[#DC2626]' : interaction.severity === 'moderate' ? 'bg-[#D97706]' : 'bg-[#16A34A]'}`} />
              {interaction.severity} INTERACTION
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg bg-gray-50/50 p-4 flex flex-col gap-2 shadow-2xs">
            <div className="flex items-center justify-between">
              <h2 className="text-[11px] font-bold text-gray-400 tracking-wider uppercase">
                CLINICAL DETAILS
              </h2>
              <FlaskConical className="w-4 h-4 text-gray-400" />
            </div>
            <p className="text-[13px] text-gray-800 leading-relaxed font-normal">
              {interaction.description}
            </p>
            <div className="mt-2 text-[11px] text-gray-500">
              <strong>Evidence Count:</strong> {interaction.evidence_count} 
              {interaction.sources && interaction.sources.length > 0 && (
                <span className="ml-2">| <strong>Sources:</strong> {interaction.sources.join(', ')}</span>
              )}
            </div>
          </div>
        </div>
      ))}

      {/* Global Recommendations / Acknowledge */}
      <div className="border border-gray-200 rounded-lg bg-gray-50/50 p-4 flex flex-col gap-3 shadow-2xs mt-auto">
        <h2 className="text-[11px] font-bold text-gray-400 tracking-wider uppercase">
          MANAGEMENT RECOMMENDATIONS
        </h2>

        {hasSevere && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3 text-xs text-red-900 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              Major interactions detected. Avoid combination if possible or monitor patients extremely closely for adverse effects.
            </p>
          </div>
        )}

        {(hasModerate || hasSevere) && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-xs text-blue-900 flex items-start gap-2.5">
            <Activity className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              Clinical monitoring is advised. Review patient history and adjust dosages if required.
            </p>
          </div>
        )}

        <button
          type="button"
          onClick={handleAcknowledgeClick}
          className={`w-full mt-1 py-3 px-4 text-white text-xs font-bold rounded-md transition-all shadow-sm ${
            acknowledged
              ? 'bg-gray-700 hover:bg-gray-800'
              : 'bg-black hover:bg-gray-800 active:scale-[0.99]'
          }`}
        >
          {acknowledged ? 'Alert Overridden & Acknowledged' : 'Acknowledge & Override Alert'}
        </button>
      </div>
    </section>
  );
};
