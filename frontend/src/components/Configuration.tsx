import React, { useState } from 'react';
import { UploadResponse, ProcessRequest } from '../types';
import { Settings, Info, Play, ArrowLeft, Image as ImageIcon, Map, Layers } from 'lucide-react';

interface ConfigurationProps {
  uploadData: UploadResponse;
  onStart: (config: ProcessRequest) => void;
  onBack: () => void;
}

const Configuration: React.FC<ConfigurationProps> = ({ uploadData, onStart, onBack }) => {
  const [scaleFactor, setScaleFactor] = useState<number>(4);
  const [uncertaintyPasses, setUncertaintyPasses] = useState<number>(10);
  const [selectedBands, setSelectedBands] = useState<string[]>(uploadData.band_names || []);

  const handleStart = () => {
    if (!uploadData || !uploadData.job_id) return;
    
    const payload = {
      job_id: uploadData.job_id,
      scale_factor: scaleFactor,
      selected_bands: selectedBands,
      uncertainty_passes: uncertaintyPasses,
      processing_mode: uploadData.num_bands === 3 ? 'rgb_demo' : 'multispectral'
    };
    onStart(payload);
  };

  const toggleBand = (band: string) => {
    if (selectedBands.includes(band)) {
      if (selectedBands.length > 1) setSelectedBands(selectedBands.filter(b => b !== band));
    } else {
      setSelectedBands([...selectedBands, band]);
    }
  };

  return (
    <div className="max-w-5xl mx-auto mt-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button 
          onClick={onBack} 
          className="p-2.5 hover:bg-slate-200/50 dark:hover:bg-white/10 rounded-full transition-colors text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white">Analysis Configuration</h2>
          <div className="flex flex-wrap items-center gap-3 mt-2">
            <p className="text-slate-500 dark:text-slate-400 text-sm">Configure super-resolution parameters for <span className="font-mono text-slate-700 dark:text-slate-300">{uploadData.filename}</span></p>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${
              uploadData.num_bands === 3 
                ? 'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20'
                : 'bg-cyan-100 text-cyan-700 border-cyan-200 dark:bg-cyan-500/10 dark:text-cyan-400 dark:border-cyan-500/20'
            }`}>
              {uploadData.num_bands === 3 ? 'RGB Demo Mode — 3 bands' : `Multispectral Mode — ${uploadData.num_bands} bands`}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sidebar: Metadata */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel rounded-2xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-5 flex items-center gap-2 uppercase tracking-wider">
              <Info className="w-4 h-4 text-cyan-600 dark:text-cyan-400" /> Image Metadata
            </h3>
            <div className="space-y-4 text-sm">
              <div className="flex justify-between border-b border-slate-100 dark:border-white/5 pb-3">
                <span className="text-slate-500 dark:text-slate-400 flex items-center gap-2"><ImageIcon className="w-4 h-4 opacity-70"/> Dimensions</span>
                <span className="text-slate-800 dark:text-slate-200 font-mono font-medium">{uploadData.width} × {uploadData.height}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 dark:border-white/5 pb-3">
                <span className="text-slate-500 dark:text-slate-400 flex items-center gap-2"><Layers className="w-4 h-4 opacity-70"/> Bands</span>
                <span className="text-slate-800 dark:text-slate-200 font-mono font-medium">{uploadData.num_bands}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 dark:border-white/5 pb-3">
                <span className="text-slate-500 dark:text-slate-400 flex items-center gap-2"><Map className="w-4 h-4 opacity-70"/> CRS</span>
                <span className="text-slate-800 dark:text-slate-200 font-mono font-medium text-right max-w-[120px] truncate" title={uploadData.crs || 'N/A'}>
                  {uploadData.crs || 'N/A'}
                </span>
              </div>
              <div className="flex justify-between pb-1">
                <span className="text-slate-500 dark:text-slate-400">File Size</span>
                <span className="text-slate-800 dark:text-slate-200 font-mono font-medium">{(uploadData.file_size_bytes / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content: Configuration */}
        <div className="lg:col-span-2 space-y-8">
          <div className="glass-panel rounded-3xl p-8 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-8 flex items-center gap-2">
              <Settings className="w-5 h-5 text-cyan-600 dark:text-cyan-400" /> Processing Parameters
            </h3>
            
            <div className="space-y-10">
              {/* Scale Factor */}
              <div>
                <div className="flex justify-between items-end mb-4">
                  <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200">Target Scale Factor</label>
                  <span className="text-xs font-mono text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-500/10 px-2 py-1 rounded">
                    Output: {uploadData.width * scaleFactor} × {uploadData.height * scaleFactor}px
                  </span>
                </div>
                <div className="flex gap-4">
                  {[2, 4].map(scale => (
                    <button
                      key={scale}
                      onClick={() => setScaleFactor(scale)}
                      className={`flex-1 py-4 rounded-full border-2 text-sm font-bold transition-all duration-300 ${
                        scaleFactor === scale 
                          ? 'bg-slate-900 border-slate-900 text-white shadow-md dark:bg-cyan-600 dark:border-cyan-600' 
                          : 'bg-transparent border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-white/20'
                      }`}
                    >
                      {scale}× Super Resolution
                    </button>
                  ))}
                </div>
              </div>

              {/* Uncertainty Passes */}
              <div>
                <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4">
                  Uncertainty Estimation (Monte Carlo Passes)
                </label>
                <div className="flex items-center gap-6 bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/5">
                  <input 
                    type="range" 
                    min="2" max="30" step="1" 
                    value={uncertaintyPasses} 
                    onChange={(e) => setUncertaintyPasses(parseInt(e.target.value))}
                    className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-slate-900 dark:accent-cyan-500 outline-none"
                  />
                  <div className="flex flex-col items-end min-w-[3rem]">
                    <span className="font-mono text-lg font-bold text-slate-900 dark:text-cyan-400">{uncertaintyPasses}</span>
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider">Passes</span>
                  </div>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 leading-relaxed">
                  Higher passes yield highly accurate pixel-level uncertainty maps but increase total inference time proportionally.
                </p>
              </div>

              {/* Band Selection */}
              {uploadData.band_names && uploadData.band_names.length > 0 && (
                <div>
                  <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4">Target Bands</label>
                  <div className="flex flex-wrap gap-2.5">
                    {uploadData.band_names.map(band => {
                      const isSelected = selectedBands.includes(band);
                      return (
                        <button
                          key={band}
                          onClick={() => toggleBand(band)}
                          className={`px-4 py-2 rounded-full text-xs font-mono font-medium transition-all duration-300 ${
                            isSelected
                              ? 'bg-slate-800 text-white shadow-sm dark:bg-white/10 dark:text-cyan-50'
                              : 'bg-white border border-slate-200 text-slate-500 hover:border-slate-300 dark:bg-transparent dark:border-white/10 dark:text-slate-500 dark:hover:border-white/20'
                          }`}
                        >
                          {band}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button 
              onClick={handleStart}
              className="group flex items-center gap-3 px-8 py-4 bg-slate-900 hover:bg-slate-800 dark:bg-cyan-600 dark:hover:bg-cyan-500 text-white rounded-full font-bold transition-all duration-300 shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              Begin Processing
              <Play className="w-5 h-5 fill-current group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Configuration;
