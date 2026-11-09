import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { WebSocketServer } from "ws";

// https://vitejs.dev/config/
function excelCleaningPlugin() {
  return {
    name: 'excel-cleaning-api',
    configureServer(server: any) {
      server.middlewares.use(async (req: any, res: any, next: any) => {
        if (req.url?.startsWith('/api/v1/files/')) {
          try {
            const { handleExcelCleaningApi } = await import('./src/server/excel-cleaning-api');
            const handled = await handleExcelCleaningApi(req, res);
            if (handled) return;
          } catch (err) {
            console.error('API middleware error:', err);
          }
        }
        if (req.url?.startsWith('/api/v1/charts/unified')) {
          try {
            const { handleUnifiedChartApi } = await import('./src/server/unified-chart-api');
            const handled = await handleUnifiedChartApi(req, res);
            if (handled) return;
          } catch (err) {
            console.error('Unified Chart API error:', err);
          }
        }
        if (req.url?.startsWith('/api/v1/analytics/interpret') || req.url?.startsWith('/api/v1/files/interpret') || req.url?.startsWith('/api/v1/dashboard/interpret')) {
          try {
            const { handleDatasetInterpretationApi } = await import('./src/server/dataset-interpretation-api');
            const handled = await handleDatasetInterpretationApi(req, res);
            if (handled) return;
          } catch (err) {
            console.error('Dataset Interpretation API error:', err);
          }
        }
        if (req.url?.startsWith('/api/v1/analytics/')) {
          try {
            const { handleQuestionAnalysisApi } = await import('./src/server/question-analysis-api');
            const handled = await handleQuestionAnalysisApi(req, res);
            if (handled) return;
          } catch (err) {
            console.error('Analytics API middleware error:', err);
          }
        }
        if (req.url?.startsWith('/api/v1/export')) {
          try {
            const { handleExportApi } = await import('./src/server/export-api');
            const handled = await handleExportApi(req, res);
            if (handled) return;
          } catch (err) {
            console.error('Export API middleware error:', err);
          }
        }
        next();
      });

      // Integrated WebSocket server for /api/v1/ws
      const wss = new WebSocketServer({ noServer: true });

      wss.on('connection', (ws: any, req: any) => {
        ws.send(
          JSON.stringify({
            type: 'connection_established',
            data: {
              status: 'connected',
              connection_id: `ws_conn_${Date.now()}`,
              timestamp: new Date().toISOString(),
            },
            timestamp: new Date().toISOString(),
          })
        );

        ws.on('message', (message: any) => {
          try {
            const data = JSON.parse(message.toString());
            if (data.type === 'ping') {
              ws.send(
                JSON.stringify({
                  type: 'pong',
                  data: { latency_ms: 1 },
                  timestamp: new Date().toISOString(),
                })
              );
            } else if (data.type === 'subscribe') {
              const subType = data.data?.subscription || data.subscription || 'dashboard_updates';
              ws.send(
                JSON.stringify({
                  type: 'subscription_confirmed',
                  data: { subscription: subType },
                  timestamp: new Date().toISOString(),
                })
              );
            } else if (data.type === 'unsubscribe') {
              const subType = data.data?.subscription || data.subscription;
              ws.send(
                JSON.stringify({
                  type: 'unsubscription_confirmed',
                  data: { subscription: subType },
                  timestamp: new Date().toISOString(),
                })
              );
            }
          } catch {
            // ignore non-json
          }
        });

        const heartbeat = setInterval(() => {
          if (ws.readyState === 1) {
            ws.send(
              JSON.stringify({
                type: 'agent_health',
                data: { status: 'healthy', active_agents: 4, timestamp: new Date().toISOString() },
                timestamp: new Date().toISOString(),
              })
            );
          }
        }, 15000);

        ws.on('close', () => {
          clearInterval(heartbeat);
        });
      });

      server.httpServer?.on('upgrade', (request: any, socket: any, head: any) => {
        const url = request.url || '';
        if (url.includes('/api/v1/ws')) {
          wss.handleUpgrade(request, socket, head, (ws) => {
            wss.emit('connection', ws, request);
          });
        }
      });
    },
  };
}

export default defineConfig(({ mode }) => ({
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  plugins: [
    react(),
    excelCleaningPlugin(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Advanced bundle optimization
  build: {
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
    
    // Enable source maps for debugging in production
    sourcemap: mode === 'development',
    
    // Optimize bundle splitting
    rollupOptions: {
      output: {
        // Manual chunks for better caching and loading
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-slot', '@radix-ui/react-toast', '@radix-ui/react-dialog'],
          'chart-vendor': ['recharts', 'd3-scale', 'd3-interpolate'],
          'query-vendor': ['@tanstack/react-query'],
          
          // Feature chunks
          'dashboard-features': [
            './src/components/dashboard/dashboard-layout.tsx',
            './src/components/dashboard/dynamic-chart.tsx',
            './src/components/dashboard/dynamic-kpi.tsx'
          ],
          'analytics-features': [
            './src/components/analytics/advanced-filters.tsx',
            './src/components/analytics/chart-components.tsx'
          ],
          'chat-features': [
            './src/components/chat/conversational-analytics.tsx'
          ]
        },
        
        // Optimize chunk naming for better caching
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId 
            ? chunkInfo.facadeModuleId.split('/').pop()?.replace('.tsx', '').replace('.ts', '') || 'chunk'
            : 'chunk';
          return `js/${facadeModuleId}-[hash].js`;
        },
        
        // Optimize asset naming
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name || 'asset';
          const info = name.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `images/[name]-[hash][extname]`;
          }
          if (/css/i.test(ext)) {
            return `css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        }
      },
      
      // External dependencies (if needed for CDN loading)
      external: mode === 'production' ? [] : undefined
    },
    
    // Enable tree shaking
    treeshake: {
      moduleSideEffects: false
    },
    
    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: mode === 'production',
        drop_debugger: mode === 'production',
        pure_funcs: mode === 'production' ? ['console.log', 'console.info'] : undefined
      },
      mangle: {
        safari10: true
      },
      format: {
        safari10: true
      }
    },
    
    // Target modern browsers for better optimization
    target: ['es2020', 'chrome80', 'firefox78', 'safari14']
  },
  
  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'recharts',
      '@tanstack/react-query'
    ]
  },
  
  // Enable esbuild optimizations
  esbuild: {
    // Remove console logs in production
    drop: mode === 'production' ? ['console', 'debugger'] : [],
    
    // Optimize for modern browsers
    target: 'es2020'
  }
}));
