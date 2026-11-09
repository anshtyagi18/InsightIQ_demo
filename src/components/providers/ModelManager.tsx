import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from '@/hooks/use-toast';
import { 
  Plus, 
  Save, 
  Edit,
  Trash2,
  Brain,
  Eye,
  Settings,
  DollarSign,
  Clock,
  Zap,
  Image,
  Code,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { api } from '@/services/api';

interface Model {
  id: string;
  name: string;
  provider_id: string;
  litellm_model: string;
  context_length: number;
  input_cost_per_token: number;
  output_cost_per_token: number;
  supports_functions: boolean;
  description?: string;
  enabled: boolean;
}

interface Provider {
  id: string;
  name: string;
  litellm_prefix?: string;
  enabled: boolean;
}

interface ModelManagerProps {
  providers: Record<string, Provider>;
  models: Record<string, Model>;
  onModelAdded?: () => void;
  onModelUpdated?: () => void;
  onModelDeleted?: () => void;
}

const ModelManager: React.FC<ModelManagerProps> = ({ 
  providers, 
  models, 
  onModelAdded, 
  onModelUpdated,
  onModelDeleted 
}) => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<Model | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  
  const [newModel, setNewModel] = useState({
    name: '',
    provider_id: '',
    litellm_model: '',
    context_length: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0,
    supports_functions: false,
    description: '',
    enabled: true
  });

  const resetNewModel = () => {
    setNewModel({
      name: '',
      provider_id: '',
      litellm_model: '',
      context_length: 4096,
      input_cost_per_token: 0.0,
      output_cost_per_token: 0.0,
      supports_functions: false,
      description: '',
      enabled: true
    });
  };

  const generateModelId = (name: string, providerId: string): string => {
    return `${providerId}-${name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`;
  };

  const generateLiteLLMModel = (providerId: string, modelName: string): string => {
    const provider = providers[providerId];
    const prefix = provider?.litellm_prefix || '';
    
    if (prefix) {
      return `${prefix}${modelName}`;
    }
    return modelName;
  };

  const handleProviderChange = (providerId: string) => {
    setNewModel(prev => ({
      ...prev,
      provider_id: providerId,
      litellm_model: generateLiteLLMModel(providerId, prev.name)
    }));
  };

  const handleNameChange = (name: string) => {
    setNewModel(prev => ({
      ...prev,
      name,
      litellm_model: generateLiteLLMModel(prev.provider_id, name)
    }));
  };

  const handleAddModel = async () => {
    if (!newModel.name || !newModel.provider_id) {
      toast({
        title: "Error",
        description: "Please fill in all required fields",
        variant: "destructive"
      });
      return;
    }

    try {
      setSaving(true);
      
      const modelData = {
        ...newModel,
        id: generateModelId(newModel.name, newModel.provider_id)
      };

      await api.post('/api/v1/providers/models', modelData);
      
      toast({
        title: "Success",
        description: `Model "${newModel.name}" added successfully!`
      });
      
      setIsAddDialogOpen(false);
      resetNewModel();
      
      if (onModelAdded) {
        onModelAdded();
      }
      
    } catch (error) {
      console.error('Failed to add model:', error);
      toast({
        title: "Error",
        description: "Failed to add model",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleEditModel = (model: Model) => {
    setEditingModel({ ...model });
    setIsEditDialogOpen(true);
  };

  const handleUpdateModel = async () => {
    if (!editingModel) return;

    try {
      setSaving(true);
      
      await api.put(`/api/v1/providers/models/${editingModel.id}`, editingModel);
      
      toast({
        title: "Success",
        description: `Model "${editingModel.name}" updated successfully!`
      });
      
      setIsEditDialogOpen(false);
      setEditingModel(null);
      
      if (onModelUpdated) {
        onModelUpdated();
      }
      
    } catch (error) {
      console.error('Failed to update model:', error);
      toast({
        title: "Error",
        description: "Failed to update model",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteModel = async (modelId: string, modelName: string) => {
    if (!confirm(`Are you sure you want to delete the model "${modelName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setDeleting(modelId);
      
      await api.delete(`/api/v1/providers/models/${modelId}`);
      
      toast({
        title: "Success",
        description: `Model "${modelName}" deleted successfully!`
      });
      
      if (onModelDeleted) {
        onModelDeleted();
      }
      
    } catch (error) {
      console.error('Failed to delete model:', error);
      toast({
        title: "Error",
        description: "Failed to delete model",
        variant: "destructive"
      });
    } finally {
      setDeleting(null);
    }
  };

  const formatCost = (cost: number): string => {
    if (cost === 0) return 'Free';
    if (cost < 0.000001) return `$${(cost * 1000000).toFixed(2)}/M tokens`;
    if (cost < 0.001) return `$${(cost * 1000).toFixed(2)}/K tokens`;
    return `$${cost.toFixed(6)}/token`;
  };

  const getEnabledProviders = () => {
    return Object.values(providers).filter(p => p.enabled);
  };

  const getModelsByProvider = (providerId: string): Model[] => {
    return Object.values(models).filter(model => model.provider_id === providerId);
  };

  const ModelForm = ({ model, onChange }: { model: any, onChange: (updates: any) => void }) => (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="model-name">Model Name *</Label>
          <Input
            id="model-name"
            value={model.name}
            onChange={(e) => onChange({ name: e.target.value })}
            placeholder="e.g., GPT-4o, Claude 3.5 Sonnet"
          />
        </div>
        
        <div>
          <Label htmlFor="provider">Provider *</Label>
          <Select 
            value={model.provider_id} 
            onValueChange={(value) => onChange({ provider_id: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select provider" />
            </SelectTrigger>
            <SelectContent>
              {getEnabledProviders().map(provider => (
                <SelectItem key={provider.id} value={provider.id}>
                  {provider.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="litellm-model">LiteLLM Model Identifier *</Label>
        <Input
          id="litellm-model"
          value={model.litellm_model}
          onChange={(e) => onChange({ litellm_model: e.target.value })}
          placeholder="e.g., gpt-4o, claude-3-5-sonnet-20241022"
        />
        <p className="text-sm text-muted-foreground mt-1">
          The exact model identifier used by LiteLLM. Include provider prefix if required.
        </p>
      </div>

      <div>
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={model.description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="Brief description of the model's capabilities"
          rows={2}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <Label htmlFor="context-length">Context Length</Label>
          <Input
            id="context-length"
            type="number"
            value={model.context_length}
            onChange={(e) => onChange({ context_length: parseInt(e.target.value) || 0 })}
            placeholder="4096"
          />
        </div>
        
        <div>
          <Label htmlFor="input-cost">Input Cost ($/token)</Label>
          <Input
            id="input-cost"
            type="number"
            step="0.000001"
            value={model.input_cost_per_token}
            onChange={(e) => onChange({ input_cost_per_token: parseFloat(e.target.value) || 0 })}
            placeholder="0.000001"
          />
        </div>
        
        <div>
          <Label htmlFor="output-cost">Output Cost ($/token)</Label>
          <Input
            id="output-cost"
            type="number"
            step="0.000001"
            value={model.output_cost_per_token}
            onChange={(e) => onChange({ output_cost_per_token: parseFloat(e.target.value) || 0 })}
            placeholder="0.000003"
          />
        </div>
      </div>

      <div className="space-y-3">
        <Label>Capabilities</Label>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Switch
              id="supports-functions"
              checked={model.supports_functions}
              onCheckedChange={(checked) => onChange({ supports_functions: checked })}
            />
            <Label htmlFor="supports-functions" className="flex items-center gap-2">
              <Code className="h-4 w-4" />
              Function Calling
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-medium">
                Recommended
              </span>
            </Label>
          </div>
          
          <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <Code className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-blue-900">Function Calling is Essential</p>
                <p className="text-blue-700 mt-1">
                  This feature enables structured AI responses for dashboard generation, 
                  comparison analysis, and conversational analytics. Keep this enabled 
                  for optimal system performance.
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Switch
              id="enabled"
              checked={model.enabled}
              onCheckedChange={(checked) => onChange({ enabled: checked })}
            />
            <Label htmlFor="enabled" className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Enable Model
            </Label>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">AI Model Management</h2>
          <p className="text-muted-foreground">
            Add and configure AI models for your providers. Models are used by the system's AI agents.
          </p>
        </div>
        
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Add Model
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New AI Model</DialogTitle>
              <DialogDescription>
                Configure a new AI model that can be used by the system's agents.
              </DialogDescription>
            </DialogHeader>

            <ModelForm 
              model={newModel} 
              onChange={(updates) => {
                if (updates.name !== undefined) {
                  handleNameChange(updates.name);
                } else if (updates.provider_id !== undefined) {
                  handleProviderChange(updates.provider_id);
                } else {
                  setNewModel(prev => ({ ...prev, ...updates }));
                }
              }}
            />

            <div className="flex gap-3 pt-4">
              <Button
                onClick={handleAddModel}
                disabled={!newModel.name || !newModel.provider_id || saving}
                className="flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Adding...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Add Model
                  </>
                )}
              </Button>
              
              <Button 
                variant="outline" 
                onClick={() => {
                  setIsAddDialogOpen(false);
                  resetNewModel();
                }}
              >
                Cancel
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Models by Provider */}
      <div className="space-y-6">
        {Object.values(providers).filter(p => p.enabled).map(provider => {
          const providerModels = getModelsByProvider(provider.id);
          
          return (
            <Card key={provider.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  {provider.name}
                  <Badge variant="outline">{providerModels.length} models</Badge>
                </CardTitle>
                <CardDescription>
                  AI models available through {provider.name}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {providerModels.length === 0 ? (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      No models configured for this provider. Add a model to get started.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {providerModels.map(model => (
                      <Card key={model.id} className="relative">
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <CardTitle className="text-sm flex items-center gap-2">
                                {model.name}
                                {!model.enabled && <Badge variant="secondary" className="text-xs">Disabled</Badge>}
                              </CardTitle>
                              <CardDescription className="text-xs">
                                {model.litellm_model}
                              </CardDescription>
                            </div>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditModel(model)}
                                className="h-8 w-8 p-0"
                              >
                                <Edit className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteModel(model.id, model.name)}
                                disabled={deleting === model.id}
                                className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                              >
                                {deleting === model.id ? (
                                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-destructive"></div>
                                ) : (
                                  <Trash2 className="h-3 w-3" />
                                )}
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="pt-0 space-y-2">
                          <div className="text-xs space-y-1">
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              <span>{model.context_length.toLocaleString()} tokens</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <DollarSign className="h-3 w-3" />
                              <span>In: {formatCost(model.input_cost_per_token)}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <DollarSign className="h-3 w-3" />
                              <span>Out: {formatCost(model.output_cost_per_token)}</span>
                            </div>
                          </div>
                          
                          <div className="flex gap-1 flex-wrap">
                            {model.supports_functions && (
                              <Badge variant="outline" className="text-xs">
                                <Code className="h-2 w-2 mr-1" />
                                Functions
                              </Badge>
                            )}
                          </div>
                          
                          {model.description && (
                            <p className="text-xs text-muted-foreground">
                              {model.description}
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Edit Model Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Model</DialogTitle>
            <DialogDescription>
              Update the configuration for this AI model.
            </DialogDescription>
          </DialogHeader>

          {editingModel && (
            <ModelForm 
              model={editingModel} 
              onChange={(updates) => setEditingModel(prev => prev ? ({ ...prev, ...updates }) : null)}
            />
          )}

          <div className="flex gap-3 pt-4">
            <Button
              onClick={handleUpdateModel}
              disabled={!editingModel || saving}
              className="flex items-center gap-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Updating...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Update Model
                </>
              )}
            </Button>
            
            <Button 
              variant="outline" 
              onClick={() => {
                setIsEditDialogOpen(false);
                setEditingModel(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ModelManager; 