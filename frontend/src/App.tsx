import { useProcessing } from './hooks/useProcessing';
import Landing from './components/Landing';
import Upload from './components/Upload';
import Configuration from './components/Configuration';
import Pipeline from './components/Pipeline';
import Results from './components/Results';
import { Satellite, Activity, Loader2, CheckCircle2 } from 'lucide-react';

function App() {
  const {
    currentStep,
    setCurrentStep,
    uploadData,
    statusData,
    resultsData,
    error,
    handleUpload,
    handleStartProcessing,
    reset
  } = useProcessing();

  const steps = [
    { id: 'landing', label: 'Start' },
    { id: 'upload', label: 'Upload' },
    { id: 'configure', label: 'Configure' },
    { id: 'processing', label: 'Process' },
    { id: 'results', label: 'Results' }
  ];

  const currentStepIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <div className="min-h-screen transition-colors duration-500 ease-in-out relative overflow-hidden font-sans selection:bg-cyan-500/30">
      
      {/* Global Satellite Background */}
      <div className="fixed inset-0 z-[-2] w-full h-full bg-[#05080f] overflow-hidden pointer-events-none">
        
        {/* Bright Stars Layer */}
        <div className="absolute inset-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-70 animate-[pulse_10s_ease-in-out_infinite]"></div>
        
        {/* Deep Space / Galaxy Layer */}
        <img 
          src="https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?q=80&w=3000&auto=format&fit=crop" 
          alt="Stars" 
          className="absolute inset-0 w-full h-full object-cover opacity-80 mix-blend-lighten"
        />
        
        {/* Earth Layer */}
        <img 
          src="https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?q=80&w=2500&auto=format&fit=crop" 
          alt="Earth from space" 
          className="absolute inset-0 w-full h-full object-cover opacity-90 scale-105 mix-blend-lighten"
        />

        {/* Orbiting Satellites (Real Images) */}
        <div className="absolute inset-0 flex items-center justify-center">
          
          <div className="absolute w-0 h-0 animate-orbit-1">
            <div className="relative flex items-center justify-center">
              <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Suomi_NPP_satellite.png/800px-Suomi_NPP_satellite.png" alt="Satellite" className="w-24 h-24 object-contain absolute opacity-90 drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]" />
            </div>
          </div>
          
          <div className="absolute w-0 h-0 animate-orbit-2">
            <div className="relative flex items-center justify-center">
              <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Hubble_Space_Telescope_model.png/800px-Hubble_Space_Telescope_model.png" alt="Hubble Telescope" className="w-32 h-32 object-contain absolute opacity-100 drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]" />
            </div>
          </div>
          
          <div className="absolute w-0 h-0 animate-orbit-3">
            <div className="relative flex items-center justify-center">
              <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Jason-3_satellite_model.png/800px-Jason-3_satellite_model.png" alt="Jason-3" className="w-16 h-16 object-contain absolute opacity-100 scale-x-[-1] drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]" />
            </div>
          </div>

        </div>
        
        {/* Dimming Overlay to ensure text readability */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#05080f]/40 via-[#05080f]/60 to-[#05080f]/90"></div>
      </div>
      <div className="fixed inset-0 bg-grid-pattern opacity-10 pointer-events-none z-0"></div>
      
      <header className="glass-panel sticky top-0 z-50 border-b-0 border-b-white/5">
        <div className="max-w-7xl mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer group" onClick={reset}>
            <div className="bg-cyan-500/10 p-1.5 rounded-xl border border-cyan-500/20 group-hover:bg-cyan-500/20 transition-all duration-300">
              <Satellite className="text-cyan-600 dark:text-cyan-400 w-6 h-6" />
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                SpectraX
              </h1>
            </div>
          </div>
          
          {/* Elegant Stepper */}
          <nav className="hidden md:flex items-center gap-1.5">
            {steps.map((step, idx) => {
              const isActive = idx === currentStepIndex;
              const isPast = idx < currentStepIndex;
              
              return (
                <div key={step.id} className="flex items-center">
                  <div className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full transition-all duration-300 ${
                    isActive 
                      ? 'bg-slate-900 dark:bg-cyan-500/15 text-white dark:text-cyan-400 shadow-sm' 
                      : isPast 
                        ? 'text-slate-500 dark:text-slate-400' 
                        : 'text-slate-400 dark:text-slate-600'
                  }`}>
                    {isPast && <CheckCircle2 className="w-3.5 h-3.5" />}
                    {step.label}
                  </div>
                  {idx < steps.length - 1 && (
                    <div className={`w-6 h-[1px] mx-1 transition-colors duration-300 ${isPast ? 'bg-slate-900 dark:bg-cyan-500/50' : 'bg-slate-200 dark:bg-white/10'}`} />
                  )}
                </div>
              );
            })}
          </nav>
          
          <div className="flex items-center gap-4">
            {/* Non-clickable AI Engine Ready Status */}
            <div className="hidden sm:flex items-center gap-2 text-[11px] font-mono font-medium text-slate-600 dark:text-emerald-400/90 px-2.5 py-1 rounded-full border border-slate-200 dark:border-emerald-400/20 bg-white/50 dark:bg-emerald-400/5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500 dark:bg-emerald-400"></span>
              </span>
              AI Engine Ready
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-6 py-12 relative z-10">
        {error && (
          <div className="mb-8 p-4 glass-panel border-red-500/30 rounded-xl text-red-600 dark:text-red-400 flex items-start gap-3 animate-in fade-in slide-in-from-top-4 duration-300">
            <Activity className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold mb-1">System Error</h3>
              <p className="text-sm opacity-90">{error}</p>
            </div>
          </div>
        )}

        <div className="transition-all duration-500 ease-in-out">
          {currentStep === 'landing' && <Landing onStart={() => setCurrentStep('upload')} />}
          {currentStep === 'upload' && <Upload onUpload={handleUpload} />}
          {currentStep === 'configure' && uploadData && (
            <Configuration 
              uploadData={uploadData} 
              onStart={handleStartProcessing} 
              onBack={() => setCurrentStep('upload')} 
            />
          )}
          {currentStep === 'processing' && (
            statusData ? <Pipeline status={statusData} /> : <div className="flex flex-col items-center justify-center min-h-[400px]"><Loader2 className="w-10 h-10 text-cyan-600 dark:text-cyan-500 animate-spin mb-4" /><p className="text-slate-500 dark:text-slate-400 font-medium">Initializing Neural Engine...</p></div>
          )}
          {currentStep === 'results' && resultsData && (
            <Results results={resultsData} info={resultsData.processing_info || null} onNew={() => reset()} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
