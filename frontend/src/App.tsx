import { useEffect } from 'react';
import { Menu, Plus } from 'lucide-react';
import { useStore } from './store/useStore';
import { api } from './lib/api';
import { ChatInterface } from './components/ChatInterface';
import { DocumentUpload } from './components/DocumentUpload';
import { DocumentList } from './components/DocumentList';
import { SourceViewer } from './components/SourceViewer';
import { MetricsDashboard } from './components/MetricsDashboard';
import { ThemeToggle } from './components/ThemeToggle';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { ToastProvider } from './components/ui/toast';

function App() {
  const {
    conversations,
    currentConversationId,
    createConversation,
    setCurrentConversation,
    isSidebarOpen,
    toggleSidebar,
    addDocument,
  } = useStore();

  useEffect(() => {
    // Clean up any stale temp documents from previous sessions
    const cleanupTempDocuments = () => {
      const { documents, removeDocument } = useStore.getState();
      documents.forEach(doc => {
        if (doc.id.startsWith('temp_')) {
          removeDocument(doc.id);
        }
      });
    };
    
    cleanupTempDocuments();
    
    // Load initial data
    loadDocuments();
    loadConversations();
    
    // Create initial conversation if none exists
    if (conversations.length === 0) {
      createConversation();
    }
  }, []);

  const loadDocuments = async () => {
    const { data } = await api.getDocuments();
    if (data && data.documents) {
      data.documents.forEach((doc: any) => addDocument(doc));
    }
  };

  const loadConversations = async () => {
    await api.getConversations();
    // Load conversations from API if needed
  };

  const handleNewChat = () => {
    createConversation();
  };

  const currentConversation = conversations.find(
    (c) => c.id === currentConversationId
  );

  return (
    <ToastProvider>
      <div className="flex h-screen bg-background">
        {/* Sidebar */}
        <aside
          className={`bg-card border-r border-border flex flex-col transition-all duration-300 ${
            isSidebarOpen ? 'w-64' : 'w-0'
          } overflow-hidden`}
        >
          <div className="px-4 py-3 border-b border-border">
            <h1 className="text-lg font-semibold tracking-tight">Investment Research</h1>
          </div>

          {/* New Chat Button */}
          <div className="p-3">
            <Button onClick={handleNewChat} className="w-full justify-start">
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setCurrentConversation(conv.id)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  conv.id === currentConversationId
                    ? 'bg-accent text-accent-foreground font-medium'
                    : 'hover:bg-accent/50 text-muted-foreground hover:text-foreground'
                }`}
              >
                <p className="font-medium truncate text-[13px]">{conv.title}</p>
                <p className="text-[11px] opacity-60 mt-0.5">
                  {conv.messages.length} messages
                </p>
              </button>
            ))}
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Top Bar */}
          <header className="bg-card/50 backdrop-blur-sm border-b border-border px-4 py-2.5 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Button variant="ghost" size="icon" onClick={toggleSidebar}>
                <Menu className="w-4 h-4" />
              </Button>
              {currentConversation && (
                <h2 className="text-sm font-semibold tracking-tight">{currentConversation.title}</h2>
              )}
            </div>
            <ThemeToggle />
          </header>

          {/* Content Area */}
          <div className="flex-1 overflow-hidden">
            <Tabs defaultValue="chat" className="h-full flex flex-col">
              <TabsList className="mx-4 mt-3 bg-muted/50">
                <TabsTrigger value="chat">Chat</TabsTrigger>
                <TabsTrigger value="documents">Documents</TabsTrigger>
                <TabsTrigger value="metrics">Metrics</TabsTrigger>
              </TabsList>

              <TabsContent value="chat" className="flex-1 overflow-hidden mt-0">
                {currentConversationId ? (
                  <ChatInterface />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center max-w-md">
                      <h3 className="text-2xl font-semibold mb-2 tracking-tight">
                        Welcome to Investment Research AI
                      </h3>
                      <p className="text-muted-foreground mb-4 text-sm">
                        Start a new conversation to begin analyzing your documents
                      </p>
                      <Button onClick={handleNewChat}>
                        <Plus className="w-4 h-4 mr-2" />
                        New Chat
                      </Button>
                    </div>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="documents" className="flex-1 overflow-auto p-4">
                <div className="max-w-5xl mx-auto space-y-6">
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
      </div>
    </ToastProvider>
  );
}

export default App;
