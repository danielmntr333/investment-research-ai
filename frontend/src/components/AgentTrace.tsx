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
