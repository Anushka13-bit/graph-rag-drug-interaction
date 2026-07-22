import React, { useState } from 'react';
import { ArrowLeftRight, FlaskConical, AlertTriangle, Activity, CheckCircle2 } from 'lucide-react';

interface InteractionDetailsPanelProps {
  drug1?: string;
  drug2?: string;
  onOverrideAlert?: () => void;
}

export const InteractionDetailsPanel: React.FC<InteractionDetailsPanelProps> = ({
  drug1 = 'Warfarin',
  drug2 = 'Aspirin',
  onOverrideAlert,
}) => {
  const [acknowledged, setAcknowledged] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleAcknowledgeClick = () => {
    // MOCK: Acknowledge & Override Alert action
    console.log('MOCK: acknowledge alert clicked');
    setAcknowledged(true);
    setToastMessage('Alert acknowledged and override logged.');

    onOverrideAlert?.();

    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  return (
    <section className="flex-1 flex flex-col gap-5 px-6 select-text" aria-label="Interaction Details">
      {/* Toast Notification for Override Alert */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white px-4 py-2.5 rounded-lg shadow-lg text-xs flex items-center gap-2 border border-gray-700 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-green-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Heading */}
      <div className="flex flex-col gap-3">
        <h1 className="text-lg font-bold text-gray-900">
          Interaction Details
        </h1>

        {/* Drug Pill Badges with Interaction Glyph Icon */}
        <div className="flex items-center gap-2">
          <div className="px-3 py-1 bg-gray-100 border border-gray-300 rounded-md text-xs font-semibold text-gray-800">
            {drug1}
          </div>
          
          {/* Interaction Glyph Icon (User explicit requirement) */}
          <div className="p-1 text-gray-400 flex items-center justify-center" title="Interacts with">
            <ArrowLeftRight className="w-3.5 h-3.5" />
          </div>

          <div className="px-3 py-1 bg-gray-100 border border-gray-300 rounded-md text-xs font-semibold text-gray-800">
            {drug2}
          </div>
        </div>

        {/* Severity Badge */}
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#FEF2F2] border border-[#FCA5A5] text-[#DC2626] rounded-md text-[11px] font-bold uppercase tracking-wide">
            <span className="w-2 h-2 rounded-full bg-[#DC2626]" />
            MAJOR INTERACTION
          </div>
        </div>
      </div>

      {/* Thin Horizontal Divider */}
      <hr className="border-t border-gray-200 -mt-1" />

      {/* Card Block 1: CLINICAL SIGNIFICANCE */}
      <div className="border border-gray-200 rounded-lg bg-gray-50/50 p-4 flex flex-col gap-2 shadow-2xs">
        <h2 className="text-[11px] font-bold text-gray-400 tracking-wider uppercase">
          CLINICAL SIGNIFICANCE
        </h2>
        <p className="text-[13px] text-gray-800 leading-relaxed font-normal">
          Concurrent use of NSAIDs (including aspirin) and warfarin significantly increases the risk of major bleeding complications, particularly gastrointestinal bleeding. The risk is elevated due to dual pathways of impaired hemostasis.
        </p>
      </div>

      {/* Card Block 2: MECHANISM OF ACTION */}
      <div className="border border-gray-200 rounded-lg bg-gray-50/50 p-4 flex flex-col gap-2 shadow-2xs">
        <div className="flex items-center justify-between">
          <h2 className="text-[11px] font-bold text-gray-400 tracking-wider uppercase">
            MECHANISM OF ACTION
          </h2>
          <FlaskConical className="w-4 h-4 text-gray-400" />
        </div>
        <ul className="text-[13px] text-gray-800 space-y-2 list-disc list-inside leading-relaxed">
          <li className="pl-1">
            <strong className="font-bold text-gray-900">Warfarin:</strong> Depletes{' '}
            <span className="text-blue-600 hover:underline cursor-pointer font-medium">
              vitamin K
            </span>
            -dependent clotting factors (II, VII, IX, X).
          </li>
          <li className="pl-1">
            <strong className="font-bold text-gray-900">Aspirin:</strong> Irreversibly inhibits platelet cyclooxygenase (COX-1), preventing platelet aggregation and causing direct gastric mucosal irritation.
          </li>
        </ul>
      </div>

      {/* Card Block 3: MANAGEMENT RECOMMENDATIONS */}
      <div className="border border-gray-200 rounded-lg bg-gray-50/50 p-4 flex flex-col gap-3 shadow-2xs">
        <h2 className="text-[11px] font-bold text-gray-400 tracking-wider uppercase">
          MANAGEMENT RECOMMENDATIONS
        </h2>

        {/* Stacked Alert Callout Box 1 (Light Red / Pink Warning) */}
        <div className="bg-red-50 border border-red-200 rounded-md p-3 text-xs text-red-900 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            Avoid combination if possible. Evaluate indication for aspirin. If required for secondary cardiovascular prophylaxis, use lowest effective dose (e.g., 81mg).
          </p>
        </div>

        {/* Stacked Alert Callout Box 2 (Light Blue Monitor) */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-xs text-blue-900 flex items-start gap-2.5">
          <Activity className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            Monitor INR closely (target usually 2.0–3.0 depending on indication) and monitor for clinical signs of bleeding (hematochezia, melena, ecchymosis).
          </p>
        </div>

        {/* Full-width Black Button */}
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
