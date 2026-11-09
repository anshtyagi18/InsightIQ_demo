import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Eye, 
  ArrowRight, 
  Sparkles, 
  Brain, 
  Zap, 
  Target, 
  MessageCircle, 
  Rocket, 
  ChartBar,
  Shield,
  Globe,
  TrendingUp,
  CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const Homepage = () => {
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Intelligence",
      description: "Advanced machine learning algorithms automatically analyze your data patterns",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: Zap,
      title: "Lightning Fast Insights",
      description: "Generate comprehensive dashboards and insights in seconds, not hours",
      color: "from-cyan-500 to-teal-500"
    },
    {
      icon: Target,
      title: "Precision Analytics",
      description: "Pinpoint accuracy in trend detection and business metric calculations",
      color: "from-teal-500 to-green-500"
    },
    {
      icon: MessageCircle,
      title: "Conversational Interface",
      description: "Ask questions in natural language and get intelligent visual responses",
      color: "from-green-500 to-yellow-500"
    },
    {
      icon: Rocket,
      title: "Predictive Modeling",
      description: "Forecast future trends with advanced statistical models and ML",
      color: "from-yellow-500 to-orange-500"
    },
    {
      icon: ChartBar,
      title: "Smart Visualizations",
      description: "Automatically generate the perfect charts for your data story",
      color: "from-orange-500 to-red-500"
    }
  ];

  const stats = [
    { number: "10M+", label: "Data Points Processed" },
    { number: "50K+", label: "Dashboards Created" },
    { number: "99.9%", label: "Uptime Guarantee" },
    { number: "24/7", label: "AI-Powered Support" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-pink-500/10 rounded-full blur-2xl animate-pulse delay-500"></div>
        <div className="absolute top-10 right-10 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl animate-pulse delay-2000"></div>
        <div className="absolute bottom-10 left-10 w-40 h-40 bg-emerald-500/10 rounded-full blur-2xl animate-pulse delay-1500"></div>
      </div>

      {/* Navigation Header */}
      <nav className="relative z-50 flex items-center justify-between p-6 lg:px-8">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-r from-blue-500 via-teal-500 via-green-500 via-orange-500 to-purple-600 flex items-center justify-center shadow-lg">
            <Eye className="w-6 h-6 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">InsightIQ</span>
            <span className="text-xs text-blue-300/70">Intelligence Platform</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <Link to="/dashboard">
            <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white">
              Launch Application
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10">
        <section className="pt-20 pb-32 px-6 lg:px-8">
          <div className="mx-auto max-w-7xl text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full border border-blue-400/30 mb-8 backdrop-blur-sm">
              <Sparkles className="w-5 h-5 text-blue-400 animate-pulse" />
              <span className="text-base font-medium text-blue-200">Next-Generation AI Analytics Platform</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold mb-8 leading-tight">
              <span className="bg-gradient-to-r from-blue-400 via-teal-400 via-green-400 via-orange-400 to-purple-400 bg-clip-text text-transparent drop-shadow-2xl">
                See Your Data
              </span>
              <br />
              <span className="text-white drop-shadow-lg">Like Never Before</span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl md:text-2xl text-white/80 mb-12 max-w-4xl mx-auto leading-relaxed">
              Transform your data into intelligent visual insights with InsightIQ's advanced AI. 
              Upload, analyze, and discover patterns in minutes, not hours.
            </p>

            {/* CTA Button */}
            <div className="flex justify-center items-center mb-16">
              <Link to="/dashboard">
                <Button
                  size="lg"
                  className="group relative bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-12 py-6 text-xl font-bold shadow-2xl shadow-blue-500/25 transition-all duration-300 hover:shadow-3xl hover:shadow-blue-500/40 hover:scale-105 rounded-2xl min-w-[320px]"
                >
                  <Rocket className="w-6 h-6 mr-3" />
                  Launch Dashboard
                  <ArrowRight className="w-6 h-6 ml-3 group-hover:translate-x-1 transition-transform" />
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-400 rounded-2xl blur opacity-0 group-hover:opacity-30 transition-opacity duration-300 -z-10"></div>
                </Button>
              </Link>
            </div>

            {/* Trust Indicators */}
            <div className="flex flex-wrap justify-center items-center gap-8 text-white/50 text-sm mb-20">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-400" />
                <span>Enterprise-grade security</span>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-purple-400" />
                <span>Supports 15+ file formats</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-pink-400" />
                <span>Real-time analytics</span>
              </div>
            </div>

            {/* Stats Section */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
                    {stat.number}
                  </div>
                  <div className="text-white/60 text-sm">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-6 lg:px-8 bg-black/20 backdrop-blur-sm">
          <div className="mx-auto max-w-7xl">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                Powered by Advanced AI
              </h2>
              <p className="text-xl text-white/70 max-w-3xl mx-auto">
                Experience the future of data analytics with cutting-edge artificial intelligence
                that understands your data and generates insights automatically.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <Card key={index} className="group relative bg-white/5 border-white/10 backdrop-blur-sm hover:bg-white/10 transition-all duration-300 hover:scale-105 overflow-hidden">
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}></div>
                  <CardContent className="p-8">
                    <div className={`inline-flex p-3 rounded-xl bg-gradient-to-r ${feature.color} bg-opacity-20 mb-6`}>
                      <feature.icon className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-4">{feature.title}</h3>
                    <p className="text-white/70 leading-relaxed">{feature.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 px-6 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Ready to Transform Your Data?
            </h2>
            <p className="text-xl text-white/70 mb-12">
              Join thousands of businesses already using InsightIQ to make smarter, data-driven decisions.
            </p>
            <div className="flex justify-center">
              <Link to="/dashboard">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-12 py-6 text-xl font-bold shadow-2xl shadow-blue-500/25 transition-all duration-300 hover:scale-105 rounded-2xl"
                >
                  Start Free Trial
                  <ArrowRight className="w-6 h-6 ml-3" />
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 bg-black/40 backdrop-blur-sm py-12 px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-r from-blue-500 via-teal-500 via-green-500 via-orange-500 to-purple-600 flex items-center justify-center">
                <Eye className="w-4 h-4 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">InsightIQ</span>
                <span className="text-xs text-blue-300/70">Intelligence Platform</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-8 text-white/60">
              <Link to="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
              <Link to="/profile" className="hover:text-white transition-colors">Profile</Link>
              <span className="text-white/40">© 2026 InsightIQ</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Homepage; 