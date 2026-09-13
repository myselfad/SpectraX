import React, { useState } from 'react';
import { ResultsResponse, ProcessingInfo } from '../types';
import { RotateCcw, Cpu, Target, Zap, LayoutDashboard, SplitSquareHorizontal, Layers, Activity, Download } from 'lucide-react';
import Comparison from './Comparison';
import Metrics from './Metrics';
import UncertaintyMap from './UncertaintyMap';
import Export from './Export';
import { getImageUrl } from '../api/client';

interface ResultsProps {
  results: ResultsResponse;
  info: ProcessingInfo | null;
  onNew: () => void;
}

type TabType = 'overview' | 'comparison' | 'uncertainty' | 'metrics' | 'export';

const Results: React.FC<ResultsProps> = ({ results, info, onNew }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'comparison', label: 'Comparison', icon: <SplitSquareHorizontal className="w-4 h-4" /> },
    { id: 'uncertainty', label: 'Reliability Map', icon: <Layers className="w-4 h-4" /> },
    { id: 'metrics', label: 'Validation', icon: <Activity className="w-4 h-4" /> },
    { id: 'export', label: 'Export', icon: <Download className="w-4 h-4" /> },
  ];

  return (
    <div className="w-full flex flex-col h-[calc(100vh-100px)] mt-0 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-7xl mx-auto pb-4">
      <div className="flex justify-between items-end mb-3 px-4 shrink-0">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] font-bold mb-1 uppercase tracking-widest">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
            Analysis Complete
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">
            Super Resolution Results
          </h2>
          <p className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1.5">
            <Cpu className="w-3 h-3" /> Processed in <span className="font-mono text-slate-300">{info?.processing_time_seconds.toFixed(2)}s</span> via {info?.device}
          </p>
        </div>
        <button 
          onClick={onNew}
          className="group flex items-center gap-1.5 px-3 py-1.5 bg-white/5 border border-white/10 hover:border-white/20 text-slate-200 rounded-full text-[11px] font-semibold transition-all shadow-sm hover:shadow-md hover:bg-white/10 backdrop-blur-md"
        >
          <RotateCcw className="w-3 h-3 group-hover:-rotate-90 transition-transform duration-300" /> New Analysis
        </button>
      </div>

      <div className="glass-panel rounded-[1.25rem] overflow-hidden shadow-xl flex flex-col flex-1 min-h-0 border border-white/10">
        
        {/* Segmented Control Tabs */}
        <div className="bg-black/20 border-b border-white/5 px-4 pt-2 overflow-x-auto no-scrollbar shrink-0">
          <div className="flex gap-1.5">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold transition-all rounded-t-lg whitespace-nowrap ${
                  activeTab === tab.id 
                    ? 'bg-black/40 text-cyan-400 shadow-[0_-4px_12px_rgba(0,0,0,0.2)] border-t border-l border-r border-white/10 relative z-10 before:absolute before:-bottom-[1px] before:left-0 before:right-0 before:h-[1px] before:bg-[#0c1222]' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
                }`}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="p-3 md:p-4 flex-1 bg-black/40 relative flex flex-col min-h-0 overflow-y-auto">
          {activeTab === 'overview' && (
             <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 h-full animate-in fade-in duration-300">
                
                {/* Left Column: Metrics & Info (Bento Style) */}
                <div className="lg:col-span-4 flex flex-col gap-3 min-h-0">
                  {/* Top Stats */}
                  <div className="grid grid-cols-2 gap-2 shrink-0">
                    <div className="bg-black/40 border border-white/5 rounded-lg p-2.5 shadow-inner">
                      <div className="text-slate-400 text-[9px] font-semibold uppercase tracking-wider mb-0.5 flex items-center gap-1"><Target className="w-3 h-3"/> Scale</div>
                      <div className="text-xl font-black text-white tabular-nums tracking-tight">{info?.scale_factor}x</div>
                    </div>
                    <div className="bg-black/40 border border-white/5 rounded-lg p-2.5 shadow-inner">
                      <div className="text-slate-400 text-[9px] font-semibold uppercase tracking-wider mb-0.5 flex items-center gap-1"><Zap className="w-3 h-3"/> PSNR</div>
                      <div className="text-xl font-black text-cyan-400 tabular-nums tracking-tight">
                        {results.metrics?.reference_metrics?.psnr === 0.0 ? 'N/A' : (results.metrics?.reference_metrics?.psnr ?? results.metrics?.observation_consistency?.consistency_psnr ?? 0).toFixed(1)}
                      </div>
                    </div>
                  </div>

                  {/* Summary Card */}
                  <div className="bg-black/20 border border-white/5 rounded-lg p-3 flex-1 flex flex-col shadow-inner min-h-0">
                    <h3 className="font-bold text-xs text-white mb-2 shrink-0">Job Summary</h3>
                    <ul className="space-y-2 text-[11px] overflow-y-auto pr-1">
                      <li className="flex justify-between items-center border-b border-white/5 pb-1">
                        <span className="text-slate-400">Input Res</span>
                        <span className="font-mono text-slate-200 font-medium">{info?.input_width}x{info?.input_height}</span>
                      </li>
                      <li className="flex justify-between items-center border-b border-white/5 pb-1">
                        <span className="text-slate-400">Output Res</span>
                        <span className="font-mono text-cyan-400 font-bold">{info?.output_width}x{info?.output_height}</span>
                      </li>
                      <li className="flex justify-between items-center border-b border-white/5 pb-1">
                        <span className="text-slate-400">Model</span>
                        <span className="font-mono text-slate-200 text-[9px] bg-white/10 px-1 py-0.5 rounded">{info?.model_name || 'SwinIR'}</span>
                      </li>
                      <li className="flex justify-between items-center pb-0.5">
                        <span className="text-slate-400">Uncertainty</span>
                        <span className="font-mono text-amber-400 font-medium">{info?.uncertainty_passes} passes</span>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Right Column: Output Preview */}
                <div className="lg:col-span-8 bg-black/60 border border-white/5 rounded-[1rem] p-1 relative overflow-hidden group shadow-inner min-h-0 flex flex-col">
                  <div className="absolute top-2 left-2 z-10 bg-black/60 backdrop-blur-md border border-white/10 px-2 py-0.5 rounded text-[9px] font-bold text-white shadow-lg flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse"></div> Super Resolved Output
                  </div>
                  <div className="w-full h-full rounded-lg overflow-hidden bg-[#05080f] flex items-center justify-center relative min-h-0">
                    <img 
                      src={getImageUrl(results.job_id, results.sr_image_url)} 
                      alt="Super Resolved" 
                      className="w-full h-full object-contain transition-transform duration-700 hover:scale-[1.02]"
                    />
                  </div>
                </div>
             </div>
          )}

          {activeTab === 'comparison' && (
            <div className="flex-1 w-full h-full animate-in fade-in duration-300 min-h-0">
              <Comparison 
                originalUrl={getImageUrl(results.job_id, results.original_image_url)} 
                srUrl={getImageUrl(results.job_id, results.sr_image_url)} 
              />
            </div>
          )}

          {activeTab === 'uncertainty' && (
            <div className="flex-1 w-full h-full animate-in fade-in duration-300 min-h-0">
              <UncertaintyMap 
                jobId={results.job_id} 
                uncertaintyUrl={results.uncertainty_map_url} 
                reliabilityUrl={results.outputs?.reliability_map || results.reliability_map_url}
                reliabilityStats={results.reliability}
              />
            </div>
          )}

          {activeTab === 'metrics' && (
            <div className="flex-1 animate-in fade-in duration-300 h-full overflow-y-auto">
              <Metrics metrics={results.metrics} />
            </div>
          )}

          {activeTab === 'export' && (
            <div className="flex-1 animate-in fade-in duration-300 max-w-2xl mx-auto w-full h-full overflow-y-auto">
              <Export jobId={results.job_id} available={results.export_available} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Results;
