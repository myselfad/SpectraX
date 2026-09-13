import React, { useEffect, useRef } from 'react';
import { StatusResponse } from '../types';
import { Check, Loader2, X, Clock, Zap, Server, FileSearch, Filter, Cpu, Play, Crosshair, BarChart, Download } from 'lucide-react';

interface PipelineProps {
  status: StatusResponse;
}

const Pipeline: React.FC<PipelineProps> = ({ status }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const formattedSteps = status.steps.map(s => ({
    ...s,
    displayName: s.name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }));

  const getStepIcon = (name: string, className: string) => {
    switch (name) {
      case 'input_validation': return <Server className={className} />;
      case 'metadata_extraction': return <FileSearch className={className} />;
      case 'band_selection': return <Filter className={className} />;
      case 'preprocessing': return <Cpu className={className} />;
      case 'super_resolution': return <Play className={className} />;
      case 'uncertainty_estimation': return <Crosshair className={className} />;
      case 'validation': return <BarChart className={className} />;
      case 'output_generation': return <Download className={className} />;
      default: return <Zap className={className} />;
    }
  };

  useEffect(() => {
    // Auto-scroll to the active element
    if (scrollRef.current) {
      const activeElement = scrollRef.current.querySelector('.is-running');
      if (activeElement) {
        activeElement.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
      }
    }
  }, [status.current_step]);

  return (
    <div className="max-w-6xl mx-auto mt-12 animate-in fade-in duration-500">
      <div className="glass-panel rounded-[2rem] p-8 md:p-12 shadow-2xl border border-white/10 relative bg-black/40 overflow-hidden">
        
        {/* Background Ambient Glow */}
        <div className="absolute top-0 left-1/2 w-[800px] h-[400px] bg-cyan-600/5 rounded-[100%] blur-[120px] pointer-events-none -translate-x-1/2 -translate-y-1/2"></div>

        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-16 gap-6 relative z-10">
          <div className="text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono font-medium tracking-wide mb-4">
              <Zap className="w-3 h-3 animate-pulse" /> NEURAL PIPELINE ACTIVE
            </div>
            <h2 className="text-4xl font-extrabold text-white mb-2 tracking-tight">AI Workflow</h2>
            <p className="text-xs text-slate-400 font-mono tracking-wider uppercase">Job ID: {status.job_id}</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-[10px] text-cyan-400/70 uppercase tracking-[0.2em] font-bold mb-1">Overall Progress</p>
              <div className="text-6xl font-black font-mono text-cyan-400 tabular-nums tracking-tighter drop-shadow-[0_0_20px_rgba(6,182,212,0.3)]">
                {Math.round(status.progress_percent)}<span className="text-3xl text-cyan-400/50">%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Horizontal Scrolling Workflow */}
        <div 
          ref={scrollRef}
          className="relative flex items-start overflow-x-auto pb-10 pt-4 px-4 snap-x snap-mandatory no-scrollbar"
          style={{ scrollbarWidth: 'thin', scrollbarColor: '#06b6d4 transparent' }}
        >
          <div className="flex relative z-10 mx-auto px-4 w-max">
            {formattedSteps.map((step, index) => {
              const isRunning = step.status === 'running';
              const isCompleted = step.status === 'completed';
              const isFailed = step.status === 'failed';

              return (
                <div key={index} className="relative flex-shrink-0 w-[160px]">
                  
                  {/* Connector Line to the next step */}
                  {index < formattedSteps.length - 1 && (
                    <div className="absolute top-[40px] left-[50%] w-[160px] h-1 bg-white/10 z-0 -translate-y-1/2">
                      <div className={`h-full bg-gradient-to-r from-cyan-600 to-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.8)] transition-all duration-1000 ease-in-out ${
                         isCompleted ? 'w-full' : 'w-0'
                      }`}></div>
                    </div>
                  )}

                  <div className={`flex flex-col items-center relative z-10 w-full group snap-center ${isRunning ? 'is-running' : ''}`}>
                    
                    {/* Node Orb */}
                    <div className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center transition-all duration-500 border-[3px] shadow-lg ${
                      isRunning 
                        ? 'bg-black border-cyan-400 shadow-[0_0_40px_rgba(6,182,212,0.8)] scale-110' 
                        : isCompleted 
                          ? 'bg-cyan-950 border-cyan-500 shadow-[0_0_20px_rgba(6,182,212,0.4)]' 
                          : isFailed 
                            ? 'bg-black border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.5)]'
                            : 'bg-[#0a0e17] border-white/10'
                    }`}>
                      
                      {/* Status Overlay Badge */}
                      <div className="absolute -top-2 -right-2">
                        {isRunning ? <Loader2 className="w-5 h-5 text-cyan-400 animate-spin drop-shadow-md" /> :
                         isCompleted ? <div className="bg-cyan-500 rounded-full p-0.5"><Check className="w-3 h-3 text-white" /></div> :
                         isFailed ? <div className="bg-red-500 rounded-full p-0.5"><X className="w-3 h-3 text-white" /></div> : null}
                      </div>

                      {/* Center Icon */}
                      {getStepIcon(step.name, `w-8 h-8 transition-colors duration-500 ${
                        isRunning ? 'text-cyan-400 animate-pulse' : 
                        isCompleted ? 'text-cyan-400' : 
                        isFailed ? 'text-red-400' : 
                        'text-slate-600'
                      }`)}
                    </div>
                    
                    {/* Label & Status */}
                    <div className="text-center mt-6 w-full h-16">
                      <h3 className={`font-bold text-[13px] leading-tight mb-1.5 transition-colors ${
                        isRunning ? 'text-white drop-shadow-md' : 
                        isCompleted ? 'text-slate-200' :
                        isFailed ? 'text-red-400' :
                        'text-slate-500'
                      }`}>
                        {step.displayName}
                      </h3>
                      
                      <div className="flex items-center justify-center h-4">
                        {isRunning && (
                          <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-400 animate-pulse">
                            Processing...
                          </span>
                        )}
                        {isCompleted && step.duration_ms !== null && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-500">
                            <Clock className="w-3 h-3" /> {(step.duration_ms / 1000).toFixed(1)}s
                          </span>
                        )}
                        {isFailed && step.message && (
                          <span className="text-[10px] font-medium text-red-500 truncate w-full px-2">
                            {step.message}
                          </span>
                        )}
                      </div>
                    </div>

                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Pipeline;
