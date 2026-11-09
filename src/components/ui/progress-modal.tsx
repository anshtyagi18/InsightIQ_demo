import React from 'react';
import { Loader2, CheckCircle, AlertCircle, X } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ProgressData {
  progress: number;
  message: string;
  stage: string;
  type: string;
  details?: any;
}

interface ProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  progressData: ProgressData | null;
  sessionId: string;
  isConnected: boolean;
  error?: string | null;
  canCancel?: boolean;
  onCancel?: () => void;
}

export function ProgressModal({
  isOpen,
  onClose,
  title,
  progressData,
  sessionId,
  isConnected,
  error,
  canCancel = false,
  onCancel,
}: ProgressModalProps) {
  const getStageIcon = () => {
    if (error) {
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
    
    if (progressData?.progress === 100) {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    }
    
    return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
  };

  const getProgressColor = () => {
    if (error) return 'bg-red-500';
    if (progressData?.progress === 100) return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getStatusBadge = () => {
    if (error) {
      return <Badge variant="destructive">Error</Badge>;
    }
    if (!isConnected) {
      return <Badge variant="destructive">Disconnected</Badge>;
    }
    if (progressData?.progress === 100) {
      return <Badge variant="default" className="bg-green-500">Completed</Badge>;
    }
    return <Badge variant="secondary">In Progress</Badge>;
  };

  const formatStage = (stage: string) => {
    return stage
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Check if we should show the connection waiting message
  const shouldShowConnectionWaiting = !isConnected && !error && !progressData;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              {getStageIcon()}
              {title}
            </DialogTitle>
            {getStatusBadge()}
          </div>
          <DialogDescription>
            {error ? 'An error occurred during processing' : 
             progressData?.progress === 100 ? 'Operation completed successfully' :
             isConnected ? 'Processing your request...' : 'Establishing connection...'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Session Information */}
          <div className="text-sm text-muted-foreground">
            Session: <code className="bg-muted px-1 rounded text-xs">{sessionId}</code>
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Connection Status - Only show if truly waiting for connection */}
          {shouldShowConnectionWaiting && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Waiting for connection to establish...
              </AlertDescription>
            </Alert>
          )}

          {/* Progress Information */}
          {progressData && isConnected && !error && (
            <div className="space-y-3">
              {/* Current Stage */}
              <div className="text-sm">
                <div className="font-medium">{formatStage(progressData.stage)}</div>
                {progressData.message && (
                  <div className="text-muted-foreground mt-1">{progressData.message}</div>
                )}
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span>{progressData.progress}%</span>
                </div>
                <Progress 
                  value={progressData.progress} 
                  className="w-full"
                  style={{
                    '--progress-foreground': getProgressColor(),
                  } as React.CSSProperties}
                />
              </div>

              {/* Processing Type */}
              <div className="text-xs text-muted-foreground">
                Type: {progressData.type.replace('_', ' ')}
              </div>
            </div>
          )}

          {/* No Progress Data */}
          {!progressData && isConnected && !error && (
            <div className="text-center text-muted-foreground py-4">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
              <div>Initializing...</div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-between pt-4 border-t">
            <div>
              {canCancel && onCancel && progressData?.progress !== 100 && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={onCancel}
                  disabled={!isConnected}
                >
                  Cancel
                </Button>
              )}
            </div>

            <div className="flex gap-2">
              {progressData?.progress === 100 || error ? (
                <Button onClick={onClose} size="sm">
                  Close
                </Button>
              ) : (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={onClose}
                  disabled={!isConnected}
                >
                  Run in Background
                </Button>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default ProgressModal; 