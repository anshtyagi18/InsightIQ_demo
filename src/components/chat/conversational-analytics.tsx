import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Upload, Send, MessageCircle, BarChart3, Settings, Sparkles, Brain } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/services/api';
import { datasetStorage, SavedDataset } from '@/services/dataset-storage.service';
import { detectDatasetDomain, generateKPIs, generateBusinessInsights, formatValue } from '@/services/bi-engine';

interface ChatMessage {
  role: 'agent' | 'user';
  content: string;
  timestamp: string;
  message_type: 'question' | 'response' | 'analysis' | 'suggestion' | 'completion';
  data_context?: any;
}

interface DataAnalysis {
  data_type: string;
  data_summary: string;
  key_metrics: string[];
  potential_insights: string[];
  recommended_chart_types: string[];
  data_quality_score: number;
}

interface ConversationalAnalyticsProps {
  onAnalyticsGenerated: (analytics: any) => void;
  onClose?: () => void;
}

export const ConversationalAnalytics: React.FC<ConversationalAnalyticsProps> = ({
  onAnalyticsGenerated,
  onClose
}) => {
  const [phase, setPhase] = useState<'upload' | 'analysis' | 'questioning' | 'preference_gathering' | 'generation'>('questioning');
  const [sessionId, setSessionId] = useState<string | null>(`local_session_${Date.now()}`);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [dataAnalysis, setDataAnalysis] = useState<DataAnalysis | null>(null);
  const [initialQuestions, setInitialQuestions] = useState<string[]>([]);
  const [activeDataset, setActiveDataset] = useState<SavedDataset | null>(null);
  const [showGenerateButton, setShowGenerateButton] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load active dataset from storage on mount
  useEffect(() => {
    const initDataset = async () => {
      try {
        const dataset = await datasetStorage.getActiveDataset();
        if (dataset) {
          setActiveDataset(dataset);
          const domainMeta = detectDatasetDomain(dataset.cleanedRows, dataset.profile);
          const kpis = generateKPIs(dataset.cleanedRows, dataset.profile);
          const insights = generateBusinessInsights(dataset.cleanedRows, dataset.profile);

          setDataAnalysis({
            data_type: domainMeta.domainName,
            data_summary: `${dataset.rowCount} records across ${dataset.columnCount} columns. Primary metric: ${dataset.profile.primaryMetric || 'N/A'}.`,
            key_metrics: kpis.map(k => `${k.name}: ${k.unit === '$' ? '$' : ''}${k.value}`),
            potential_insights: insights.map(i => i.title),
            recommended_chart_types: ['Bar Chart', 'Line Trend', 'Donut Share', 'KPI Metrics'],
            data_quality_score: dataset.profile.completeness,
          });

          const questions = [
            `What is the primary trend in ${dataset.profile.primaryMetric || 'our dataset'}?`,
            `Show me top breakdown by ${dataset.profile.primaryDimension || 'category'}`,
            `Are there any statistical anomalies or outliers?`,
            `Summarize key KPIs for ${dataset.name}`
          ];
          setInitialQuestions(questions);

          setMessages([
            {
              role: 'agent',
              content: `Hello! I'm connected to your active dataset: **${dataset.name}** (${domainMeta.domainName}). I've analyzed ${dataset.rowCount} rows across ${dataset.columnCount} columns. What would you like to investigate?`,
              timestamp: new Date().toLocaleTimeString(),
              message_type: 'analysis',
              data_context: { datasetName: dataset.name, domain: domainMeta.domainName }
            }
          ]);
        }
      } catch (err) {
        console.warn('Failed to load active dataset for chat:', err);
      }
    };
    initDataset();
  }, []);

  const sendMessage = async (userMessageText: string) => {
    if (!userMessageText.trim()) return;
    
    const userMsg: ChatMessage = {
      role: 'user',
      content: userMessageText,
      timestamp: new Date().toLocaleTimeString(),
      message_type: 'question',
    };

    setMessages(prev => [...prev, userMsg]);
    setCurrentMessage('');
    setIsLoading(true);

    try {
      // Try API first if available, else local smart response
      if (sessionId && !sessionId.startsWith('local_session')) {
        const data = await api.post('/api/v1/chat/send-message', {
          message: userMessageText,
          session_id: sessionId,
        });
        setMessages(data.conversation_history);
        setPhase(data.phase);
        return;
      }
    } catch (err) {
      console.log('Falling back to local dataset intelligence engine...');
    }

    // Local Dataset Intelligence fallback
    setTimeout(() => {
      let botResponse = '';
      if (activeDataset) {
        const lower = userMessageText.toLowerCase();
        const profile = activeDataset.profile;
        const rows = activeDataset.cleanedRows;
        const domainMeta = detectDatasetDomain(rows, profile);
        const kpis = generateKPIs(rows, profile);
        const insights = generateBusinessInsights(rows, profile);

        if (lower.includes('kpi') || lower.includes('summary') || lower.includes('total') || lower.includes('overview')) {
          const kpiStr = kpis.map(k => `• **${k.name}**: ${k.unit === '$' ? '$' : ''}${k.value.toLocaleString()} (${k.description})`).join('\n');
          botResponse = `Here is the current KPI summary for **${activeDataset.name}**:\n\n${kpiStr}\n\n*Domain context: ${domainMeta.domainName}*`;
        } else if (lower.includes('outlier') || lower.includes('anomaly') || lower.includes('risk') || lower.includes('variance')) {
          const outlierInsight = insights.find(i => i.type === 'anomaly' || i.type === 'risk');
          botResponse = outlierInsight 
            ? `**${outlierInsight.title}**\n${outlierInsight.description}`
            : `No major statistical anomalies found. Dataset quality score is ${profile.completeness}% across ${rows.length} records.`;
        } else if (lower.includes('top') || lower.includes('breakdown') || lower.includes('category') || lower.includes('dimension')) {
          const driverInsight = insights.find(i => i.type === 'driver');
          botResponse = driverInsight
            ? `**${driverInsight.title}**\n${driverInsight.description}`
            : `Top dimension analyzed: **${profile.primaryDimension || 'Category'}** with primary metric **${profile.primaryMetric || 'Value'}**.`;
        } else {
          botResponse = `Based on **${activeDataset.name}** (${rows.length} rows):\n\n• **Primary Metric**: ${profile.primaryMetric || 'N/A'}\n• **Primary Dimension**: ${profile.primaryDimension || 'N/A'}\n• **Domain**: ${domainMeta.domainName}\n\nKey Insight: ${insights[0]?.description || 'Dataset is clean and synchronized across all InsightIQ modules.'}`;
        }
      } else {
        botResponse = `Please select or upload a dataset in the Datasets Workspace to enable data-driven answers.`;
      }

      setMessages(prev => [
        ...prev,
        {
          role: 'agent',
          content: botResponse,
          timestamp: new Date().toLocaleTimeString(),
          message_type: 'response',
        }
      ]);
      setIsLoading(false);
    }, 400);
  };

  const generateCustomAnalytics = async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    
    try {
      const data = await api.post('/api/v1/chat/generate-custom-analytics', {
        session_id: sessionId,
      });
      
      // Update messages with completion
      setMessages(data.conversation_summary);
      setPhase(data.phase);
      
      // Pass analytics to parent component
      onAnalyticsGenerated(data.analytics);
      
    } catch (error) {
      console.error('Error generating analytics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const resetChat = async () => {
    if (sessionId) {
      try {
        await api.post('/api/v1/chat/reset-chat', {
          session_id: sessionId,
        });
      } catch (error) {
        console.error('Error resetting chat:', error);
      }
    }
    
    // Reset state
    setSessionId(null);
    setMessages([]);
    setDataAnalysis(null);
    setInitialQuestions([]);
    setFile(null);
    setPhase('upload');
    setCurrentMessage('');
    setShowGenerateButton(false);
  };

  const getPhaseIcon = () => {
    switch (phase) {
      case 'upload': return <Upload className="w-5 h-5" />;
      case 'analysis': return <Brain className="w-5 h-5" />;
      case 'questioning': return <MessageCircle className="w-5 h-5" />;
      case 'preference_gathering': return <Settings className="w-5 h-5" />;
      case 'generation': return <BarChart3 className="w-5 h-5" />;
      default: return <Sparkles className="w-5 h-5" />;
    }
  };

  const getPhaseTitle = () => {
    switch (phase) {
      case 'upload': return 'Upload Your Data';
      case 'analysis': return 'Analyzing Your Data';
      case 'questioning': return 'Understanding Your Needs';
      case 'preference_gathering': return 'Finalizing Preferences';
      case 'generation': return 'Analytics Generated!';
      default: return 'Conversational Analytics';
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto glass-card">
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getPhaseIcon()}
            <div>
              <CardTitle className="text-xl bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                {getPhaseTitle()}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                AI-guided analytics configuration
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge variant={phase === 'generation' ? 'default' : 'secondary'}>
              {phase.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Badge>
            {onClose && (
              <Button variant="ghost" size="sm" onClick={onClose}>
                ×
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {phase === 'upload' && (
          <div className="text-center py-12">
            <Upload className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Start with Your Data</h3>
            <p className="text-muted-foreground mb-6">
              Upload your data file and I'll analyze it to understand what you're working with
            </p>
            
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
              className="hidden"
            />
            
            <Button 
              onClick={() => fileInputRef.current?.click()}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              disabled={isLoading}
            >
              {isLoading ? 'Analyzing...' : 'Choose File'}
            </Button>
          </div>
        )}

        {phase !== 'upload' && (
          <>
            {/* Enhanced Data Analysis Summary */}
            {dataAnalysis && (
              <div className="mb-6 p-4 bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-900/40 dark:to-pink-900/40 rounded-lg border border-purple-200 dark:border-purple-700">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  <h4 className="font-semibold text-gray-900 dark:text-gray-100">Comprehensive Data Analysis</h4>
                  <Badge variant="outline">{dataAnalysis.data_type}</Badge>
                </div>
                
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
                  {dataAnalysis.data_summary}
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-4">
                  <div>
                    <span className="font-medium text-gray-900 dark:text-gray-100">Key Metrics:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {dataAnalysis.key_metrics.slice(0, 4).map((metric, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs bg-purple-200 dark:bg-purple-800 text-purple-800 dark:text-purple-200">
                          {metric}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <span className="font-medium text-gray-900 dark:text-gray-100">Data Quality:</span>
                    <div className="mt-1">
                      <Badge 
                        variant={dataAnalysis.data_quality_score > 0.8 ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {(dataAnalysis.data_quality_score * 100).toFixed(0)}% Quality
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <span className="font-medium text-gray-900 dark:text-gray-100">Recommended Charts:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {dataAnalysis.recommended_chart_types.slice(0, 3).map((chart, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs border-purple-300 dark:border-purple-600 text-purple-700 dark:text-purple-300">
                          {chart}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Potential Insights Preview */}
                {dataAnalysis.potential_insights && dataAnalysis.potential_insights.length > 0 && (
                  <div className="border-t border-purple-200 dark:border-purple-700 pt-3">
                    <span className="font-medium text-sm text-gray-900 dark:text-gray-100">Potential Insights:</span>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 mt-1 space-y-1">
                      {dataAnalysis.potential_insights.slice(0, 3).map((insight, idx) => (
                        <li key={idx} className="flex items-start gap-1">
                          <span className="text-purple-600 dark:text-purple-400 mt-0.5">•</span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Chat Messages */}
            <div className="space-y-4 mb-6">
              <ScrollArea className="h-64 pr-4">
                {messages.map((message, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      "flex gap-3 mb-4",
                      message.role === 'user' ? "justify-end" : "justify-start"
                    )}
                  >
                    <div
                      className={cn(
                        "max-w-[80%] p-3 rounded-lg",
                        message.role === 'user'
                          ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white"
                          : "bg-muted"
                      )}
                    >
                      <div className="text-sm whitespace-pre-line">{message.content}</div>
                      {message.message_type === 'analysis' && (
                        <Badge className="mt-2" variant="secondary">
                          <Brain className="w-3 h-3 mr-1" />
                          Comprehensive Analysis
                        </Badge>
                      )}
                      {message.message_type === 'suggestion' && (
                        <Badge className="mt-2" variant="default">
                          <Sparkles className="w-3 h-3 mr-1" />
                          Dashboard Proposal
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </ScrollArea>
            </div>

            {/* Message Input */}
                        {phase !== 'generation' && (
              <>
                {/* Generate Analytics Button - Show when AI suggests it */}
                {showGenerateButton && (
                  <div className="mb-4 p-4 bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900/40 dark:to-emerald-900/40 rounded-lg border border-green-300 dark:border-green-700">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-green-600 dark:text-green-400" />
                        <span className="font-medium text-green-800 dark:text-green-200">
                          Ready to Generate Your Analytics!
                        </span>
                      </div>
                      <Button
                        onClick={generateCustomAnalytics}
                        disabled={isLoading}
                        className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                      >
                        <BarChart3 className="w-4 h-4 mr-2" />
                        Generate Dashboard
                      </Button>
                    </div>
                    <p className="text-sm text-green-700 dark:text-green-300 mt-2">
                      I've analyzed your preferences and I'm ready to create your custom analytics dashboard.
                    </p>
                  </div>
                )}

                <div className="flex gap-2">
                  <Textarea
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    placeholder="Type your response..."
                    className="flex-1 min-h-[80px] resize-none"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage(currentMessage);
                      }
                    }}
                  />
                  
                  <div className="flex flex-col gap-2">
                    <Button
                      onClick={() => sendMessage(currentMessage)}
                      disabled={isLoading || !currentMessage.trim()}
                      size="sm"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </>
            )}

            {/* Generation Complete */}
            {phase === 'generation' && (
              <div className="text-center py-8">
                <div className="w-16 h-16 mx-auto bg-gradient-to-r from-green-600 to-emerald-600 rounded-full flex items-center justify-center mb-4">
                  <BarChart3 className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Analytics Generated!</h3>
                <p className="text-muted-foreground mb-6">
                  Your custom analytics have been created based on our conversation
                </p>
                
                <div className="flex gap-3 justify-center">
                  <Button onClick={resetChat} variant="outline">
                    Start New Analysis
                  </Button>
                  {onClose && (
                    <Button onClick={onClose}>
                      View Analytics
                    </Button>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}; 