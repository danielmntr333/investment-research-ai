import { useState, useCallback } from 'react';
import { Upload } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { api } from '@/lib/api';
import { Button } from './ui/button';
import { useToast } from './ui/toast';

export function DocumentUpload() {
  const [dragActive, setDragActive] = useState(false);
  const { addDocument, removeDocument, setProcessing, updateDocumentStatus } = useStore();
  const { toast } = useToast();

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    await handleFiles(files);
  }, []);

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      await handleFiles(files);
    }
  };

  const handleFiles = async (files: File[]) => {
    for (const file of files) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
      if (!allowedTypes.includes(file.type)) {
        toast({
          title: 'Invalid file type',
          description: `${file.name} is not a supported file type.`,
          variant: 'destructive',
        });
        continue;
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast({
          title: 'File too large',
          description: `${file.name} exceeds the 10MB limit.`,
          variant: 'destructive',
        });
        continue;
      }

      // Upload
      await uploadFile(file);
    }
  };

  const uploadFile = async (file: File) => {
    const tempId = `temp_${Date.now()}`;
    
    // Add to state immediately
    addDocument({
      id: tempId,
      filename: file.name,
      file_type: file.type,
      file_size: file.size,
      uploaded_at: new Date().toISOString(),
      processed: false,
    });

    setProcessing(tempId, true);

    try {
      const { data, error } = await api.uploadDocument(file);

      if (error) {
        throw new Error(error);
      }

      // Remove temp document and add real one
      removeDocument(tempId);
      
      addDocument({
        id: data.id,
        filename: data.filename,
        file_type: data.file_type,
        file_size: data.file_size,
        uploaded_at: data.uploaded_at,
        processed: data.processed,
        metadata: data.metadata,
      });

      toast({
        title: 'Upload successful',
        description: `${file.name} ${data.processed ? 'has been processed' : 'is being processed'}.`,
      });

      // Poll for processing status if not yet processed
      if (!data.processed) {
        pollProcessingStatus(data.id);
      }
    } catch (error) {
      // Remove temp document on failure
      removeDocument(tempId);
      
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setProcessing(tempId, false);
    }
  };

  const pollProcessingStatus = async (docId: string) => {
    const maxAttempts = 30; // 30 seconds max
    let attempts = 0;

    const poll = setInterval(async () => {
      attempts++;

      if (attempts >= maxAttempts) {
        clearInterval(poll);
        setProcessing(docId, false);
        return;
      }

      const { data } = await api.getDocuments();
      const doc = data?.documents?.find((d: any) => d.id === docId);

      if (doc?.processed) {
        clearInterval(poll);
        updateDocumentStatus(docId, true);
        setProcessing(docId, false);
        
        toast({
          title: 'Processing complete',
          description: `${doc.filename} is ready to use.`,
        });
      }
    }, 1000);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
        dragActive
          ? 'border-foreground bg-accent scale-[1.01]'
          : 'border-border hover:border-foreground/50 hover:bg-accent/50'
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <Upload className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <p className="text-base font-semibold mb-1 tracking-tight">Drop files here</p>
      <p className="text-xs text-muted-foreground mb-4">
        or click to browse (PDF, Excel - max 10MB)
      </p>
      
      <input
        type="file"
        id="file-upload"
        className="hidden"
        onChange={handleFileInput}
        multiple
        accept=".pdf,.xlsx,.xls"
      />
      
      <Button asChild>
        <label htmlFor="file-upload" className="cursor-pointer">
          Choose Files
        </label>
      </Button>
    </div>
  );
}
