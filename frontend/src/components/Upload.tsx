import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, Loader2, Image as ImageIcon } from 'lucide-react';

interface UploadProps {
  onUpload: (file: File) => Promise<void>;
}

const Upload: React.FC<UploadProps> = ({ onUpload }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    setError(null);
    setIsUploading(true);

    try {
      await onUpload(file);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (Array.isArray(detail) ? JSON.stringify(detail) : (err.message || 'Error uploading file'));
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8 text-center">
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-3">Upload Imagery</h2>
        <p className="text-slate-500 dark:text-slate-400 text-base">Provide a low-resolution satellite image for neural super-resolution processing.</p>
      </div>

      <div 
        className={`relative overflow-hidden border-2 border-dashed rounded-3xl p-14 text-center transition-all duration-300 ${
          isDragging 
            ? 'border-cyan-500 bg-cyan-50 dark:bg-cyan-500/10 scale-[1.02] shadow-xl' 
            : 'border-slate-300 dark:border-white/10 glass-panel hover:border-slate-400 dark:hover:border-white/20 hover:shadow-lg'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          className="hidden" 
          ref={fileInputRef} 
          onChange={handleFileInput}
          accept=".tif,.tiff,.png,.jpg,.jpeg"
          disabled={isUploading}
        />
        
        {isUploading ? (
          <div className="flex flex-col items-center justify-center space-y-6">
            <Loader2 className="w-14 h-14 text-cyan-600 dark:text-cyan-500 animate-spin" />
            <div className="space-y-1">
              <p className="text-slate-900 dark:text-white font-medium text-lg">Uploading and extracting metadata...</p>
              <p className="text-slate-500 dark:text-cyan-400/70 font-mono text-sm">Please do not close this window</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-6 cursor-pointer group">
            <div className="w-20 h-20 bg-slate-100 dark:bg-white/5 rounded-full flex items-center justify-center group-hover:bg-slate-200 dark:group-hover:bg-white/10 group-hover:scale-110 transition-all duration-300 shadow-sm">
              <UploadCloud className="w-10 h-10 text-cyan-600 dark:text-cyan-400" />
            </div>
            <div>
              <p className="text-slate-900 dark:text-white font-semibold text-lg mb-1">Click to browse or drag file here</p>
              <p className="text-slate-500 dark:text-slate-400 text-sm">Supports GeoTIFF, PNG, JPG up to 50MB</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-6 p-4 glass-panel border-red-500/30 rounded-2xl text-red-600 dark:text-red-400 flex items-start gap-3 animate-in fade-in slide-in-from-top-2">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      <div className="mt-8 glass-panel rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-300 mb-4 flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-cyan-600 dark:text-cyan-500" /> Supported Data Types
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start gap-3">
            <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 mt-2"></div>
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Multispectral GeoTIFFs</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Up to 8 bands, full georeferencing preserved</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2"></div>
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Standard RGB Imagery</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">PNG, JPG/JPEG formats supported in Demo Mode</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;
