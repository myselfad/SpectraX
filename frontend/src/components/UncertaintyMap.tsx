import React, { useState } from 'react';
import { AlertCircle, ShieldCheck } from 'lucide-react';
import { getImageUrl } from '../api/client';

interface UncertaintyProps {
  jobId: string;
  uncertaintyUrl: string | null;
  reliabilityUrl?: string | null;
  passes?: number | null;
  reliabilityStats?: any;
}

const UncertaintyMap: React.FC<UncertaintyProps> = ({ jobId, uncertaintyUrl, reliabilityUrl, reliabilityStats }) => {
  const [showReliability, setShowReliability] = useState(true);

  if (!uncertaintyUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center py-20 bg-black/20 rounded-2xl border border-white/5">
        <AlertCircle className="w-10 h-10 text-slate-600 mb-4" />
        <h3 className="text-sm font-semibold text-slate-400 mb-2">Estimation Disabled</h3>
        <p className="text-xs text-slate-500 max-w-sm">
          Uncertainty estimation was not performed for this run. Enable Monte Carlo passes in the configuration step to generate maps.
        </p>
      </div>
    );
  }

  const activeUrl = showReliability && reliabilityUrl ? reliabilityUrl : uncertaintyUrl;
  
  return (
    <div className="flex flex-col h-full gap-3 min-h-0">
      
      {/* Header & Toggle */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 shrink-0">
        <div>
          <h4 className="text-xs font-bold text-white mb-0.5 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Interpretation
          </h4>
          <p className="text-[10px] text-slate-400 leading-relaxed max-w-md">
            {showReliability 
              ? 'Pixel reliability (1.0 = Highly certain). Bright yellow/green indicates high confidence.'
              : 'Raw pixel uncertainty from MC-Dropout. Brighter areas indicate higher variance.'}
          </p>
        </div>

        <div className="flex bg-black/40 backdrop-blur-md rounded-lg border border-white/10 overflow-hidden shadow-sm">
          <button 
            onClick={() => setShowReliability(true)}
            className={`px-3 py-1.5 text-[10px] font-bold transition-colors ${showReliability ? 'bg-emerald-500/20 text-emerald-400' : 'text-slate-400 hover:text-white'}`}
          >
            Reliability Map
          </button>
          <button 
            onClick={() => setShowReliability(false)}
            className={`px-3 py-1.5 text-[10px] font-bold transition-colors border-l border-white/10 ${!showReliability ? 'bg-amber-500/20 text-amber-400' : 'text-slate-400 hover:text-white'}`}
          >
            Raw Uncertainty
          </button>
        </div>
      </div>

      {/* Visualizer Area */}
      <div className="w-full relative flex-1 bg-[#05080f] border border-white/5 rounded-xl flex items-center justify-center overflow-hidden shadow-inner min-h-0">
        <img 
          src={getImageUrl(jobId, activeUrl)} 
          alt={showReliability ? "Reliability Map" : "Uncertainty Map"} 
          className="w-full h-full object-contain transition-transform duration-700 hover:scale-[1.02]"
        />
      </div>

      {/* Stats */}
      {reliabilityStats && (
        <div className="shrink-0 flex justify-end">
          <div className="bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg flex items-center gap-3">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Mean Score</div>
            <div className="text-sm font-mono text-emerald-400 font-black">
               {(reliabilityStats.mean_score || 0).toFixed(3)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UncertaintyMap;
