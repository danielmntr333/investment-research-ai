# UI/UX Enhancement TODO List

## ✅ Completed Today

- [x] Real-time agent status updates during query processing
- [x] Multi-step document processing progress indicators
- [x] Enhanced source viewer with action buttons
- [x] Streaming API updated to handle agent step events

---

## 🎯 High Priority (Next 1-2 Days)

### 1. Add Confidence Scores to Messages

**File: `frontend/src/store/useStore.ts`**
```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  sources?: Source[];
  agentTrace?: AgentStep[];
  confidence?: number;  // ADD THIS
  tools_used?: string[]; // ADD THIS
  metadata?: Record<string, any>;
}
```

**File: `frontend/src/components/MessageBubble.tsx`**

Add after sources section:
```tsx
{/* Confidence Score */}
{!isUser && message.confidence !== undefined && (
  <div className="mt-2 flex items-center gap-1.5 text-[11px]">
    <span className="text-muted-foreground">Confidence:</span>
    <span className={`font-semibold ${
      message.confidence > 0.9 ? 'text-green-600 dark:text-green-500' : 
      message.confidence > 0.7 ? 'text-yellow-600 dark:text-yellow-500' : 
      'text-red-600 dark:text-red-500'
    }`}>
      {(message.confidence * 100).toFixed(0)}%
    </span>
  </div>
)}
```

---

### 2. Make Agent Trace More Prominent

**File: `frontend/src/components/MessageBubble.tsx`**

Replace the current collapsible details with:
```tsx
{/* Agent Trace - Always visible summary */}
{!isUser && message.agentTrace && message.agentTrace.length > 0 && (
  <div className="mt-3 p-2.5 bg-accent/30 rounded-lg border border-border/50">
    <div className="flex items-center justify-between text-[11px]">
      <div className="flex items-center gap-1.5 font-medium text-foreground">
        <Zap className="w-3.5 h-3.5" />
        <span>
          Agent execution: {message.agentTrace.length} steps, 
          {' '}{message.agentTrace.reduce((sum, s) => sum + s.duration, 0).toFixed(1)}s
        </span>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowFullTrace(!showFullTrace)}
        className="h-6 text-[10px]"
      >
        {showFullTrace ? 'Hide' : 'View details'} {showFullTrace ? '▼' : '▶'}
      </Button>
    </div>
    {showFullTrace && (
      <div className="mt-2 space-y-1 text-[11px] border-t border-border/30 pt-2">
        {message.agentTrace.map((step, idx) => (
          <div key={idx} className="flex items-center gap-2 text-muted-foreground">
            <span>{getAgentIcon(step.agent)}</span>
            <span className="font-medium text-foreground">{step.agent}:</span>
            <span>{step.action}</span>
            <span className="opacity-60 ml-auto">({step.duration.toFixed(2)}s)</span>
          </div>
        ))}
      </div>
    )}
  </div>
)}
```

Add state to MessageBubble:
```tsx
const [showFullTrace, setShowFullTrace] = useState(false);

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
```

---

### 3. Display Tool Usage

**File: `frontend/src/components/MessageBubble.tsx`**

Add after confidence score:
```tsx
{/* Tools Used */}
{!isUser && message.tools_used && message.tools_used.length > 0 && (
  <div className="mt-2 flex items-center gap-1.5 flex-wrap">
    <span className="text-[11px] text-muted-foreground">Tools used:</span>
    {message.tools_used.map((tool, idx) => (
      <span 
        key={idx}
        className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-[10px] rounded-full font-medium"
      >
        🔧 {tool}
      </span>
    ))}
  </div>
)}
```

---

### 4. Graceful Error Handling

**Create: `frontend/src/components/ErrorMessage.tsx`**
```tsx
import { AlertCircle, RefreshCw, Search, Upload } from 'lucide-react';
import { Button } from './ui/button';

interface ErrorMessageProps {
  error: string;
  onRetry?: () => void;
}

export function ErrorMessage({ error, onRetry }: ErrorMessageProps) {
  const errorType = detectErrorType(error);
  
  const errorConfig = {
    timeout: {
      icon: <AlertCircle className="w-5 h-5 text-yellow-600" />,
      title: 'Request Timeout',
      message: 'The request took longer than expected. I\'ve switched to a backup system.',
      actions: [
        { label: 'Retry', icon: <RefreshCw className="w-3 h-3" />, onClick: onRetry }
      ]
    },
    no_results: {
      icon: <Search className="w-5 h-5 text-blue-600" />,
      title: 'No Results Found',
      message: 'I couldn\'t find information about this in your uploaded documents.',
      suggestions: [
        'Try rephrasing your question',
        'Upload relevant documents',
        'Search the web for this information'
      ],
      actions: [
        { label: 'Upload Document', icon: <Upload className="w-3 h-3" /> },
        { label: 'Try Web Search', icon: <Search className="w-3 h-3" /> }
      ]
    },
    rate_limit: {
      icon: <AlertCircle className="w-5 h-5 text-red-600" />,
      title: 'Rate Limit Reached',
      message: 'Too many requests. Please wait a moment before trying again.',
    },
    generic: {
      icon: <AlertCircle className="w-5 h-5 text-gray-600" />,
      title: 'Something Went Wrong',
      message: error,
      actions: [
        { label: 'Retry', icon: <RefreshCw className="w-3 h-3" />, onClick: onRetry }
      ]
    }
  };

  const config = errorConfig[errorType] || errorConfig.generic;

  return (
    <div className="bg-accent/50 border border-border rounded-lg p-4">
      <div className="flex items-start gap-3">
        {config.icon}
        <div className="flex-1">
          <h4 className="font-semibold text-sm mb-1">{config.title}</h4>
          <p className="text-[13px] text-muted-foreground mb-3">{config.message}</p>
          
          {config.suggestions && (
            <ul className="space-y-1 mb-3">
              {config.suggestions.map((suggestion, idx) => (
                <li key={idx} className="text-[12px] text-muted-foreground flex items-center gap-1.5">
                  <span className="w-1 h-1 bg-muted-foreground rounded-full" />
                  {suggestion}
                </li>
              ))}
            </ul>
          )}
          
          {config.actions && (
            <div className="flex gap-2">
              {config.actions.map((action, idx) => (
                <Button 
                  key={idx}
                  variant="outline" 
                  size="sm" 
                  onClick={action.onClick}
                  className="text-xs h-7"
                >
                  {action.icon}
                  <span className="ml-1.5">{action.label}</span>
                </Button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function detectErrorType(error: string): 'timeout' | 'no_results' | 'rate_limit' | 'generic' {
  if (error.toLowerCase().includes('timeout')) return 'timeout';
  if (error.toLowerCase().includes('no results') || error.toLowerCase().includes('not found')) return 'no_results';
  if (error.toLowerCase().includes('rate limit')) return 'rate_limit';
  return 'generic';
}
```

**Update: `frontend/src/components/ChatInterface.tsx`**

Replace error handling:
```tsx
} catch (error) {
  console.error('Error sending message:', error);
  const errorMessage = error instanceof Error ? error.message : 'Unknown error';
  
  updateMessage(currentConversationId, assistantMessageId, {
    content: '', // Clear content
    error: errorMessage, // Add error field
  });
  setAgentStatus('');
}
```

**Update: `frontend/src/store/useStore.ts`**
```typescript
export interface Message {
  // ... existing fields
  error?: string; // ADD THIS
}
```

**Update: `frontend/src/components/MessageBubble.tsx`**
```tsx
// Add after content
{!isUser && message.error && (
  <ErrorMessage 
    error={message.error} 
    onRetry={() => {
      // Trigger retry logic
    }}
  />
)}
```

---

## 📊 Medium Priority (Next Week)

### 5. Metrics Dashboard Trends

**File: `frontend/src/components/MetricsDashboard.tsx`**

- [ ] Fetch historical metrics data (last 30 days)
- [ ] Add trend indicators (↗️ improving, → stable, ↘️ declining)
- [ ] Display line chart with multiple metrics
- [ ] Show "Recent Test Results" section

### 6. Loading Skeletons

**Create: `frontend/src/components/ui/skeleton.tsx`**
```tsx
export function Skeleton({ className = "", ...props }) {
  return (
    <div 
      className={`animate-pulse bg-muted rounded ${className}`}
      {...props}
    />
  );
}
```

Use in ChatInterface while loading:
```tsx
{isLoading && !agentStatus && (
  <div className="flex items-start gap-3">
    <Skeleton className="w-7 h-7 rounded-lg" />
    <div className="flex-1 space-y-2">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  </div>
)}
```

### 7. Keyboard Shortcuts

**Create: `frontend/src/hooks/useKeyboardShortcuts.ts`**
```tsx
import { useEffect } from 'react';

export function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K: New chat
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        // Trigger new chat
      }
      
      // Cmd/Ctrl + /: Focus search
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault();
        // Focus search input
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);
}
```

Use in `App.tsx`:
```tsx
useKeyboardShortcuts();
```

---

## 🎨 Low Priority (Nice to Have)

### 8. Chart Embedding
- [ ] Support for embedded charts in responses
- [ ] Recharts integration for data visualization

### 9. Export Conversation
- [ ] Export to PDF
- [ ] Export to Markdown
- [ ] Copy to clipboard

### 10. Empty States
- [ ] Beautiful illustrations
- [ ] Helpful onboarding tips
- [ ] Quick action buttons

---

## 🧪 Testing Checklist

Before considering UX complete:

- [ ] Test agent status updates with real backend
- [ ] Verify document processing steps show correctly
- [ ] Test source viewer on mobile
- [ ] Check dark mode for all new components
- [ ] Test error handling with various error types
- [ ] Verify confidence scores display properly
- [ ] Test agent trace expand/collapse
- [ ] Mobile responsiveness (< 640px)
- [ ] Tablet view (640px - 1024px)
- [ ] Desktop view (> 1024px)

---

## 📝 Notes

- All color classes use Tailwind with dark mode support
- Font sizes: `text-[13px]` for body, `text-[11px]` for secondary, `text-[10px]` for badges
- Spacing: Use `gap-2` (8px) and `gap-3` (12px) for consistency
- Icons from `lucide-react`: Keep size at `w-4 h-4` or `w-3 h-3`
- Animations: Use `animate-in fade-in` for smooth entrances

---

## 🚀 Quick Wins (30 min each)

1. ✅ Add confidence scores display
2. ✅ Make agent trace more visible
3. ✅ Display tool usage badges
4. ✅ Create error message component
5. Add loading skeletons
6. Implement keyboard shortcuts

Choose one and implement it today! 💪
