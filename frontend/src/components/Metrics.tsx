import React from 'react';
import { MetricsResult } from '../types';
import { BarChart, CheckCircle } from 'lucide-react';

interface MetricsProps {
  metrics: MetricsResult | null;
}

const Metrics: React.FC<MetricsProps> = ({ metrics }) => {
  if (!metrics) {
    return <div className="text-center py-10 text-slate-500">Validation metrics not available.</div>;
  }

  const renderMetricCard = (label: string, value: number, desc: string) => (
    <div className="bg-black/20 border border-white/5 p-4 rounded-xl flex flex-col justify-between">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className="text-xl font-mono text-white mb-1">
        {value === 0.0 ? 'N/A' : value.toFixed(4)}
      </div>
      <div className="text-[10px] leading-tight text-slate-500">{desc}</div>
    </div>
  );

  return (
    <div className="space-y-6">
      {metrics.observation_consistency && (
        <section>
          <div className="flex items-center gap-2 mb-3 border-b border-white/10 pb-2">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Consistency</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {metrics.observation_consistency.consistency_psnr !== undefined && 
              renderMetricCard('Cons. PSNR', metrics.observation_consistency.consistency_psnr, 'Signal-to-Noise Ratio')
            }
            {metrics.observation_consistency.consistency_ssim !== undefined && 
              renderMetricCard('Cons. SSIM', metrics.observation_consistency.consistency_ssim, 'Structural Similarity')
            }
          </div>
        </section>
      )}

      <section>
        <div className="flex items-center gap-2 mb-3 border-b border-white/10 pb-2">
          <BarChart className="w-4 h-4 text-purple-500" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Reference</h3>
        </div>
        
        {metrics.reference_metrics ? (
          <div className="grid grid-cols-2 gap-3">
            {metrics.reference_metrics.psnr !== undefined && renderMetricCard('PSNR', metrics.reference_metrics.psnr, 'Peak Signal/Noise')}
            {metrics.reference_metrics.ssim !== undefined && renderMetricCard('SSIM', metrics.reference_metrics.ssim, 'Structural Sim')}
            {metrics.reference_metrics.sam !== undefined && renderMetricCard('SAM (Deg)', metrics.reference_metrics.sam, 'Spectral Angle')}
            {metrics.reference_metrics.ergas !== undefined && renderMetricCard('ERGAS', metrics.reference_metrics.ergas, 'Global Error')}
          </div>
        ) : (
          <div className="bg-white/5 border border-white/10 border-dashed rounded-lg p-4 text-center">
            <p className="text-xs text-slate-400">
              Reference metrics require ground-truth HR image.
            </p>
          </div>
        )}
      </section>
    </div>
  );
};

export default Metrics;
