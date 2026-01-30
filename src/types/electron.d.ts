// Electron API Types
interface ElectronAPI {
  saveFile: (filename: string, content: string) => Promise<{
    success: boolean;
    path?: string;
    error?: string;
    canceled?: boolean;
  }>;
  openFile: (filename: string) => Promise<{
    success: boolean;
    content?: string;
    path?: string;
    error?: string;
    canceled?: boolean;
  }>;
  getPlatform: () => string;
  getAppVersion: () => Promise<string>;
  showNotification: (title: string, body: string) => void;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export {};
