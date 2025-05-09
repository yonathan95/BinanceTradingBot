import { invoke } from '@tauri-apps/api/tauri';
import { appWindow } from '@tauri-apps/api/window';
import { save } from '@tauri-apps/api/dialog';
import { writeTextFile, createDir, exists, readDir } from '@tauri-apps/api/fs';
import { desktopDir, join } from '@tauri-apps/api/path';
import html2canvas from 'html2canvas';

interface ScreenshotOptions {
  captureActiveElement?: boolean;
  includeMetadata?: boolean;
  quality?: number;
}

interface ScreenshotMetadata {
  timestamp: string;
  url: string;
  viewport: {
    width: number;
    height: number;
  };
  elementSelector?: string;
}

/**
 * Service for capturing screenshots of the UI for agent awareness
 */
export class ScreenshotService {
  private readonly screenshotsFolder = 'hive-mind-screenshots';
  private initialized = false;
  
  constructor() {
    this.init();
  }
  
  private async init() {
    try {
      // Create screenshots directory if it doesn't exist
      const desktopPath = await desktopDir();
      const screenshotsPath = await join(desktopPath, this.screenshotsFolder);
      
      if (!(await exists(screenshotsPath))) {
        await createDir(screenshotsPath, { recursive: true });
      }
      
      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize screenshot service:', error);
    }
  }
  
  /**
   * Captures a screenshot of the current UI
   */
  async captureFullScreen(options: ScreenshotOptions = {}): Promise<string | null> {
    if (!this.initialized) await this.init();
    
    try {
      // Use html2canvas to capture the full page
      const canvas = await html2canvas(document.body, {
        scale: 1,
        useCORS: true,
        logging: false,
        allowTaint: true,
        ...options
      });
      
      const screenshotData = canvas.toDataURL('image/png');
      const filePath = await this.saveScreenshot(screenshotData, options);
      return filePath;
    } catch (error) {
      console.error('Failed to capture screenshot:', error);
      return null;
    }
  }
  
  /**
   * Captures a specific element in the UI
   */
  async captureElement(selector: string, options: ScreenshotOptions = {}): Promise<string | null> {
    if (!this.initialized) await this.init();
    
    try {
      const element = document.querySelector(selector);
      if (!element) {
        console.error(`Element with selector ${selector} not found`);
        return null;
      }
      
      // Use html2canvas to capture the element
      const screenshotData = await this.captureElementToDataUrl(element as HTMLElement);
      
      const filePath = await this.saveScreenshot(
        screenshotData, 
        { ...options, captureActiveElement: true }
      );
      return filePath;
    } catch (error) {
      console.error('Failed to capture element screenshot:', error);
      return null;
    }
  }
  
  private async captureElementToDataUrl(element: HTMLElement): Promise<string> {
    const canvas = await html2canvas(element, {
      scale: 1,
      useCORS: true,
      logging: false,
      allowTaint: true
    });
    
    return canvas.toDataURL('image/png');
  }
  
  private async saveScreenshot(
    dataUrl: string, 
    options: ScreenshotOptions
  ): Promise<string> {
    const desktopPath = await desktopDir();
    const screenshotsPath = await join(desktopPath, this.screenshotsFolder);
    
    const timestamp = new Date().toISOString().replace(/:/g, '-');
    const filename = `screenshot-${timestamp}.png`;
    const filePath = await join(screenshotsPath, filename);
    
    // Convert data URL to blob data
    const base64Data = dataUrl.replace(/^data:image\/\w+;base64,/, '');
    
    // Save metadata if requested
    if (options.includeMetadata) {
      const metadata: ScreenshotMetadata = {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        },
        elementSelector: options.captureActiveElement ? document.activeElement?.tagName : undefined
      };
      
      const metadataFilePath = await join(screenshotsPath, `screenshot-${timestamp}.json`);
      await writeTextFile(metadataFilePath, JSON.stringify(metadata, null, 2));
    }
    
    // Save the screenshot
    await writeTextFile(filePath, base64Data, { append: false });
    
    console.log(`Screenshot saved to ${filePath}`);
    return filePath;
  }
  
  /**
   * Provides the latest screenshot to agents
   */
  async getLatestScreenshotForAgent(): Promise<{ path: string; base64Data?: string } | null> {
    if (!this.initialized) await this.init();
    
    try {
      const desktopPath = await desktopDir();
      const screenshotsPath = await join(desktopPath, this.screenshotsFolder);
      
      // Read the directory to find all screenshots
      const entries = await readDir(screenshotsPath);
      
      // Filter for PNG files and sort by creation time (filename contains timestamp)
      const pngFiles = entries
        .filter(entry => entry.name && entry.name.endsWith('.png'))
        .sort((a, b) => {
          // Sort in descending order (newest first)
          return (b.name || '').localeCompare(a.name || '');
        });
      
      if (pngFiles.length === 0) {
        return null;
      }
      
      // Return the most recent screenshot
      const latestScreenshot = pngFiles[0];
      return { 
        path: latestScreenshot.path
      };
    } catch (error) {
      console.error('Failed to get latest screenshot:', error);
      return null;
    }
  }
}

export const screenshotService = new ScreenshotService(); 