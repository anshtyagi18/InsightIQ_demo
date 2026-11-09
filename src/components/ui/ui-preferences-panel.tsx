import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useTheme } from '@/contexts/ThemeContext';
import { UIPreferences } from '@/services/enhanced-ui.service';
import { Palette, Zap, Eye, Monitor, Accessibility, Save, RefreshCw } from 'lucide-react';

interface UIPreferencesPanelProps {
  className?: string;
  onClose?: () => void;
}

export const UIPreferencesPanel: React.FC<UIPreferencesPanelProps> = ({ 
  className = '',
  onClose 
}) => {
  const { theme, preferences, updatePreferences, isLoading } = useTheme();
  const [tempPreferences, setTempPreferences] = useState<UIPreferences>(preferences);
  const [isSaving, setIsSaving] = useState(false);

  const handlePreferenceChange = (key: keyof UIPreferences, value: any) => {
    // Force theme to always be dark
    if (key === 'theme') {
      value = 'dark';
    }
    setTempPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Ensure theme is always dark before saving
      const darkModePrefs = { ...tempPreferences, theme: 'dark' as const };
      await updatePreferences(darkModePrefs);
      console.log('✅ UI preferences saved successfully');
    } catch (error) {
      console.error('❌ Failed to save UI preferences:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setTempPreferences(preferences);
  };

  const hasChanges = JSON.stringify(tempPreferences) !== JSON.stringify(preferences);

  return (
    <Card className={`glass-card border-white/10 ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-r from-purple-500/20 to-pink-500/20">
              <Palette className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-white">UI Preferences</CardTitle>
              <CardDescription className="text-white/60">
                Customize your dashboard experience with database-backed settings
              </CardDescription>
            </div>
          </div>
          {hasChanges && (
            <Badge variant="secondary" className="bg-blue-500/20 text-blue-300 border-blue-400/30">
              Unsaved changes
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Theme Settings */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Monitor className="w-4 h-4 text-blue-400" />
            <Label className="text-white font-medium">Theme & Appearance</Label>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-white/80 text-sm">Color Theme</Label>
              <div className="flex items-center gap-2 p-3 rounded-md bg-white/5 border border-white/20">
                <span className="text-white">🌙 Dark Mode</span>
                <Badge className="ml-auto bg-green-500/20 text-green-400 border-green-500/30">
                  Active
                </Badge>
              </div>
              <p className="text-xs text-white/60">
                This application is optimized for dark mode only
              </p>
            </div>

            <div className="space-y-2">
              <Label className="text-white/80 text-sm">Display Density</Label>
              <Select 
                value={tempPreferences.density} 
                onValueChange={(value: 'compact' | 'normal' | 'spacious') => handlePreferenceChange('density', value)}
              >
                <SelectTrigger className="bg-white/5 border-white/20 text-white">
                  <SelectValue placeholder="Select density" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="compact">🔹 Compact</SelectItem>
                  <SelectItem value="normal">🔸 Normal</SelectItem>
                  <SelectItem value="spacious">🔶 Spacious</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <Separator className="bg-white/10" />

        {/* Animation Settings */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-400" />
            <Label className="text-white font-medium">Animations & Transitions</Label>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label className="text-white/80">Enable Animations</Label>
                <p className="text-xs text-white/60">Smooth transitions and micro-interactions</p>
              </div>
              <Switch
                checked={tempPreferences.animations}
                onCheckedChange={(checked) => handlePreferenceChange('animations', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label className="text-white/80">Reduce Motion</Label>
                <p className="text-xs text-white/60">Minimize animations for accessibility</p>
              </div>
              <Switch
                checked={tempPreferences.reducedMotion}
                onCheckedChange={(checked) => handlePreferenceChange('reducedMotion', checked)}
              />
            </div>
          </div>
        </div>

        <Separator className="bg-white/10" />

        {/* Typography & Layout */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-green-400" />
            <Label className="text-white font-medium">Typography & Layout</Label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-white/80 text-sm">Font Size</Label>
              <Select 
                value={tempPreferences.fontSize} 
                onValueChange={(value: 'small' | 'medium' | 'large') => handlePreferenceChange('fontSize', value)}
              >
                <SelectTrigger className="bg-white/5 border-white/20 text-white">
                  <SelectValue placeholder="Select font size" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="small">📝 Small</SelectItem>
                  <SelectItem value="medium">📄 Medium</SelectItem>
                  <SelectItem value="large">📰 Large</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-white/80 text-sm">Contrast</Label>
              <Select 
                value={tempPreferences.contrast} 
                onValueChange={(value: 'normal' | 'high') => handlePreferenceChange('contrast', value)}
              >
                <SelectTrigger className="bg-white/5 border-white/20 text-white">
                  <SelectValue placeholder="Select contrast" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="normal">🎨 Normal</SelectItem>
                  <SelectItem value="high">🔆 High Contrast</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <Separator className="bg-white/10" />

        {/* Sidebar Settings */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Accessibility className="w-4 h-4 text-purple-400" />
            <Label className="text-white font-medium">Layout Preferences</Label>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label className="text-white/80">Collapsed Sidebar</Label>
              <p className="text-xs text-white/60">Start with sidebar collapsed by default</p>
            </div>
            <Switch
              checked={tempPreferences.sidebarCollapsed}
              onCheckedChange={(checked) => handlePreferenceChange('sidebarCollapsed', checked)}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={!hasChanges || isSaving}
            className="bg-white/5 border-white/20 text-white hover:bg-white/10"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset
          </Button>

          <div className="flex items-center gap-3">
            {onClose && (
              <Button
                variant="ghost"
                onClick={onClose}
                className="text-white/70 hover:text-white hover:bg-white/10"
              >
                Cancel
              </Button>
            )}
            <Button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-0"
            >
              {isSaving ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Status Info */}
        <div className="pt-2 text-xs text-white/50 text-center">
          Preferences are automatically synchronized across all your devices
        </div>
      </CardContent>
    </Card>
  );
}; 