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
  overall_score: number;
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
  context_recall: number;
  answer_correctness: number;
  retrieval_time_avg: number;
  total_queries: number;
  timestamp: string;
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

  const getMetricsMap = () => {
    if (!data) return {};
    return {
      faithfulness: data.faithfulness,
      answer_relevancy: data.answer_relevancy,
      context_precision: data.context_precision,
      context_recall: data.context_recall,
      answer_correctness: data.answer_correctness,
    };
  };

  const prepareChartData = () => {
    // For now, show current metrics as a single point
    // In production, this would fetch historical data
    if (!data) return [];
    
    return [
      {
        name: 'Current',
        faithfulness: data.faithfulness,
        answer_relevancy: data.answer_relevancy,
        context_precision: data.context_precision,
        context_recall: data.context_recall,
        answer_correctness: data.answer_correctness,
      }
    ];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No evaluation data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold tracking-tight">Evaluation Metrics</h2>
        <div className="flex items-center space-x-3">
          <span className="text-xs text-muted-foreground">
            Last updated: {new Date(data.timestamp).toLocaleString()}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overall Score */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-green-600 dark:text-green-500">
            {(data.overall_score * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground mt-1.5">
            Based on {data.total_queries} total queries • Avg retrieval time: {data.retrieval_time_avg.toFixed(2)}s
          </p>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(getMetricsMap()).map(([metric, value]) => (
          <MetricCard
            key={metric}
            name={formatMetricName(metric)}
            value={value}
          />
        ))}
      </div>

      {/* Metrics Comparison Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Metrics Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart
              data={Object.entries(getMetricsMap()).map(([name, value]) => ({
                name: formatMetricName(name),
                score: value,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-15} textAnchor="end" height={80} style={{ fontSize: '12px' }} />
              <YAxis domain={[0, 1]} style={{ fontSize: '12px' }} />
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
}: {
  name: string;
  value: number;
}) {
  const getScoreColor = () => {
    if (value >= 0.85) return 'text-green-600 dark:text-green-500';
    if (value >= 0.70) return 'text-yellow-600 dark:text-yellow-500';
    return 'text-red-600 dark:text-red-500';
  };

  const getQualityLabel = () => {
    if (value >= 0.85) return 'Excellent';
    if (value >= 0.70) return 'Good';
    return 'Needs Improvement';
  };

  return (
    <Card>
      <CardContent className="pt-4">
        <h4 className="text-xs font-medium text-muted-foreground mb-2">{name}</h4>
        <div className={`text-2xl font-bold ${getScoreColor()}`}>
          {value.toFixed(3)}
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {getQualityLabel()}
        </div>
      </CardContent>
    </Card>
  );
}
