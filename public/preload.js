const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  
  // Dialog methods
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  
  // External links
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // Menu actions
  onMenuAction: (callback) => ipcRenderer.on('menu-action', callback),
  removeMenuActionListener: () => ipcRenderer.removeAllListeners('menu-action'),
  
  // Notifications
  showNotification: (title, body, icon) => {
    if (Notification.permission === 'granted') {
      new Notification(title, { body, icon });
    }
  },
  
  // File system operations (limited)
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, data) => ipcRenderer.invoke('write-file', filePath, data),
  
  // Window controls
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  
  // Development
  isDev: process.env.NODE_ENV === 'development'
});