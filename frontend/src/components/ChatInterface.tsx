import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { api } from '@/lib/api';
import { MessageBubble } from './MessageBubble';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';

export function ChatInterface() {
  const [input, setInput] = useState('');
  const [streamingContent, setStreamingContent] = useState('');
  const [agentStatus, setAgentStatus] = useState<string>('');
  const [pipelineStep, setPipelineStep] = useState<string>('');
  const [startTime, setStartTime] = useState<number>(0);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  const {
    conversations,
    currentConversationId,
    addMessage,
    updateMessage,
    isLoading,
    setLoading,
  } = useStore();

  const currentConversation = conversations.find(
    (c) => c.id === currentConversationId
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages, streamingContent]);

  // Timer effect for elapsed time display
  useEffect(() => {
    if (isLoading && startTime > 0) {
      timerRef.current = setInterval(() => {
        setElapsedTime(Date.now() - startTime);
      }, 100);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isLoading, startTime]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !currentConversationId) return;

    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user' as const,
      content: input,
      timestamp: Date.now(),
    };

    // Add user message
    addMessage(currentConversationId, userMessage);
    setInput('');
    setLoading(true);
    setStartTime(Date.now());
    setElapsedTime(0);

    // Prepare assistant message ID (but don't create message yet)
    const assistantMessageId = `msg_${Date.now() + 1}`;
    let messageCreated = false;

    try {
      // Stream response
      let fullContent = '';
      const agentSteps: any[] = [];
      let sources: any[] = [];
      
      for await (const event of api.streamMessage(input, currentConversationId)) {
        // Handle pipeline step progress
        if (typeof event === 'object' && event.type === 'pipeline_step') {
          const stepIcons: Record<string, string> = {
            query_transform: '🔄',
            retrieval: '🔍',
            reranking: '📊',
            generation: '✨',
          };
          const icon = stepIcons[event.step] || '⚙️';
          
          if (event.status === 'start') {
            setPipelineStep(`${icon} ${event.message || event.step}...`);
          } else if (event.status === 'complete') {
            // Show completion briefly
            if (event.data?.chunks_found) {
              setPipelineStep(`${icon} Found ${event.data.chunks_found} relevant chunks`);
            } else if (event.data?.final_chunks) {
              setPipelineStep(`${icon} Prioritized to ${event.data.final_chunks} best matches`);
            }
            // Clear after a moment to show next step
            setTimeout(() => setPipelineStep(''), 500);
          }
        }
        // Handle agent status updates
        else if (typeof event === 'object' && event.type === 'agent_step') {
          const agentIcons: Record<string, string> = {
            supervisor: '🧭',
            research: '🔍',
            analysis: '📊',
            fact_checker: '✅',
            web_search: '🌐',
            synthesizer: '🔄',
          };
          const icon = agentIcons[event.agent] || '🤖';
          setAgentStatus(`${icon} ${event.agent} ${event.action}...`);
          setPipelineStep('');  // Clear pipeline step when agent takes over
          agentSteps.push(event);
        }
        // Handle sources found
        else if (typeof event === 'object' && event.type === 'sources_found') {
          sources = event.sources || [];
          setPipelineStep('📚 Sources ready');
          setTimeout(() => setPipelineStep(''), 500);
        }
        // Handle final answer with sources
        else if (typeof event === 'object' && event.type === 'final_answer') {
          fullContent = event.answer;
          sources = event.sources || [];
          setStreamingContent(fullContent);
          setPipelineStep('');
          setAgentStatus('');
          
          // Create or update message with complete data
          if (!messageCreated) {
            addMessage(currentConversationId, {
              id: assistantMessageId,
              role: 'assistant' as const,
              content: fullContent,
              sources: sources,
              agentTrace: agentSteps.length > 0 ? agentSteps : undefined,
              timestamp: Date.now(),
              metadata: {
                confidence_score: event.confidence_score,
                execution_time: event.execution_time,
                ...(event.metadata || {})
              }
            });
            messageCreated = true;
          } else {
            updateMessage(currentConversationId, assistantMessageId, {
              content: fullContent,
              sources: sources,
              agentTrace: agentSteps.length > 0 ? agentSteps : undefined,
              metadata: {
                confidence_score: event.confidence_score,
                execution_time: event.execution_time,
                ...(event.metadata || {})
              }
            });
          }
        }
        // Handle token streaming (character by character)
        else if (typeof event === 'string') {
          fullContent += event;
          setStreamingContent(fullContent);
          setPipelineStep('');  // Clear pipeline step when content starts flowing
          
          // Create message on first token if not created yet
          if (!messageCreated) {
            addMessage(currentConversationId, {
              id: assistantMessageId,
              role: 'assistant' as const,
              content: fullContent,
              timestamp: Date.now(),
            });
            messageCreated = true;
          } else {
            // Update message in real-time
            updateMessage(currentConversationId, assistantMessageId, {
              content: fullContent,
              sources: sources,
              agentTrace: agentSteps.length > 0 ? agentSteps : undefined,
            });
          }
        }
      }

      setStreamingContent('');
      setAgentStatus('');
      setPipelineStep('');
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Provide user-friendly error message
      let errorMessage = 'Sorry, I encountered an error while processing your request.';
      if (error instanceof Error) {
        if (error.message.includes('fetch')) {
          errorMessage = 'Unable to connect to the server. Please check your connection and try again.';
        } else if (error.message.includes('timeout')) {
          errorMessage = 'The request took too long. Please try a simpler query or try again later.';
        } else {
          errorMessage = `Error: ${error.message}`;
        }
      }
      
      // Create error message if message wasn't created yet
      if (!messageCreated) {
        addMessage(currentConversationId, {
          id: assistantMessageId,
          role: 'assistant' as const,
          content: errorMessage,
          timestamp: Date.now(),
        });
      } else {
        updateMessage(currentConversationId, assistantMessageId, {
          content: errorMessage,
        });
      }
      setAgentStatus('');
      setPipelineStep('');
      setStreamingContent('');
    } finally {
      setLoading(false);
      setStartTime(0);
      setElapsedTime(0);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {currentConversation?.messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {/* AI Thinking/Processing Indicator - only show when loading and no content yet */}
        {isLoading && (pipelineStep || agentStatus) && !streamingContent && (
          <div className="flex items-start gap-3 animate-in fade-in-50 duration-300">
            {/* AI Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-xs shadow-lg shadow-blue-500/20">
              <div className="animate-pulse">AI</div>
            </div>
            
            {/* Processing Status Card */}
            <div className="flex-1 max-w-[85%]">
              <div className="bg-gradient-to-r from-muted/40 to-muted/20 backdrop-blur-sm rounded-2xl px-4 py-3 border border-border/40 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    {/* Animated thinking dots */}
                    <div className="flex gap-1">
                      <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1000ms' }}></div>
                      <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1000ms' }}></div>
                      <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1000ms' }}></div>
                    </div>
                    
                    {/* Status text */}
                    <div className="flex flex-col gap-0.5 min-w-0">
                      <span className="text-sm font-medium text-foreground truncate">
                        {pipelineStep || agentStatus}
                      </span>
                      {elapsedTime > 0 && (
                        <span className="text-xs text-muted-foreground font-mono">
                          {(elapsedTime / 1000).toFixed(1)}s elapsed
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Streaming text with typing cursor */}
        {isLoading && streamingContent && (
          <div className="flex items-start gap-3 animate-in fade-in duration-300">
            {/* AI Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-xs shadow-lg shadow-blue-500/20">
              AI
            </div>
            
            {/* Streaming content bubble */}
            <div className="flex-1 max-w-[85%]">
              <div className="bg-muted/60 backdrop-blur-sm rounded-2xl px-4 py-2.5 border border-border/50 shadow-sm">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <div className="whitespace-pre-wrap text-[13px] leading-relaxed">
                    {streamingContent}
                    <span 
                      className="inline-block w-0.5 h-4 bg-blue-500 ml-0.5 animate-pulse" 
                      style={{ 
                        animation: 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        verticalAlign: 'baseline'
                      }} 
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border px-4 py-3 bg-card/50 backdrop-blur-sm">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-2 items-end">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              className="flex-1 min-h-[40px] max-h-[200px] resize-none text-[13px]"
              disabled={isLoading}
            />
            <Button
              type="submit"
              disabled={isLoading || !input.trim()}
              size="icon"
              className="h-[40px] w-[40px] shrink-0"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
