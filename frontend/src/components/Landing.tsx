import React, { useEffect, useState } from 'react';
import { ArrowRight, Satellite, Layers, ShieldCheck, CheckCircle } from 'lucide-react';
import { checkHealth } from '../api/client';
import { HealthResponse } from '../types';

interface LandingProps {
  onStart: () => void;
}

const Landing: React.FC<LandingProps> = ({ onStart }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    checkHealth().then(setHealth).catch(console.error);
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`flex flex-col items-center justify-center min-h-[85vh] py-12 transition-all duration-1000 ease-out ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
      
      {/* Hero Section */}
      <div className="text-center max-w-5xl mb-24 relative z-10">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel text-cyan-400 text-[13px] font-mono font-medium tracking-wide mb-8 shadow-[0_0_20px_rgba(6,182,212,0.15)] border-cyan-500/30">
          <Satellite className="w-4 h-4" /> Team SpectraX — SIH 2026
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-6 tracking-tight leading-[1.1]">
          Reliability-Aware <br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-400 drop-shadow-[0_0_30px_rgba(6,182,212,0.4)]">
            Multispectral Super Resolution
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-slate-300 mb-8 font-light italic max-w-2xl mx-auto">
          "Resolution without Reliability is not Intelligence."
        </p>
        
        <p className="text-lg md:text-xl text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed font-light">
          The ultimate deep learning pipeline for enhancing satellite imagery spatial resolution, integrating rigorous pixel-wise uncertainty estimation for operational confidence.
        </p>

        <button 
          onClick={onStart}
          className="group relative inline-flex items-center justify-center px-14 py-6 font-black text-slate-900 transition-all duration-300 bg-cyan-400 border border-cyan-300 rounded-full hover:bg-cyan-300 shadow-[0_0_50px_rgba(6,182,212,0.6)] hover:shadow-[0_0_80px_rgba(6,182,212,0.8)] hover:-translate-y-1 overflow-hidden"
        >
          <span className="relative flex items-center gap-4 text-xl tracking-wider uppercase">
            Start Analysis <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform duration-300" />
          </span>
        </button>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl relative z-10 mb-16">
        <div className="glass-panel p-8 rounded-3xl hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(6,182,212,0.15)] hover:border-cyan-500/30 transition-all duration-500 group bg-black/40">
          <div className="w-14 h-14 bg-cyan-500/10 rounded-2xl flex items-center justify-center mb-6 border border-cyan-500/20 group-hover:scale-110 group-hover:bg-cyan-500/20 transition-all duration-500">
            <Layers className="text-cyan-400 w-7 h-7" />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Multispectral Super Resolution</h3>
          <p className="text-sm text-slate-400 leading-relaxed">Preserves radiometric integrity across VNIR and SWIR bands critical for NDVI and agricultural remote sensing indices.</p>
        </div>

        <div className="glass-panel p-8 rounded-3xl hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(99,102,241,0.15)] hover:border-indigo-500/30 transition-all duration-500 group bg-black/40">
          <div className="w-14 h-14 bg-indigo-500/10 rounded-2xl flex items-center justify-center mb-6 border border-indigo-500/20 group-hover:scale-110 group-hover:bg-indigo-500/20 transition-all duration-500">
            <ShieldCheck className="text-indigo-400 w-7 h-7" />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Pixel-Level Reliability</h3>
          <p className="text-sm text-slate-400 leading-relaxed">Leverages Monte Carlo Dropout to generate exact pixel-level confidence maps, preventing hallucinated structural artifacts.</p>
        </div>

        <div className="glass-panel p-8 rounded-3xl hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(16,185,129,0.15)] hover:border-emerald-500/30 transition-all duration-500 group bg-black/40">
          <div className="w-14 h-14 bg-emerald-500/10 rounded-2xl flex items-center justify-center mb-6 border border-emerald-500/20 group-hover:scale-110 group-hover:bg-emerald-500/20 transition-all duration-500">
            <CheckCircle className="text-emerald-400 w-7 h-7" />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Validation Consistency</h3>
          <p className="text-sm text-slate-400 leading-relaxed">Ensures the super-resolved output strictly obeys observation consistency via advanced downsampling metrics and PSNR validation.</p>
        </div>
      </div>

      {health && (
        <div className="mt-8 text-[10px] font-mono text-slate-600 uppercase tracking-widest flex items-center gap-4">
          <span>Engine v{health.version}</span>
          <span className="w-1 h-1 bg-slate-800 rounded-full"></span>
          <span>Compute: {health.device}</span>
          <span className="w-1 h-1 bg-slate-800 rounded-full"></span>
          <span className="flex items-center gap-1.5 text-emerald-500/70"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div> Neural Net Active</span>
        </div>
      )}
    </div>
  );
};

export default Landing;
