import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { 
  Brain, 
  Settings, 
  Zap, 
  Monitor, 
  Image, 
  Play, 
  Pause, 
  Square, 
  Download, 
  Eye, 
  Trash2,
  Plus,
  Server,
  Activity,
  Bell,
  Moon,
  Sun,
  Wifi,
  WifiOff,
  AlertTriangle,
  CheckCircle,
  Clock,
  Layers,
  BarChart3,
  RefreshCw,
  Cog,
  Palette,
  Users,
  Database,
  TrendingUp,
  Filter,
  Search,
  MoreVertical,
  Minimize2,
  Maximize2,
  X
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

// Desktop-specific components
const TitleBar = ({ darkMode, onMinimize, onMaximize, onClose }) => {
  const [isMaximized, setIsMaximized] = useState(false);

  return (
    <div className={`h-8 ${darkMode ? 'bg-gray-900' : 'bg-gray-100'} flex items-center justify-between px-4 select-none drag-handle`}>
      <div className="flex items-center space-x-2">
        <div className="w-3 h-3 rounded-full bg-red-500"></div>
        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
        <div className="w-3 h-3 rounded-full bg-green-500"></div>
      </div>
      
      <div className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
        AI Image Generator Manager
      </div>
      
      <div className="flex items-center space-x-1 no-drag">
        <button
          onClick={onMinimize}
          className={`p-1 rounded hover:${darkMode ? 'bg-gray-800' : 'bg-gray-200'} transition-colors`}
        >
          <Minimize2 className="w-3 h-3" />
        </button>
        <button
          onClick={() => {
            setIsMaximized(!isMaximized);
            onMaximize();
          }}
          className={`p-1 rounded hover:${darkMode ? 'bg-gray-800' : 'bg-gray-200'} transition-colors`}
        >
          <Maximize2 className="w-3 h-3" />
        </button>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-red-500 hover:text-white transition-colors"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};

const DesktopNotification = ({ title, message, type = 'info', onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const getIcon = () => {
    switch (type) {
      case 'success': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default: return <Bell className="w-5 h-5 text-blue-500" />;
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg border p-4 min-w-80 max-w-96 animate-slide-in">
      <div className="flex items-start space-x-3">
        {getIcon()}
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 dark:text-white">{title}</h4>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{message}</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

// Enhanced Desktop Features
const useDesktopFeatures = () => {
  const [systemInfo, setSystemInfo] = useState(null);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Get system information if running in Electron
    if (window.electronAPI) {
      window.electronAPI.getSystemInfo().then(setSystemInfo);
      
      // Listen for menu actions
      window.electronAPI.onMenuAction((event, action, data) => {
        handleMenuAction(action, data);
      });
    }

    return () => {
      if (window.electronAPI) {
        window.electronAPI.removeMenuActionListener();
      }
    };
  }, []);

  const handleMenuAction = (action, data) => {
    switch (action) {
      case 'new-job':
        showNotification('New Job', 'Creating new image generation job...', 'info');
        break;
      case 'import-prompts':
        showNotification('Import', `Importing prompts from ${data}`, 'info');
        break;
      case 'export-results':
        showNotification('Export', `Exporting results to ${data}`, 'info');
        break;
      case 'preferences':
        showNotification('Preferences', 'Opening preferences...', 'info');
        break;
      default:
        console.log('Unknown menu action:', action);
    }
  };

  const showNotification = (title, message, type = 'info') => {
    const id = Date.now();
    const notification = { id, title, message, type };
    
    setNotifications(prev => [...prev, notification]);
    
    // Also show native notification if available
    if (window.electronAPI) {
      window.electronAPI.showNotification(title, message);
    }
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return {
    systemInfo,
    notifications,
    showNotification,
    removeNotification
  };
};

// File operations for desktop
const useFileOperations = () => {
  const saveFile = async (data, filename, filters) => {
    if (!window.electronAPI) {
      // Fallback for web
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }

    const result = await window.electronAPI.showSaveDialog({
      defaultPath: filename,
      filters: filters || [
        { name: 'JSON Files', extensions: ['json'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    if (!result.canceled) {
      // In a real app, you'd write the file here
      console.log('Would save to:', result.filePath);
      return result.filePath;
    }
  };

  const openFile = async (filters) => {
    if (!window.electronAPI) {
      return new Promise((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json,.txt';
        input.onchange = (e) => {
          const file = e.target.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsText(file);
          }
        };
        input.click();
      });
    }

    const result = await window.electronAPI.showOpenDialog({
      properties: ['openFile'],
      filters: filters || [
        { name: 'Text Files', extensions: ['txt'] },
        { name: 'JSON Files', extensions: ['json'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    if (!result.canceled && result.filePaths.length > 0) {
      // In a real app, you'd read the file here
      console.log('Would open:', result.filePaths[0]);
      return result.filePaths[0];
    }
  };

  return { saveFile, openFile };
};
import { 
  Brain, 
  Settings, 
  Zap, 
  Monitor, 
  Image, 
  Play, 
  Pause, 
  Square, 
  Download, 
  Eye, 
  Trash2,
  Plus,
  Server,
  Activity,
  Bell,
  Moon,
  Sun,
  Wifi,
  WifiOff,
  AlertTriangle,
  CheckCircle,
  Clock,
  Layers,
  BarChart3,
  RefreshCw,
  Cog,
  Palette,
  Users,
  Database,
  TrendingUp,
  Filter,
  Search,
  MoreVertical
} from 'lucide-react';

// Custom Hook para WebSocket
const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(url.replace('https:', 'wss:').replace('http:', 'ws:'));
    
    ws.onopen = () => {
      setConnected(true);
      setSocket(ws);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages(prev => [...prev.slice(-99), data]); // Keep last 100 messages
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };
    
    ws.onclose = () => {
      setConnected(false);
      setSocket(null);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, [url]);
  
  return { socket, connected, messages };
};

// Components
const Sidebar = ({ activeTab, setActiveTab, darkMode }) => {
  const menuItems = [
    { id: 'dashboard', icon: Monitor, label: 'Dashboard' },
    { id: 'prompts', icon: Brain, label: 'AI Prompts' },
    { id: 'batch', icon: Layers, label: 'Batch Jobs' },
    { id: 'providers', icon: Server, label: 'Providers' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className={`w-64 h-screen ${darkMode ? 'bg-gray-900 border-gray-700' : 'bg-white border-gray-200'} border-r flex flex-col`}>
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 ${darkMode ? 'bg-blue-600' : 'bg-blue-500'} rounded-lg flex items-center justify-center`}>
            <Image className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className={`font-bold text-lg ${darkMode ? 'text-white' : 'text-gray-900'}`}>AI Generator</h1>
            <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Desktop Manager</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
              activeTab === item.id
                ? darkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
                : darkMode ? 'text-gray-300 hover:bg-gray-800' : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
      
      <div className="p-4 border-t border-gray-700">
        <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
          Version 2.0.0 • Desktop
        </div>
      </div>
    </div>
  );
};

const StatusBar = ({ connected, darkMode, systemHealth }) => {
  return (
    <div className={`h-8 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-100 border-gray-200'} border-t flex items-center justify-between px-4 text-xs`}>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          {connected ? (
            <Wifi className="w-3 h-3 text-green-500" />
          ) : (
            <WifiOff className="w-3 h-3 text-red-500" />
          )}
          <span className={darkMode ? 'text-gray-300' : 'text-gray-700'}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        
        {systemHealth && (
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Activity className="w-3 h-3 text-blue-500" />
              <span className={darkMode ? 'text-gray-300' : 'text-gray-700'}>
                {systemHealth.active_jobs} Active
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <Clock className="w-3 h-3 text-orange-500" />
              <span className={darkMode ? 'text-gray-300' : 'text-gray-700'}>
                {systemHealth.queued_jobs} Queued
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle className="w-3 h-3 text-green-500" />
              <span className={darkMode ? 'text-gray-300' : 'text-gray-700'}>
                {systemHealth.completed_jobs_today} Today
              </span>
            </div>
          </div>
        )}
      </div>
      
      <div className={`${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
        {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

const Card = ({ title, children, darkMode, className = "", actions = null }) => (
  <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg border p-6 ${className}`}>
    {title && (
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{title}</h3>
        {actions}
      </div>
    )}
    {children}
  </div>
);

// Dashboard Component
const Dashboard = ({ darkMode, systemHealth, messages }) => {
  const [metrics, setMetrics] = useState({
    totalJobs: 0,
    successRate: 0,
    avgProcessingTime: 0,
    activeProviders: 0
  });

  const recentActivity = messages.slice(-10).reverse();

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Dashboard</h2>
          <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Monitor your AI image generation pipeline</p>
        </div>
        <button className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
          darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'
        } text-white transition-colors`}>
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card darkMode={darkMode}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Active Jobs</p>
              <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {systemHealth?.active_jobs || 0}
              </p>
            </div>
            <Activity className="w-8 h-8 text-blue-500" />
          </div>
        </Card>

        <Card darkMode={darkMode}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Queued</p>
              <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {systemHealth?.queued_jobs || 0}
              </p>
            </div>
            <Clock className="w-8 h-8 text-orange-500" />
          </div>
        </Card>

        <Card darkMode={darkMode}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Completed Today</p>
              <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {systemHealth?.completed_jobs_today || 0}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </Card>

        <Card darkMode={darkMode}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Success Rate</p>
              <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {systemHealth ? (100 - systemHealth.error_rate).toFixed(1) : 0}%
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card title="Recent Activity" darkMode={darkMode}>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {recentActivity.length > 0 ? (
            recentActivity.map((message, index) => (
              <div key={index} className={`flex items-start space-x-3 p-3 rounded-lg ${
                darkMode ? 'bg-gray-700' : 'bg-gray-50'
              }`}>
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  message.type === 'job_completed' ? 'bg-green-500' :
                  message.type === 'job_failed' ? 'bg-red-500' :
                  message.type === 'job_started' ? 'bg-blue-500' :
                  'bg-gray-500'
                }`} />
                <div className="flex-1">
                  <p className={`text-sm ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    {message.message || `${message.type?.replace('_', ' ')} event`}
                  </p>
                  <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    {new Date().toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              No recent activity
            </p>
          )}
        </div>
      </Card>
    </div>
  );
};

// AI Prompts Component
const AIPrompts = ({ darkMode }) => {
  const [theme, setTheme] = useState('');
  const [promptCount, setPromptCount] = useState(5);
  const [provider, setProvider] = useState('openai');
  const [generatedPrompts, setGeneratedPrompts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedPrompts, setSelectedPrompts] = useState([]);

  const generatePrompts = async () => {
    if (!theme.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API}/generate-prompts?theme=${encodeURIComponent(theme)}&count=${promptCount}&provider=${provider}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setGeneratedPrompts(data.prompts);
      } else {
        console.error('Failed to generate prompts');
      }
    } catch (error) {
      console.error('Error generating prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const createJobsFromPrompts = async () => {
    if (selectedPrompts.length === 0) return;
    
    for (const prompt of selectedPrompts) {
      try {
        await fetch(`${API}/jobs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt,
            provider: 'ImageFX',
            priority: 2
          })
        });
      } catch (error) {
        console.error('Error creating job:', error);
      }
    }
    
    setSelectedPrompts([]);
    alert(`Created ${selectedPrompts.length} generation jobs!`);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>AI Prompt Generator</h2>
        <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Generate creative prompts using OpenAI or Gemini</p>
      </div>

      <Card title="Generate New Prompts" darkMode={darkMode}>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                Theme/Topic
              </label>
              <input
                type="text"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                placeholder="e.g., cyberpunk city, medieval fantasy, space exploration"
                className={`w-full px-3 py-2 rounded-lg border ${
                  darkMode 
                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              />
            </div>
            
            <div>
              <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                Number of Prompts
              </label>
              <select
                value={promptCount}
                onChange={(e) => setPromptCount(parseInt(e.target.value))}
                className={`w-full px-3 py-2 rounded-lg border ${
                  darkMode 
                    ? 'bg-gray-700 border-gray-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              >
                {[3, 5, 8, 10, 15].map(num => (
                  <option key={num} value={num}>{num} prompts</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                AI Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border ${
                  darkMode 
                    ? 'bg-gray-700 border-gray-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              >
                <option value="openai">OpenAI GPT-4</option>
                <option value="gemini">Google Gemini</option>
              </select>
            </div>
          </div>
          
          <button
            onClick={generatePrompts}
            disabled={loading || !theme.trim()}
            className={`px-6 py-2 rounded-lg flex items-center space-x-2 ${
              loading || !theme.trim()
                ? darkMode ? 'bg-gray-600 text-gray-400' : 'bg-gray-300 text-gray-500'
                : darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'
            } text-white transition-colors`}
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <Brain className="w-4 h-4" />
                <span>Generate Prompts</span>
              </>
            )}
          </button>
        </div>
      </Card>

      {generatedPrompts.length > 0 && (
        <Card title="Generated Prompts" darkMode={darkMode}
          actions={
            <div className="flex space-x-2">
              <button
                onClick={() => setSelectedPrompts(generatedPrompts)}
                className={`px-3 py-1 text-sm rounded ${
                  darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200'
                } transition-colors`}
              >
                Select All
              </button>
              <button
                onClick={() => setSelectedPrompts([])}
                className={`px-3 py-1 text-sm rounded ${
                  darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200'
                } transition-colors`}
              >
                Clear
              </button>
              {selectedPrompts.length > 0 && (
                <button
                  onClick={createJobsFromPrompts}
                  className="px-3 py-1 text-sm rounded bg-blue-500 hover:bg-blue-600 text-white transition-colors"
                >
                  Create {selectedPrompts.length} Jobs
                </button>
              )}
            </div>
          }
        >
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {generatedPrompts.map((prompt, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedPrompts.includes(prompt)
                    ? darkMode ? 'bg-blue-900 border-blue-500' : 'bg-blue-50 border-blue-300'
                    : darkMode ? 'bg-gray-700 border-gray-600 hover:bg-gray-600' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                }`}
                onClick={() => {
                  setSelectedPrompts(prev => 
                    prev.includes(prompt) 
                      ? prev.filter(p => p !== prompt)
                      : [...prev, prompt]
                  );
                }}
              >
                <div className="flex items-start justify-between">
                  <p className={`flex-1 ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                    {prompt}
                  </p>
                  <input
                    type="checkbox"
                    checked={selectedPrompts.includes(prompt)}
                    onChange={() => {}}
                    className="ml-3 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

// Settings Component
const SettingsPanel = ({ darkMode, setDarkMode }) => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch(`${API}/config`);
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;
    
    setSaving(true);
    try {
      const response = await fetch(`${API}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        alert('Configuration saved successfully!');
      }
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-6">Loading configuration...</div>;
  }

  if (!config) {
    return <div className="p-6">Failed to load configuration</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Settings</h2>
        <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Configure your AI Image Generator Manager</p>
      </div>

      <Card title="API Configuration" darkMode={darkMode}>
        <div className="space-y-4">
          <div>
            <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              OpenAI API Key
            </label>
            <input
              type="password"
              value={config.openai_api_key}
              onChange={(e) => setConfig({...config, openai_api_key: e.target.value})}
              className={`w-full px-3 py-2 rounded-lg border ${
                darkMode 
                  ? 'bg-gray-700 border-gray-600 text-white' 
                  : 'bg-white border-gray-300 text-gray-900'
              } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
            />
          </div>
          
          <div>
            <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              Gemini API Key
            </label>
            <input
              type="password"
              value={config.gemini_api_key}
              onChange={(e) => setConfig({...config, gemini_api_key: e.target.value})}
              className={`w-full px-3 py-2 rounded-lg border ${
                darkMode 
                  ? 'bg-gray-700 border-gray-600 text-white' 
                  : 'bg-white border-gray-300 text-gray-900'
              } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
            />
          </div>
          
          <div>
            <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              Gemini OR API Key
            </label>
            <input
              type="password"
              value={config.gemini_or_api_key}
              onChange={(e) => setConfig({...config, gemini_or_api_key: e.target.value})}
              className={`w-full px-3 py-2 rounded-lg border ${
                darkMode 
                  ? 'bg-gray-700 border-gray-600 text-white' 
                  : 'bg-white border-gray-300 text-gray-900'
              } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
            />
          </div>
        </div>
      </Card>

      <Card title="Application Settings" darkMode={darkMode}>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>Dark Mode</h4>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Use dark theme for the interface</p>
            </div>
            <button
              onClick={() => {
                const newDarkMode = !darkMode;
                setDarkMode(newDarkMode);
                setConfig({...config, dark_mode: newDarkMode});
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                darkMode ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                darkMode ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <h4 className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>Auto Retry</h4>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Automatically retry failed jobs</p>
            </div>
            <button
              onClick={() => setConfig({...config, auto_retry_enabled: !config.auto_retry_enabled})}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                config.auto_retry_enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                config.auto_retry_enabled ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <h4 className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>Notifications</h4>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Show desktop notifications</p>
            </div>
            <button
              onClick={() => setConfig({...config, notifications_enabled: !config.notifications_enabled})}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                config.notifications_enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                config.notifications_enabled ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                Max Retry Attempts
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={config.max_retry_attempts}
                onChange={(e) => setConfig({...config, max_retry_attempts: parseInt(e.target.value)})}
                className={`w-full px-3 py-2 rounded-lg border ${
                  darkMode 
                    ? 'bg-gray-700 border-gray-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              />
            </div>
            
            <div>
              <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                Concurrent Jobs
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={config.concurrent_jobs}
                onChange={(e) => setConfig({...config, concurrent_jobs: parseInt(e.target.value)})}
                className={`w-full px-3 py-2 rounded-lg border ${
                  darkMode 
                    ? 'bg-gray-700 border-gray-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              />
            </div>
          </div>
        </div>
      </Card>

      <div className="flex justify-end">
        <button
          onClick={saveConfig}
          disabled={saving}
          className={`px-6 py-2 rounded-lg flex items-center space-x-2 ${
            saving
              ? darkMode ? 'bg-gray-600 text-gray-400' : 'bg-gray-300 text-gray-500'
              : darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'
          } text-white transition-colors`}
        >
          {saving ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Saving...</span>
            </>
          ) : (
            <>
              <Settings className="w-4 h-4" />
              <span>Save Settings</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [darkMode, setDarkMode] = useState(true);
  const [systemHealth, setSystemHealth] = useState(null);
  
  const { connected, messages } = useWebSocket(`${API.replace('http', 'ws')}/ws`);
  const { systemInfo, notifications, showNotification, removeNotification } = useDesktopFeatures();
  const { saveFile, openFile } = useFileOperations();

  // Desktop window controls
  const handleMinimize = () => {
    if (window.electronAPI) {
      window.electronAPI.minimizeWindow();
    }
  };

  const handleMaximize = () => {
    if (window.electronAPI) {
      window.electronAPI.maximizeWindow();
    }
  };

  const handleClose = () => {
    if (window.electronAPI) {
      window.electronAPI.closeWindow();
    }
  };

  useEffect(() => {
    const loadSystemHealth = async () => {
      try {
        const response = await fetch(`${API}/health`);
        if (response.ok) {
          const health = await response.json();
          setSystemHealth(health);
        }
      } catch (error) {
        console.error('Error loading system health:', error);
      }
    };

    loadSystemHealth();
    const interval = setInterval(loadSystemHealth, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard darkMode={darkMode} systemHealth={systemHealth} messages={messages} />;
      case 'prompts':
        return <AIPrompts darkMode={darkMode} />;
      case 'batch':
        return (
          <div className="p-6">
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Batch Jobs</h2>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Manage batch image generation jobs</p>
            <div className="mt-8 text-center">
              <p className={`${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>Batch jobs component coming soon...</p>
            </div>
          </div>
        );
      case 'providers':
        return (
          <div className="p-6">
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>AI Providers</h2>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Configure and manage AI image generation providers</p>
            <div className="mt-8 text-center">
              <p className={`${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>Providers management component coming soon...</p>
            </div>
          </div>
        );
      case 'analytics':
        return (
          <div className="p-6">
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Analytics</h2>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>View detailed analytics and performance metrics</p>
            <div className="mt-8 text-center">
              <p className={`${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>Analytics component coming soon...</p>
            </div>
          </div>
        );
      case 'settings':
        return <SettingsPanel darkMode={darkMode} setDarkMode={setDarkMode} />;
      default:
        return <Dashboard darkMode={darkMode} systemHealth={systemHealth} messages={messages} />;
    }
  };

  return (
    <div className={`flex flex-col h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'} overflow-hidden`}>
      {/* Title Bar for Desktop */}
      {window.electronAPI && (
        <TitleBar 
          darkMode={darkMode}
          onMinimize={handleMinimize}
          onMaximize={handleMaximize}
          onClose={handleClose}
        />
      )}
      
      {/* Notifications */}
      {notifications.map(notification => (
        <DesktopNotification
          key={notification.id}
          title={notification.title}
          message={notification.message}
          type={notification.type}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
      
      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} darkMode={darkMode} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          {renderContent()}
        </div>
        <StatusBar connected={connected} darkMode={darkMode} systemHealth={systemHealth} />
      </div>
      </div>
    </div>
  );
}

export default App;