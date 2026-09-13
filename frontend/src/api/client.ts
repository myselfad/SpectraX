import axios from 'axios';
import {
  HealthResponse,
  UploadResponse,
  ProcessRequest,
  ProcessResponse,
  StatusResponse,
  ResultsResponse
} from '../types';

// Use empty string to leverage Vite proxy in development, 
// which avoids CORS preflight issues on large file uploads
// @ts-ignore
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 second timeout
});

export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await api.get('/api/health');
  return response.data;
};

export const uploadFile = async (file: File): Promise<UploadResponse> => {
  console.log("[API] uploadFile called, file:", file.name, "size:", file.size);
  const formData = new FormData();
  formData.append('file', file);
  console.log("[API] sending POST /api/upload...");
  try {
    const response = await api.post('/api/upload', formData, {
      timeout: 120000, // 2 min timeout for large files
    });
    console.log("[API] upload response:", response.status, response.data);
    return response.data;
  } catch (error: any) {
    console.error("[API] upload error:", error);
    if (error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail);
    }
    throw error;
  }
};

export const startProcessing = async (request: ProcessRequest): Promise<ProcessResponse> => {
  console.log("[API] startProcessing called:", request);
  try {
    const response = await api.post('/api/process', request);
    console.log("[API] process response:", response.status, response.data);
    return response.data;
  } catch (error: any) {
    if (error.response && error.response.data && error.response.data.detail) {
      throw new Error(error.response.data.detail);
    }
    throw error;
  }
};

export const getStatus = async (jobId: string): Promise<StatusResponse> => {
  const response = await api.get(`/api/status/${jobId}`);
  return response.data;
};

export const getResults = async (jobId: string): Promise<ResultsResponse> => {
  const response = await api.get(`/api/results/${jobId}`);
  return response.data;
};

export const getExportUrl = (jobId: string, fileType: string): string => {
  return `${API_BASE_URL}/api/export/${jobId}/${fileType}`;
};

export const getImageUrl = (jobId: string, filename: string): string => {
  if (filename.startsWith('/api/files/')) {
    return `${API_BASE_URL}${filename}`;
  }
  return `${API_BASE_URL}/api/files/${jobId}/${filename}`;
};
