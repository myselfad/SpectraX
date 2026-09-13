import React from 'react';
import { Download, FileImage, Map, FileJson, Layers } from 'lucide-react';
import { getExportUrl } from '../api/client';

interface ExportProps {
  jobId: string;
  available: string[];
}

const Export: React.FC<ExportProps> = ({ jobId, available }) => {
  const getExportDetails = (type: string) => {
    switch (type) {
      case 'sr_image': return { icon: <FileImage className="w-6 h-6 text-cyan-400" />, label: 'Super-Resolved Output (PNG)', desc: 'Visual representation, lossy compression.' };
      case 'sr_geotiff': return { icon: <Map className="w-6 h-6 text-emerald-400" />, label: 'Super-Resolved Output (GeoTIFF)', desc: 'Preserves georeferencing and exact data values.' };
      case 'uncertainty_map': return { icon: <Layers className="w-6 h-6 text-amber-400" />, label: 'Uncertainty Heatmap (PNG)', desc: 'Visual map of prediction variance.' };
      case 'metrics_report': return { icon: <FileJson className="w-6 h-6 text-purple-400" />, label: 'Processing Report (JSON)', desc: 'Complete metadata, parameters, and metrics.' };
      case 'original': return { icon: <FileImage className="w-6 h-6 text-slate-500 dark:text-slate-400" />, label: 'Original Input', desc: 'The original uploaded file.' };
      default: return { icon: <Download className="w-6 h-6 text-slate-900 dark:text-white" />, label: type, desc: '' };
    }
  };

  const handleDownload = async (type: string) => {
    const url = getExportUrl(jobId, type);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error('Network response was not ok');
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = blobUrl;
      
      // Determine file extension based on type
      let ext = '.bin';
      if (type.includes('image') || type.includes('map') || type === 'original') ext = '.png';
      if (type.includes('geotiff')) ext = '.tif';
      if (type.includes('report')) ext = '.json';
      
      a.download = `spectrax_${jobId}_${type}${ext}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    } catch (e) {
      console.error('Download failed, falling back to new tab', e);
      window.open(url, '_blank');
    }
  };

  if (!available || available.length === 0) {
    return <div className="p-8 text-center text-slate-500 dark:text-slate-500">No export files available.</div>;
  }

  return (
    <div className="max-w-3xl">
      <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Data Export & Products</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {available.map(type => {
          const details = getExportDetails(type);
          return (
            <div key={type} className="bg-slate-100 dark:bg-space-950 border border-slate-200 dark:border-white/10 rounded-xl p-5 flex flex-col items-start gap-4 hover:border-space-600 transition-colors">
              <div className="flex items-start gap-4 w-full">
                <div className="bg-slate-50 dark:bg-space-900 p-3 rounded-lg border border-slate-200 dark:border-white/10 shrink-0">
                  {details.icon}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-800 dark:text-slate-200">{details.label}</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">{details.desc}</p>
                </div>
              </div>
              <button 
                onClick={() => handleDownload(type)}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 mt-2 bg-slate-200 dark:bg-white/10 hover:bg-space-700 text-cyan-400 rounded border border-slate-300 dark:border-white/20 transition-colors font-medium text-sm"
              >
                <Download className="w-4 h-4" /> Download
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Export;
