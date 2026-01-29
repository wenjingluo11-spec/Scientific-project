const { ipcMain, dialog, Notification, app } = require('electron');
const fs = require('fs').promises;
const path = require('path');

// File save handler
ipcMain.handle('save-file', async (event, filename, content) => {
  try {
    const { filePath, canceled } = await dialog.showSaveDialog({
      defaultPath: filename,
      filters: [
        { name: 'Markdown Files', extensions: ['md'] },
        { name: 'PDF Files', extensions: ['pdf'] },
        { name: 'Word Documents', extensions: ['docx'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });

    if (!canceled && filePath) {
      await fs.writeFile(filePath, content, 'utf-8');
      return { success: true, path: filePath };
    }
    return { success: false, canceled: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// File open handler
ipcMain.handle('open-file', async (event, filename) => {
  try {
    const { filePaths, canceled } = await dialog.showOpenDialog({
      properties: ['openFile'],
      filters: [
        { name: 'Markdown Files', extensions: ['md'] },
        { name: 'Text Files', extensions: ['txt'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });

    if (!canceled && filePaths.length > 0) {
      const content = await fs.readFile(filePaths[0], 'utf-8');
      return { success: true, content, path: filePaths[0] };
    }
    return { success: false, canceled: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Get app version
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

// Show notification
ipcMain.on('show-notification', (event, { title, body }) => {
  new Notification({ title, body }).show();
});
