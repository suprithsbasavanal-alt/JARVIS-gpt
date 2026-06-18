import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

process.env.DIST = path.join(__dirname, '../dist')
process.env.VITE_PUBLIC = app.isPackaged ? process.env.DIST : path.join(process.env.DIST, '../public')

let win: BrowserWindow | null = null

function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 800,
    frame: false,
    transparent: true,
    titleBarStyle: 'hidden',
    vibrancy: 'hud', // Premium macOS translucent HUD effect
    visualEffectState: 'active',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  // Test active Vite Dev Server URL or load static production files
  if (process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL)
    // Open dev tools in dev mode (commented out for clean HUD view)
    // win.webContents.openDevTools({ mode: 'detach' })
  } else {
    win.loadFile(path.join(process.env.DIST, 'index.html'))
  }

  win.on('closed', () => {
    win = null
  })
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC Handler Example (e.g. system control or closing window)
ipcMain.handle('minimize-window', () => {
  win?.minimize()
})

ipcMain.handle('close-window', () => {
  win?.close()
})
