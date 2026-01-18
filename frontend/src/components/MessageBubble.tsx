import { User, Bot, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useStore, type Message } from '@/store/useStore';
import { Button } from './ui/button';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { openSourceViewer } = useStore();
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 font-medium text-xs ${
        isUser ? 'bg-muted text-foreground' : 'bg-foreground text-background'
      }`}>
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          'AI'
        )}
      </div>

      {/* Content */}
      <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block rounded-lg px-3 py-2.5 max-w-[85%] ${
          isUser 
            ? 'bg-foreground text-background' 
            : 'bg-muted/50 text-foreground'
        }`}>
          {isUser ? (
            <p className="whitespace-pre-wrap text-[13px] leading-relaxed">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-p:leading-relaxed prose-p:text-[13px]">
              <ReactMarkdown
                components={{
                  a: ({ node, ...props }) => (
                    <a {...props} className="text-foreground underline underline-offset-2 hover:opacity-70 transition-opacity" target="_blank" rel="noopener noreferrer" />
                  ),
                  code: ({ node, inline, ...props }: any) => (
                    inline ? (
                      <code className="bg-accent px-1.5 py-0.5 rounded text-[12px] font-mono" {...props} />
                    ) : (
                      <code className="block bg-accent p-2 rounded text-[12px] font-mono overflow-x-auto" {...props} />
                    )
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Agent Trace */}
        {!isUser && message.agentTrace && message.agentTrace.length > 0 && (
          <details className="mt-2 group">
            <summary className="text-[11px] font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors list-none flex items-center gap-1">
              <span className="group-open:rotate-90 transition-transform">▶</span>
              View agent execution ({message.agentTrace.length} steps)
            </summary>
            <div className="mt-2 space-y-1 text-[11px] bg-muted/30 rounded-lg p-2">
              {message.agentTrace.map((step, idx) => (
                <div key={idx} className="flex items-center gap-2 text-muted-foreground">
                  <span className="font-semibold text-foreground">{step.agent}:</span>
                  <span>{step.action}</span>
                  <span className="opacity-60">({step.duration.toFixed(2)}s)</span>
                </div>
              ))}
            </div>
          </details>
        )}

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <details className="mt-2 group">
            <summary className="text-[11px] font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors list-none flex items-center gap-1">
              <span className="group-open:rotate-90 transition-transform">▶</span>
              View sources ({message.sources.length} documents)
            </summary>
            <div className="mt-2 space-y-2 bg-muted/30 rounded-lg p-2">
              {message.sources.map((source, idx) => (
                <div 
                  key={idx}
                  className="bg-background/50 rounded p-2 hover:bg-background/80 transition-colors cursor-pointer"
                  onClick={() => openSourceViewer(source)}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span className="text-[10px] font-semibold text-foreground bg-muted px-1.5 py-0.5 rounded flex-shrink-0">
                        {source.source_number}
                      </span>
                      <span className="text-[11px] font-medium text-foreground truncate">
                        {source.document_name}
                      </span>
                    </div>
                    {source.similarity !== undefined && (
                      <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {(source.similarity * 100).toFixed(0)}% match
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-muted-foreground line-clamp-2 leading-relaxed">
                    {source.content_preview || source.content}
                  </p>
                  <button className="text-[10px] text-foreground/70 hover:text-foreground flex items-center gap-1 mt-1">
                    <ExternalLink className="w-3 h-3" />
                    View full content
                  </button>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  );
}
