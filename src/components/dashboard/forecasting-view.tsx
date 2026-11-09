import React, { useState, useMemo } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Calendar, 
  BarChart2, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  Info,
  Sliders,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { 
  DatasetProfile, 
  generateForecast, 
  ForecastResult, 
  formatValue 
} from '@/services/bi-engine';

interface ForecastingViewProps {
  data: Record<string, any>[];
  profile: DatasetProfile;
  datasetName?: string;
}

export const ForecastingView: React.FC<ForecastingViewProps> = ({
  data,
  profile,
  datasetName = 'Dataset'
}) => {
  const [selectedMetric, setSelectedMetric] = useState<string>(
    profile.primaryMetric || profile.numericColumns[0] || ''
  );
  const [selectedDateCol, setSelectedDateCol] = useState<string>(
    profile.primaryDate || profile.dateColumns[0] || ''
  );
  const [horizon, setHorizon] = useState<number>(6);
  const [confidenceLevel, setConfidenceLevel] = useState<number>(90);

  // Re-generate forecast when inputs change
  const forecast: ForecastResult = useMemo(() => {
    return generateForecast(data, profile, {
      dateCol: selectedDateCol || undefined,
      metricCol: selectedMetric || undefined,
      horizon: horizon,
      confidenceLevel: confidenceLevel
    });
  }, [data, profile, selectedDateCol, selectedMetric, horizon, confidenceLevel]);

  const isCurrency = selectedMetric.toLowerCase().match(/(sales|revenue|profit|cost|price|amount)/);
  const fmtType = isCurrency ? 'currency' : 'number';

  if (forecast.status === 'no_date_column') {
    return (
      <div className="space-y-6">
        <Alert className="bg-amber-950/40 border-amber-800/60 text-amber-200 p-6 rounded-2xl">
          <AlertCircle className="w-6 h-6 text-amber-400 mt-0.5 mr-3" />
          <div>
            <AlertTitle className="text-lg font-semibold text-amber-300">No Date/Time Column Detected</AlertTitle>
            <AlertDescription className="text-sm text-amber-200/90 mt-2 space-y-2">
              <p>
                Statistical time-series forecasting requires a recognized chronological date or timestamp column in your dataset.
              </p>
              <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 text-xs font-mono text-slate-300 space-y-1">
                <div className="font-sans font-semibold text-slate-200 mb-1">Supported Date Formats:</div>
                <div>• ISO 8601: <span className="text-emerald-400">2026-08-12</span></div>
                <div>• US Standard: <span className="text-emerald-400">08/12/2026</span></div>
                <div>• Full Date String: <span className="text-emerald-400">2026/08/12 14:30</span></div>
              </div>
            </AlertDescription>
          </div>
        </Alert>
      </div>
    );
  }

  if (forecast.status === 'insufficient_data') {
    return (
      <div className="space-y-6">
        <Alert className="bg-amber-950/40 border-amber-800/60 text-amber-200 p-6 rounded-2xl">
          <AlertCircle className="w-6 h-6 text-amber-400 mt-0.5 mr-3" />
          <div>
            <AlertTitle className="text-lg font-semibold text-amber-300">Insufficient Historical Time Points</AlertTitle>
            <AlertDescription className="text-sm text-amber-200/90 mt-2">
              {forecast.message} Please upload a dataset with a longer chronological history or aggregate by a different time frequency.
            </AlertDescription>
          </div>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Forecasting Control Panel */}
      <Card className="bg-slate-900/90 border-slate-800 rounded-2xl shadow-xl backdrop-blur-md">
        <CardHeader className="pb-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
                Predictive Trend Forecasting
              </CardTitle>
              <CardDescription className="text-slate-400 text-xs mt-1">
                Automated statistical projection using historical linear trend & dampening model
              </CardDescription>
            </div>
            <Badge variant="outline" className="border-emerald-500/40 bg-emerald-950/50 text-emerald-300 px-3 py-1 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
              R² Fit Score: {forecast.modelConfidenceScore}%
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
            {/* Metric Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <BarChart2 className="w-3.5 h-3.5 text-cyan-400" /> Target Metric
              </label>
              <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-200 text-xs h-9">
                  <SelectValue placeholder="Select metric" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700 text-slate-200">
                  {profile.numericColumns.map(col => (
                    <SelectItem key={col} value={col} className="text-xs">
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Date Column Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-purple-400" /> Date Dimension
              </label>
              <Select value={selectedDateCol} onValueChange={setSelectedDateCol}>
                <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-200 text-xs h-9">
                  <SelectValue placeholder="Select date column" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700 text-slate-200">
                  {profile.dateColumns.map(col => (
                    <SelectItem key={col} value={col} className="text-xs">
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Horizon Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-emerald-400" /> Forecast Horizon
              </label>
              <Select value={String(horizon)} onValueChange={val => setHorizon(Number(val))}>
                <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-200 text-xs h-9">
                  <SelectValue placeholder="Horizon" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700 text-slate-200">
                  <SelectItem value="3" className="text-xs">3 Future Periods</SelectItem>
                  <SelectItem value="6" className="text-xs">6 Future Periods</SelectItem>
                  <SelectItem value="12" className="text-xs">12 Future Periods</SelectItem>
                  <SelectItem value="24" className="text-xs">24 Future Periods</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Confidence Interval Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-amber-400" /> Confidence Band
              </label>
              <Select value={String(confidenceLevel)} onValueChange={val => setConfidenceLevel(Number(val))}>
                <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-200 text-xs h-9">
                  <SelectValue placeholder="Confidence" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700 text-slate-200">
                  <SelectItem value="80" className="text-xs">80% Confidence Interval</SelectItem>
                  <SelectItem value="90" className="text-xs">90% Confidence Interval</SelectItem>
                  <SelectItem value="95" className="text-xs">95% Confidence Interval</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPI Cards for Forecast Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-slate-900/80 border-slate-800 p-5 rounded-2xl shadow-lg">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Baseline (Last Actual)</div>
          <div className="text-2xl font-bold text-white">
            {formatValue(forecast.historicalBaseline, fmtType)}
          </div>
          <div className="text-xs text-slate-500 mt-1">Most recent historical data point</div>
        </Card>

        <Card className="bg-slate-900/80 border-slate-800 p-5 rounded-2xl shadow-lg">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Projected End Value</div>
          <div className="text-2xl font-bold text-emerald-400">
            {formatValue(forecast.forecastEndValue, fmtType)}
          </div>
          <div className="text-xs text-slate-500 mt-1">At end of period {horizon}</div>
        </Card>

        <Card className="bg-slate-900/80 border-slate-800 p-5 rounded-2xl shadow-lg">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Projected Change</div>
          <div className="flex items-center gap-2">
            <span className={`text-2xl font-bold ${
              (forecast.projectedChangePercent || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}>
              {(forecast.projectedChangePercent || 0) >= 0 ? '+' : ''}{forecast.projectedChangePercent}%
            </span>
            <Badge variant="outline" className={`${
              (forecast.projectedChangePercent || 0) >= 0 
                ? 'border-emerald-500/40 text-emerald-300 bg-emerald-950/40' 
                : 'border-rose-500/40 text-rose-300 bg-rose-950/40'
            } text-xs px-2 py-0.5`}>
              {(forecast.projectedChangePercent || 0) >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
              {forecast.trendDirection?.toUpperCase()}
            </Badge>
          </div>
          <div className="text-xs text-slate-500 mt-1">Total change over forecast horizon</div>
        </Card>

        <Card className="bg-slate-900/80 border-slate-800 p-5 rounded-2xl shadow-lg">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Model Accuracy</div>
          <div className="text-2xl font-bold text-cyan-400">
            {forecast.modelConfidenceScore}%
          </div>
          <div className="text-xs text-slate-500 mt-1">R² Statistical Variance Fit</div>
        </Card>
      </div>

      {/* Main Forecast Visual Chart */}
      <Card className="bg-slate-900/90 border-slate-800 rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-white">
              Historical vs. Projected {selectedMetric} Forecast
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Solid line represents historical actuals; dashed line shows projected forecast with {confidenceLevel}% confidence range.
            </p>
          </div>
        </div>

        <div className="h-[380px] w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={forecast.chartData} margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 11, fill: '#94a3b8' }} 
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
              />
              <YAxis 
                tick={{ fontSize: 11, fill: '#94a3b8' }} 
                axisLine={{ stroke: '#475569' }}
                tickFormatter={(val) => formatValue(val, fmtType)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.95)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  borderRadius: '12px',
                  color: '#f8fafc',
                  fontSize: '13px',
                  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'
                }}
                formatter={(value: any, name: string) => [
                  value !== null ? formatValue(Number(value), fmtType) : 'N/A',
                  name
                ]}
              />
              <Legend 
                wrapperStyle={{ fontSize: '12px', color: '#cbd5e1', paddingTop: '10px' }} 
              />
              {/* Upper / Lower Confidence Band */}
              <Area 
                type="monotone" 
                dataKey="upperBound" 
                stroke="transparent" 
                fill="#10b981" 
                fillOpacity={0.12} 
                name="Confidence Range (Upper)" 
              />
              <Area 
                type="monotone" 
                dataKey="lowerBound" 
                stroke="transparent" 
                fill="#0f172a" 
                fillOpacity={0.8} 
                name="Confidence Range (Lower)" 
              />
              {/* Historical Line */}
              <Line 
                type="monotone" 
                dataKey="historical" 
                stroke="#3b82f6" 
                strokeWidth={3} 
                dot={{ r: 3, fill: '#3b82f6' }}
                activeDot={{ r: 6 }} 
                name="Historical Actuals" 
              />
              {/* Forecast Line */}
              <Line 
                type="monotone" 
                dataKey="forecast" 
                stroke="#10b981" 
                strokeWidth={3} 
                strokeDasharray="6 6" 
                dot={{ r: 4, fill: '#10b981' }}
                activeDot={{ r: 7 }} 
                name="Projected Forecast" 
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Business Narrative & Key Takeaways */}
      <Card className="bg-slate-900/80 border-slate-800 rounded-2xl p-6 shadow-xl">
        <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-emerald-400" /> Executive Forecast Explanation
        </h4>
        
        <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 mb-4">
          {forecast.narrativeSummary}
        </p>

        <div className="space-y-2">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Key Takeaways & Insights</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {forecast.keyTakeaways?.map((takeaway, idx) => (
              <div key={idx} className="flex items-start gap-2.5 p-3 bg-slate-950/40 rounded-lg border border-slate-800/50 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{takeaway}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
};
