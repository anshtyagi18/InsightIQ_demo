import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error Boundary caught an error:', error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-[400px] flex items-center justify-center p-4">
          <Card className="w-full max-w-lg border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-700 dark:text-red-400">
                <AlertTriangle className="w-5 h-5" />
                Something went wrong
              </CardTitle>
              <CardDescription className="text-red-600 dark:text-red-300">
                An error occurred while rendering this component
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Error Details */}
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Error:</strong> {this.state.error?.message || 'Unknown error'}
                </AlertDescription>
              </Alert>

              {/* Error Info in Development */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded border">
                  <summary className="cursor-pointer text-gray-700 dark:text-gray-300 mb-2">
                    Technical Details (Development)
                  </summary>
                  <pre className="whitespace-pre-wrap text-gray-600 dark:text-gray-400 overflow-auto max-h-32">
                    {this.state.error.stack}
                  </pre>
                  {this.state.errorInfo && (
                    <pre className="whitespace-pre-wrap text-gray-600 dark:text-gray-400 overflow-auto max-h-32 mt-2">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </details>
              )}

              {/* Retry Info */}
              {this.state.retryCount > 0 && (
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Retry attempts: {this.state.retryCount}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-2">
                <Button 
                  onClick={this.handleRetry}
                  variant="outline"
                  className="flex items-center gap-2"
                  disabled={this.state.retryCount >= 3}
                >
                  <RefreshCw className="w-4 h-4" />
                  {this.state.retryCount >= 3 ? 'Max retries reached' : 'Try Again'}
                </Button>
                <Button 
                  onClick={this.handleGoHome}
                  variant="default"
                  className="flex items-center gap-2"
                >
                  <Home className="w-4 h-4" />
                  Go to Home
                </Button>
              </div>

              {/* Help Text */}
              <div className="text-xs text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700 pt-3">
                <p>If this problem persists, please:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Refresh the page</li>
                  <li>Clear your browser cache</li>
                  <li>Check your internet connection</li>
                  <li>Contact support if the issue continues</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

// High-Order Component for easier usage
export function withErrorBoundary<T extends object>(
  Component: React.ComponentType<T>,
  errorHandler?: (error: Error, errorInfo: ErrorInfo) => void
) {
  const WrappedComponent = (props: T) => (
    <ErrorBoundary onError={errorHandler}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

// Functional Error Boundary Hook (React 18+)
export function useErrorHandler() {
  return (error: Error, errorInfo?: ErrorInfo) => {
    // Log to external service
    console.error('Application Error:', error, errorInfo);
    
    // You can integrate with error reporting services here
    // e.g., Sentry, LogRocket, etc.
  };
} 