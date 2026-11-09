/**
 * Preline Survey View Component
 * Styled in Pure Smooth Z-Black (#0e0e11) with crisp zinc-800 separators.
 */

import React, { useState } from 'react';
import { 
  MessageSquare, 
  Star, 
  ThumbsUp, 
  CheckCircle2, 
  TrendingUp, 
  Smile
} from 'lucide-react';

export const PrelineSurveyView: React.FC = () => {
  const [selectedSentiment, setSelectedSentiment] = useState<'all' | 'positive' | 'neutral' | 'negative'>('all');

  const ratingDistribution = [
    { stars: 5, percentage: 76, count: 1079 },
    { stars: 4, percentage: 16, count: 227 },
    { stars: 3, percentage: 5, count: 71 },
    { stars: 2, percentage: 2, count: 28 },
    { stars: 1, percentage: 1, count: 15 },
  ];

  const feedbackList = [
    {
      id: 1,
      author: 'Sarah Jenkins',
      role: 'VP Analytics at FinPulse',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=faces',
      rating: 5,
      date: '2 hours ago',
      comment: 'The automated outlier detection and one-click data cleaning cut our data audit time by 80%. The Preline UI is super crisp and intuitive.',
      sentiment: 'positive',
      tags: ['Data Cleaning', 'UI Craft'],
    },
    {
      id: 2,
      author: 'Marcus Vance',
      role: 'Data Engineer at TechCorp',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=faces',
      rating: 5,
      date: 'Yesterday',
      comment: 'Natural language queries in Hinglish and English work flawlessly. Verified deterministic Python math with 0% hallucination is what sold us.',
      sentiment: 'positive',
      tags: ['Copilot', 'Deterministic Math'],
    },
    {
      id: 3,
      author: 'Elena Rostova',
      role: 'Product Lead at GlobalCart',
      avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&h=100&fit=crop&crop=faces',
      rating: 4,
      date: '2 days ago',
      comment: 'The executive PDF and formatted Excel export features are great for C-suite presentations. The z-black smooth dark theme looks magnificent.',
      sentiment: 'neutral',
      tags: ['Export Engine', 'Reporting'],
    },
  ];

  const filteredFeedback = feedbackList.filter((item) => {
    if (selectedSentiment === 'all') return true;
    return item.sentiment === selectedSentiment;
  });

  return (
    <div className="space-y-6 select-none">
      {/* View Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              Survey &amp; User Feedback
            </h1>
            <span className="text-[11px] font-semibold bg-blue-600/15 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20">
              Beta
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Customer sentiment analysis, CSAT scores, and Net Promoter telemetry
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-xs transition-colors">
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Create Survey</span>
          </button>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Total Responses</span>
            <MessageSquare className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">1,420</span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> 18.2%
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">High participation rate</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>CSAT Score</span>
            <Smile className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">4.8 / 5.0</span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> +0.3
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Top tier satisfaction</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Net Promoter Score</span>
            <ThumbsUp className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">+64 NPS</span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> +5 pts
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Classified: Excellent (&gt;50)</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Completion Rate</span>
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">94.2%</span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> 1.8%
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Avg 1m 15s to finish</p>
        </div>
      </div>

      {/* Breakdown Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Rating Bars (Col 5) */}
        <div className="lg:col-span-5 bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <h3 className="text-sm font-bold text-zinc-100 mb-4">
            Rating Distribution
          </h3>
          <div className="space-y-3">
            {ratingDistribution.map((item) => (
              <div key={item.stars} className="flex items-center gap-3">
                <div className="flex items-center gap-1 w-16 text-xs text-zinc-300 font-medium">
                  <span>{item.stars}</span>
                  <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                </div>
                <div className="flex-1 bg-[#18181d] h-2.5 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-400 h-2.5 rounded-full"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
                <span className="w-12 text-right text-xs font-mono font-bold text-zinc-300">
                  {item.percentage}%
                </span>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-[#27272a]">
            <div className="flex items-center justify-between text-xs text-zinc-400">
              <span>Overall Positive Ratio</span>
              <span className="font-bold text-emerald-400">92%</span>
            </div>
          </div>
        </div>

        {/* Verbatim Feedback Cards (Col 7) */}
        <div className="lg:col-span-7 bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-zinc-100">
                Customer Testimonials
              </h3>
              <div className="flex items-center gap-1 bg-[#141418] border border-[#27272a] p-1 rounded-lg text-xs font-medium text-zinc-300">
                <button
                  onClick={() => setSelectedSentiment('all')}
                  className={`px-2 py-0.5 rounded transition-colors ${selectedSentiment === 'all' ? 'bg-[#22222a] border border-zinc-700/60 font-bold text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'}`}
                >
                  All
                </button>
                <button
                  onClick={() => setSelectedSentiment('positive')}
                  className={`px-2 py-0.5 rounded transition-colors ${selectedSentiment === 'positive' ? 'bg-[#22222a] border border-zinc-700/60 font-bold text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'}`}
                >
                  Positive
                </button>
                <button
                  onClick={() => setSelectedSentiment('neutral')}
                  className={`px-2 py-0.5 rounded transition-colors ${selectedSentiment === 'neutral' ? 'bg-[#22222a] border border-zinc-700/60 font-bold text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'}`}
                >
                  Neutral
                </button>
              </div>
            </div>

            <div className="space-y-3">
              {filteredFeedback.map((f) => (
                <div key={f.id} className="p-3.5 bg-[#141418] border border-[#27272a] rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <img src={f.avatar} alt={f.author} className="w-7 h-7 rounded-full object-cover border border-[#27272a]" />
                      <div>
                        <p className="text-xs font-bold text-zinc-100">{f.author}</p>
                        <p className="text-[10px] text-zinc-500">{f.role}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-0.5">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star
                          key={i}
                          className={`w-3 h-3 ${
                            i < f.rating ? 'fill-amber-400 text-amber-400' : 'text-zinc-700'
                          }`}
                        />
                      ))}
                    </div>
                  </div>

                  <p className="text-xs text-zinc-300 leading-relaxed">
                    "{f.comment}"
                  </p>

                  <div className="flex items-center gap-1.5 pt-1">
                    {f.tags.map((tag) => (
                      <span key={tag} className="text-[10px] bg-[#1a1a20] border border-[#27272a] text-zinc-300 px-2 py-0.5 rounded">
                        {tag}
                      </span>
                    ))}
                    <span className="text-[10px] text-zinc-500 ml-auto">{f.date}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
