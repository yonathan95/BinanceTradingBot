import { useState, useCallback } from 'react';
import { screenshotService } from '../services';

interface UseScreenshotOptions {
  includeMetadata?: boolean;
  quality?: number;
}

interface UseScreenshotResult {
  captureFullScreen: () => Promise<string | null>;
  captureElement: (selector: string) => Promise<string | null>;
  lastScreenshotPath: string | null;
  isCapturing: boolean;
  error: Error | null;
}

/**
 * Hook for capturing screenshots of the UI
 */
export function useScreenshot(options: UseScreenshotOptions = {}): UseScreenshotResult {
  const [lastScreenshotPath, setLastScreenshotPath] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const captureFullScreen = useCallback(async (): Promise<string | null> => {
    setIsCapturing(true);
    setError(null);
    
    try {
      const screenshotPath = await screenshotService.captureFullScreen({
        includeMetadata: options.includeMetadata,
        quality: options.quality
      });
      
      if (screenshotPath) {
        setLastScreenshotPath(screenshotPath);
      }
      
      return screenshotPath;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      return null;
    } finally {
      setIsCapturing(false);
    }
  }, [options.includeMetadata, options.quality]);
  
  const captureElement = useCallback(async (selector: string): Promise<string | null> => {
    setIsCapturing(true);
    setError(null);
    
    try {
      const screenshotPath = await screenshotService.captureElement(selector, {
        includeMetadata: options.includeMetadata,
        quality: options.quality,
        captureActiveElement: true
      });
      
      if (screenshotPath) {
        setLastScreenshotPath(screenshotPath);
      }
      
      return screenshotPath;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      return null;
    } finally {
      setIsCapturing(false);
    }
  }, [options.includeMetadata, options.quality]);
  
  return {
    captureFullScreen,
    captureElement,
    lastScreenshotPath,
    isCapturing,
    error
  };
} 