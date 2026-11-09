import { useState, useRef } from "react";
import { Camera, Mail, Calendar, Save, User, Shield, Bell, Palette, Clock, AlertCircle, CheckCircle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTheme } from "@/contexts/ThemeContext";

function Profile() {
  const { theme } = useTheme();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [profileData, setProfileData] = useState({
    firstName: "Analyst",
    lastName: "User",
    email: "analyst@insightiq.internal",
    profileImage: null as string | null,
    role: "Admin Analyst"
  });

  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    pushNotifications: false,
    darkMode: theme === 'dark',
    autoRefresh: 5,
    showAdvancedFeatures: true,
    dataRetention: 30,
  });

  const [activeTab, setActiveTab] = useState("personal");
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleInputChange = (field: string, value: string) => {
    setProfileData(prev => ({ ...prev, [field]: value }));
    setSaveStatus("idle");
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setErrorMessage("Image size should be less than 5MB");
        return;
      }
      
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        setProfileData(prev => ({ ...prev, profileImage: result }));
        setSaveStatus("idle");
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveChanges = async () => {
    setSaveStatus("saving");
    setErrorMessage("");
    
    try {
      setTimeout(() => {
        setSaveStatus("success");
        setTimeout(() => setSaveStatus("idle"), 3000);
      }, 300);
    } catch (error) {
      setSaveStatus("error");
      setErrorMessage("An unexpected error occurred");
    }
  };

  const togglePreference = (key: keyof typeof preferences) => {
    setPreferences(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const cycleAutoRefresh = () => {
    const intervals = [1, 5, 15, 30, 60];
    const currentIndex = intervals.indexOf(preferences.autoRefresh);
    const nextIndex = (currentIndex + 1) % intervals.length;
    setPreferences(prev => ({ ...prev, autoRefresh: intervals[nextIndex] }));
  };

  const cycleDataRetention = () => {
    const periods = [7, 30, 90, 365];
    const currentIndex = periods.indexOf(preferences.dataRetention);
    const nextIndex = (currentIndex + 1) % periods.length;
    setPreferences(prev => ({ ...prev, dataRetention: periods[nextIndex] }));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <Header />
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Profile Summary Card */}
        <div className="lg:col-span-1">
          <GlassCard className="text-center p-6">
            <div className="relative inline-block mb-4">
              <div className="w-24 h-24 rounded-full mx-auto overflow-hidden flex items-center justify-center bg-gradient-to-r from-pink-500 to-orange-500">
                {profileData.profileImage ? (
                  <img 
                    src={profileData.profileImage} 
                    alt="Profile" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-white text-2xl font-bold">
                    {profileData.firstName[0]}{profileData.lastName[0]}
                  </span>
                )}
              </div>
              <Button 
                size="sm" 
                className="absolute bottom-0 right-0 rounded-full w-8 h-8 p-0 glass-button"
                onClick={() => fileInputRef.current?.click()}
              >
                <Camera className="h-4 w-4" />
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleImageUpload}
              />
            </div>
            
            <h3 className="text-xl font-semibold text-foreground">{profileData.firstName} {profileData.lastName}</h3>
            <Badge className="mt-2 bg-blue-500/20 text-blue-400 border-blue-500/30">
              <Shield className="h-3 w-3 mr-1" />
              {profileData.role}
            </Badge>
            
            <div className="space-y-3 mt-6 text-sm">
              <div className="flex items-center justify-center space-x-2 text-muted-foreground">
                <Mail className="h-4 w-4" />
                <span className="truncate">{profileData.email}</span>
              </div>
              <div className="flex items-center justify-center space-x-2 text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Workspace Active</span>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-3 glass-card">
              <TabsTrigger value="personal" className="flex items-center space-x-2">
                <User className="h-4 w-4" />
                <span>Personal</span>
              </TabsTrigger>
              <TabsTrigger value="preferences" className="flex items-center space-x-2">
                <Palette className="h-4 w-4" />
                <span>Preferences</span>
              </TabsTrigger>
              <TabsTrigger value="notifications" className="flex items-center space-x-2">
                <Bell className="h-4 w-4" />
                <span>Notifications</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="personal">
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center">
                  <User className="h-5 w-5 mr-2" />
                  Personal Information
                </h3>
                
                {errorMessage && (
                  <Alert variant="destructive" className="mb-4 bg-red-900/20 border-red-500/30">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-red-200">{errorMessage}</AlertDescription>
                  </Alert>
                )}

                {saveStatus === "success" && (
                  <Alert className="mb-4 bg-green-900/20 border-green-500/30">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    <AlertDescription className="text-green-200">Settings updated successfully!</AlertDescription>
                  </Alert>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="firstName" className="text-foreground">First Name</Label>
                    <Input 
                      id="firstName" 
                      value={profileData.firstName}
                      onChange={(e) => handleInputChange('firstName', e.target.value)}
                      className="mt-1 bg-background/50 border-border text-foreground" 
                    />
                  </div>
                  <div>
                    <Label htmlFor="lastName" className="text-foreground">Last Name</Label>
                    <Input 
                      id="lastName" 
                      value={profileData.lastName}
                      onChange={(e) => handleInputChange('lastName', e.target.value)}
                      className="mt-1 bg-background/50 border-border text-foreground" 
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label htmlFor="email" className="text-foreground">Email Address</Label>
                    <Input 
                      id="email" 
                      type="email"
                      value={profileData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      className="mt-1 bg-background/50 border-border text-foreground" 
                    />
                  </div>
                </div>
                
                <div className="mt-6">
                  <Button
                    className="glass-button-primary"
                    onClick={handleSaveChanges}
                    disabled={saveStatus === "saving"}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {saveStatus === "saving" ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </GlassCard>
            </TabsContent>

            <TabsContent value="preferences">
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center">
                  <Palette className="h-5 w-5 mr-2" />
                  Display & Behavior
                </h3>
                
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-foreground font-medium">Auto-refresh Data</h4>
                      <p className="text-muted-foreground text-sm">Automatically refresh dashboard data every</p>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="glass-button"
                      onClick={cycleAutoRefresh}
                    >
                      <Clock className="h-4 w-4 mr-2" />
                      {preferences.autoRefresh} min{preferences.autoRefresh !== 1 ? 's' : ''}
                    </Button>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-foreground font-medium">Data Retention</h4>
                      <p className="text-muted-foreground text-sm">How long to keep historical data</p>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="glass-button"
                      onClick={cycleDataRetention}
                    >
                      {preferences.dataRetention} days
                    </Button>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-foreground font-medium">Advanced Features</h4>
                      <p className="text-muted-foreground text-sm">Show advanced analytics and debugging tools</p>
                    </div>
                    <Switch 
                      checked={preferences.showAdvancedFeatures}
                      onCheckedChange={() => togglePreference('showAdvancedFeatures')}
                    />
                  </div>
                </div>
              </GlassCard>
            </TabsContent>

            <TabsContent value="notifications">
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center">
                  <Bell className="h-5 w-5 mr-2" />
                  Notification Settings
                </h3>
                
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-foreground font-medium">Email Notifications</h4>
                      <p className="text-muted-foreground text-sm">Receive important updates via email</p>
                    </div>
                    <Switch 
                      checked={preferences.emailNotifications}
                      onCheckedChange={() => togglePreference('emailNotifications')}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-foreground font-medium">Push Notifications</h4>
                      <p className="text-muted-foreground text-sm">Get real-time alerts in your browser</p>
                    </div>
                    <Switch 
                      checked={preferences.pushNotifications}
                      onCheckedChange={() => togglePreference('pushNotifications')}
                    />
                  </div>

                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <h4 className="text-blue-400 font-medium mb-2">Notification Types</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Data processing completed</li>
                      <li>• System maintenance alerts</li>
                      <li>• Security notifications</li>
                      <li>• Feature updates and announcements</li>
                    </ul>
                  </div>
                </div>
              </GlassCard>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

export default Profile;
