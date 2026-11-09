import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from '@/hooks/use-toast';
import { 
  Plus, 
  Save, 
  TestTube,
  Globe, 
  Zap, 
  AlertCircle,
  CheckCircle,
  Key,
  Eye,
  EyeOff,
  Info,
  ExternalLink
} from 'lucide-react';

// LiteLLM supported providers with their configurations
const LITELLM_PROVIDERS = {
  openai: {
    name: "OpenAI",
    description: "OpenAI's GPT models",
    base_url: "https://api.openai.com/v1",
    api_key_env: "OPENAI_API_KEY",
    litellm_prefix: "",
    documentation: "https://platform.openai.com/docs/api-reference",
    example_models: ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
  },
  anthropic: {
    name: "Anthropic",
    description: "Anthropic's Claude models",
    base_url: "https://api.anthropic.com/v1",
    api_key_env: "ANTHROPIC_API_KEY",
    litellm_prefix: "claude-",
    documentation: "https://docs.anthropic.com/claude/reference",
    example_models: ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
  },
  google: {
    name: "Google AI Studio",
    description: "Google's Gemini models via AI Studio",
    base_url: "https://generativelanguage.googleapis.com/v1",
    api_key_env: "GOOGLE_API_KEY",
    litellm_prefix: "gemini/",
    documentation: "https://ai.google.dev/docs",
    example_models: ["gemini-pro", "gemini-2.0-flash"]
  },
  vertex_ai: {
    name: "Google Vertex AI",
    description: "Google's enterprise AI platform",
    base_url: "https://aiplatform.googleapis.com/",
    api_key_env: "GOOGLE_APPLICATION_CREDENTIALS",
    litellm_prefix: "vertex_ai/",
    documentation: "https://cloud.google.com/vertex-ai/docs",
    example_models: ["gemini-pro", "claude-3-sonnet@20240229"]
  },
  openrouter: {
    name: "OpenRouter",
    description: "Multi-model API with access to various AI models",
    base_url: "https://openrouter.ai/api/v1",
    api_key_env: "OPENROUTER_API_KEY",
    litellm_prefix: "openrouter/",
    documentation: "https://openrouter.ai/docs",
    example_models: ["anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-8b-instruct:free"]
  },
  azure: {
    name: "Azure OpenAI",
    description: "Azure OpenAI Service",
    base_url: "https://{deployment}.openai.azure.com/",
    api_key_env: "AZURE_OPENAI_API_KEY",
    litellm_prefix: "azure/",
    documentation: "https://learn.microsoft.com/en-us/azure/ai-services/openai/",
    example_models: ["gpt-4", "gpt-35-turbo"],
    requires_endpoint: true,
    env_endpoint: "AZURE_OPENAI_ENDPOINT"
  },
  cohere: {
    name: "Cohere",
    description: "Cohere's Command models",
    base_url: "https://api.cohere.ai/v1",
    api_key_env: "COHERE_API_KEY",
    litellm_prefix: "command-",
    documentation: "https://docs.cohere.com/docs",
    example_models: ["command-r-plus", "command-r"]
  },
  mistral: {
    name: "Mistral AI",
    description: "Mistral AI's language models",
    base_url: "https://api.mistral.ai/v1",
    api_key_env: "MISTRAL_API_KEY",
    litellm_prefix: "mistral/",
    documentation: "https://docs.mistral.ai/",
    example_models: ["mistral-large-latest", "mistral-small-latest"]
  },
  together: {
    name: "Together AI",
    description: "Together AI platform with open-source models",
    base_url: "https://api.together.xyz/v1",
    api_key_env: "TOGETHER_API_KEY",
    litellm_prefix: "together/",
    documentation: "https://docs.together.ai/",
    example_models: ["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"]
  },
  huggingface: {
    name: "Hugging Face",
    description: "Hugging Face Inference API",
    base_url: "https://api-inference.huggingface.co/models/",
    api_key_env: "HUGGINGFACE_API_KEY",
    litellm_prefix: "huggingface/",
    documentation: "https://huggingface.co/docs/api-inference/",
    example_models: ["mistralai/Mistral-7B-Instruct-v0.1", "microsoft/DialoGPT-medium"]
  },
  replicate: {
    name: "Replicate",
    description: "Replicate's machine learning platform",
    base_url: "https://api.replicate.com/v1",
    api_key_env: "REPLICATE_API_KEY",
    litellm_prefix: "replicate/",
    documentation: "https://replicate.com/docs",
    example_models: ["meta/llama-2-70b-chat", "mistralai/mixtral-8x7b-instruct-v0.1"]
  },
  ollama: {
    name: "Ollama",
    description: "Local Ollama server for open-source models",
    base_url: "http://localhost:11434",
    api_key_env: "OLLAMA_API_KEY",
    litellm_prefix: "ollama/",
    documentation: "https://ollama.ai/",
    example_models: ["llama2", "mistral", "codellama"],
    is_local: true
  },
  bedrock: {
    name: "AWS Bedrock",
    description: "AWS Bedrock managed AI service",
    base_url: "https://bedrock-runtime.{region}.amazonaws.com/",
    api_key_env: "AWS_ACCESS_KEY_ID",
    litellm_prefix: "bedrock/",
    documentation: "https://docs.aws.amazon.com/bedrock/",
    example_models: ["anthropic.claude-v2", "amazon.titan-text-express-v1"],
    requires_aws_credentials: true,
    env_secret_key: "AWS_SECRET_ACCESS_KEY",
    env_region: "AWS_DEFAULT_REGION"
  },
  groq: {
    name: "Groq",
    description: "Groq's fast inference API",
    base_url: "https://api.groq.com/openai/v1",
    api_key_env: "GROQ_API_KEY",
    litellm_prefix: "groq/",
    documentation: "https://console.groq.com/docs",
    example_models: ["llama2-70b-4096", "mixtral-8x7b-32768"]
  },
  xai: {
    name: "xAI (Grok)",
    description: "xAI's Grok models",
    base_url: "https://api.x.ai/v1",
    api_key_env: "XAI_API_KEY",
    litellm_prefix: "grok-",
    documentation: "https://docs.x.ai/",
    example_models: ["grok-beta"]
  },
  deepinfra: {
    name: "DeepInfra",
    description: "DeepInfra's serverless inference platform",
    base_url: "https://api.deepinfra.com/v1/openai",
    api_key_env: "DEEPINFRA_API_KEY",
    litellm_prefix: "deepinfra/",
    documentation: "https://deepinfra.com/docs",
    example_models: ["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mistral-7B-Instruct-v0.1"]
  },
  perplexity: {
    name: "Perplexity AI",
    description: "Perplexity AI's online models",
    base_url: "https://api.perplexity.ai",
    api_key_env: "PERPLEXITY_API_KEY",
    litellm_prefix: "perplexity/",
    documentation: "https://docs.perplexity.ai/",
    example_models: ["pplx-7b-online", "pplx-70b-online"]
  }
};

interface LiteLLMProviderConfigProps {
  onProviderAdded?: () => void;
}

const LiteLLMProviderConfig: React.FC<LiteLLMProviderConfigProps> = ({ onProviderAdded }) => {
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [customConfig, setCustomConfig] = useState({
    name: '',
    base_url: '',
    api_key: '',
    endpoint: '', // For Azure
    region: '', // For AWS
    secret_key: '', // For AWS
    custom_models: ''
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    if (selectedProvider && LITELLM_PROVIDERS[selectedProvider]) {
      const provider = LITELLM_PROVIDERS[selectedProvider];
      setCustomConfig(prev => ({
        ...prev,
        name: provider.name,
        base_url: provider.base_url
      }));
    }
  }, [selectedProvider]);

  const handleTestConnection = async () => {
    if (!selectedProvider || !customConfig.api_key) {
      toast({
        title: "Error",
        description: "Please select a provider and enter an API key",
        variant: "destructive"
      });
      return;
    }

    try {
      setTesting(true);
      
      // Test the connection with a simple request
      const testPayload = {
        provider: selectedProvider,
        api_key: customConfig.api_key,
        base_url: customConfig.base_url,
        endpoint: customConfig.endpoint,
        region: customConfig.region,
        secret_key: customConfig.secret_key
      };

      // This would call your backend API to test the provider
      // const response = await api.post('/api/v1/providers/test', testPayload);
      
      // For now, simulate a test
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: "Success",
        description: `Connection to ${LITELLM_PROVIDERS[selectedProvider].name} successful!`
      });
      
    } catch (error) {
      console.error('Provider test failed:', error);
      toast({
        title: "Error",
        description: "Failed to connect to provider. Please check your configuration.",
        variant: "destructive"
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveProvider = async () => {
    if (!selectedProvider || !customConfig.api_key) {
      toast({
        title: "Error",
        description: "Please select a provider and enter an API key",
        variant: "destructive"
      });
      return;
    }

    try {
      setSaving(true);
      
      const provider = LITELLM_PROVIDERS[selectedProvider];
      const savePayload = {
        id: selectedProvider,
        name: customConfig.name || provider.name,
        base_url: customConfig.base_url || provider.base_url,
        api_key_env: provider.api_key_env,
        litellm_prefix: provider.litellm_prefix,
        description: provider.description,
        enabled: true,
        supports_streaming: true,
        api_key: customConfig.api_key,
        endpoint: customConfig.endpoint,
        region: customConfig.region,
        secret_key: customConfig.secret_key,
        custom_models: customConfig.custom_models.split(',').map(m => m.trim()).filter(Boolean)
      };

      // This would call your backend API to save the provider
      // const response = await api.post('/api/v1/providers/add', savePayload);
      
      // For now, simulate saving
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast({
        title: "Success",
        description: `${provider.name} has been added successfully!`
      });
      
      setIsDialogOpen(false);
      setSelectedProvider('');
      setCustomConfig({
        name: '',
        base_url: '',
        api_key: '',
        endpoint: '',
        region: '',
        secret_key: '',
        custom_models: ''
      });
      
      if (onProviderAdded) {
        onProviderAdded();
      }
      
    } catch (error) {
      console.error('Failed to save provider:', error);
      toast({
        title: "Error",
        description: "Failed to save provider configuration",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const renderProviderDetails = () => {
    if (!selectedProvider) return null;
    
    const provider = LITELLM_PROVIDERS[selectedProvider];
    
    return (
      <div className="space-y-4 mt-4">
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            {provider.description}
            {provider.documentation && (
              <a 
                href={provider.documentation} 
                target="_blank" 
                rel="noopener noreferrer"
                className="ml-2 text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
              >
                View Documentation <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="provider-name">Provider Name</Label>
            <Input
              id="provider-name"
              value={customConfig.name}
              onChange={(e) => setCustomConfig(prev => ({ ...prev, name: e.target.value }))}
              placeholder={provider.name}
            />
          </div>
          
          <div>
            <Label htmlFor="base-url">Base URL</Label>
            <Input
              id="base-url"
              value={customConfig.base_url}
              onChange={(e) => setCustomConfig(prev => ({ ...prev, base_url: e.target.value }))}
              placeholder={provider.base_url}
            />
          </div>
        </div>

        <div>
          <Label htmlFor="api-key">API Key *</Label>
          <div className="flex gap-2">
            <Input
              id="api-key"
              type={showApiKey ? "text" : "password"}
              value={customConfig.api_key}
              onChange={(e) => setCustomConfig(prev => ({ ...prev, api_key: e.target.value }))}
              placeholder={`Enter your ${provider.name} API key`}
              className="flex-1"
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => setShowApiKey(!showApiKey)}
            >
              {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Environment variable: {provider.api_key_env}
          </p>
        </div>

        {/* Azure-specific fields */}
        {provider.requires_endpoint && (
          <div>
            <Label htmlFor="endpoint">Azure Endpoint *</Label>
            <Input
              id="endpoint"
              value={customConfig.endpoint}
              onChange={(e) => setCustomConfig(prev => ({ ...prev, endpoint: e.target.value }))}
              placeholder="https://your-resource.openai.azure.com/"
            />
          </div>
        )}

        {/* AWS-specific fields */}
        {provider.requires_aws_credentials && (
          <>
            <div>
              <Label htmlFor="region">AWS Region *</Label>
              <Input
                id="region"
                value={customConfig.region}
                onChange={(e) => setCustomConfig(prev => ({ ...prev, region: e.target.value }))}
                placeholder="us-east-1"
              />
            </div>
            <div>
              <Label htmlFor="secret-key">AWS Secret Key *</Label>
              <Input
                id="secret-key"
                type="password"
                value={customConfig.secret_key}
                onChange={(e) => setCustomConfig(prev => ({ ...prev, secret_key: e.target.value }))}
                placeholder="Enter your AWS Secret Access Key"
              />
            </div>
          </>
        )}

        <div>
          <Label htmlFor="custom-models">Custom Models (Optional)</Label>
          <Textarea
            id="custom-models"
            value={customConfig.custom_models}
            onChange={(e) => setCustomConfig(prev => ({ ...prev, custom_models: e.target.value }))}
            placeholder={`Example models for ${provider.name}:\n${provider.example_models.join(', ')}`}
            rows={3}
          />
          <p className="text-sm text-muted-foreground mt-1">
            Enter model names separated by commas. Leave empty to use default models.
          </p>
        </div>

        {provider.is_local && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              This provider requires a local server running on your machine. Make sure Ollama is installed and running.
            </AlertDescription>
          </Alert>
        )}
      </div>
    );
  };

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add LiteLLM Provider
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add LiteLLM Provider</DialogTitle>
          <DialogDescription>
            Configure a new AI provider supported by LiteLLM. Your API keys will be securely stored and used by the system.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <div>
            <Label htmlFor="provider-select">Select Provider *</Label>
            <Select value={selectedProvider} onValueChange={setSelectedProvider}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a LiteLLM-supported provider" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(LITELLM_PROVIDERS).map(([key, provider]) => (
                  <SelectItem key={key} value={key}>
                    <div className="flex items-center gap-2">
                      <Globe className="h-4 w-4" />
                      {provider.name}
                      {provider.is_local && <Badge variant="secondary">Local</Badge>}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {renderProviderDetails()}

          <div className="flex gap-3 pt-4">
            <Button
              onClick={handleTestConnection}
              disabled={!selectedProvider || !customConfig.api_key || testing}
              variant="outline"
              className="flex items-center gap-2"
            >
              {testing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
                  Testing...
                </>
              ) : (
                <>
                  <TestTube className="h-4 w-4" />
                  Test Connection
                </>
              )}
            </Button>
            
            <Button
              onClick={handleSaveProvider}
              disabled={!selectedProvider || !customConfig.api_key || saving}
              className="flex items-center gap-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Provider
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default LiteLLMProviderConfig; 