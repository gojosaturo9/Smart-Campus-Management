import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_CANDIDATES = [
  API_BASE,
  'http://127.0.0.1:8001',
  'http://localhost:8001',
].filter((value, index, values) => value && values.indexOf(value) === index);
const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

export default function FileUpload({ onChaptersDetected }) {
  const [uploading, setUploading] = useState(false);
  const [filename, setFilename] = useState('');
  const [error, setError] = useState('');
  const [progressMessage, setProgressMessage] = useState('');

  const waitForJob = async (apiBase, jobId) => {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      const response = await axios.get(`${apiBase}/jobs/${jobId}`);
      if (response.data.status === 'completed') return response.data.result;
      if (response.data.status === 'failed') {
        throw new Error(response.data.error || 'Upload processing failed.');
      }
      setProgressMessage(response.data.message || 'Processing material...');
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    throw new Error('Processing is taking too long. Check the backend and try again.');
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp'],
      'image/tiff': ['.tif', '.tiff'],
      'image/bmp': ['.bmp'],
    },
    maxFiles: 1,
    onDrop: async (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (!file) return;
      if (file.size > MAX_UPLOAD_BYTES) {
        setFilename(file.name);
        setError('File is too large. Upload a file up to 25 MB.');
        return;
      }

      setUploading(true);
      setError('');
      setFilename(file.name);
      setProgressMessage('Uploading material...');

      const formData = new FormData();
      formData.append('file', file);

      try {
        let response;
        let lastError;

        for (const apiBase of API_CANDIDATES) {
          try {
            response = await axios.post(`${apiBase}/upload/background`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
            });
            response.data = await waitForJob(apiBase, response.data.job_id);
            break;
          } catch (err) {
            lastError = err;
            if (err.response) break;
          }
        }

        if (!response && lastError) {
          throw lastError;
        }

        if (!response.data?.chapters?.length) {
          setError('File processed, but no chapters were detected.');
          return;
        }

        onChaptersDetected(response.data);
      } catch (err) {
        if (err.message && !err.response) {
          setError(err.message);
        } else if (err.response?.data?.detail) {
          setError(err.response.data.detail);
        } else if (err.response?.data) {
          setError(typeof err.response.data === 'string' ? err.response.data : 'Upload failed on the backend.');
        } else if (err.response) {
          setError(`Upload failed with status ${err.response.status}.`);
        } else if (err.request) {
          setError(`Cannot reach backend. Tried: ${API_CANDIDATES.join(', ')}`);
        } else {
          setError(err.message || 'Upload failed.');
        }
      } finally {
        setUploading(false);
        setProgressMessage('');
      }
    },
  });

  return (
    <div className="rounded-lg border border-[#d9ded2] bg-white p-4">
      <p className="text-sm font-semibold text-[#334155]">Upload notes</p>
      <div
        {...getRootProps()}
        className={`mt-3 flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-5 py-8 text-center transition ${
          isDragActive ? 'border-[#4f6f52] bg-[#eef5ea]' : 'border-[#b9c3b1] bg-[#fbfcf8] hover:bg-[#f4f7ee]'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#304c3a] text-lg font-bold text-white">
          +
        </div>
        <p className="mt-4 text-sm font-medium text-[#334155]">
          Drop a PDF, DOCX, or photo here
        </p>
        <p className="mt-1 text-xs text-[#6b7280]">Supports notes, scanned PDFs, and clear page photos</p>
      </div>

      {filename && <p className="mt-3 truncate text-sm text-[#55616c]">Selected: {filename}</p>}
      {uploading && (
        <div className="mt-3 rounded-md border border-[#bfdbfe] bg-[#eff6ff] p-3">
          <p className="text-sm font-medium text-[#315f95]">{progressMessage || 'Processing material...'}</p>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#dbeafe]">
            <div className="h-full w-2/3 animate-pulse rounded-full bg-[#315f95]" />
          </div>
        </div>
      )}
      {error && <p className="mt-2 text-sm font-medium text-[#b42318]">{error}</p>}
    </div>
  );
}
