import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  sources?: Source[];
  agentTrace?: AgentStep[];
  metadata?: Record<string, any>;
}

export interface Source {
  source_number: number;
  document_name: string;
  content_preview: string;
  chunk_id?: string;
  similarity?: number;
  source_type?: 'document' | 'web';
  url?: string;
  // Legacy fields for backward compatibility
  content?: string;
  score?: number;
  metadata?: Record<string, any>;
}

export interface AgentStep {
  agent: string;
  action: string;
  result?: any;
  timestamp: number;
  duration: number;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
  processed: boolean;
  metadata?: Record<string, any>;
}

export interface Conversation {
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
      (set) => ({
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
          // Filter out temp documents before persisting
          documents: state.documents.filter(doc => !doc.id.startsWith('temp_')),
          isSidebarOpen: state.isSidebarOpen,
        }),
      }
    )
  )
);
