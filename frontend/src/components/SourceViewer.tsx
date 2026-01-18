import { X } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { Button } from './ui/button';

export function SourceViewer() {
  const { isSourceViewerOpen, selectedSource, closeSourceViewer } = useStore();

  if (!isSourceViewerOpen || !selectedSource) return null;

  // Get content (support both new and legacy structure)
  const content = selectedSource.content_preview || selectedSource.content || '';
  const similarity = selectedSource.similarity ?? selectedSource.score ?? 0;
  const documentName = selectedSource.document_name || 'Unknown Document';

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 z-40"
        onClick={closeSourceViewer}
      />
      
      {/* Panel */}
      <div className="fixed right-0 top-0 bottom-0 w-full sm:max-w-2xl bg-white dark:bg-gray-900 shadow-xl z-50 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-foreground/10 text-foreground font-bold text-sm flex-shrink-0">
                  {selectedSource.source_number}
                </span>
                <h2 className="text-xl font-bold truncate">{documentName}</h2>
              </div>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span>
                  Relevance: <span className="font-medium text-foreground">{(similarity * 100).toFixed(1)}%</span>
                </span>
                {selectedSource.chunk_id && (
                  <span className="text-xs">
                    • Chunk: {selectedSource.chunk_id.slice(0, 8)}...
                  </span>
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={closeSourceViewer}
              className="flex-shrink-0"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Metadata */}
          {selectedSource.metadata && Object.keys(selectedSource.metadata).length > 0 && (
            <div className="bg-muted/50 rounded-lg p-4 mb-6">
              <h3 className="font-medium mb-3 text-sm">Document Information</h3>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                {Object.entries(selectedSource.metadata).map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-muted-foreground text-xs mb-0.5">{key}:</dt>
                    <dd className="font-medium text-foreground break-words">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Content */}
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <h3 className="text-base font-semibold mb-3">Content Excerpt</h3>
            <div className="bg-muted/30 dark:bg-muted/10 border border-border rounded-lg p-4 whitespace-pre-wrap text-sm leading-relaxed">
              {content}
            </div>
            <p className="text-xs text-muted-foreground mt-2 italic">
              This excerpt was used to generate the answer
            </p>
          </div>
          
          {/* Actions */}
          <div className="mt-6 flex gap-2">
            <Button variant="outline" size="sm" className="text-xs">
              View Full Document
            </Button>
            <Button variant="outline" size="sm" className="text-xs">
              Download PDF
            </Button>
            <Button variant="outline" size="sm" className="text-xs">
              Copy Content
            </Button>
          </div>

          {/* Footer info */}
          {selectedSource.chunk_id && (
            <div className="mt-6 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground">
                <span className="font-medium">Reference ID:</span> {selectedSource.chunk_id}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
