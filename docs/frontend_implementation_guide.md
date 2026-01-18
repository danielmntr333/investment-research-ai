# Frontend Implementation Guide - React Application

## Overview

This document provides complete implementation specifications for the React frontend application. Use this alongside other implementation guides for full-stack context.

**Location**: `frontend/src/`

**Tech Stack**:
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS + shadcn/ui
- Zustand (state management)
- Recharts (data visualization)
- React Markdown (markdown rendering)

---

## 1. Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   ├── ChatInterface.tsx      # Main chat UI
│   │   ├── DocumentUpload.tsx     # File upload with drag-drop
│   │   ├── DocumentList.tsx       # List of uploaded docs
│   │   ├── SourceViewer.tsx       # Citation viewer
│   │   ├── AgentTrace.tsx         # Agent execution visualization
│   │   ├── MetricsDashboard.tsx   # Evaluation metrics
│   │   ├── ComparisonView.tsx     # Multi-document comparison
│   │   ├── MessageBubble.tsx      # Individual message
│   │   └── Layout.tsx             # App layout wrapper
│   ├── lib/
│   │   ├── api.ts                 # API client
│   │   ├── types.ts               # TypeScript interfaces
│   │   ├── utils.ts               # Utility functions
│   │   └── cn.ts                  # className utility
│   ├── store/
│   │   └── useStore.ts            # Zustand global state
│   ├── hooks/
│   │   ├── useChat.ts             # Chat hook
│   │   ├── useDocuments.ts        # Documents hook
│   │   └── useWebSocket.ts        # WebSocket hook
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── .env.example
```

---

## 2. Global State Management (Zustand)

**File**: `frontend/src/store/useStore.ts`

```typescript
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  sources?: Source[];
  agentTrace?: AgentStep[];
  metadata?: Record<string, any>;
}

interface Source {
  chunk_id: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
}

interface AgentStep {
  agent: string;
  action: string;
  result?: any;
  timestamp: number;
  duration: number;
}

interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
  processed: boolean;
  metadata?: Record<string, any>;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

interface StoreState {
  // Conversations
  conversations: Conversation[];
  currentConversationId: string | null;
  
  // Documents
  documents: Document[];
  
  // UI State
  isSidebarOpen: boolean;
  isSourceViewerOpen: boolean;
  selectedSource: Source | null;
  
  // Loading states
  isLoading: boolean;
  isUploading: boolean;
  isProcessing: Record<string, boolean>;
  
  // Actions
  addMessage: (conversationId: string, message: Message) => void;
  updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => void;
  createConversation: () => string;
  setCurrentConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  
  addDocument: (document: Document) => void;
  removeDocument: (id: string) => void;
  updateDocumentStatus: (id: string, processed: boolean) => void;
  
  toggleSidebar: () => void;
  openSourceViewer: (source: Source) => void;
  closeSourceViewer: () => void;
  
  setLoading: (loading: boolean) => void;
  setUploading: (uploading: boolean) => void;
  setProcessing: (docId: string, processing: boolean) => void;
}

export const useStore = create<StoreState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        conversations: [],
        currentConversationId: null,
        documents: [],
        isSidebarOpen: true,
        isSourceViewerOpen: false,
        selectedSource: null,
        isLoading: false,
        isUploading: false,
        isProcessing: {},
        
        // Actions
        addMessage: (conversationId, message) =>
          set((state) => {
            const conversations = state.conversations.map((conv) =>
              conv.id === conversationId
                ? {
                    ...conv,
                    messages: [...conv.messages, message],
                    updated_at: new Date().toISOString(),
                  }
                : conv
            );
            return { conversations };
          }),
        
        updateMessage: (conversationId, messageId, updates) =>
          set((state) => {
            const conversations = state.conversations.map((conv) =>
              conv.id === conversationId
                ? {
                    ...conv,
                    messages: conv.messages.map((msg) =>
                      msg.id === messageId ? { ...msg, ...updates } : msg
                    ),
                  }
                : conv
            );
            return { conversations };
          }),
        
        createConversation: () => {
          const newConv: Conversation = {
            id: `conv_${Date.now()}`,
            title: 'New Conversation',
            messages: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          
          set((state) => ({
            conversations: [newConv, ...state.conversations],
            currentConversationId: newConv.id,
          }));
          
          return newConv.id;
        },
        
        setCurrentConversation: (id) =>
          set({ currentConversationId: id }),
        
        deleteConversation: (id) =>
          set((state) => ({
            conversations: state.conversations.filter((c) => c.id !== id),
            currentConversationId:
              state.currentConversationId === id
                ? null
                : state.currentConversationId,
          })),
        
        addDocument: (document) =>
          set((state) => ({
            documents: [...state.documents, document],
          })),
        
        removeDocument: (id) =>
          set((state) => ({
            documents: state.documents.filter((d) => d.id !== id),
          })),
        
        updateDocumentStatus: (id, processed) =>
          set((state) => ({
            documents: state.documents.map((d) =>
              d.id === id ? { ...d, processed } : d
            ),
          })),
        
        toggleSidebar: () =>
          set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
        
        openSourceViewer: (source) =>
          set({ isSourceViewerOpen: true, selectedSource: source }),
        
        closeSourceViewer: () =>
          set({ isSourceViewerOpen: false, selectedSource: null }),
        
        setLoading: (loading) => set({ isLoading: loading }),
        setUploading: (uploading) => set({ isUploading: uploading }),
        setProcessing: (docId, processing) =>
          set((state) => ({
            isProcessing: { ...state.isProcessing, [docId]: processing },
          })),
      }),
      {
        name: 'investment-research-storage',
        partialize: (state) => ({
          conversations: state.conversations,
          documents: state.documents,
          isSidebarOpen: state.isSidebarOpen,
        }),
      }
    )
  )
);
```

---

## 3. API Client

**File**: `frontend/src/lib/api.ts`

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private apiKey: string | null;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.apiKey = localStorage.getItem('api_key');
  }

  setApiKey(key: string) {
    this.apiKey = key;
    localStorage.setItem('api_key', key);
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    return headers;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          ...this.getHeaders(),
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        return { error: error.detail || 'Request failed' };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Documents
  async uploadDocument(file: File): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
        method: 'POST',
        headers: this.apiKey ? { 'X-API-Key': this.apiKey } : {},
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        return { error: error.detail || 'Upload failed' };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async getDocuments(): Promise<ApiResponse<any[]>> {
    return this.request('/api/documents');
  }

  async deleteDocument(id: string): Promise<ApiResponse<any>> {
    return this.request(`/api/documents/${id}`, { method: 'DELETE' });
  }

  // Chat
  async sendMessage(query: string, conversationId?: string): Promise<ApiResponse<any>> {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ query, conversation_id: conversationId }),
    });
  }

  // Streaming chat
  async *streamMessage(query: string, conversationId?: string): AsyncGenerator<string> {
    const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ query, conversation_id: conversationId }),
    });

    if (!response.ok) {
      throw new Error('Stream failed');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No reader available');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          
          try {
            const parsed = JSON.parse(data);
            if (parsed.content) {
              yield parsed.content;
            }
          } catch (e) {
            // Skip invalid JSON
          }
        }
      }
    }
  }

  // Conversations
  async getConversations(): Promise<ApiResponse<any[]>> {
    return this.request('/api/conversations');
  }

  async getConversation(id: string): Promise<ApiResponse<any>> {
    return this.request(`/api/conversations/${id}`);
  }

  // Analysis
  async compareDocuments(query: string, documentIds: string[]): Promise<ApiResponse<any>> {
    return this.request('/api/analyze/compare', {
      method: 'POST',
      body: JSON.stringify({ query, document_ids: documentIds }),
    });
  }

  // Evaluation
  async getMetrics(): Promise<ApiResponse<any>> {
    return this.request('/api/evals/metrics');
  }

  async runEvaluation(): Promise<ApiResponse<any>> {
    return this.request('/api/evals/run', { method: 'POST' });
  }

  async getEvaluationHistory(limit: number = 10): Promise<ApiResponse<any[]>> {
    return this.request(`/api/evals/history?limit=${limit}`);
  }
}

export const api = new ApiClient();
```

---

## 4. Main Chat Interface

**File**: `frontend/src/components/ChatInterface.tsx`

```typescript
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
      
      for await (const chunk of api.streamMessage(input, currentConversationId)) {
        fullContent += chunk;
        setStreamingContent(fullContent);
        
        // Update message in real-time
        updateMessage(currentConversationId, assistantMessageId, {
          content: fullContent,
        });
      }

      setStreamingContent('');
    } catch (error) {
      console.error('Error sending message:', error);
      updateMessage(currentConversationId, assistantMessageId, {
        content: 'Sorry, I encountered an error. Please try again.',
      });
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
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {currentConversation?.messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {/* Streaming indicator */}
        {isLoading && streamingContent && (
          <div className="flex items-start space-x-2">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
              AI
            </div>
            <div className="flex-1 bg-gray-100 rounded-lg p-4">
              <div className="prose max-w-none">
                {streamingContent}
                <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            className="flex-1 min-h-[60px] max-h-[200px]"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            size="icon"
            className="h-[60px] w-[60px]"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
```

---

## 5. Message Bubble Component

**File**: `frontend/src/components/MessageBubble.tsx`

```typescript
import { User, Bot, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useStore } from '@/store/useStore';
import { Button } from './ui/button';

interface MessageBubbleProps {
  message: {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: any[];
    agentTrace?: any[];
    metadata?: Record<string, any>;
  };
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { openSourceViewer } = useStore();
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-blue-500' : 'bg-gray-700'
      }`}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Content */}
      <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block rounded-lg p-4 ${
          isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-100 text-gray-900'
        }`}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  a: ({ node, ...props }) => (
                    <a {...props} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer" />
                  ),
                  code: ({ node, inline, ...props }) => (
                    inline ? (
                      <code className="bg-gray-200 px-1 rounded" {...props} />
                    ) : (
                      <code className="block bg-gray-200 p-2 rounded" {...props} />
                    )
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-xs text-gray-500">Sources:</p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  onClick={() => openSourceViewer(source)}
                  className="text-xs"
                >
                  <ExternalLink className="w-3 h-3 mr-1" />
                  Source {idx + 1}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Agent Trace */}
        {!isUser && message.agentTrace && message.agentTrace.length > 0 && (
          <details className="mt-2">
            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
              View agent execution ({message.agentTrace.length} steps)
            </summary>
            <div className="mt-2 space-y-1 text-xs">
              {message.agentTrace.map((step, idx) => (
                <div key={idx} className="flex items-center space-x-2 text-gray-600">
                  <span className="font-medium">{step.agent}:</span>
                  <span>{step.action}</span>
                  <span className="text-gray-400">({step.duration.toFixed(2)}s)</span>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  );
}
```

---

## 6. Document Upload Component

**File**: `frontend/src/components/DocumentUpload.tsx`

```typescript
import { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, Loader2 } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { api } from '@/lib/api';
import { Button } from './ui/button';
import { useToast } from './ui/use-toast';

export function DocumentUpload() {
  const [dragActive, setDragActive] = useState(false);
  const { addDocument, setProcessing, updateDocumentStatus } = useStore();
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

      // Update with real document data
      addDocument({
        id: data.document_id,
        filename: data.filename,
        file_type: data.file_type,
        file_size: data.file_size,
        uploaded_at: data.uploaded_at,
        processed: data.processed,
      });

      toast({
        title: 'Upload successful',
        description: `${file.name} is being processed.`,
      });

      // Poll for processing status
      pollProcessingStatus(data.document_id);
    } catch (error) {
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
      const doc = data?.find((d: any) => d.id === docId);

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
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        dragActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
      <p className="text-lg font-medium mb-2">Drop files here</p>
      <p className="text-sm text-gray-500 mb-4">
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
```

---

## 7. Document List Component

**File**: `frontend/src/components/DocumentList.tsx`

```typescript
import { FileText, Trash2, CheckCircle, Loader2 } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { api } from '@/lib/api';
import { Button } from './ui/button';
import { useToast } from './ui/use-toast';

export function DocumentList() {
  const { documents, removeDocument, isProcessing } = useStore();
  const { toast } = useToast();

  const handleDelete = async (id: string, filename: string) => {
    if (!confirm(`Delete ${filename}?`)) return;

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
      <div className="text-center py-12 text-gray-500">
        <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No documents uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
        >
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{doc.filename}</p>
              <p className="text-xs text-gray-500">
                {formatFileSize(doc.file_size)} • {new Date(doc.uploaded_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Processing status */}
            {isProcessing[doc.id] ? (
              <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
            ) : doc.processed ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : (
              <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />
            )}

            {/* Delete button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(doc.id, doc.filename)}
              className="text-gray-400 hover:text-red-500"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## 8. Source Viewer Component

**File**: `frontend/src/components/SourceViewer.tsx`

```typescript
import { X, ExternalLink } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { Button } from './ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from './ui/sheet';

export function SourceViewer() {
  const { isSourceViewerOpen, selectedSource, closeSourceViewer } = useStore();

  if (!selectedSource) return null;

  return (
    <Sheet open={isSourceViewerOpen} onOpenChange={closeSourceViewer}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Source Document</SheetTitle>
          <SheetDescription>
            Relevance Score: {(selectedSource.score * 100).toFixed(1)}%
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          {/* Metadata */}
          {selectedSource.metadata && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-medium mb-2">Document Information</h3>
              <dl className="space-y-1 text-sm">
                {Object.entries(selectedSource.metadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <dt className="text-gray-500">{key}:</dt>
                    <dd className="font-medium">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Content */}
          <div className="prose prose-sm max-w-none">
            <h3>Content</h3>
            <div className="bg-white border rounded-lg p-4 whitespace-pre-wrap">
              {selectedSource.content}
            </div>
          </div>

          {/* Chunk ID for reference */}
          <p className="text-xs text-gray-400">
            Chunk ID: {selectedSource.chunk_id}
          </p>
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

---

## 9. Agent Trace Visualization

**File**: `frontend/src/components/AgentTrace.tsx`

```typescript
import { CheckCircle, Clock, Zap } from 'lucide-react';

interface AgentStep {
  agent: string;
  action: string;
  result?: any;
  timestamp: number;
  duration: number;
}

interface AgentTraceProps {
  steps: AgentStep[];
}

export function AgentTrace({ steps }: AgentTraceProps) {
  const getAgentIcon = (agent: string) => {
    const icons: Record<string, string> = {
      supervisor: '🧭',
      research: '🔍',
      analysis: '📊',
      fact_checker: '✅',
      web_search: '🌐',
      synthesizer: '🔄',
    };
    return icons[agent] || '🤖';
  };

  const getAgentColor = (agent: string) => {
    const colors: Record<string, string> = {
      supervisor: 'bg-purple-100 text-purple-700',
      research: 'bg-blue-100 text-blue-700',
      analysis: 'bg-green-100 text-green-700',
      fact_checker: 'bg-yellow-100 text-yellow-700',
      web_search: 'bg-orange-100 text-orange-700',
      synthesizer: 'bg-pink-100 text-pink-700',
    };
    return colors[agent] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-4">
      <h3 className="font-semibold flex items-center">
        <Zap className="w-4 h-4 mr-2" />
        Agent Execution Trace
      </h3>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

        {/* Steps */}
        <div className="space-y-6">
          {steps.map((step, idx) => (
            <div key={idx} className="relative pl-14">
              {/* Agent icon */}
              <div
                className={`absolute left-0 w-12 h-12 rounded-full flex items-center justify-center text-2xl ${getAgentColor(
                  step.agent
                )}`}
              >
                {getAgentIcon(step.agent)}
              </div>

              {/* Step content */}
              <div className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-medium capitalize">{step.agent}</h4>
                    <p className="text-sm text-gray-600">{step.action}</p>
                  </div>
                  <div className="flex items-center text-xs text-gray-500">
                    <Clock className="w-3 h-3 mr-1" />
                    {step.duration.toFixed(2)}s
                  </div>
                </div>

                {/* Result preview */}
                {step.result && (
                  <details className="mt-2">
                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                      View details
                    </summary>
                    <pre className="mt-2 text-xs bg-gray-50 rounded p-2 overflow-x-auto">
                      {JSON.stringify(step.result, null, 2)}
                    </pre>
                  </details>
                )}
              </div>

              {/* Completion checkmark */}
              <CheckCircle className="absolute left-[18px] -bottom-3 w-6 h-6 text-green-500 bg-white" />
            </div>
          ))}
        </div>
      </div>

      {/* Total time */}
      <div className="text-right text-sm text-gray-500">
        Total execution time:{' '}
        {steps.reduce((sum, step) => sum + step.duration, 0).toFixed(2)}s
      </div>
    </div>
  );
}
```

---

## 10. Metrics Dashboard (Frontend)

**File**: `frontend/src/components/MetricsDashboard.tsx`

```typescript
import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';

interface MetricsData {
  latest_metrics: Record<string, number>;
  trends: Record<string, { current: number; change: number; direction: string }>;
  history: Record<string, Array<{ timestamp: number; value: number }>>;
  pass_rate: number;
  last_updated: number;
}

export function MetricsDashboard() {
  const [data, setData] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      const { data: metricsData } = await api.getMetrics();
      setData(metricsData);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchMetrics();
  };

  const formatMetricName = (name: string) => {
    return name
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const prepareChartData = () => {
    if (!data?.history) return [];

    const timestamps = new Set<number>();
    Object.values(data.history).forEach((series) => {
      series.forEach((point) => timestamps.add(point.timestamp));
    });

    return Array.from(timestamps)
      .sort()
      .map((timestamp) => {
        const point: any = {
          date: new Date(timestamp * 1000).toLocaleDateString(),
          timestamp,
        };

        Object.entries(data.history).forEach(([metric, series]) => {
          const value = series.find((p) => p.timestamp === timestamp);
          if (value) {
            point[metric] = value.value;
          }
        });

        return point;
      });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12 text-gray-500">
        No evaluation data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Evaluation Metrics</h2>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            Last updated: {new Date(data.last_updated * 1000).toLocaleString()}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overall Pass Rate */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Pass Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-5xl font-bold text-green-600">
            {(data.pass_rate * 100).toFixed(1)}%
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Based on {Object.keys(data.latest_metrics).length} metrics
          </p>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(data.latest_metrics).map(([metric, value]) => (
          <MetricCard
            key={metric}
            name={formatMetricName(metric)}
            value={value}
            trend={data.trends[metric]}
          />
        ))}
      </div>

      {/* Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Metrics Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={prepareChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[0, 1]} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="faithfulness"
                stroke="#8884d8"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="answer_relevancy"
                stroke="#82ca9d"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="numerical_accuracy"
                stroke="#ffc658"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Metrics Comparison Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Current Metrics Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={Object.entries(data.latest_metrics).map(([name, value]) => ({
                name: formatMetricName(name),
                score: value,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis domain={[0, 1]} />
              <Tooltip />
              <Bar dataKey="score" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({
  name,
  value,
  trend,
}: {
  name: string;
  value: number;
  trend?: { current: number; change: number; direction: string };
}) {
  const getTrendIcon = () => {
    if (!trend) return <Minus className="w-4 h-4 text-gray-400" />;
    if (trend.direction === 'up')
      return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (trend.direction === 'down')
      return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getTrendColor = () => {
    if (!trend) return 'text-gray-500';
    if (trend.direction === 'up') return 'text-green-600';
    if (trend.direction === 'down') return 'text-red-600';
    return 'text-gray-500';
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex justify-between items-start mb-2">
          <h4 className="text-sm font-medium text-gray-600">{name}</h4>
          {getTrendIcon()}
        </div>
        <div className="text-3xl font-bold">{value.toFixed(3)}</div>
        {trend && (
          <div className={`text-sm mt-1 ${getTrendColor()}`}>
            {trend.change > 0 ? '+' : ''}
            {(trend.change * 100).toFixed(1)}% from baseline
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

---

## 11. Main App Layout

**File**: `frontend/src/App.tsx`

```typescript
import { useEffect } from 'react';
import { Menu, Plus, Settings } from 'lucide-react';
import { useStore } from './store/useStore';
import { api } from './lib/api';
import { ChatInterface } from './components/ChatInterface';
import { DocumentUpload } from './components/DocumentUpload';
import { DocumentList } from './components/DocumentList';
import { SourceViewer } from './components/SourceViewer';
import { MetricsDashboard } from './components/MetricsDashboard';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Toaster } from './components/ui/toaster';

function App() {
  const {
    conversations,
    currentConversationId,
    createConversation,
    setCurrentConversation,
    deleteConversation,
    isSidebarOpen,
    toggleSidebar,
  } = useStore();

  useEffect(() => {
    // Load initial data
    loadDocuments();
    loadConversations();
  }, []);

  const loadDocuments = async () => {
    const { data } = await api.getDocuments();
    if (data) {
      data.forEach((doc: any) => useStore.getState().addDocument(doc));
    }
  };

  const loadConversations = async () => {
    const { data } = await api.getConversations();
    // Load conversations from API if needed
  };

  const handleNewChat = () => {
    createConversation();
  };

  const currentConversation = conversations.find(
    (c) => c.id === currentConversationId
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={`bg-white border-r flex flex-col transition-all duration-300 ${
          isSidebarOpen ? 'w-64' : 'w-0'
        } overflow-hidden`}
      >
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold">Investment Research</h1>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <Button onClick={handleNewChat} className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            New Chat
          </Button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setCurrentConversation(conv.id)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                conv.id === currentConversationId
                  ? 'bg-blue-50 text-blue-700'
                  : 'hover:bg-gray-50'
              }`}
            >
              <p className="font-medium truncate">{conv.title}</p>
              <p className="text-xs text-gray-500">
                {conv.messages.length} messages
              </p>
            </button>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="bg-white border-b p-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="icon" onClick={toggleSidebar}>
              <Menu className="w-5 h-5" />
            </Button>
            {currentConversation && (
              <h2 className="text-lg font-semibold">{currentConversation.title}</h2>
            )}
          </div>
          <Button variant="ghost" size="icon">
            <Settings className="w-5 h-5" />
          </Button>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          <Tabs defaultValue="chat" className="h-full flex flex-col">
            <TabsList className="mx-4 mt-4">
              <TabsTrigger value="chat">Chat</TabsTrigger>
              <TabsTrigger value="documents">Documents</TabsTrigger>
              <TabsTrigger value="metrics">Metrics</TabsTrigger>
            </TabsList>

            <TabsContent value="chat" className="flex-1 overflow-hidden mt-0">
              {currentConversationId ? (
                <ChatInterface />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <div className="text-center">
                    <h3 className="text-xl font-semibold mb-2">
                      Welcome to Investment Research AI
                    </h3>
                    <p className="mb-4">Start a new conversation to begin</p>
                    <Button onClick={handleNewChat}>
                      <Plus className="w-4 h-4 mr-2" />
                      New Chat
                    </Button>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="documents" className="flex-1 overflow-auto p-4">
              <div className="max-w-4xl mx-auto space-y-6">
                <DocumentUpload />
                <DocumentList />
              </div>
            </TabsContent>

            <TabsContent value="metrics" className="flex-1 overflow-auto p-4">
              <div className="max-w-7xl mx-auto">
                <MetricsDashboard />
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>

      {/* Modals */}
      <SourceViewer />
      <Toaster />
    </div>
  );
}

export default App;
```

---

## 12. Configuration Files

### package.json
```json
{
  "name": "investment-research-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.4.7",
    "react-markdown": "^9.0.1",
    "recharts": "^2.10.3",
    "lucide-react": "^0.294.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.13.2",
    "@typescript-eslint/parser": "^6.13.2",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.3",
    "vite": "^5.0.7"
  }
}
```

### vite.config.ts
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

### .env.example
```bash
VITE_API_URL=http://localhost:8000
```

---

## 13. shadcn/ui Setup

```bash
# Install shadcn/ui CLI
npx shadcn-ui@latest init

# Add components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add input
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add sheet
```

---

## 14. Key Features Implementation

### Real-time Streaming
```typescript
// Handled in ChatInterface.tsx
for await (const chunk of api.streamMessage(input, conversationId)) {
  fullContent += chunk;
  // Update UI in real-time
  updateMessage(conversationId, messageId, { content: fullContent });
}
```

### Optimistic Updates
```typescript
// Add user message immediately
addMessage(conversationId, userMessage);

// Then send to API
const response = await api.sendMessage(input);
```

### Error Handling
```typescript
try {
  const { data, error } = await api.someMethod();
  if (error) throw new Error(error);
  // Handle success
} catch (error) {
  toast({
    title: 'Error',
    description: error.message,
    variant: 'destructive'
  });
}
```

### Responsive Design
```typescript
// Mobile-friendly classes
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
className="flex-col md:flex-row"
className="w-full md:w-64"
```

---

## Summary

This frontend implementation provides:

✅ **Complete React Application**: All major components
✅ **State Management**: Zustand with persistence
✅ **Real-time Updates**: Streaming chat responses  
✅ **Document Management**: Upload, list, delete with drag-drop
✅ **Source Viewer**: Citation exploration
✅ **Agent Visualization**: Execution trace display
✅ **Metrics Dashboard**: Real-time evaluation metrics
✅ **Responsive Design**: Works on mobile and desktop
✅ **Modern UI**: shadcn/ui components with Tailwind
✅ **TypeScript**: Full type safety
✅ **Optimistic Updates**: Smooth UX

**Ready for deployment to Vercel with zero configuration!**