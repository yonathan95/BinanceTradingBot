import React, { useState } from 'react';
import { useScreenshot } from '../hooks/useScreenshot';

interface ScreenshotToolProps {
  selector?: string;
  onScreenshotTaken?: (path: string) => void;
}

/**
 * A component that provides UI controls for taking screenshots
 * and displays the latest screenshot path when taken
 */
export const ScreenshotTool: React.FC<ScreenshotToolProps> = ({
  selector,
  onScreenshotTaken
}) => {
  const [customSelector, setCustomSelector] = useState<string>(selector || '');
  const {
    captureFullScreen,
    captureElement,
    lastScreenshotPath,
    isCapturing,
    error
  } = useScreenshot({ includeMetadata: true });
  
  const handleCaptureFullScreen = async () => {
    const path = await captureFullScreen();
    if (path && onScreenshotTaken) {
      onScreenshotTaken(path);
    }
  };
  
  const handleCaptureElement = async () => {
    if (!customSelector) return;
    
    const path = await captureElement(customSelector);
    if (path && onScreenshotTaken) {
      onScreenshotTaken(path);
    }
  };
  
  return (
    <div className="screenshot-tool p-3 border rounded mb-4">
      <h5>UI Screenshot Tool</h5>
      <p className="text-muted small">Capture UI screenshots for agent awareness</p>
      
      <div className="d-flex gap-2 mb-3">
        <button 
          className="btn btn-primary" 
          onClick={handleCaptureFullScreen}
          disabled={isCapturing}
        >
          {isCapturing ? 'Capturing...' : 'Capture Full UI'}
        </button>
      </div>
      
      <div className="mb-3">
        <label htmlFor="element-selector" className="form-label">Element Selector</label>
        <div className="input-group">
          <input
            id="element-selector"
            type="text"
            className="form-control"
            placeholder=".className or #elementId"
            value={customSelector}
            onChange={(e) => setCustomSelector(e.target.value)}
            disabled={isCapturing}
          />
          <button 
            className="btn btn-outline-secondary" 
            onClick={handleCaptureElement}
            disabled={isCapturing || !customSelector}
          >
            Capture Element
          </button>
        </div>
      </div>
      
      {error && (
        <div className="alert alert-danger" role="alert">
          {error.message}
        </div>
      )}
      
      {lastScreenshotPath && (
        <div className="mt-3">
          <p className="mb-1 fw-bold">Latest Screenshot:</p>
          <code className="d-block p-2 bg-light rounded small">{lastScreenshotPath}</code>
        </div>
      )}
    </div>
  );
}; 