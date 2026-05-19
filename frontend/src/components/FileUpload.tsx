import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUpload.css';

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  accept: string;
  label: string;
  description: string;
  icon: string;
}

export default function FileUpload({ onUpload, accept, label, description, icon }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setFileName(file.name);
    setUploading(true);
    setError(null);
    setUploaded(false);

    try {
      await onUpload(file);
      setUploaded(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Error al subir archivo');
      setUploaded(false);
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { [accept]: [] },
    multiple: false,
  });

  return (
    <div className="file-upload-card">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'drag-active' : ''} ${uploaded ? 'uploaded' : ''} ${error ? 'error' : ''}`}
      >
        <input {...getInputProps()} />
        
        <div className="upload-icon">{icon}</div>
        
        <div className="upload-label">{label}</div>
        <div className="upload-description">{description}</div>

        {uploading && (
          <div className="upload-status uploading">
            <div className="spinner"></div>
            <span>Procesando...</span>
          </div>
        )}

        {uploaded && fileName && (
          <div className="upload-status success">
            <span>✅ {fileName}</span>
          </div>
        )}

        {error && (
          <div className="upload-status error-message">
            <span>❌ {error}</span>
          </div>
        )}

        {!uploading && !uploaded && (
          <div className="upload-hint">
            Arrastra el archivo aquí o haz clic para seleccionar
          </div>
        )}
      </div>
    </div>
  );
}
