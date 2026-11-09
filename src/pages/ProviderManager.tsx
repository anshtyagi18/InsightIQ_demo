import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from '@/hooks/use-toast';
import { 
  Settings, 
  Globe, 
  Zap, 
  AlertCircle,
  CheckCircle,
  Cpu,
  Brain,
  Key,
  Eye,
  EyeOff,
  Save,
  TestTube
} from 'lucide-react';
import { api } from '@/services/api';
import ModelManager from '@/components/providers/ModelManager';

// Types
interface Provider {
  id: string;
  name: string;
  base_url: string;
  api_key_env: string;
  description?: string;
  enabled: boolean;
  supports_streaming: boolean;
  rate_limit?: any;
  api_key_configured?: boolean;
}

interface Model {
  id: string;
  name: string;
  provider_id: string;
  litellm_model: string;
  context_length: number;
  input_cost_per_token: number;
  output_cost_per_token: number;
  supports_functions: boolean;
  supports_vision: boolean;
  description?: string;
  enabled: boolean;
}

interface ProviderSelection {
  main_provider: string;
  main_model: string;
  fallback_provider?: string;
  fallback_model?: string;
  research_provider?: string;
  research_model?: string;
}

interface AIConfiguration {
  main_model: string;
  fallback_models: string[];
  provider: string;
  base_url?: string;
  litellm_enabled?: boolean;
  selected_main_model?: string;
  selected_fallback_models?: string[];
}

const ProviderManager: React.FC = () => {
  const [providers, setProviders] = useState<Record<string, Provider>>({});
  const [models, setModels] = useState<Record<string, Model>>({});
  const [selection, setSelection] = useState<ProviderSelection>({
    main_provider: '',
    main_model: ''
  });
  const [aiConfig, setAiConfig] = useState<AIConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  // API Key management state
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [testingProviders, setTestingProviders] = useState<Record<string, boolean>>({});
  const [savingApiKeys, setSavingApiKeys] = useState<Record<string, boolean>>({});

  // Load data on component mount
  useEffect(() => {
    loadProviderData();
  }, []);

  const loadProviderData = async () => {
    try {
      setLoading(true);
      
      // Load providers, models, current selection, and AI configuration
      const [providersRes, modelsRes, selectionRes, aiConfigRes] = await Promise.all([
        api.get('/api/v1/providers/'),
        api.get('/api/v1/providers/models'),
        api.get('/api/v1/providers/selection'),
        api.get('/api/v1/providers/ai-config')
      ]);
      
      console.log('API Responses:', { providersRes, modelsRes, selectionRes, aiConfigRes });
      
      // Handle different response structures
      setProviders(providersRes?.data?.providers || providersRes?.providers || {});
      setModels(modelsRes?.data?.models || modelsRes?.models || {});
      setSelection(selectionRes?.data?.selection || selectionRes?.selection || { main_provider: '', main_model: '' });
      setAiConfig(aiConfigRes?.data?.ai_configuration || aiConfigRes?.ai_configuration || null);
      
    } catch (error) {
      console.error('Failed to load provider data:', error);
      toast({
        title: "Error",
        description: "Failed to load provider configuration. Please ensure the backend server is running.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const updateSelection = async (newSelection: ProviderSelection) => {
    try {
      setSaving(true);
      
      const response = await api.put('/api/v1/providers/selection', newSelection);
      console.log('Update selection response:', response);
      
      setSelection(newSelection);
      
      // Reload AI configuration to show the updated settings
      try {
        const aiConfigRes = await api.get('/api/v1/providers/ai-config');
        setAiConfig(aiConfigRes?.data?.ai_configuration || aiConfigRes?.ai_configuration || null);
      } catch (err) {
        console.warn('Could not reload AI configuration:', err);
      }
      
      toast({
        title: "Success",
        description: "Provider selection updated successfully. AI agents will now use the new configuration."
      });
      
    } catch (error) {
      console.error('Failed to update selection:', error);
      toast({
        title: "Error",
        description: "Failed to update provider selection",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const getProviderModels = (providerId: string): Model[] => {
    return Object.values(models).filter(model => model.provider_id === providerId);
  };

  const formatCost = (cost: number): string => {
    if (cost === 0) return 'Free';
    if (cost < 0.000001) return `$${(cost * 1000000).toFixed(2)}/M tokens`;
    if (cost < 0.001) return `$${(cost * 1000).toFixed(2)}/K tokens`;
    return `$${cost.toFixed(6)}/token`;
  };

  const updateApiKey = async (providerId: string, apiKey: string, validateKey: boolean = false) => {
    try {
      setSavingApiKeys(prev => ({ ...prev, [providerId]: true }));
      
      const response = await api.put(`/api/v1/providers/${providerId}/api-key`, {
        api_key: apiKey,
        validate_key: validateKey
      });
      
      console.log('Update API key response:', response);
      
      // Update local state
      setProviders(prev => ({
        ...prev,
        [providerId]: {
          ...prev[providerId],
          api_key_configured: true
        }
      }));
      
      toast({
        title: "Success",
        description: `API key updated successfully for ${providers[providerId]?.name || providerId}${
          response.validation ? 
            (response.validation.valid ? " and validated" : " but validation failed") : 
            ""
        }`
      });
      
      // Clear the input after successful update
      setApiKeys(prev => ({ ...prev, [providerId]: '' }));
      
    } catch (error) {
      console.error('Failed to update API key:', error);
      toast({
        title: "Error",
        description: `Failed to update API key for ${providers[providerId]?.name || providerId}`,
        variant: "destructive"
      });
    } finally {
      setSavingApiKeys(prev => ({ ...prev, [providerId]: false }));
    }
  };

  const testApiKey = async (providerId: string) => {
    try {
      setTestingProviders(prev => ({ ...prev, [providerId]: true }));
      
      const response = await api.post(`/api/v1/providers/test/${providerId}`);
      
      toast({
        title: response.status === 'success' ? "Success" : "Error",
        description: response.message,
        variant: response.status === 'success' ? "default" : "destructive"
      });
      
    } catch (error) {
      console.error('Failed to test provider:', error);
      toast({
        title: "Error", 
        description: `Failed to test ${providers[providerId]?.name || providerId}`,
        variant: "destructive"
      });
    } finally {
      setTestingProviders(prev => ({ ...prev, [providerId]: false }));
    }
  };

  const toggleApiKeyVisibility = (providerId: string) => {
    setShowApiKeys(prev => ({ ...prev, [providerId]: !prev[providerId] }));
  };

  const ProviderOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Providers</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(providers).length}</div>
            <p className="text-xs text-muted-foreground">
              {Object.values(providers).filter(p => p.enabled).length} enabled
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Models</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(models).length}</div>
            <p className="text-xs text-muted-foreground">
              {Object.values(models).filter(m => m.enabled).length} enabled
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Configuration Status</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.values(providers).filter(p => p.api_key_configured).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Configured providers
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Current AI Configuration */}
      {aiConfig && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              Active AI Configuration
            </CardTitle>
            <CardDescription>
              Configuration currently being used by AI agents
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <Label>Current Main Model</Label>
                <p className="text-muted-foreground font-mono">{aiConfig.main_model}</p>
              </div>
              <div>
                <Label>Provider</Label>
                <p className="text-muted-foreground">{aiConfig.provider}</p>
              </div>
              <div className="md:col-span-2">
                <Label>Fallback Models</Label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {aiConfig.fallback_models?.map((model, index) => (
                    <Badge key={index} variant="outline" className="font-mono text-xs">
                      {model}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                {aiConfig.litellm_enabled ? 
                  "LiteLLM is enabled. AI agents are using the dynamically selected models." :
                  "LiteLLM is disabled. Using fallback configuration."
                }
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* Current Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Current Selection</CardTitle>
          <CardDescription>
            Active provider and model configuration for AI operations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="main-provider">Main Provider</Label>
              <Select
                value={selection.main_provider}
                onValueChange={(value) => {
                  const newSelection = { ...selection, main_provider: value };
                  // Reset main model when provider changes
                  const providerModels = getProviderModels(value);
                  if (providerModels.length > 0) {
                    newSelection.main_model = providerModels[0].id;
                  }
                  updateSelection(newSelection);
                }}
                disabled={saving}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(providers)
                    .filter(p => p.enabled && p.api_key_configured)
                    .map(provider => (
                      <SelectItem key={provider.id} value={provider.id}>
                        <div className="flex items-center gap-2">
                          {provider.api_key_configured ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-orange-500" />
                          )}
                          {provider.name}
                        </div>
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="main-model">Main Model</Label>
              <Select
                value={selection.main_model}
                onValueChange={(value) => {
                  updateSelection({ ...selection, main_model: value });
                }}
                disabled={saving || !selection.main_provider}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {getProviderModels(selection.main_provider).map(model => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center gap-2">
                        <Cpu className="h-4 w-4" />
                        {model.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const ApiKeysTab = () => (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">API Key Management</h2>
        <p className="text-muted-foreground">
          Configure API keys for your AI providers. Keys are stored securely and used for authentication.
        </p>
      </div>
      
      <div className="space-y-4">
        {Object.values(providers).map(provider => (
          <Card key={provider.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Key className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <CardTitle>{provider.name}</CardTitle>
                    <CardDescription>
                      Environment Variable: <code className="text-xs bg-muted px-1 py-0.5 rounded">{provider.api_key_env}</code>
                    </CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={provider.api_key_configured ? 'default' : 'destructive'}>
                    {provider.api_key_configured ? 'Configured' : 'Not Configured'}
                  </Badge>
                  {provider.api_key_configured && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => testApiKey(provider.id)}
                      disabled={testingProviders[provider.id]}
                    >
                      {testingProviders[provider.id] ? (
                        <Settings className="h-4 w-4 animate-spin" />
                      ) : (
                        <TestTube className="h-4 w-4" />
                      )}
                      Test
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Input
                    type={showApiKeys[provider.id] ? "text" : "password"}
                    placeholder={provider.api_key_configured ? "Enter new API key to update" : "Enter your API key"}
                    value={apiKeys[provider.id] || ''}
                    onChange={(e) => setApiKeys(prev => ({ ...prev, [provider.id]: e.target.value }))}
                    className="pr-10"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0"
                    onClick={() => toggleApiKeyVisibility(provider.id)}
                  >
                    {showApiKeys[provider.id] ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <Button
                  onClick={() => updateApiKey(provider.id, apiKeys[provider.id], false)}
                  disabled={!apiKeys[provider.id]?.trim() || savingApiKeys[provider.id]}
                  className="shrink-0"
                >
                  {savingApiKeys[provider.id] ? (
                    <Settings className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Save
                </Button>
                <Button
                  variant="outline"
                  onClick={() => updateApiKey(provider.id, apiKeys[provider.id], true)}
                  disabled={!apiKeys[provider.id]?.trim() || savingApiKeys[provider.id]}
                  className="shrink-0"
                >
                  {savingApiKeys[provider.id] ? (
                    <Settings className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <TestTube className="h-4 w-4 mr-2" />
                  )}
                  Save & Test
                </Button>
              </div>
              
              {provider.description && (
                <p className="text-sm text-muted-foreground">
                  {provider.description}
                </p>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <Label>Base URL</Label>
                  <p className="text-muted-foreground">{provider.base_url}</p>
                </div>
                <div>
                  <Label>Features</Label>
                  <div className="flex gap-1 mt-1">
                    {provider.supports_streaming && (
                      <Badge variant="outline" className="text-xs">
                        <Zap className="h-3 w-3 mr-1" />
                        Streaming
                      </Badge>
                    )}
                    <Badge variant="outline" className="text-xs">
                      Rate Limit: {provider.rate_limit?.requests_per_minute || 'N/A'}/min
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Security Note:</strong> API keys are stored in environment variables and will persist until the server is restarted. 
          For production use, configure these keys in your server environment or .env file.
        </AlertDescription>
      </Alert>
    </div>
  );

  const ProvidersTab = () => (
    <div className="space-y-4">
      {Object.values(providers).map(provider => (
        <Card key={provider.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {provider.api_key_configured ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-orange-500" />
                  )}
                  {provider.name}
                  {!provider.enabled && <Badge variant="secondary">Disabled</Badge>}
                </CardTitle>
                <CardDescription>
                  {provider.description || 'No description available'}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                {provider.supports_streaming && (
                  <Badge variant="outline">
                    <Zap className="h-3 w-3 mr-1" />
                    Streaming
                  </Badge>
                )}
                <Badge variant={provider.api_key_configured ? 'default' : 'destructive'}>
                  {provider.api_key_configured ? 'Configured' : 'Not Configured'}
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <Label>Base URL</Label>
                <p className="text-muted-foreground">{provider.base_url}</p>
              </div>
              <div>
                <Label>API Key Environment Variable</Label>
                <p className="text-muted-foreground">{provider.api_key_env}</p>
              </div>
            </div>
            
            {/* Show models for this provider */}
            <Separator className="my-4" />
            <div>
              <Label className="text-sm font-medium">Available Models ({getProviderModels(provider.id).length})</Label>
              <div className="mt-2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {getProviderModels(provider.id).map(model => (
                  <Card key={model.id} className="p-3">
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-sm">{model.name}</p>
                        {!model.enabled && <Badge variant="secondary" className="text-xs">Disabled</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Context: {model.context_length.toLocaleString()} tokens
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        {model.supports_functions && <Badge variant="outline" className="text-xs">Functions</Badge>}
                        {model.supports_vision && <Badge variant="outline" className="text-xs">Vision</Badge>}
                      </div>
                      <div className="text-xs">
                        <span className="text-green-600">In: {formatCost(model.input_cost_per_token)}</span>
                        {' | '}
                        <span className="text-blue-600">Out: {formatCost(model.output_cost_per_token)}</span>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <Settings className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="text-muted-foreground">Loading provider configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Provider Management</h1>
          <p className="text-muted-foreground">
            Manage AI providers, models, and configuration for the InsightIQ Platform
          </p>
        </div>

        {/* API Key Warning */}
        {Object.values(providers).filter(p => !p.api_key_configured).length > 0 && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="flex items-center justify-between">
                <div>
                  <strong>Action Required:</strong> Some providers need API keys to be configured.
                  <br />
                  Missing API keys for: {Object.values(providers)
                    .filter(p => !p.api_key_configured)
                    .map(p => p.name)
                    .join(', ')}
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setActiveTab('api-keys')}
                  className="shrink-0 ml-4"
                >
                  <Key className="h-4 w-4 mr-2" />
                  Configure API Keys
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="api-keys">API Keys</TabsTrigger>
            <TabsTrigger value="providers">Providers & Models</TabsTrigger>
            <TabsTrigger value="model-manager">Model Manager</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <ProviderOverview />
          </TabsContent>

          <TabsContent value="api-keys" className="space-y-6">
            <ApiKeysTab />
          </TabsContent>

          <TabsContent value="providers" className="space-y-6">
            <ProvidersTab />
          </TabsContent>

          <TabsContent value="model-manager" className="space-y-6">
            <ModelManager 
              providers={providers} 
              models={models} 
              onModelUpdated={loadProviderData} 
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default ProviderManager; 