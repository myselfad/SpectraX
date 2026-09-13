import React, { useState, useRef, MouseEvent as ReactMouseEvent, TouchEvent as ReactTouchEvent } from 'react';
import { ScanSearch } from 'lucide-react';

interface ComparisonProps {
  originalUrl: string;
  srUrl: string;
}

const Comparison: React.FC<ComparisonProps> = ({ originalUrl, srUrl }) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = (clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percentage = (x / rect.width) * 100;
    setSliderPosition(percentage);
  };

  const onMouseMove = (e: ReactMouseEvent) => handleMove(e.clientX);
  const onTouchMove = (e: ReactTouchEvent) => handleMove(e.touches[0].clientX);

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex justify-between text-sm font-mono mb-3 text-slate-500 dark:text-slate-400 px-4 pt-4 absolute w-full z-20 pointer-events-none">
        <span className="flex items-center gap-1 bg-black/60 px-3 py-1.5 rounded-lg border border-white/10 backdrop-blur-md shadow-lg text-white font-bold text-xs"><ScanSearch className="w-3 h-3 text-slate-400"/> Before (Original Input)</span>
        <span className="flex items-center gap-1 bg-cyan-900/60 px-3 py-1.5 rounded-lg border border-cyan-500/30 backdrop-blur-md shadow-lg text-cyan-100 font-bold text-xs">After (Super-Resolved)</span>
      </div>
      
      <div 
        ref={containerRef}
        className="relative flex-1 w-full h-full cursor-ew-resize select-none bg-black/40"
        onMouseMove={onMouseMove}
        onTouchMove={onTouchMove}
        onMouseLeave={() => setSliderPosition(50)}
      >
        {/* Base Image (SR - Right side/After) */}
        <img 
          src={srUrl} 
          alt="Super Resolved" 
          className="absolute inset-0 w-full h-full object-contain pointer-events-none"
        />

        {/* Overlay Image (Original - Left side/Before) */}
        <div 
          className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden"
          style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
        >
          <img 
            src={originalUrl} 
            alt="Original" 
            className="absolute inset-0 w-full h-full object-contain"
          />
          {/* Border for the slider edge */}
          <div className="absolute top-0 bottom-0 right-0 w-0.5 bg-cyan-500/50"></div>
        </div>

        {/* Slider Line */}
        <div 
          className="absolute top-0 bottom-0 w-1 bg-cyan-400 flex items-center justify-center pointer-events-none shadow-[0_0_15px_rgba(6,182,212,0.8)] z-10"
          style={{ left: `calc(${sliderPosition}% - 2px)` }}
        >
          <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center border-2 border-cyan-500 pointer-events-auto">
            <div className="flex gap-1">
              <div className="w-0.5 h-3 bg-slate-800 rounded-full"></div>
              <div className="w-0.5 h-3 bg-slate-800 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Comparison;
