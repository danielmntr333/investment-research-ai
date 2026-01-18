import { useState } from 'react';
import { FileText, Search } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { api } from '@/lib/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { useToast } from './ui/toast';

export function ComparisonView() {
  const [query, setQuery] = useState('');
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const { documents } = useStore();
  const { toast } = useToast();

  const toggleDocument = (docId: string) => {
    setSelectedDocs((prev) =>
      prev.includes(docId)
        ? prev.filter((id) => id !== docId)
        : [...prev, docId]
    );
  };

  const handleCompare = async () => {
    if (selectedDocs.length < 2) {
      toast({
        title: 'Select at least 2 documents',
        description: 'Comparison requires at least two documents.',
        variant: 'destructive',
      });
      return;
    }

    if (!query.trim()) {
      toast({
        title: 'Enter a query',
        description: 'Please enter a comparison query.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      const { data, error } = await api.compareDocuments(query, selectedDocs);

      if (error) {
        throw new Error(error);
      }

      setResults(data);
    } catch (error) {
      toast({
        title: 'Comparison failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-4">Document Comparison</h2>
        <p className="text-gray-600">
          Select multiple documents and ask a question to compare insights across them.
        </p>
      </div>

      {/* Document Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {documents.map((doc) => (
              <label
                key={doc.id}
                className={`flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedDocs.includes(doc.id)
                    ? 'bg-blue-50 border-blue-500'
                    : 'hover:bg-gray-50'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedDocs.includes(doc.id)}
                  onChange={() => toggleDocument(doc.id)}
                  className="w-4 h-4"
                />
                <FileText className="w-4 h-4 text-gray-400" />
                <span className="flex-1 text-sm truncate">{doc.filename}</span>
              </label>
            ))}
          </div>
          {documents.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              No documents available. Upload documents first.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Query Input */}
      <Card>
        <CardHeader>
          <CardTitle>Comparison Query</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What insights do you want to compare?"
              className="flex-1"
            />
            <Button
              onClick={handleCompare}
              disabled={loading || selectedDocs.length < 2 || !query.trim()}
            >
              <Search className="w-4 h-4 mr-2" />
              Compare
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle>Comparison Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
