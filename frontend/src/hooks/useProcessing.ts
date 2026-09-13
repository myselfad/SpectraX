import { useState, useEffect, useCallback } from 'react';
import {
  UploadResponse,
  ProcessRequest,
  StatusResponse,
  ResultsResponse,
  AppStep
} from '../types';
import { uploadFile, startProcessing, getStatus, getResults } from '../api/client';

export const useProcessing = () => {
  const [currentStep, setCurrentStep] = useState<AppStep>('landing');
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const [processConfig, setProcessConfig] = useState<ProcessRequest | null>(null);
  const [statusData, setStatusData] = useState<StatusResponse | null>(null);
  const [resultsData, setResultsData] = useState<ResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Wrap setCurrentStep with logging
  const goToStep = (step: AppStep) => {
    console.log(`[STEP] transitioning: ${currentStep} → ${step}`);
    setCurrentStep(step);
  };

  const handleUpload = async (file: File) => {
    try {
      setError(null);
      console.log("[UPLOAD-HOOK] calling uploadFile API...");
      const data = await uploadFile(file);
      console.log("[UPLOAD-HOOK] upload success, job_id:", data.job_id);
      console.log("[UPLOAD-HOOK] full response:", JSON.stringify(data));
      setUploadData(data);
      goToStep('configure');
    } catch (err: any) {
      console.error("[UPLOAD-HOOK] upload failed:", err);
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (Array.isArray(detail) ? JSON.stringify(detail) : (err.message || 'Upload failed'));
      setError(msg);
      throw err;
    }
  };

  const handleStartProcessing = async (config: ProcessRequest) => {
    try {
      setError(null);
      setProcessConfig(config);
      console.log("[PROCESS-HOOK] calling startProcessing API...", JSON.stringify(config));
      await startProcessing(config);
      console.log("[PROCESS-HOOK] process started successfully, transitioning to processing step");
      goToStep('processing');
    } catch (err: any) {
      console.error("[PROCESS-HOOK] process failed:", err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : (Array.isArray(detail) ? JSON.stringify(detail) : (err.message || 'Failed to start processing')));
    }
  };

  const pollStatus = useCallback(async () => {
    console.log(`[POLL] polling... uploadData?.job_id=${uploadData?.job_id}, currentStep=${currentStep}`);
    if (!uploadData?.job_id || currentStep !== 'processing') {
      console.log("[POLL] skipping poll (guard failed)");
      return;
    }

    try {
      console.log(`[POLL] GET /api/status/${uploadData.job_id}`);
      const status = await getStatus(uploadData.job_id);
      console.log(`[POLL] status: ${status.status}, progress: ${status.progress_percent}%`);
      setStatusData(status);

      if (status.status === 'completed') {
        console.log("[POLL] completed! fetching results...");
        const results = await getResults(uploadData.job_id);
        setResultsData(results);
        goToStep('results');
      } else if (status.status === 'failed') {
        console.error("[POLL] processing failed:", status.error);
        setError(status.error || 'Processing failed');
      }
    } catch (err: any) {
      console.error("[POLL] poll error:", err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : (Array.isArray(detail) ? JSON.stringify(detail) : (err.message || 'Failed to fetch status')));
    }
  }, [uploadData?.job_id, currentStep]);

  useEffect(() => {
    let intervalId: number | undefined;

    console.log(`[EFFECT] useEffect fired: currentStep=${currentStep}, statusData?.status=${statusData?.status}`);

    if (currentStep === 'processing' && statusData?.status !== 'failed') {
      console.log("[EFFECT] starting status polling interval (1.5s)");
      // Poll immediately, then on interval
      pollStatus();
      intervalId = window.setInterval(pollStatus, 1500);
    }

    return () => {
      if (intervalId) {
        console.log("[EFFECT] clearing interval");
        window.clearInterval(intervalId);
      }
    };
  }, [currentStep, pollStatus, statusData?.status]);

  const reset = () => {
    console.log("[RESET] resetting all state");
    setCurrentStep('landing');
    setUploadData(null);
    setProcessConfig(null);
    setStatusData(null);
    setResultsData(null);
    setError(null);
  };

  return {
    currentStep,
    setCurrentStep,
    uploadData,
    processConfig,
    statusData,
    resultsData,
    error,
    handleUpload,
    handleStartProcessing,
    reset,
  };
};
