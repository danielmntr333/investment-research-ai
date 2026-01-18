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
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 font-semibold text-xs shadow-md ${
        isUser 
          ? 'bg-gradient-to-br from-slate-600 to-slate-800 text-white' 
          : 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
      }`}>
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          'AI'
        )}
      </div>

      {/* Content */}
      <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block rounded-2xl px-4 py-2.5 max-w-[85%] ${
          isUser 
            ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-md' 
            : 'bg-muted/60 backdrop-blur-sm text-foreground border border-border/50'
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
            <summary className="text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors list-none flex items-center gap-2 select-none">
              <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              <span className="flex items-center gap-1.5">
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white text-[9px] font-bold">
                  {message.agentTrace.length}
                </span>
                Agent execution trace
              </span>
            </summary>
            <div className="mt-3 space-y-2 bg-gradient-to-br from-muted/50 to-muted/30 backdrop-blur-sm rounded-xl p-3 border border-border/50">
              {message.agentTrace.map((step, idx) => {
                const agentIcons: Record<string, string> = {
                  supervisor: '🧭',
                  research: '🔍',
                  analysis: '📊',
                  fact_checker: '✅',
                  web_search: '🌐',
                  synthesizer: '🔄',
                };
                const icon = agentIcons[step.agent] || '🤖';
                
                return (
                  <div key={idx} className="flex items-start gap-2.5 text-xs bg-background/50 rounded-lg p-2.5 hover:bg-background/80 transition-colors">
                    <span className="text-lg flex-shrink-0">{icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-semibold text-foreground capitalize">{step.agent}</span>
                        <span className="text-muted-foreground/60">•</span>
                        <span className="text-muted-foreground text-[11px] font-mono">
                          {step.duration?.toFixed(2) || '0.00'}s
                        </span>
                      </div>
                      <span className="text-muted-foreground block">{step.action}</span>
                    </div>
                  </div>
                );
              })}
              <div className="pt-2 border-t border-border/30 flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground">Total execution time</span>
                <span className="font-mono font-semibold text-foreground">
                  {message.agentTrace.reduce((sum, step) => sum + (step.duration || 0), 0).toFixed(2)}s
                </span>
              </div>
            </div>
          </details>
        )}

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <details className="mt-2 group">
            <summary className="text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground transition-colors list-none flex items-center gap-2 select-none">
              <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              <span className="flex items-center gap-1.5">
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-white text-[9px] font-bold">
                  {message.sources.length}
                </span>
                Sources
              </span>
            </summary>
            <div className="mt-3 space-y-2 bg-gradient-to-br from-muted/50 to-muted/30 backdrop-blur-sm rounded-xl p-3 border border-border/50">
              {message.sources.map((source, idx) => (
                <div 
                  key={idx}
                  className="bg-background/60 rounded-lg p-3 hover:bg-background/90 transition-all cursor-pointer border border-border/30 hover:border-border/60 hover:shadow-sm group/source"
                  onClick={() => openSourceViewer(source)}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span className="inline-flex items-center justify-center w-6 h-6 text-[10px] font-bold text-white bg-gradient-to-br from-blue-500 to-indigo-600 rounded-md flex-shrink-0">
                        {source.source_number}
                      </span>
                      <span className="text-xs font-semibold text-foreground truncate">
                        {source.document_name}
                      </span>
                    </div>
                    {source.similarity !== undefined && (
                      <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 px-2 py-0.5 rounded-full whitespace-nowrap">
                        {(source.similarity * 100).toFixed(0)}% match
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed mb-2">
                    {source.content_preview || source.content}
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground group-hover/source:text-foreground transition-colors">
                    <span className="flex items-center gap-1">
                      <ExternalLink className="w-3 h-3" />
                      View full content
                    </span>
                    <span className="opacity-0 group-hover/source:opacity-100 transition-opacity">→</span>
                  </div>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  );
}
