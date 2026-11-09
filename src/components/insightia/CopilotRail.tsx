/**
 * Multilingual & Hinglish AI Copilot Drawer for Insightia.
 * Strictly Grounded: executes deterministic Pandas code in Python sandbox.
 * Returns humanized takeaway, verified figures, renderable interactive charts,
 * and executable Python source snippets.
 */

import React, { useState, useRef, useEffect } from 'react';
import { 
  Bot, 
  Send, 
  Terminal, 
  ChevronDown, 
  ChevronUp, 
  CheckCircle2, 
  Sparkles, 
  BarChart2, 
  LineChart as LineChartIcon,
  ScatterChart as ScatterChartIcon,
  HelpCircle,
  ShieldCheck,
  Languages
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { ChartPayload, CopilotResponse, dataIntelligenceService } from '@/services/data-intelligence.service';
import { toast } from 'sonner';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  verified_figures?: Record<string, any>;
  chart_payload?: ChartPayload | null;
  executed_code?: string;
  is_hinglish?: boolean;
  timestamp: string;
}

interface CopilotRailProps {
  sessionId: string | null;
  datasetName?: string;
  onDatasetMutated?: () => void;
}

const SUGGESTED_PROMPTS = [
  "Is data ka sales distribution kaisa hai?",
  "Top 5 categories by total revenue dikhao",
  "Price aur rating me correlation kya hai?",
  "Drop all missing rows in price column",
  "Show statistical outliers in revenue"
];

export const CopilotRail: React.FC<CopilotRailProps> = ({
  sessionId,
  datasetName,
  onDatasetMutated
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Namaste! I am your Insightia Data Copilot. Ask me questions in **English**, **Hindi**, or **Hinglish**.\n\nEvery insight is grounded in deterministic Python execution with 0% math hallucination.",
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [expandedCodeIds, setExpandedCodeIds] = useState<Set<string>>(new Set());
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const toggleCodeExpansion = (id: string) => {
    setExpandedCodeIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSend = async (queryToSend?: string) => {
    const query = queryToSend || inputQuery;
    if (!query.trim() || !sessionId) {
      if (!sessionId) toast.error("Please load or upload a dataset first.");
      return;
    }

    const userMsg: Message = {
      id: String(Date.now()),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMsg]);
    if (!queryToSend) setInputQuery('');
    setIsProcessing(true);

    try {
      const resp = await dataIntelligenceService.chatCopilot(sessionId, query);
      
      const assistantMsg: Message = {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: resp.reply || resp.explanation,
        verified_figures: resp.verified_figures,
        chart_payload: resp.chart_payload || (resp.chart_config ? {
          chartType: resp.chart_config.type,
          xAxis: resp.chart_config.x_axis,
          yAxis: resp.chart_config.y_axis,
          data: resp.chart_config.data,
          title: resp.chart_config.title
        } : null),
        executed_code: resp.executed_code,
        is_hinglish: resp.is_hinglish,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, assistantMsg]);

      // If query was a cleaning mutation (e.g. drop missing rows), notify parent
      if (resp.executed_code && (resp.executed_code.includes('dropna') || resp.executed_code.includes('drop'))) {
        toast.success("Dataset state mutated by Copilot query!");
        onDatasetMutated?.();
      }
    } catch (err: any) {
      toast.error("Copilot computation error");
      setMessages(prev => [
        ...prev,
        {
          id: String(Date.now() + 1),
          sender: 'assistant',
          text: `An error occurred executing your request: ${err.message || 'Unknown error'}`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <aside className="w-96 h-full bg-zinc-950 border-l border-zinc-800 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-3.5 border-b border-zinc-800 bg-zinc-950 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-zinc-100 flex items-center gap-1.5">
              Multilingual Copilot
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            </h3>
            <p className="text-xs text-zinc-400 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Grounded AI &amp; Python Sandbox
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-zinc-300 font-mono bg-zinc-900 px-2.5 py-1 rounded border border-zinc-800">
          <Languages className="w-3.5 h-3.5 text-indigo-400" />
          EN / HI / HINGLISH
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="p-2.5 border-b border-zinc-800/80 bg-zinc-950/70 overflow-x-auto flex gap-2 no-scrollbar">
        {SUGGESTED_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            disabled={isProcessing || !sessionId}
            className="text-xs whitespace-nowrap bg-zinc-900 hover:bg-zinc-800 border border-zinc-700/60 text-zinc-200 hover:text-white px-2.5 py-1.5 rounded-md transition-colors disabled:opacity-40 font-medium"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3.5">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          const isCodeExpanded = expandedCodeIds.has(msg.id);

          return (
            <div 
              key={msg.id} 
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1.5`}
            >
              <div 
                className={`max-w-[92%] p-3 rounded-lg text-xs leading-relaxed ${
                  isUser 
                    ? 'bg-indigo-600 text-white rounded-br-none shadow-sm' 
                    : 'bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-bl-none shadow-sm'
                }`}
              >
                {/* Message Body */}
                <div className="whitespace-pre-wrap font-sans">
                  {msg.text}
                </div>

                {/* Renderable Interactive Chart in Message */}
                {msg.chart_payload && (
                  <div className="mt-3 p-3 bg-zinc-950/80 rounded-lg border border-zinc-800">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-zinc-100">
                        {msg.chart_payload.title}
                      </span>
                      <span className="text-xs uppercase font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/40 font-semibold">
                        {msg.chart_payload.chartType}
                      </span>
                    </div>

                    <div className="h-44 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        {msg.chart_payload.chartType === 'scatter' ? (
                          <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: -20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                            <XAxis dataKey="x" stroke="#a1a1aa" fontSize={11} />
                            <YAxis dataKey="y" stroke="#a1a1aa" fontSize={11} />
                            <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px', color: '#f4f4f5' }} />
                            <Scatter data={msg.chart_payload.data} fill="#818cf8" />
                          </ScatterChart>
                        ) : (
                          <BarChart data={msg.chart_payload.data} margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                            <XAxis dataKey="name" stroke="#a1a1aa" fontSize={11} interval={0} angle={-25} textAnchor="end" />
                            <YAxis stroke="#a1a1aa" fontSize={11} />
                            <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px', color: '#f4f4f5' }} />
                            <Bar dataKey="value" fill="#6366f1" radius={[3, 3, 0, 0]} />
                          </BarChart>
                        )}
                      </ResponsiveContainer>
                    </div>

                    {msg.chart_payload.insights && msg.chart_payload.insights.length > 0 && (
                      <div className="mt-2 text-xs text-zinc-300 space-y-0.5">
                        {msg.chart_payload.insights.map((ins, i) => (
                          <p key={i}>• {ins}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Collapsible Executed Python Code View */}
                {msg.executed_code && (
                  <div className="mt-2.5 pt-2 border-t border-zinc-800">
                    <button
                      onClick={() => toggleCodeExpansion(msg.id)}
                      className="flex items-center justify-between w-full text-xs text-zinc-300 hover:text-white transition-colors"
                    >
                      <span className="flex items-center gap-1.5 font-mono">
                        <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                        Executed Python Code
                      </span>
                      {isCodeExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>

                    {isCodeExpanded && (
                      <pre className="mt-1.5 p-2.5 bg-zinc-950 rounded-md border border-zinc-800 text-xs font-mono text-zinc-200 overflow-x-auto whitespace-pre-wrap">
                        {msg.executed_code}
                      </pre>
                    )}
                  </div>
                )}
              </div>

              <span className="text-xs text-zinc-400 font-mono px-1">
                {msg.timestamp}
              </span>
            </div>
          );
        })}

        {isProcessing && (
          <div className="flex items-center gap-2 p-3 bg-zinc-900 border border-zinc-800 rounded-lg max-w-[80%] text-xs text-zinc-400">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
            <span>Executing Python sandbox & computing figures...</span>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Box */}
      <div className="p-3 border-t border-zinc-800 bg-zinc-950">
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            placeholder={sessionId ? "Ask in English or Hinglish..." : "Upload dataset first..."}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isProcessing || !sessionId}
            className="w-full bg-zinc-900 border border-zinc-800 rounded-md pl-3 pr-10 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 disabled:opacity-40"
          />
          <button
            type="submit"
            disabled={isProcessing || !inputQuery.trim() || !sessionId}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-3 h-3" />
          </button>
        </form>
      </div>
    </aside>
  );
};

