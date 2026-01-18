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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
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

    // Create placeholder for assistant message
    const assistantMessageId = `msg_${Date.now() + 1}`;
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant' as const,
      content: '',
      timestamp: Date.now(),
    };
    addMessage(currentConversationId, assistantMessage);

    try {
      // Stream response
      let fullContent = '';
      const agentSteps: any[] = [];
      let sources: any[] = [];
      
      for await (const event of api.streamMessage(input, currentConversationId)) {
        // Handle agent status updates
        if (typeof event === 'object' && event.type === 'agent_step') {
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
          agentSteps.push(event);
        } else if (typeof event === 'object' && event.type === 'final_answer') {
          // Handle final answer with sources
          fullContent = event.answer;
          sources = event.sources || [];
          setStreamingContent(fullContent);
          
          // Update message with complete data
          updateMessage(currentConversationId, assistantMessageId, {
            content: fullContent,
            sources: sources,
            agentTrace: agentSteps.length > 0 ? agentSteps : undefined,
            metadata: {
              confidence_score: event.confidence_score,
              execution_time: event.execution_time
            }
          });
        } else if (typeof event === 'string') {
          // Handle content chunks
          fullContent += event;
          setStreamingContent(fullContent);
          
          // Update message in real-time
          updateMessage(currentConversationId, assistantMessageId, {
            content: fullContent,
            agentTrace: agentSteps.length > 0 ? agentSteps : undefined,
          });
        }
      }

      setStreamingContent('');
      setAgentStatus('');
    } catch (error) {
      console.error('Error sending message:', error);
      updateMessage(currentConversationId, assistantMessageId, {
        content: 'Sorry, I encountered an error. Please try again.',
      });
      setAgentStatus('');
    } finally {
      setLoading(false);
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
        
        {/* Agent status indicator */}
        {isLoading && agentStatus && !streamingContent && (
          <div className="flex items-start gap-3 animate-in fade-in duration-200">
            <div className="w-7 h-7 rounded-lg bg-foreground flex items-center justify-center text-background font-medium text-xs">
              AI
            </div>
            <div className="flex-1 bg-muted/30 rounded-lg px-3 py-2.5 border border-border/50">
              <div className="flex items-center gap-2 text-[13px] text-muted-foreground">
                <div className="w-1.5 h-1.5 rounded-full bg-foreground animate-pulse" />
                {agentStatus}
              </div>
            </div>
          </div>
        )}
        
        {/* Streaming indicator */}
        {isLoading && streamingContent && (
          <div className="flex items-start gap-3 animate-in fade-in duration-300">
            <div className="w-7 h-7 rounded-lg bg-foreground flex items-center justify-center text-background font-medium text-xs">
              AI
            </div>
            <div className="flex-1 bg-muted/50 rounded-lg px-3 py-2.5">
              <div className="prose prose-sm max-w-none text-[13px]">
                {streamingContent}
                <span className="inline-block w-1 h-4 bg-foreground animate-pulse ml-1 rounded-sm" />
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
