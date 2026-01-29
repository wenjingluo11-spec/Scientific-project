const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // File operations
  saveFile: (filename, content) => ipcRenderer.invoke('save-file', filename, content),
  openFile: (filename) => ipcRenderer.invoke('open-file', filename),

  // System operations
  getPlatform: () => process.platform,
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),

  // Notifications
  showNotification: (title, body) => ipcRenderer.send('show-notification', { title, body }),
});
