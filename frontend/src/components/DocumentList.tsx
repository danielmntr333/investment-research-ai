import { useState } from 'react';
import { FileText, Trash2, CheckCircle, Loader2 } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { api } from '@/lib/api';
import { Button } from './ui/button';
import { useToast } from './ui/toast';

export function DocumentList() {
  const { documents, removeDocument, isProcessing } = useStore();
  const { toast } = useToast();
  const [processingSteps, setProcessingSteps] = useState<Record<string, string>>({});

  const handleDelete = async (id: string, filename: string) => {
    if (!confirm(`Delete ${filename}?`)) return;

    // If it's a temp document (failed upload), just remove from store
    if (id.startsWith('temp_')) {
      removeDocument(id);
      toast({
        title: 'Document removed',
        description: `${filename} has been removed.`,
      });
      return;
    }

    // Otherwise, delete from backend
    const { error } = await api.deleteDocument(id);

    if (error) {
      toast({
        title: 'Delete failed',
        description: error,
        variant: 'destructive',
      });
      return;
    }

    removeDocument(id);
    toast({
      title: 'Document deleted',
      description: `${filename} has been removed.`,
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (documents.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <FileText className="w-12 h-12 mx-auto mb-3 opacity-40" />
        <p className="text-sm font-medium">No documents uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div key={doc.id} className="p-3 border border-border rounded-lg hover:bg-accent/50 transition-all">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <FileText className="w-5 h-5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-semibold truncate">{doc.filename}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  {formatFileSize(doc.file_size)} • {new Date(doc.uploaded_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Processing status */}
              {isProcessing[doc.id] ? (
                <Loader2 className="w-4 h-4 text-foreground animate-spin" />
              ) : doc.processed ? (
                <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-500" />
              ) : (
                <Loader2 className="w-4 h-4 text-yellow-600 dark:text-yellow-500 animate-spin" />
              )}

              {/* Delete button */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleDelete(doc.id, doc.filename)}
                className="text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
          
          {/* Processing steps - shown during upload */}
          {(isProcessing[doc.id] || !doc.processed) && (
            <div className="mt-3 space-y-1.5 text-[11px] pl-8">
              <div className="flex items-center gap-2 text-green-600 dark:text-green-500">
                <CheckCircle className="w-3 h-3" />
                <span>Parsing document...</span>
              </div>
              <div className="flex items-center gap-2 text-green-600 dark:text-green-500">
                <CheckCircle className="w-3 h-3" />
                <span>Extracting tables...</span>
              </div>
              <div className="flex items-center gap-2 text-foreground">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Chunking content...</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground opacity-50">
                <span className="w-3 h-3 rounded-full border-2 border-muted-foreground/30" />
                <span>Generating embeddings...</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground opacity-50">
                <span className="w-3 h-3 rounded-full border-2 border-muted-foreground/30" />
                <span>Storing in database...</span>
              </div>
            </div>
          )}
          
          {/* Completion message */}
          {doc.processed && doc.metadata?.chunks_count && (
            <p className="mt-2 text-[11px] text-green-600 dark:text-green-500 pl-8 font-medium">
              ✅ Processing complete ({doc.metadata.chunks_count} chunks created)
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
