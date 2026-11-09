/**
 * Advanced Analytics Upload Component
 * Specialized upload interface for advanced statistical analysis and AI-powered insights
 */

import React, { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, Brain, BarChart3, TrendingUp, Zap, MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { ConversationalAnalytics } from '@/components/chat/conversational-analytics';

interface AdvancedAnalyticsUploadProps {
  onAnalysisComplete: (dashboard: any) => void;
  isLoading?: boolean;
}

export const AdvancedAnalyticsUpload: React.FC<AdvancedAnalyticsUploadProps> = ({
  onAnalysisComplete,
  isLoading = false
}) => {
  const [businessContext, setBusinessContext] = useState('');
  const [analysisType, setAnalysisType] = useState<'standard' | 'advanced' | 'chat'>('advanced');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showChatMode, setShowChatMode] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.name.endsWith('.xlsx') || selectedFile.name.endsWith('.xls')) {
        setFile(selectedFile);
        setError(null);
        
        // Auto-trigger chat mode if selected
        if (analysisType === 'chat') {
          setShowChatMode(true);
        }
      } else {
        setError('Please upload an Excel file (.xlsx or .xls)');
        setFile(null);
      }
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (businessContext.trim()) {
        formData.append('business_context', businessContext.trim());
      }

      const endpoint = analysisType === 'advanced' 
        ? '/api/dashboard/generate-advanced'
        : '/api/dashboard/generate';

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success && result.dashboard) {
        onAnalysisComplete(result.dashboard);
      } else {
        throw new Error(result.message || 'Analysis failed');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed');
    }
  };

  const advancedFeatures = [
    { icon: BarChart3, label: 'Correlation Analysis', desc: 'Statistical relationship mapping' },
    { icon: TrendingUp, label: 'Distribution Testing', desc: 'Normality and skewness analysis' },
    { icon: Brain, label: 'AI Pattern Recognition', desc: 'Machine learning insights' },
    { icon: Zap, label: 'Outlier Detection', desc: 'Anomaly identification' }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-white">Advanced Analytics Engine</h1>
        <p className="text-white/70">
          AI-powered statistical analysis with sophisticated visualizations and predictive insights
        </p>
      </div>

      {/* Analysis Type Toggle */}
      <Card className="bg-white/5 border-white/20">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Analysis Mode
          </CardTitle>
          <CardDescription className="text-white/70">
            Choose between standard dashboard generation or advanced statistical analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <Button
              variant={analysisType === 'standard' ? 'default' : 'outline'}
              onClick={() => setAnalysisType('standard')}
              className="flex-1"
            >
              Standard Analysis
            </Button>
            <Button
              variant={analysisType === 'advanced' ? 'default' : 'outline'}
              onClick={() => setAnalysisType('advanced')}
              className="flex-1"
            >
              Advanced Analytics
            </Button>
            <Button
              variant={analysisType === 'chat' ? 'default' : 'outline'}
              onClick={() => setAnalysisType('chat')}
              className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            >
              <MessageCircle className="w-4 h-4 mr-2" />
              Chat Mode
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Chat Mode Description */}
      {analysisType === 'chat' && (
        <Card className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-400/30">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              Conversational Analytics
            </CardTitle>
            <CardDescription className="text-white/70">
              AI agent guides you through personalized dashboard creation via natural conversation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm text-white/80">
                <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                <span>Upload your data and I'll analyze what you're working with</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-white/80">
                <div className="w-2 h-2 bg-pink-400 rounded-full"></div>
                <span>Tell me your goals, preferred chart types, and visualization needs</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-white/80">
                <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                <span>Get perfectly customized analytics based on our conversation</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Advanced Features Preview */}
      {analysisType === 'advanced' && (
        <Card className="bg-white/5 border-white/20">
          <CardHeader>
            <CardTitle className="text-white">Advanced Features</CardTitle>
            <CardDescription className="text-white/70">
              Powerful statistical and AI capabilities included in advanced mode
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {advancedFeatures.map((feature, index) => (
                <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-white/5">
                  <feature.icon className="w-5 h-5 text-blue-400 mt-0.5" />
                  <div>
                    <div className="text-white font-medium text-sm">{feature.label}</div>
                    <div className="text-white/60 text-xs">{feature.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* File Upload */}
      <Card className="bg-white/5 border-white/20">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5" />
            Upload Excel File
          </CardTitle>
          <CardDescription className="text-white/70">
            Upload your Excel file for analysis (.xlsx or .xls format)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200
              ${file 
                ? 'border-green-400 bg-green-500/10' 
                : 'border-white/30 hover:border-white/50 hover:bg-white/5'
              }
              ${isLoading ? 'cursor-not-allowed opacity-50' : ''}
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileSelect}
              className="hidden"
              disabled={isLoading}
            />
            <Upload className={`w-12 h-12 mx-auto mb-4 ${
              file ? 'text-green-400' : 'text-white/60'
            }`} />
            
            {file ? (
              <div className="space-y-2">
                <p className="text-white font-medium">{file.name}</p>
                <p className="text-green-400 text-sm">
                  ✓ File ready for analysis ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
                <Badge variant="outline" className="border-green-400 text-green-300">
                  Excel File
                </Badge>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-white">
                  Click to select an Excel file for analysis
                </p>
                <p className="text-white/60 text-sm">
                  Supports .xlsx and .xls formats
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Business Context */}
      <Card className="bg-white/5 border-white/20">
        <CardHeader>
          <CardTitle className="text-white">Business Context (Optional)</CardTitle>
          <CardDescription className="text-white/70">
            Provide context about your data to get more relevant insights and recommendations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="context" className="text-white/90">
              Describe your data and analysis goals
            </Label>
            <Textarea
              id="context"
              placeholder="e.g., Sales data from Q4 2024, looking for revenue trends and customer patterns..."
              value={businessContext}
              onChange={(e) => setBusinessContext(e.target.value)}
              className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert className="border-red-500/50 bg-red-500/10">
          <AlertDescription className="text-red-300">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Conversational Analytics Mode */}
      {showChatMode && file && analysisType === 'chat' && (
        <div className="mt-8">
          <ConversationalAnalytics 
            onAnalyticsGenerated={(dashboard) => {
              setShowChatMode(false);
              onAnalysisComplete(dashboard);
            }}
          />
        </div>
      )}

      {/* Analysis Button - Hidden in chat mode when chat is active */}
      {!(showChatMode && analysisType === 'chat') && (
        <Card className="bg-white/5 border-white/20">
          <CardContent className="pt-6">
          {analysisType === 'chat' && file ? (
            <Button
              onClick={() => setShowChatMode(true)}
              disabled={isLoading}
              size="lg"
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            >
              <MessageCircle className="w-4 h-4 mr-2" />
              Start Conversational Analytics
            </Button>
          ) : (
            <Button
              onClick={handleAnalyze}
              disabled={!file || isLoading}
              size="lg"
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                {analysisType === 'advanced' ? 'Running Advanced Analytics...' : 'Analyzing Data...'}
              </>
            ) : (
              <>
                {analysisType === 'advanced' ? (
                  <>
                    <Brain className="w-4 h-4 mr-2" />
                    Generate Advanced Analytics Dashboard
                  </>
                ) : (
                  <>
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Generate Standard Dashboard
                  </>
                )}
              </>
            )}
          </Button>
          )}
          
          {file && (
            <p className="text-white/60 text-sm text-center mt-3">
              {analysisType === 'advanced' 
                ? 'Advanced analysis may take 30-60 seconds to complete'
                : analysisType === 'chat'
                ? 'Click above to start your personalized analytics conversation'
                : 'Analysis typically completes in 10-20 seconds'
              }
            </p>
          )}
        </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AdvancedAnalyticsUpload; 